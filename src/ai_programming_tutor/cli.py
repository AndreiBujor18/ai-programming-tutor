from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_programming_tutor.catalog import list_exercises
from ai_programming_tutor.service import TutorService


def _read_bounded_utf8(path: Path, max_bytes: int, label: str) -> str:
    if not path.is_file():
        raise ValueError(f"{label} must be a regular file.")
    with path.open("rb") as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError(f"{label} exceeds the {max_bytes}-byte limit.")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} must be UTF-8 text.") from exc


def _command_list(_: argparse.Namespace) -> int:
    for exercise in list_exercises():
        public_count = sum(not case.hidden for case in exercise.tests)
        hidden_count = sum(case.hidden for case in exercise.tests)
        print(f"{exercise.id:22} {exercise.title} ({public_count} public, {hidden_count} hidden)")
    return 0


def _command_evaluate(args: argparse.Namespace) -> int:
    source = args.source.read_text(encoding="utf-8")
    response = TutorService(model_path=args.model).submit(args.exercise_id, source, args.hint_level)
    if args.json:
        print(json.dumps(response.to_dict(reveal_hidden=args.reveal_hidden), indent=2))
        return 0 if response.evaluation.all_passed else 1

    matching = next(exercise for exercise in list_exercises() if exercise.id == args.exercise_id)
    result = response.evaluation
    print(f"Exercise: {matching.title}")
    if not result.compilation.succeeded:
        print("Compilation: failed")
        print(result.compilation.stderr.rstrip())
    else:
        print("Compilation: succeeded")
        print(f"Tests: {result.passed_count}/{result.total_count} passed")
        for test in result.tests:
            visibility = "hidden" if test.hidden else "public"
            print(f"  - {test.name} [{visibility}]: {test.status}")
    if response.candidates:
        likely = response.candidates[0]
        print(f"Likely issue: {likely.category} ({likely.confidence:.0%})")
        print(f"Evidence: {likely.evidence}")
        print(f"Hint {response.hint_level}: {response.hint}")
    elif result.all_passed:
        print("No hint needed: all tests pass.")
    return 0 if result.all_passed else 1


def _command_generate_data(args: argparse.Namespace) -> int:
    from ai_programming_tutor.dataset import generate_dataset

    count = generate_dataset(args.output, variants=args.variants, evaluate=not args.no_signals)
    print(f"Wrote {count} labeled samples to {args.output}")
    return 0


def _command_train(args: argparse.Namespace) -> int:
    from ai_programming_tutor.baseline import train_baseline

    metrics = train_baseline(args.dataset, args.model, args.metrics, args.confusion_matrix)
    print(json.dumps(metrics, indent=2))
    return 0


def _command_evaluate_natural(args: argparse.Namespace) -> int:
    from ai_programming_tutor.natural_evaluation import evaluate_natural_dataset

    report = evaluate_natural_dataset(args.dataset, args.output, args.model)
    print(json.dumps(report, indent=2))
    return 0


def _command_run_isolated(args: argparse.Namespace) -> int:
    from ai_programming_tutor.worker_protocol import (
        MAX_WORKER_SOURCE_BYTES,
        create_worker_job,
        run_docker_worker,
        write_worker_result,
    )

    source = _read_bounded_utf8(
        args.source,
        MAX_WORKER_SOURCE_BYTES,
        "Worker source",
    )
    if args.source.resolve() == args.output.resolve():
        raise ValueError("Worker source and result paths must differ.")
    job = create_worker_job(args.exercise_id, source)
    result = run_docker_worker(
        job,
        image=args.image,
        docker_executable=args.docker,
        timeout_seconds=args.timeout,
    )
    write_worker_result(args.output, result, job)
    print(json.dumps(result, indent=2))
    return 0


