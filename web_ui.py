import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


STATIC_DIR = Path(__file__).parent / "webui"
INDEX_FILE = STATIC_DIR / "index.html"
SELECTOR_KEYS = ("q_L", "q_R", "q_M", "q_C", "q_O")


def parse_selector_rows(source: str) -> list[list[int]]:
    rows = []
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            parts = [item.strip() for item in line[1:-1].split(",")]
        else:
            parts = line.replace(",", " ").split()

        if len(parts) != 5:
            raise ValueError(f"Line {line_number} must contain exactly 5 values: q_L q_R q_M q_C q_O.")

        try:
            values = [int(part) for part in parts]
        except ValueError as exc:
            raise ValueError(f"Line {line_number} contains a non-integer value.") from exc

        rows.append(values)

    if not rows:
        raise ValueError("Please enter at least one selector row.")
    return rows


def term_text(coefficient: int, term: str) -> str:
    if coefficient == 0:
        return ""
    if coefficient == 1:
        return term
    if coefficient == -1:
        return f"-{term}"
    return f"{coefficient}·{term}"


def constant_text(value: int) -> str:
    if value == 0:
        return ""
    return str(value)


def build_equation(row: list[int]) -> str:
    q_l, q_r, q_m, q_c, q_o = row
    parts = [
        term_text(q_l, "w_a"),
        term_text(q_r, "w_b"),
        term_text(q_m, "w_a·w_b"),
        constant_text(q_c),
        term_text(-q_o, "w_c"),
    ]
    filtered = [part for part in parts if part]
    if not filtered:
        return "0 = 0"

    expression = filtered[0]
    for part in filtered[1:]:
        if part.startswith("-"):
            expression += f" - {part[1:]}"
        else:
            expression += f" + {part}"
    return f"{expression} = 0"


def classify_row(row: list[int]) -> str:
    q_l, q_r, q_m, q_c, q_o = row
    if q_m != 0:
        return "Multiplication"
    if q_l or q_r or q_c:
        return "Linear"
    if q_o:
        return "Output"
    return "Empty"


def generate_payload(selector_source: str, group_order_input: str | None) -> dict:
    rows = parse_selector_rows(selector_source)
    default_group_order = len(rows)

    if group_order_input in (None, ""):
        group_order = default_group_order
    else:
        group_order = int(group_order_input)

    if group_order < len(rows):
        raise ValueError(f"Group order must be at least {len(rows)}.")

    selectors = []
    active_counts = dict.fromkeys(SELECTOR_KEYS, 0)

    for index, row in enumerate(rows, start=1):
        selector_map = dict(zip(SELECTOR_KEYS, row))
        for key, value in selector_map.items():
            if value != 0:
                active_counts[key] += 1

        selectors.append(
            {
                "index": index,
                "selectors": selector_map,
                "equation": build_equation(row),
                "kind": classify_row(row),
                "binary": all(value in (0, 1) for value in row),
            }
        )

    return {
        "summary": {
            "constraint_count": len(rows),
            "group_order": group_order,
            "binary_rows": sum(1 for row in rows if all(value in (0, 1) for value in row)),
            "active_counts": active_counts,
        },
        "selectors": selectors,
    }


class PlonkWebHandler(BaseHTTPRequestHandler):
    server_version = "BabyPlonkWeb/0.2"

    def do_HEAD(self):
        self._handle_request(include_body=False)

    def do_GET(self):
        self._handle_request(include_body=True)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            payload = json.loads(raw_body.decode("utf-8"))
            result = generate_payload(
                selector_source=payload.get("selectors", ""),
                group_order_input=payload.get("group_order"),
            )
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body."}, status=HTTPStatus.BAD_REQUEST)
            return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json(result)

    def log_message(self, format, *args):
        return

    def _handle_request(self, include_body: bool):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_file(INDEX_FILE, include_body=include_body)
            return
        if parsed.path.startswith("/static/"):
            relative_path = parsed.path.removeprefix("/static/")
            self._serve_file(STATIC_DIR / relative_path, include_body=include_body)
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND, include_body=include_body)

    def _serve_file(self, file_path: Path, include_body: bool = True):
        if not file_path.exists() or not file_path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND, include_body=include_body)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        else:
            content_type = content_type or "application/octet-stream"

        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if include_body:
            self.wfile.write(data)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK, include_body: bool = True):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if include_body:
            self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser(description="Run the Baby PlonK selector visualizer web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), PlonkWebHandler)
    print(f"Baby PlonK web UI running at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
