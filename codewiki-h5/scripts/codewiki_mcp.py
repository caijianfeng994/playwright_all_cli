#!/usr/bin/env python3
"""stdlib 客户端：连接 CodeWiki MCP（与 yapi_mcp 同一套 streamable HTTP）。"""

from __future__ import annotations

import json
import os
import ssl
from typing import Any
from urllib.request import Request, urlopen

def require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"缺少环境变量 {name}。Skill 不内置密钥或内部域名。")
    return value


def _parse_body(raw: str) -> Any:
    text = raw.strip()
    if text.startswith("event:") or "\ndata:" in text:
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
                break
    return json.loads(text)


class CodewikiMcpClient:
    def __init__(self, *, mcp_url: str | None = None, token: str | None = None) -> None:
        self.mcp_url = (mcp_url or require_env("CODEWIKI_MCP_URL")).strip()
        raw_token = (token or require_env("CODEWIKI_MCP_TOKEN")).strip()
        self.token = raw_token[7:].strip() if raw_token.lower().startswith("bearer ") else raw_token
        self._session_id: str | None = None
        self._next_id = 1
        self._ssl = ssl._create_unverified_context()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _post(self, payload: dict[str, Any]) -> Any:
        req = Request(
            self.mcp_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urlopen(req, timeout=60, context=self._ssl) as resp:
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self._session_id = sid
            body = resp.read().decode("utf-8").strip()
        if not body:
            return {}
        data = _parse_body(body)
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"MCP error: {data['error']}")
        return data

    def initialize(self) -> dict[str, Any]:
        result = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "api-test-suite-codewiki-mcp", "version": "1.0"},
                },
            }
        )
        self._next_id += 1
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result.get("result") or {}

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        if not self._session_id:
            self.initialize()
        payload = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }
        )
        self._next_id += 1
        result = payload.get("result") if isinstance(payload, dict) else payload
        if isinstance(result, dict) and isinstance(result.get("content"), list):
            texts: list[str] = []
            for item in result["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(str(item.get("text") or ""))
                elif isinstance(item, str):
                    texts.append(item)
            joined = "\n".join(texts).strip()
            if joined:
                try:
                    return json.loads(joined)
                except json.JSONDecodeError:
                    return joined
        return result
