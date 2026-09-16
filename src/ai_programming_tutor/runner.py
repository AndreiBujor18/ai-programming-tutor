from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

from ai_programming_tutor.models import (
    CompilationResult,
    EvaluationResult,
    Exercise,
    TestResult,
)


def _normalise_output(value: str) -> str:
    return " ".join(value.split())


def _process_environment(workdir: Path) -> dict[str, str]:
    """Build a small compiler environment with a writable private temp directory."""
    environment = {
        "PATH": os.environ.get("PATH", os.defpath) if sys.platform == "win32" else "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TMP": str(workdir),
        "TEMP": str(workdir),
        "TMPDIR": str(workdir),
    }
    if sys.platform == "win32":
        # Windows process creation and MinGW may need these system locations, but
        # learner code still receives no unrelated user or application secrets.
        for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT"):
            value = os.environ.get(key)
            if value:
                environment[key] = value
    return environment


def _resource_limiter(
    cpu_seconds: int,
    memory_mb: int,
    file_mb: int,
    *,
    process_limit: int | None,
) -> Callable[[], None] | None:
    if sys.platform == "win32":
        return None

    def apply_limits() -> None:
        import resource

        memory_bytes = memory_mb * 1024 * 1024
        file_bytes = file_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if process_limit is not None and hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (process_limit, process_limit))

    return apply_limits


def _compiler_resource_limiter() -> Callable[[], None] | None:
    # RLIMIT_NPROC counts every process owned by the real user, not just this
    # subprocess tree. A low value can therefore prevent GCC from starting cc1
    # on shared hosts such as CI runners. Compilation remains bounded by CPU,
    # address-space, file-size, and wall-clock limits.
    return _resource_limiter(4, 512, 16, process_limit=None)


def _program_resource_limiter() -> Callable[[], None] | None:
    return _resource_limiter(1, 128, 1, process_limit=16)


def _terminate_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class CRunner:
    """Development-only C/C++ compiler/runner; resource limits are not a sandbox."""

    def __init__(
        self,
        *,
        compiler: str = "gcc",
        cpp_compiler: str = "g++",
        compile_timeout_seconds: float = 4.0,
        run_timeout_seconds: float = 1.0,
        max_source_bytes: int = 50_000,
        max_output_bytes: int = 32_000,
    ) -> None:
        self.compiler = compiler
        self.cpp_compiler = cpp_compiler
        self.compile_timeout_seconds = compile_timeout_seconds
        self.run_timeout_seconds = run_timeout_seconds
        self.max_source_bytes = max_source_bytes
        self.max_output_bytes = max_output_bytes

    def evaluate(self, source: str, exercise: Exercise, *, dialect: str = "c17") -> EvaluationResult:
        if dialect not in {"c17", "cpp17"}:
            raise ValueError("Dialect must be c17 or cpp17.")
        encoded = source.encode("utf-8")
        if len(encoded) > self.max_source_bytes:
            compilation = CompilationResult(
                succeeded=False,
                return_code=None,
                stderr=f"Source exceeds the {self.max_source_bytes}-byte limit.",
            )
            return EvaluationResult(exercise.id, compilation)

        with tempfile.TemporaryDirectory(prefix="aptutor-") as temp_directory:
            workdir = Path(temp_directory)
            source_path = workdir / ("submission.cpp" if dialect == "cpp17" else "submission.c")
            executable_path = workdir / ("submission.exe" if sys.platform == "win32" else "submission")
            source_path.write_text(source, encoding="utf-8")
            compilation = self._compile(source_path, executable_path, workdir, dialect)
            if not compilation.succeeded:
                return EvaluationResult(exercise.id, compilation)

            results = tuple(
                self._run_test(executable_path, case.name, case.input, case.expected, case.hidden, workdir)
                for case in exercise.tests
            )
            return EvaluationResult(exercise.id, compilation, results)

    def _compile(
        self, source: Path, executable: Path, workdir: Path, dialect: str
    ) -> CompilationResult:
        compiler = self.cpp_compiler if dialect == "cpp17" else self.compiler
        compiler_path = shutil.which(compiler)
        if compiler_path is None:
            return CompilationResult(False, None, stderr=f"Compiler '{compiler}' was not found.")
        command = [
            compiler_path,
            "-std=c++17" if dialect == "cpp17" else "-std=c17",
            "-O0",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-fdiagnostics-color=never",
            source.name,
            "-o",
            executable.name,
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=workdir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                preexec_fn=_compiler_resource_limiter(),
                env=_process_environment(workdir),
            )
        except FileNotFoundError:
            return CompilationResult(False, None, stderr=f"Compiler '{compiler}' was not found.")

        try:
            stdout, stderr = process.communicate(timeout=self.compile_timeout_seconds)
        except subprocess.TimeoutExpired:
            _terminate_group(process)
            stdout, stderr = process.communicate()
            return CompilationResult(
                False,
                process.returncode,
                self._decode(stdout),
                self._decode(stderr) or "Compilation timed out.",
                timed_out=True,
            )

        return CompilationResult(
            process.returncode == 0,
            process.returncode,
            self._decode(stdout),
            self._decode(stderr),
        )

    def _run_test(
        self,
        executable: Path,
        name: str,
        test_input: str,
        expected: str,
        hidden: bool,
        workdir: Path,
    ) -> TestResult:
        started = time.perf_counter()
        stdout_path = workdir / "program.stdout"
        stderr_path = workdir / "program.stderr"
        with stdout_path.open("w+b") as stdout_file, stderr_path.open("w+b") as stderr_file:
            try:
                process = subprocess.Popen(
                    [str(executable)],
                    cwd=workdir,
                    stdin=subprocess.PIPE,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    start_new_session=True,
                    preexec_fn=_program_resource_limiter(),
                    env=_process_environment(workdir),
                )
            except OSError as exc:
                return TestResult(name, hidden, "runtime_error", expected, "", str(exc), None, 0.0)

            try:
                process.communicate(
                    input=test_input.encode("utf-8"), timeout=self.run_timeout_seconds
                )
                timed_out = False
            except subprocess.TimeoutExpired:
                _terminate_group(process)
                process.communicate()
                timed_out = True

            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(self.max_output_bytes + 1)
            stderr = stderr_file.read(self.max_output_bytes + 1)

        duration_ms = (time.perf_counter() - started) * 1000
        actual_text = self._decode(stdout)
        stderr_text = self._decode(stderr)
        if timed_out:
            status = "timeout"
        elif process.returncode != 0:
            status = "runtime_error"
        elif _normalise_output(actual_text) == _normalise_output(expected):
            status = "passed"
        else:
            status = "wrong_answer"
        return TestResult(
            name,
            hidden,
            status,
            expected,
            actual_text,
            stderr_text,
            process.returncode,
            round(duration_ms, 3),
        )

    def _decode(self, value: bytes) -> str:
        decoded = value[: self.max_output_bytes].decode("utf-8", errors="replace")
        if len(value) > self.max_output_bytes:
            decoded += "\n[output truncated]"
        return decoded
