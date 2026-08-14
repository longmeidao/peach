from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping

import httpx

from .http import HttpRequest, HttpTransport, HttpxTransport


class StashError(RuntimeError):
    pass


@dataclass
class StashClient:
    graphql_url: str = "http://127.0.0.1:9999/graphql"
    timeout: float = 10.0
    api_key: str | None = None
    transport: HttpTransport | None = None

    def graphql(self, query: str, variables: Mapping[str, object] | None = None) -> dict:
        body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["ApiKey"] = self.api_key
        transport = self.transport or HttpxTransport()
        request = HttpRequest("POST", self.graphql_url, headers, body)
        try:
            response = transport(request, self.timeout, 5 * 1024 * 1024)
            if response.status != 200:
                raise StashError(f"Stash returned HTTP {response.status}")
            result = json.loads(response.body)
        except (OSError, UnicodeError, json.JSONDecodeError, httpx.HTTPError) as exc:
            raise StashError(f"Stash request failed: {type(exc).__name__}") from exc
        if result.get("errors"):
            raise StashError(str(result["errors"]))
        return result.get("data") or {}
