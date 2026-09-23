from __future__ import annotations

import os
import shutil
import signal
import stat
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
    FileResult,
    TestCase,
    TestFile,
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


def _subprocess_setup(
    limiter: Callable[[], None] | None,
    execution_uid: int | None,
) -> Callable[[], None] | None:
    """Apply resource limits, then irreversibly select the untrusted UID."""
    if sys.platform == "win32" or (limiter is None and execution_uid is None):
        return None

    def apply_setup() -> None:
        if limiter is not None:
            limiter()
        if execution_uid is not None:
            # Set the real, effective, and saved IDs together. The worker grants
            # CAP_SETUID and CAP_KILL only to its trusted namespace-root
            # controller; changing all real/effective/saved UIDs to a nonzero
            # value clears capabilities, and no-new-privileges prevents the
            # submitted program from gaining them.
            if hasattr(os, "setresuid"):
                os.setresuid(execution_uid, execution_uid, execution_uid)
            else:
                os.setuid(execution_uid)

    return apply_setup


def _terminate_group(process: subprocess.Popen[bytes]) -> None:
    try:
        if sys.platform == "win32":
            if process.poll() is None:
                process.kill()
        else:
            # The group may still contain descendants after its leader exits.
            os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        pass


def _clear_isolated_pid_namespace(enabled: bool) -> None:
    """Kill and reap every process other than the worker controller.

    A submitted program can call ``setsid()`` after ``fork()`` and thereby
    leave the process group used for ordinary timeout cleanup.  The disposable
    worker runs its controller as PID 1 in a private PID namespace and grants
    that controller CAP_KILL, so it can clear the entire namespace between
    compiler/test invocations.  Refuse to perform this broad operation anywhere
    else; ``kill(-1, ...)`` must never be usable from the development runner.
    """
    if not enabled:
        return
    if sys.platform != "linux" or os.getpid() != 1:
        raise RuntimeError("Isolated PID cleanup requires a Linux PID 1 controller.")

    try:
        os.kill(-1, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        raise RuntimeError("Isolated PID namespace cleanup failed.") from exc

    deadline = time.monotonic() + 1.0
    while True:
        try:
            child_pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        except OSError as exc:
            raise RuntimeError("Isolated PID namespace cleanup failed.") from exc
        if child_pid != 0:
            continue
        # Close the fork-vs-kill race: a task created near the first namespace
        # sweep may only become an adopted PID 1 child afterwards.
        try:
            os.kill(-1, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            raise RuntimeError("Isolated PID namespace cleanup failed.") from exc
        if time.monotonic() >= deadline:
            raise RuntimeError("Isolated PID namespace cleanup timed out.")
        time.sleep(0.01)


def _read_regular_file(path: Path, max_bytes: int) -> tuple[str | None, bytes]:
    """Read a bounded regular file without following a final symbolic link."""
    try:
        path_stat = path.lstat()
    except FileNotFoundError:
        return "missing", b""
    except OSError:
        return "unreadable", b""
    if not stat.S_ISREG(path_stat.st_mode):
        return "invalid_type", b""

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return "missing", b""
    except OSError:
        return "unreadable", b""
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode) or (
            opened_stat.st_dev,
            opened_stat.st_ino,
        ) != (path_stat.st_dev, path_stat.st_ino):
            return "invalid_type", b""
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            content = stream.read(max_bytes + 1)
    except OSError:
        return "unreadable", b""
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > max_bytes:
        return "output_limit", content
    return None, content


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
        execution_uid: int | None = None,
        isolated_pid_namespace: bool = False,
    ) -> None:
        if execution_uid is not None and (
            isinstance(execution_uid, bool) or not isinstance(execution_uid, int)
        ):
            raise ValueError("Execution UID must be an integer or None.")
        if execution_uid is not None and execution_uid <= 0:
            raise ValueError("Execution UID must be a positive non-root UID.")
        if execution_uid is not None and sys.platform == "win32":
            raise ValueError("Execution UID separation requires a POSIX worker.")
        if not isinstance(isolated_pid_namespace, bool):
            raise ValueError("PID namespace isolation flag must be a boolean.")
        if isolated_pid_namespace and execution_uid is None:
            raise ValueError("PID namespace cleanup requires an untrusted UID.")
        self.compiler = compiler
        self.cpp_compiler = cpp_compiler
        self.compile_timeout_seconds = compile_timeout_seconds
        self.run_timeout_seconds = run_timeout_seconds
        self.max_source_bytes = max_source_bytes
        self.max_output_bytes = max_output_bytes
        self.execution_uid = execution_uid
        self.isolated_pid_namespace = isolated_pid_namespace

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
            if self.execution_uid is not None:
                # The controller and submitted processes keep the same primary
                # group. Group access is therefore limited to this disposable
                # workspace while their differing UIDs protect controller files
                # and process descriptors from the submitted program.
                workdir.chmod(0o770)
            source_path = workdir / ("submission.cpp" if dialect == "cpp17" else "submission.c")
            executable_path = workdir / ("submission.exe" if sys.platform == "win32" else "submission")
            source_path.write_text(source, encoding="utf-8")
            compilation = self._compile(source_path, executable_path, workdir, dialect)
            if not compilation.succeeded:
                return EvaluationResult(exercise.id, compilation)

            results = []
            for index, case in enumerate(exercise.tests):
                with tempfile.TemporaryDirectory(
                    prefix=f"case-{index:03d}-", dir=workdir
                ) as case_directory:
                    case_workdir = Path(case_directory)
                    if self.execution_uid is not None:
                        case_workdir.chmod(0o770)
                    try:
                        for fixture in case.fixtures:
                            with (case_workdir / fixture.name).open("xb") as stream:
                                stream.write(fixture.content.encode("utf-8"))
                    except OSError:
                        results.append(
                            TestResult(
                                case.name,
                                case.hidden,
                                "runtime_error",
                                case.expected,
                                "",
                                "The test workspace could not be prepared.",
                                None,
                                0.0,
                            )
                        )
                    else:
                        results.append(self._run_test(executable_path, case, case_workdir))
            return EvaluationResult(exercise.id, compilation, tuple(results))

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
                preexec_fn=_subprocess_setup(
                    _compiler_resource_limiter(), self.execution_uid
                ),
                env=_process_environment(workdir),
            )
        except FileNotFoundError:
            return CompilationResult(False, None, stderr=f"Compiler '{compiler}' was not found.")
        except (OSError, subprocess.SubprocessError):
            return CompilationResult(
                False,
                None,
                stderr="Compiler execution could not be isolated.",
            )

        try:
            stdout, stderr = process.communicate(timeout=self.compile_timeout_seconds)
        except subprocess.TimeoutExpired:
            _terminate_group(process)
            stdout, stderr = process.communicate()
            _clear_isolated_pid_namespace(self.isolated_pid_namespace)
            return CompilationResult(
                False,
                process.returncode,
                self._decode(stdout),
                self._decode(stderr) or "Compilation timed out.",
                timed_out=True,
            )

        _clear_isolated_pid_namespace(self.isolated_pid_namespace)

        return CompilationResult(
            process.returncode == 0,
            process.returncode,
            self._decode(stdout),
            self._decode(stderr),
        )

    def _run_test(
        self,
        executable: Path,
        case: TestCase,
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
                    preexec_fn=_subprocess_setup(
                        _program_resource_limiter(), self.execution_uid
                    ),
                    env=_process_environment(workdir),
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return TestResult(
                    case.name,
                    case.hidden,
                    "runtime_error",
                    case.expected,
                    "",
                    str(exc),
                    None,
                    0.0,
                )

            try:
                process.communicate(
                    input=case.input.encode("utf-8"), timeout=self.run_timeout_seconds
                )
                timed_out = False
            except subprocess.TimeoutExpired:
                _terminate_group(process)
                process.communicate()
                timed_out = True
            finally:
                if sys.platform != "win32":
                    _terminate_group(process)
                _clear_isolated_pid_namespace(self.isolated_pid_namespace)

            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read(self.max_output_bytes + 1)
            stderr = stderr_file.read(self.max_output_bytes + 1)

        duration_ms = (time.perf_counter() - started) * 1000
        actual_text = self._decode(stdout)
        stderr_text = self._decode(stderr)
        file_results = tuple(
            self._inspect_file(workdir, expected_file)
            for expected_file in case.expected_files
        )
        if timed_out:
            status = "timeout"
        elif process.returncode != 0:
            status = "runtime_error"
        elif (
            _normalise_output(actual_text) == _normalise_output(case.expected)
            and all(result.status == "passed" for result in file_results)
        ):
            status = "passed"
        else:
            status = "wrong_answer"
        return TestResult(
            case.name,
            case.hidden,
            status,
            case.expected,
            actual_text,
            stderr_text,
            process.returncode,
            round(duration_ms, 3),
            file_results,
        )

    def _inspect_file(self, workdir: Path, expected_file: TestFile) -> FileResult:
        read_status, content = _read_regular_file(
            workdir / expected_file.name, self.max_output_bytes
        )
        if read_status is not None:
            actual = self._decode(content)
            status = read_status
        else:
            try:
                actual = content.decode("utf-8")
            except UnicodeDecodeError:
                actual = self._decode(content)
                status = "invalid_encoding"
            else:
                status = (
                    "passed"
                    if _normalise_output(actual) == _normalise_output(expected_file.content)
                    else "wrong_answer"
                )
        return FileResult(expected_file.name, status, expected_file.content, actual)

    def _decode(self, value: bytes) -> str:
        decoded = value[: self.max_output_bytes].decode("utf-8", errors="replace")
        if len(value) > self.max_output_bytes:
            decoded += "\n[output truncated]"
        return decoded
