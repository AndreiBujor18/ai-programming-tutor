"""Single-job stdin/stdout entry point used inside the disposable worker image."""

from __future__ import annotations

import json
import sys

from ai_programming_tutor.worker_protocol import (
    MAX_WORKER_JOB_BYTES,
    evaluate_worker_job,
)


def main() -> None:
    payload = sys.stdin.buffer.read(MAX_WORKER_JOB_BYTES + 1)
    if len(payload) > MAX_WORKER_JOB_BYTES:
        print("Worker job exceeds the transport limit.", file=sys.stderr)
        raise SystemExit(2)
    try:
        value = json.loads(payload.decode("utf-8"))
        result = evaluate_worker_job(value)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Worker rejected the job: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