def _command_audit_isolated(args: argparse.Namespace) -> int:
    from ai_programming_tutor.worker_audit import (
        run_worker_adversarial_audit,
        write_worker_audit_report,
    )

    report = run_worker_adversarial_audit(
        image=args.image,
        docker_executable=args.docker,
        timeout_seconds=args.timeout,
    )
    write_worker_audit_report(args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


def _command_inspect_host(args: argparse.Namespace) -> int:
    from ai_programming_tutor.host_preflight import (
        inspect_worker_host,
        write_host_preflight_report,
    )

    report = inspect_worker_host(docker_executable=args.docker)
    write_host_preflight_report(args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "automated_ready" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aptutor", description="AI Programming Tutor prototype")
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_parser = subcommands.add_parser("list", help="List available exercises")
    list_parser.set_defaults(handler=_command_list)

    evaluate_parser = subcommands.add_parser("evaluate", help="Compile and evaluate a C submission")
    evaluate_parser.add_argument("exercise_id")
    evaluate_parser.add_argument("source", type=Path)
    evaluate_parser.add_argument("--hint-level", type=int, choices=(1, 2, 3), default=1)
    evaluate_parser.add_argument("--json", action="store_true")
    evaluate_parser.add_argument("--model", type=Path, help="Optional trained baseline .joblib file")
    evaluate_parser.add_argument("--reveal-hidden", action="store_true", help="Development use only")
    evaluate_parser.set_defaults(handler=_command_evaluate)

    data_parser = subcommands.add_parser("generate-data", help="Generate controlled buggy solutions")
    data_parser.add_argument("--output", type=Path, default=Path("data/synthetic_bugs.jsonl"))
    data_parser.add_argument("--variants", type=int, default=16)
    data_parser.add_argument("--no-signals", action="store_true", help="Skip compilation and test signals")
    data_parser.set_defaults(handler=_command_generate_data)

    train_parser = subcommands.add_parser("train", help="Train the interpretable ML baseline")
    train_parser.add_argument("--dataset", type=Path, default=Path("data/synthetic_bugs.jsonl"))
    train_parser.add_argument("--model", type=Path, default=Path("artifacts/baseline.joblib"))
    train_parser.add_argument("--metrics", type=Path, default=Path("artifacts/metrics.json"))
    train_parser.add_argument(
        "--confusion-matrix", type=Path, default=Path("artifacts/confusion_matrix.csv")
    )
    train_parser.set_defaults(handler=_command_train)

    natural_parser = subcommands.add_parser(
        "evaluate-natural",
        help="Evaluate a private frozen natural-code set from precomputed signals",
    )
    natural_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("private_evaluation/natural_samples.jsonl"),
    )
    natural_parser.add_argument(
        "--output",
        type=Path,
        default=Path("private_evaluation/aggregate_metrics.json"),
    )
    natural_parser.add_argument(
        "--model",
        type=Path,
        help="Optional controlled-mutation baseline .joblib file",
    )
    natural_parser.set_defaults(handler=_command_evaluate_natural)

    worker_parser = subcommands.add_parser(
        "run-isolated",
        help="Run one C17 submission in a fresh no-network worker container",
    )
    worker_parser.add_argument("exercise_id")
    worker_parser.add_argument("source", type=Path)
    worker_parser.add_argument(
        "--image",
        required=True,
        help="Immutable worker image ID or repository@sha256 digest",
    )
    worker_parser.add_argument(
        "--output",
        type=Path,
        default=Path("private_evaluation/worker_result.json"),
    )
    worker_parser.add_argument(
        "--docker",
        default="docker",
        help="Container runtime executable with Docker-compatible arguments",
    )
    worker_parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Outer wall timeout in seconds (maximum 60)",
    )
    worker_parser.set_defaults(handler=_command_run_isolated)

    audit_parser = subcommands.add_parser(
        "audit-isolated",
        help="Run source-free adversarial probes against a pinned worker image",
    )
    audit_parser.add_argument(
        "--image",
        required=True,
        help="Immutable worker image ID or repository@sha256 digest",
    )
    audit_parser.add_argument(
        "--output",
        type=Path,
        default=Path("private_evaluation/worker_adversarial_report.json"),
    )
    audit_parser.add_argument(
        "--docker",
        default="docker",
        help="Container runtime executable with Docker-compatible arguments",
    )
    audit_parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Outer wall timeout for each probe in seconds (maximum 60)",
    )
    audit_parser.set_defaults(handler=_command_audit_isolated)

    host_parser = subcommands.add_parser(
        "inspect-host",
        help="Inspect a candidate dedicated worker host without changing it",
    )
    host_parser.add_argument(
        "--output",
        type=Path,
        default=Path("private_evaluation/host_preflight.json"),
    )
    host_parser.add_argument(
        "--docker",
        default="docker",
        help="Docker executable used only for bounded read-only inspection",
    )
    host_parser.set_defaults(handler=_command_inspect_host)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        raise SystemExit(args.handler(args))
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
