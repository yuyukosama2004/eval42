from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from eval42.adapters.http import HttpAdapter
from eval42.errors import AdapterError, ConfigError
from eval42.models import EvalCase


def _adapter(config: dict[str, Any], base_dir: Path) -> HttpAdapter:
    return HttpAdapter(
        config,
        base_dir=base_dir,
        config_hash=f"sha256:{'0' * 64}",
        revision="abc",
    )


def test_fixture_adapter_normalizes(
    tmp_path: Path,
    eval_case: EvalCase,
) -> None:
    fixture = {
        "responses": {
            eval_case.id: {
                "products": [{"product_id": 1, "price": 3999}],
                "ids": [1, 1],
                "text": "ok",
            }
        }
    }
    (tmp_path / "responses.json").write_text(json.dumps(fixture), encoding="utf-8")
    adapter = _adapter(
        {
            "base_url": "https://offline.invalid",
            "endpoint": "/evaluate",
            "fixture_path": "responses.json",
            "response_mapping": {
                "retrieved_items": "$.products",
                "recommended_ids": "$.ids",
                "answer": "$.text",
            },
        },
        tmp_path,
    )
    result = adapter.execute(eval_case)
    assert result.retrieved_items[0]["id"] == 1
    assert result.retrieved_items[0]["attributes"]["price"] == 3999
    assert result.recommended_ids == [1]
    assert result.usage["token_count_kind"] == "unavailable"


def test_fixture_errors(tmp_path: Path, eval_case: EvalCase) -> None:
    (tmp_path / "missing.json").write_text('{"responses": {}}', encoding="utf-8")
    adapter = _adapter(
        {
            "base_url": "https://offline.invalid",
            "endpoint": "/evaluate",
            "fixture_path": "missing.json",
        },
        tmp_path,
    )
    with pytest.raises(AdapterError, match="no response"):
        adapter.execute(eval_case)
    (tmp_path / "error.json").write_text(
        json.dumps(
            {
                "responses": {
                    eval_case.id: {
                        "_error": {"type": "timeout", "message": "slow", "retryable": True}
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    adapter = _adapter(
        {
            "base_url": "https://offline.invalid",
            "endpoint": "/evaluate",
            "fixture_path": "error.json",
        },
        tmp_path,
    )
    with pytest.raises(AdapterError) as caught:
        adapter.execute(eval_case)
    assert caught.value.retryable
    with pytest.raises(ConfigError, match="responses"):
        _adapter(
            {
                "base_url": "https://offline.invalid",
                "endpoint": "/evaluate",
                "fixture_path": "bad.json",
            },
            _write(tmp_path, "bad.json", "{}"),
        )


def _write(directory: Path, name: str, content: str) -> Path:
    (directory / name).write_text(content, encoding="utf-8")
    return directory


@contextmanager
def _server() -> Iterator[tuple[str, type[BaseHTTPRequestHandler]]]:
    class Handler(BaseHTTPRequestHandler):
        polls = 0
        last_body = b""

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            type(self).last_body = self.rfile.read(length)
            if self.path == "/create":
                self._json(200, {"run_id": "run-1"})
            elif self.path == "/create-fail":
                self._json(200, {"run_id": "failed-run"})
            elif self.path == "/error":
                self._json(503, {"error": "unavailable"})
            else:
                self._json(404, {})

        def do_GET(self) -> None:
            if self.path == "/status/run-1":
                type(self).polls += 1
                status = "completed" if type(self).polls > 1 else "running"
                self._json(200, {"status": status})
            elif self.path == "/status/failed-run":
                self._json(200, {"status": "failed"})
            elif self.path == "/result/run-1":
                self._json(
                    200,
                    {
                        "products": [{"id": 1, "rank": 1, "score": 1, "price": 3999}],
                        "usage": {"total_latency_ms": 20, "token_count_kind": "actual"},
                    },
                )
            elif self.path == "/invalid":
                body = b"not-json"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._json(404, {})

        def _json(self, status: int, value: dict[str, Any]) -> None:
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", Handler
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_async_http_adapter(tmp_path: Path, eval_case: EvalCase) -> None:
    with _server() as (base_url, handler):
        adapter = _adapter(
            {
                "base_url": base_url,
                "endpoint": "/create",
                "method": "POST",
                "request": {"json": {"q": "$.input.query"}},
                "async_run": {
                    "status_endpoint": "/status/{run_id}",
                    "result_endpoint": "/result/{run_id}",
                    "poll_interval_seconds": 0.01,
                    "max_wait_seconds": 1,
                },
                "response_mapping": {
                    "retrieved_items": "$.products",
                    "usage": "$.usage",
                },
            },
            tmp_path,
        )
        result = adapter.execute(eval_case)
    assert result.status == "completed"
    assert result.retrieved_items[0]["id"] == 1
    assert b"expected" not in handler.last_body


def test_async_failure_and_invalid_json(tmp_path: Path, eval_case: EvalCase) -> None:
    with _server() as (base_url, _handler):
        failed = _adapter(
            {
                "base_url": base_url,
                "endpoint": "/create-fail",
                "method": "POST",
                "async_run": {
                    "status_endpoint": "/status/{run_id}",
                    "failure_values": ["failed"],
                    "poll_interval_seconds": 0.01,
                },
            },
            tmp_path,
        )
        with pytest.raises(AdapterError, match="ended with status failed"):
            failed.execute(eval_case)
        invalid = _adapter(
            {"base_url": base_url, "endpoint": "/invalid", "method": "GET"},
            tmp_path,
        )
        with pytest.raises(AdapterError, match="not valid JSON"):
            invalid.execute(eval_case)


def test_http_error_and_invalid_scheme(tmp_path: Path, eval_case: EvalCase) -> None:
    with _server() as (base_url, _handler):
        adapter = _adapter(
            {"base_url": base_url, "endpoint": "/error", "method": "POST"},
            tmp_path,
        )
        with pytest.raises(AdapterError) as caught:
            adapter.execute(eval_case)
        assert caught.value.retryable
    adapter = _adapter(
        {"base_url": "file:///tmp", "endpoint": "/x", "method": "GET"},
        tmp_path,
    )
    with pytest.raises(AdapterError, match="only permits"):
        adapter.execute(eval_case)
