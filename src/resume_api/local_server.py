"""Local dev server -- lets another application develop against this API
without any AWS infrastructure.

Translates real HTTP requests into the same API-Gateway-HTTP-API (payload
2.0) event shape resume_api.app.handler already expects, and translates
its response dict back into a real HTTP response. Not used by Lambda;
only entrypoint is `python -m resume_api.local_server`.

Point DynamoDB at a local instance (e.g. DynamoDB Local via
docker-compose) with the standard AWS_ENDPOINT_URL_DYNAMODB env var --
boto3 already honors it, no code change needed here or in db.py.
"""

from __future__ import annotations

import base64
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

# Must be set before importing resume_api.app -- it reads this at import
# time to decide whether to turn CORS on.
os.environ.setdefault("LOCAL_DEV", "1")

from resume_api.app import handler  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    def _handle(self, method: str) -> None:
        split = urlsplit(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length else b""
        body, is_base64 = _encode_body(raw_body)
        query_params = dict(parse_qsl(split.query))

        event = {
            "version": "2.0",
            "routeKey": f"{method} {split.path}",
            "rawPath": split.path,
            "rawQueryString": split.query,
            "headers": {key.lower(): value for key, value in self.headers.items()},
            "queryStringParameters": query_params or None,
            "requestContext": {
                "stage": "$default",
                "http": {"method": method, "path": split.path},
            },
            "body": body,
            "isBase64Encoded": is_base64,
        }

        response = handler(event, {})
        self._write_response(response)

    def _write_response(self, response: dict) -> None:
        self.send_response(response.get("statusCode", 200))
        headers = response.get("headers") or {}
        response_body = response.get("body") or ""
        payload = (
            base64.b64decode(response_body)
            if response.get("isBase64Encoded")
            else response_body.encode()
        )
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def do_PUT(self) -> None:
        self._handle("PUT")

    def do_DELETE(self) -> None:
        self._handle("DELETE")

    def do_PATCH(self) -> None:
        self._handle("PATCH")

    def do_OPTIONS(self) -> None:
        self._handle("OPTIONS")

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        print(f"{self.address_string()} - {format % args}")


def _encode_body(raw: bytes) -> tuple[str | None, bool]:
    if not raw:
        return None, False
    try:
        return raw.decode("utf-8"), False
    except UnicodeDecodeError:
        return base64.b64encode(raw).decode(), True


def _ensure_table_exists(table_name: str, attempts: int = 10, delay_seconds: float = 1.0) -> None:
    import boto3
    from botocore.exceptions import ClientError

    client = boto3.client("dynamodb")
    for attempt in range(1, attempts + 1):
        try:
            client.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {"AttributeName": "pk", "AttributeType": "S"},
                    {"AttributeName": "sk", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            print(f"Created local table {table_name!r}")
            return
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code == "ResourceInUseException":
                return
            if attempt == attempts:
                raise
            print(f"Waiting for local DynamoDB ({attempt}/{attempts})...")
            time.sleep(delay_seconds)


def main() -> None:
    table_name = os.environ.get("TABLE_NAME", "resume-api")
    _ensure_table_exists(table_name)

    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    print(f"resume-api listening on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
