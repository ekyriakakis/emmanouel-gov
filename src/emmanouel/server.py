from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .state import EmmanouelState

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"
STATE = EmmanouelState()


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "EmmanouelHTTP/1.0"

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload, status=HTTPStatus.OK):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/dashboard":
            return self._send_json(STATE.dashboard_snapshot())
        if parsed.path == "/api/policies":
            return self._send_json(list(STATE.policies.values()))
        if parsed.path == "/api/wallet":
            holder_id = parse_qs(parsed.query).get("holder_id", [""])[0]
            if not holder_id:
                return self._send_json({"error": "holder_id_required"}, HTTPStatus.BAD_REQUEST)
            return self._send_json(STATE.wallet_view(holder_id))
        return self._serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/api/register/citizen":
                result = STATE.register_citizen(body["full_name"], body["tax_id"], body["email"])
                return self._send_json(result, HTTPStatus.CREATED)
            if parsed.path == "/api/register/enterprise":
                result = STATE.register_enterprise(body["legal_name"], body["tax_id"], body["representative_holder_id"])
                return self._send_json(result, HTTPStatus.CREATED)
            if parsed.path == "/api/citizen/deceased":
                result = STATE.mark_citizen_deceased(body["citizen_id"], body["requested_by"], body["relation"])
                return self._send_json(result)
            if parsed.path == "/api/certificates":
                result = STATE.issue_certificate(body["holder_id"], body["type"], body.get("data", {}))
                return self._send_json(result, HTTPStatus.CREATED)
            if parsed.path == "/api/policies":
                result = STATE.publish_policy(body["title"], body["summary"], body["details"])
                return self._send_json(result, HTTPStatus.CREATED)
            if parsed.path.startswith("/api/policies/") and parsed.path.endswith("/comment"):
                policy_id = int(parsed.path.split("/")[3])
                result = STATE.add_policy_comment(policy_id, body["author"], body["text"])
                return self._send_json(result, HTTPStatus.CREATED)
            if parsed.path.startswith("/api/policies/") and parsed.path.endswith("/vote"):
                policy_id = int(parsed.path.split("/")[3])
                result = STATE.vote_policy(policy_id, body["holder_id"], body["vote"])
                return self._send_json(result)
        except KeyError as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        return self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def _serve_static(self, path: str):
        if path in ("/", ""):
            path = "/index.html"
        file_path = (WEB_DIR / path.lstrip("/")).resolve()
        if not str(file_path).startswith(str(WEB_DIR)) or not file_path.exists() or not file_path.is_file():
            return self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

        content = file_path.read_bytes()
        content_type = "text/plain"
        if file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Emmanouel platform running on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
