"""Generic synchronous and submit/poll/result HTTP adapter."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, cast

from eval42.adapters.base import Adapter
from eval42.errors import AdapterError, ConfigError
from eval42.mapping import apply_mapping, get_path, map_optional
from eval42.models import CaseResult, EvalCase, JsonObject

_MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class HttpAdapter(Adapter):
    """A small declarative HTTP adapter with an offline fixture transport."""

    def __init__(
        self,
        config: JsonObject,
        *,
        base_dir: Path,
        config_hash: str,
        revision: str,
    ) -> None:
        self.config = config
        self.base_dir = base_dir
        self.config_hash = config_hash
        self.revision = revision
        self.timeout = float(config.get("timeout_seconds", 60))
        self._fixture_responses = self._load_fixtures(config.get("fixture_path"))

    def _load_fixtures(self, fixture_path: Any) -> dict[str, Any] | None:
        if fixture_path is None:
            return None
        path = Path(str(fixture_path))
        if not path.is_absolute():
            path = (self.base_dir / path).resolve()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"cannot load adapter fixture {path}: {exc}") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("responses"), dict):
            raise ConfigError("adapter fixture must contain an object named 'responses'")
        return cast(dict[str, Any], raw["responses"])

    def execute(self, case: EvalCase) -> CaseResult:
        started = time.perf_counter()
        if self._fixture_responses is not None:
            raw = self._fixture_response(case)
        else:
            raw = self._network_response(case)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return self._normalize(case, raw, elapsed_ms)

    def _fixture_response(self, case: EvalCase) -> JsonObject:
        assert self._fixture_responses is not None
        response = self._fixture_responses.get(case.id)
        if response is None:
            raise AdapterError(
                f"fixture contains no response for case {case.id!r}",
                error_type="fixture_missing",
            )
        if not isinstance(response, dict):
            raise AdapterError("fixture response must be an object", error_type="fixture_invalid")
        configured_error = response.get("_error")
        if isinstance(configured_error, dict):
            raise AdapterError(
                str(configured_error.get("message", "fixture adapter error")),
                error_type=str(configured_error.get("type", "fixture_error")),
                retryable=bool(configured_error.get("retryable", False)),
            )
        return response

    def _network_response(self, case: EvalCase) -> JsonObject:
        request_config = self.config.get("request", {})
        json_template = request_config.get("json", {"input": "$.input"})
        payload = apply_mapping(json_template, case.as_mapping_source())
        created = self._request(
            str(self.config.get("method", "POST")),
            str(self.config["endpoint"]),
            payload,
        )
        async_config = self.config.get("async_run")
        if not isinstance(async_config, dict):
            return created
        return self._complete_async(created, async_config)

    def _complete_async(self, created: JsonObject, config: JsonObject) -> JsonObject:
        try:
            run_id = str(get_path(created, str(config.get("id_path", "$.run_id"))))
        except ConfigError as exc:
            raise AdapterError(str(exc), error_type="mapping_error") from exc
        poll_endpoint = str(config["status_endpoint"]).format(run_id=run_id)
        status_path = str(config.get("status_path", "$.status"))
        success = set(config.get("success_values", ["completed"]))
        failure = set(config.get("failure_values", ["failed", "cancelled"]))
        interval = float(config.get("poll_interval_seconds", 1))
        deadline = time.monotonic() + float(config.get("max_wait_seconds", self.timeout))
        last_status = "unknown"
        while time.monotonic() <= deadline:
            status_response = self._request("GET", poll_endpoint, None)
            try:
                last_status = str(get_path(status_response, status_path))
            except ConfigError as exc:
                raise AdapterError(str(exc), error_type="mapping_error") from exc
            if last_status in success:
                result_endpoint = str(config.get("result_endpoint", poll_endpoint)).format(
                    run_id=run_id
                )
                return self._request("GET", result_endpoint, None)
            if last_status in failure:
                raise AdapterError(
                    f"async run {run_id} ended with status {last_status}",
                    error_type=f"target_{last_status}",
                )
            time.sleep(max(interval, 0.01))
        raise AdapterError(
            f"async run did not complete (last status: {last_status})",
            error_type="timeout",
            retryable=True,
        )

    def _request(self, method: str, endpoint: str, payload: Any) -> JsonObject:
        base_url = str(self.config["base_url"])
        url = urllib.parse.urljoin(f"{base_url.rstrip('/')}/", endpoint.lstrip("/"))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise AdapterError("HTTP adapter only permits http and https URLs")
        body = None
        headers = {"Accept": "application/json", **self.config.get("headers", {})}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = response.read(_MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or exc.code >= 500
            raise AdapterError(
                f"target returned HTTP {exc.code}",
                error_type=f"http_{exc.code}",
                retryable=retryable,
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AdapterError(
                f"target request failed: {exc.reason if hasattr(exc, 'reason') else exc}",
                error_type="network_error",
                retryable=True,
            ) from exc
        if len(data) > _MAX_RESPONSE_BYTES:
            raise AdapterError("target response exceeded 10 MiB", error_type="response_too_large")
        try:
            decoded = json.loads(data)
        except json.JSONDecodeError as exc:
            raise AdapterError(
                "target response is not valid JSON", error_type="invalid_json"
            ) from exc
        if not isinstance(decoded, dict):
            raise AdapterError(
                "target response root must be an object", error_type="invalid_response"
            )
        return decoded

    def _normalize(self, case: EvalCase, raw: JsonObject, elapsed_ms: float) -> CaseResult:
        mapping = self.config.get("response_mapping", {})
        mapped = map_optional(raw, mapping) if mapping else dict(raw)
        retrieved = _normalize_items(mapped.get("retrieved_items") or [])
        eligible = _normalize_items(mapped.get("eligible_items") or [])
        recommended = mapped.get("recommended_ids")
        if not isinstance(recommended, list):
            recommended = [item["id"] for item in eligible or retrieved]
        usage = mapped.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        usage = dict(usage)
        usage.setdefault("total_latency_ms", round(elapsed_ms, 3))
        usage.setdefault("token_count_kind", "unavailable")
        usage.setdefault("input_tokens", None)
        usage.setdefault("output_tokens", None)
        usage.setdefault("estimated_cost", None)
        usage.setdefault("currency", None)
        system = mapped.get("system")
        if not isinstance(system, dict):
            system = {}
        system = {
            "adapter": "http",
            "revision": self.revision,
            "config_hash": self.config_hash,
            **system,
        }
        if mapped.get("outcome") is not None:
            system["outcome"] = mapped["outcome"]
        return CaseResult(
            case_id=case.id,
            status="completed",
            retrieved_items=retrieved,
            eligible_items=eligible,
            recommended_ids=_unique_identifiers(recommended),
            answer=mapped.get("answer") if isinstance(mapped.get("answer"), str) else None,
            claims=_normalize_objects(mapped.get("claims")),
            citations=_normalize_objects(mapped.get("citations")),
            usage=usage,
            system=system,
        )


def _normalize_items(value: Any) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    normalized: list[JsonObject] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        identifier = next(
            (item[key] for key in ("id", "product_id", "source_id", "url") if key in item),
            str(index),
        )
        attributes = item.get("attributes")
        if not isinstance(attributes, dict):
            attributes = {
                key: content
                for key, content in item.items()
                if key not in {"id", "product_id", "source_id", "score", "rank", "attributes"}
            }
        normalized.append(
            {
                "id": identifier,
                "score": item.get("score"),
                "rank": int(item.get("rank", index)),
                "attributes": attributes,
            }
        )
    return normalized


def _normalize_objects(value: Any) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item if isinstance(item, dict) else {"value": item} for item in value]


def _unique_identifiers(value: list[Any]) -> list[str | int]:
    result: list[str | int] = []
    for item in value:
        if isinstance(item, (str, int)) and not isinstance(item, bool) and item not in result:
            result.append(item)
    return result
