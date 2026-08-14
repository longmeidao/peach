from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Mapping


class StashError(RuntimeError):
    pass


@dataclass
class StashClient:
    graphql_url: str = "http://127.0.0.1:9999/graphql"
    timeout: float = 10.0
    api_key: str | None = None

    def graphql(self, query: str, variables: Mapping[str, object] | None = None) -> dict:
        body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["ApiKey"] = self.api_key
        request = urllib.request.Request(self.graphql_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except Exception as exc:
            raise StashError(f"Stash request failed: {type(exc).__name__}") from exc
        if result.get("errors"):
            raise StashError(str(result["errors"]))
        return result.get("data") or {}
