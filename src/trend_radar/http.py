from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class HttpClient:
    def __init__(self, timeout: int = 20, user_agent: str = "ai-trend-radar/0.1"):
        self.timeout = timeout
        self.user_agent = user_agent

    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str | int] | None = None,
        retries: int = 2,
    ) -> Any:
        raw = self.get_text(url, headers=headers, params=params, retries=retries)
        return json.loads(raw)

    def get_text(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str | int] | None = None,
        retries: int = 2,
    ) -> str:
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urllib.parse.urlencode(params)}"

        merged_headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if headers:
            merged_headers.update(headers)

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            request = urllib.request.Request(url, headers=merged_headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code in {403, 429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise

        raise RuntimeError(f"HTTP request failed: {url}") from last_error

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        retries: int = 2,
    ) -> Any:
        body = json.dumps(payload).encode("utf-8")
        merged_headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            merged_headers.update(headers)

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            request = urllib.request.Request(url, data=body, headers=merged_headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code in {403, 429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise

        raise RuntimeError(f"HTTP POST failed: {url}") from last_error
