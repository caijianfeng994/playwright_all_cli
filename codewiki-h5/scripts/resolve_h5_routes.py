#!/usr/bin/env python3
"""按功能名从 CodeWiki 解析 C 端 H5 路由，并拼 7to12 全量 URL（不含 token）。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

SCRIPT_DIR = Path(__file__).resolve().parent
API_TEST_SCRIPTS = (
    Path(__file__).resolve().parents[3] / "api-test-suite" / "scripts"
)
for candidate in (SCRIPT_DIR, API_TEST_SCRIPTS):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from codewiki_mcp import CodewikiMcpClient  # noqa: E402

ROUTE_CELL_RE = re.compile(
    r"(?:`(/[A-Za-z0-9][A-Za-z0-9_./:-]*)`)|(?:\|\s*(/[A-Za-z0-9][A-Za-z0-9_./:-]*)\s*\|)"
)
HEADING_ROUTE_RE = re.compile(r"^#{2,3}\s+(/[A-Za-z0-9][A-Za-z0-9_./:-]*)\s*$", re.M)
PAGE_DIR_RE = re.compile(r"src/pages/([A-Za-z0-9][A-Za-z0-9_-]*)/")
VIEWS_DIR_RE = re.compile(r"src/views/([A-Za-z0-9][A-Za-z0-9_-]*)/")

H5_ENVS = ("test", "stage", "online")
_H5_ORIGIN_ENV = {
    "test": "H5_TEST_ORIGIN",
    "stage": "H5_STAGE_ORIGIN",
    "online": "H5_ONLINE_ORIGIN",
}


def h5_origin(env: str) -> str:
    name = _H5_ORIGIN_ENV[env]
    value = (os.environ.get(name) or "").strip().rstrip("/")
    if not value:
        raise RuntimeError(f"缺少环境变量 {name}。Skill 不内置业务域名。")
    return value

# 已用 web_cli 打开验证过的 C 端仓；其它仓仍可出现在候选里，但不能无证据当现行入口
PREFERRED_REPOS = ("payment", "revenue-resident-page")
FRONTEND_REPO_MARKERS = ("payment", "resident", "h5", "activity-page", "padh5")

SKIP_PATH_PREFIXES = (
    "/api/",
    "/backend",
    "/codewiki/",
    "/go-",
    "/shadow",
    "/course-mall/",
)

FEATURE_HINTS = {
    "洋葱福利": ("welfare", "welfare-index", "redeem"),
    "兑换码": ("welfare", "welfare-index", "redeem"),
    "优惠券": ("welfare", "coupon"),
    "体验券": ("welfare", "experience", "trial"),
    "课程权益": ("my-tab-course", "course"),
    "身份权益": ("my-tab-identity", "identity"),
    "售后权益": ("my-tab-rights", "my-tab-sell", "after-sales", "afterSales"),
    "我的购买": ("purchase-history", "purchase"),
}


def wiki_repo_names(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        names = payload.get("names") or payload.get("repos")
        if isinstance(names, list):
            out = [str(item) for item in names if isinstance(item, str)]
            if out:
                return out
        details = payload.get("repoDetails") or payload.get("details")
        if isinstance(details, dict):
            return [str(k) for k in details.keys()]
    if isinstance(payload, list):
        names: list[str] = []
        for item in payload:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
        return names
    return []


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("results", "pages", "items", "hits"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if payload.get("id") or payload.get("scope") or payload.get("markdown"):
            return [payload]
    return []


def _text_blob(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("snippet") or ""),
        str(item.get("markdown") or ""),
        str(item.get("id") or ""),
        str(item.get("relativePath") or ""),
    ]
    return "\n".join(parts)


def extract_paths(text: str) -> list[str]:
    found: list[str] = []
    for match in ROUTE_CELL_RE.finditer(text or ""):
        path = match.group(1) or match.group(2)
        if path:
            found.append(path.rstrip(".,;"))
    for match in HEADING_ROUTE_RE.finditer(text or ""):
        found.append(match.group(1).rstrip(".,;"))
    for match in PAGE_DIR_RE.finditer(text or ""):
        found.append("/" + match.group(1))
    for match in VIEWS_DIR_RE.finditer(text or ""):
        found.append("/" + match.group(1))
    return found


def is_page_path(path: str) -> bool:
    if not path.startswith("/") or path == "/":
        return False
    lowered = path.lower()
    if any(lowered.startswith(prefix) or prefix in lowered for prefix in SKIP_PATH_PREFIXES):
        return False
    if lowered.endswith((".md", ".js", ".ts", ".vue", ".json")):
        return False
    if " " in path:
        return False
    return True


def is_frontend_repo(repo: str) -> bool:
    name = (repo or "").lower()
    return any(mark in name for mark in FRONTEND_REPO_MARKERS)


def score_path(query: str, path: str, repo: str) -> int:
    q = (query or "").strip()
    blob = f"{repo} {path}".lower()
    score = 0
    hints = FEATURE_HINTS.get(q, ())
    for hint in hints:
        if hint.lower() in blob:
            score += 8
    for token in re.split(r"[\s/]+", q):
        if len(token) >= 2 and token.lower() in blob:
            score += 2
    if repo in PREFERRED_REPOS:
        score += 3
    if is_frontend_repo(repo):
        score += 4
    if path.count("/") <= 3:
        score += 1
    if not is_frontend_repo(repo):
        score -= 6
    return score


def assemble_full_path(repo: str, route: str) -> str:
    route = "/" + route.strip().strip("/")
    prefix = "/" + repo.strip("/")
    if route == prefix or route.startswith(prefix + "/"):
        return route
    return prefix + route


def assemble_url(env: str, full_path: str) -> str:
    host = h5_origin(env)
    path = full_path if full_path.startswith("/") else "/" + full_path
    return host + path


def pick_candidates(
    query: str,
    hits: list[dict[str, Any]],
    known_repos: set[str],
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for hit in hits:
        repo = str(hit.get("scope") or hit.get("repo") or "").strip()
        if repo and known_repos and repo not in known_repos:
            continue
        blob = _text_blob(hit)
        paths = [p for p in extract_paths(blob) if is_page_path(p)]
        if not paths and repo:
            continue
        category = str(hit.get("category") or "")
        for path in paths:
            key = (repo, path)
            if key in seen:
                continue
            seen.add(key)
            ranked.append(
                {
                    "query": query,
                    "repo": repo,
                    "routePath": path,
                    "fullPath": assemble_full_path(repo, path) if repo else path,
                    "wikiPageId": hit.get("id") or "",
                    "title": hit.get("title") or "",
                    "category": category,
                    "score": score_path(query, path, repo),
                }
            )
    ranked.sort(key=lambda item: (-int(item["score"]), item["repo"], item["fullPath"]))
    return ranked


def unique_best(ranked: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    if not ranked:
        return None, "zero"
    preferred = [item for item in ranked if item.get("repo") in PREFERRED_REPOS]
    pool = preferred or ranked
    top_score = int(pool[0]["score"])
    same_score_paths = {item["fullPath"] for item in pool if int(item["score"]) == top_score}
    if len(same_score_paths) > 1:
        return None, "conflict"
    return pool[0], "unique"


def resolve_query(client: CodewikiMcpClient, query: str, known_repos: set[str]) -> dict[str, Any]:
    search_hits = _as_list(client.call_tool("search_wiki", {"query": query, "limit": 15}))
    route_hits = _as_list(
        client.call_tool("search_wiki", {"query": query, "category": "route", "limit": 10})
    )
    hint_hits: list[dict[str, Any]] = []
    for hint in FEATURE_HINTS.get(query, ())[:2]:
        hint_hits.extend(
            _as_list(client.call_tool("search_wiki", {"query": hint, "category": "route", "limit": 8}))
        )
    hits = search_hits + route_hits + hint_hits

    repos_from_hits: list[str] = []
    for hit in hits:
        repo = str(hit.get("scope") or hit.get("repo") or "").strip()
        if repo and repo not in repos_from_hits and is_frontend_repo(repo):
            repos_from_hits.append(repo)
    for repo in PREFERRED_REPOS:
        if repo in known_repos and repo not in repos_from_hits:
            repos_from_hits.insert(0, repo)

    extra_pages: list[dict[str, Any]] = []
    route_keys = (query,) + FEATURE_HINTS.get(query, ())[:2]
    for repo in repos_from_hits[:6]:
        for route_key in route_keys:
            try:
                page = client.call_tool(
                    "get_wiki_route_reference", {"repo": repo, "route": route_key}
                )
            except Exception:  # noqa: BLE001
                continue
            extra_pages.extend(_as_list(page))
    ranked = pick_candidates(query, hits + extra_pages, known_repos)
    chosen, status = unique_best(ranked)
    return {
        "query": query,
        "matchStatus": status,
        "candidates": ranked[:12],
        "chosen": chosen,
        "probedRepos": repos_from_hits[:6],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按功能名从 CodeWiki 解析 C 端 H5 全量 URL")
    parser.add_argument("--query", action="append", required=True, help="功能名，可重复")
    parser.add_argument("--env", choices=H5_ENVS, default="test")
    parser.add_argument("--output", "-o", help="写入 JSON")
    parser.add_argument("--mcp-url", help="覆盖 CodeWiki MCP 地址")
    parser.add_argument("--user-id", help="可选，写入 rawUrl 的 userId（仍不含 token）")
    return parser


def attach_url(chosen: dict[str, Any] | None, env: str, user_id: str | None) -> dict[str, Any] | None:
    if not chosen:
        return None
    url = assemble_url(env, chosen["fullPath"])
    if user_id:
        sep = "&" if "?" in url else "?"
        url = url + sep + urlencode({"userId": user_id})
    attached = dict(chosen)
    attached["env"] = env
    attached["rawUrl"] = url
    return attached


def main() -> int:
    args = build_parser().parse_args()
    client = CodewikiMcpClient(mcp_url=args.mcp_url)
    info: dict[str, Any] = {"mcp_url": client.mcp_url, "ok": False, "env": args.env}
    try:
        listed = client.call_tool("list_codewiki_repos", {"type": "repo"})
        repos = wiki_repo_names(listed)
        known = set(repos)
        info["repoCount"] = len(repos)
        queries: list[dict[str, Any]] = []
        all_ok = True
        for query in args.query:
            resolved = resolve_query(client, query, known)
            resolved["chosen"] = attach_url(resolved.get("chosen"), args.env, args.user_id)
            if resolved["matchStatus"] != "unique" or not resolved.get("chosen"):
                all_ok = False
            queries.append(resolved)
        info["ok"] = all_ok
        info["queries"] = queries
        if not all_ok:
            info["error"] = "存在功能名路由不唯一或零匹配，停止猜测，见 queries[].candidates"
    except Exception as exc:  # noqa: BLE001
        info["ok"] = False
        info["error"] = str(exc)

    text = json.dumps(info, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if info.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
