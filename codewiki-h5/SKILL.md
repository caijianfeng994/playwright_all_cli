---
name: codewiki-h5
description: Use when Web UI tests need C-end H5 routes from a feature name via CodeWiki, then assemble full 7to12 URLs before playwright-cli goto.
---

# C 端 H5 路由解析（CodeWiki）

测试 H5 需求时，若用户给的是**功能名称**（如「洋葱福利」「我的购买」「课程权益」）而不是完整 URL，必须先用 CodeWiki 查前端路由，再拼出可打开的全量 URL，最后才 `buildH5UrlWithAppToken` + `playwright-cli goto`。禁止凭记忆或历史报告猜 path。

## 何时必须调用

满足任一条件即必须跑本 Skill：

- 目标是 C 端 H5，且输入是功能名、页面名、App 入口名，而不是完整 path/URL
- 用户只给了短路由（如 `/welfare`），但未确认仓、部署前缀、是否现行页
- 同一功能可能有多仓（如 `revenue-resident-page` 与 `middle-resident`），需要唯一确认后再打开

用户已给出完整可打开 URL（含 host + 部署前缀 + 页面 path）时，不必再查 CodeWiki。登录态按 `ops-ass/SKILL.md` 准备。

Shadow / `onion-backstage` / `/backend/zlb` **不走本 Skill**，走 `shadow-path`。

## 工具选择

1. 当前会话已注册 `list_codewiki_repos` / `search_wiki` / `get_wiki_route_reference` 时直接调用。
2. **否则必须**执行：

```bash
python .claude/skills/web_cli/codewiki-h5/scripts/resolve_h5_routes.py \
  --query "洋葱福利" \
  --env test \
  --output "<run_dir>/h5-routes.json"
```

多个功能名重复 `--query`。`CODEWIKI_MCP_URL` 与 `CODEWIKI_MCP_TOKEN` 必填，Skill 不内置地址或 token。`ok=false` 或路由不唯一时停止打开页面，列出候选，禁止猜测。

禁止调用 GitNexus 图谱工具（`list_gitnexus_repos`、`get_route_graph`、`get_symbol_context` 等）替代本流程。禁止用本地仓扫描替代 CodeWiki。

## 标准流程

1. **列仓**：`list_codewiki_repos`（`type=repo`）。后续 `repo` 必须用 Wiki 名（如 `payment`，不是 `frontend/payment`）。
2. **按功能名搜**：`search_wiki`，`query` 用用户原话功能名；可加 `category=route`。未知仓不得把第一条搜索命中直接当唯一仓。
3. **唯一确认仓**：优先商业化 C 端仓（`payment`、`revenue-resident-page`）。`middle-resident`、`onion-activity` 仅当 Wiki 写明现行入口或用户指定时使用。零匹配或冲突：列出候选并停止。
4. **拉路由**：对唯一仓调用 `get_wiki_route_reference`（`repo` 必填；`route` 传功能名或已命中的短 path）。需要页面全文时再 `get_wiki_page`。
5. **取 path**：只采用 Wiki 中有证据的前端路由或 MPA 页面目录名，不得按中文名翻译成英文 path。
6. **拼全量 URL**（见下节），写入报告：`feature`、`repo`、`wikiPageId`、`routePath`、`fullUrl`（不含 token）。
7. **再交给打开流程**：按 `ops-ass/SKILL.md` 准备用户与登录态 → `playwright-cli goto`。

## 全量 URL 拼接

环境 host：

| env | host |
|---|---|
| test | `https://<h5-test-host>` |
| stage | `https://<h5-stage-host>` |
| online | `https://<h5-online-host>` |

部署前缀：C 端 H5 的站点前缀一般是 `/{wikiRepo}`。Wiki 里 vue-router 的 path 若已带该前缀则不要再拼一层。

| 仓 | 形态 | 示例 |
|---|---|---|
| `payment` | SPA：`/{repo}{route}` | `/my-tab-course` → `/payment/my-tab-course` |
| `revenue-resident-page` | MPA：`/{repo}/{page}` | 页面 `welfare-index` → `/revenue-resident-page/welfare-index` |
| `middle-resident` | SPA：`/{repo}{route}` | `/purchase-history` → `/middle-resident/purchase-history` |

打开前按 `ops-ass/SKILL.md` 准备 `userId` 和登录态。不要手写 token。

## 打开后校验

`goto` 后必须用 `snapshot` 或页面标题/主文案确认与功能名一致。例如：

- 洋葱福利 → 标题或 Tab 含「兑换码 / 优惠券 / 体验券」
- 课程权益 → 「我的课程权益」
- 身份权益 → 「我的身份权益」
- 售后权益 → 总览可能是 `/payment/my-tab-rights`；点击入口后详情可能是 `/payment/my-tab-sell`
- 我的购买 → 「我的购买」

校验失败：记该条失败，回到 CodeWiki 候选，不得改猜另一 path 冒充通过。

## 报告必写

- CodeWiki `repo`、检索 `query`、命中页面 id
- 拼出的 path（无 token）
- 打开后实际 `location.pathname`
- 多仓取舍理由（现行 C 端仓优先）

## 禁止事项

- 禁止用户只给功能名时跳过 CodeWiki、直接拼历史 URL。
- 禁止把 `search_wiki` 第一条当唯一路由。
- 禁止用后端 `get_api_reference` 的 HTTP API path 冒充 H5 页面 path。
- 禁止在报告或终端打印 App `token`。
