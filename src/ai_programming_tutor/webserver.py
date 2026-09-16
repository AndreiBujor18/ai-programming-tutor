"""Dependency-free localhost demo; deliberately not an internet-facing code runner."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.compatibility import analyse_compatibility
from ai_programming_tutor.exam import get_practice_exam
from ai_programming_tutor.hints import get_hint
from ai_programming_tutor.service import TutorService
from ai_programming_tutor.solutions import available_styles, reference_answer
from ai_programming_tutor.style_profile import learn_c_style


WEB_ROOT = Path(__file__).resolve().parent / "web"
MAX_REQUEST_BYTES = 60_000
SERVICE = TutorService()


def public_exercise(exercise_id: str) -> dict[str, object]:
    exercise = get_exercise(exercise_id)
    return exercise.public_view() | {
        "course": "PCLP1",
        "default_dialect": "c17",
        "solution_styles": list(available_styles(exercise)),
    }


def submit_payload(
    exercise_id: str, source: str, dialect: str, hint_level: int = 1
) -> dict[str, object]:
    if dialect != "c17":
        raise ValueError("This prototype currently accepts classic C17 only.")
    response = SERVICE.submit(exercise_id, source, hint_level, dialect=dialect)
    payload = response.to_dict(reveal_hidden=False)
    payload["progressive_hints"] = (
        [get_hint(response.candidates[0].category, level) for level in (1, 2, 3)]
        if response.candidates else []
    )
    payload["diagnosis_scope"] = "C17 rules (optional ML model not loaded)"
    payload["compatibility_warnings"] = list(analyse_compatibility(source))
    return payload


class LocalHandler(BaseHTTPRequestHandler):
    server: ThreadingHTTPServer

    def _send(self, status: int, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, value: object) -> None:
        self._send(status, json.dumps(value).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"detail": message})

    def _is_local_request(self) -> bool:
        expected = f"127.0.0.1:{self.server.server_port}"
        return self.client_address[0] == "127.0.0.1" and self.headers.get("Host") == expected

    def _valid_origin(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://127.0.0.1:{self.server.server_port}"

    def _exercise_id(self, path: str, suffix: str = "") -> str | None:
        sections = path.split("/")
        if suffix:
            if len(sections) == 4 and sections[1] == "exercises" and sections[3] == suffix:
                return sections[2]
            return None
        return sections[2] if len(sections) == 3 and sections[1] == "exercises" else None

    def do_GET(self) -> None:
        if not self._is_local_request():
            self._error(403, "This demo only accepts direct localhost requests.")
            return
        path = urlsplit(self.path).path
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/static/style.css": ("style.css", "text/css; charset=utf-8"),
            "/static/theme.js": ("theme.js", "text/javascript; charset=utf-8"),
            "/static/i18n.js": ("i18n.js", "text/javascript; charset=utf-8"),
            "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
        }
        if path in assets:
            filename, content_type = assets[path]
            self._send(200, (WEB_ROOT / filename).read_bytes(), content_type)
        elif path == "/health":
            self._json(200, {"status": "ok"})
        elif path == "/exercises":
            self._json(200, [public_exercise(exercise.id) for exercise in list_exercises()])
        elif path == "/exam":
            self._json(200, get_practice_exam().public_view())
        elif exercise_id := self._exercise_id(path):
            try:
                self._json(200, public_exercise(exercise_id))
            except KeyError:
                self._error(404, "Unknown exercise.")
        else:
            self._error(404, "Not found.")

    def _read_body(self) -> dict[str, object] | None:
        if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
            self._error(415, "Use application/json.")
            return None
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._error(413, "Invalid or oversized JSON request.")
            return None
        try:
            data = json.loads(self.rfile.read(length))
        except (UnicodeError, ValueError):
            self._error(400, "Invalid JSON.")
            return None
        if not isinstance(data, dict):
            self._error(400, "Expected a JSON object.")
            return None
        return data

    def do_POST(self) -> None:
        if not self._is_local_request() or not self._valid_origin():
            self._error(403, "Only same-origin localhost requests are accepted.")
            return
        path = urlsplit(self.path).path
        submit_id = self._exercise_id(path, "submit")
        solution_id = self._exercise_id(path, "solution")
        style_learning = path == "/style-profile/learn"
        if not submit_id and not solution_id and not style_learning:
            self._error(404, "Not found.")
            return
        if submit_id and not self.server.allow_local_execution:
            self._error(
                403,
                "Local code execution is disabled. Restart with --enable-local-execution; "
                "never expose this runner publicly.",
            )
            return
        body = self._read_body()
        if body is None:
            return
        source = body.get("source", "")
        if (
            not isinstance(source, str)
            or len(source) > 50_000
            or ((submit_id or style_learning) and not source)
        ):
            self._error(422, "Source must be a nonempty string of at most 50,000 characters.")
            return
        try:
            if style_learning:
                self._json(200, learn_c_style(source, body.get("profile")))
            elif submit_id:
                dialect = body.get("dialect", "c17")
                if dialect != "c17":
                    raise ValueError("This prototype currently accepts classic C17 only.")
                self._json(200, submit_payload(submit_id, source, dialect))
            else:
                style = body.get("style", "auto")
                if not isinstance(style, str):
                    raise ValueError("Style must be a string.")
                self._json(
                    200,
                    reference_answer(
                        get_exercise(solution_id),
                        style=style,
                        source=source,
                        profile=body.get("profile"),
                    ),
                )
        except KeyError:
            self._error(404, "Unknown exercise.")
        except ValueError as exc:
            self._error(422, str(exc))


def create_server(port: int = 8000, *, allow_local_execution: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), LocalHandler)
    server.allow_local_execution = allow_local_execution
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-only PCLP1 web demo (not a public code sandbox)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--enable-local-execution", action="store_true")
    args = parser.parse_args()
    with create_server(args.port, allow_local_execution=args.enable_local_execution) as server:
        print(f"Open http://127.0.0.1:{server.server_port}/ (Ctrl+C to stop)")
        if not args.enable_local_execution:
            print("Code execution is disabled; pass --enable-local-execution for trusted local use.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
