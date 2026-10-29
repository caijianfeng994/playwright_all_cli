---
name: web-cli
description: Use when executing Web UI automation with playwright-cli, resolving C-end H5 routes from feature names via CodeWiki, or running professional Web QA. Business data setup is not bundled; follow ops-ass/SKILL.md.
---

# Web CLI 自动化测试总入口

本 Skill 是 `.claude/skills/web_cli/` 的总流程入口。执行 Web UI 自动化测试时，必须先读取本 Skill，再按顺序调用子 Skill。任何前置步骤未完成或验证失败，都不能继续执行后续 UI 自动化。

## 严格执行顺序

必须按以下顺序执行，不允许跳步：

1. **识别测试目标**
   - 明确用户要测试的页面、环境、业务模块、平台、账号角色、输入数据和期望结果。
   - 若需求涉及 `Shadow`、`APP运营平台`、`onion-backstage`、菜单层级或后台页面，后续必须使用 `shadow-path`。
   - **C 端 H5 且输入是功能名/页面名（没有完整 URL）时，必须先走 `codewiki-h5`**：用 CodeWiki 按功能名查前端路由，拼出业务 H5 地址后再进入打开流程。禁止凭记忆或历史报告猜 path。业务域名从环境变量读取，不写进 Skill。
   - 需要造数、解析用户或准备登录态时，读取 `ops-ass/SKILL.md`：根据你的业务场景造数。本套件不附带造数脚本。
   - 若需求是系统性页面巡检、缺陷发现、性能/安全/可访问性审查，后续必须使用 `dogfood`。
   - **埋点 / ETS 验收**：需求含飞书埋点表、事件名、属性字段核验时，读取 `reference/ets-tracking-verify.md`。依赖特定业务态时，先按 `ops-ass/SKILL.md` 准备数据，再触发埋点。

2. **加载浏览器自动化能力**
   - **REQUIRED SUB-SKILL:** Use `playwright-cli`。
   - 先按 `playwright-cli` Skill 打开监控面板、准备浏览器会话和 artifact 输出目录。
   - 打开前先 `playwright-cli list`。已有会话能用时，继续用同一 `-s` 名称，不要换新 session 名再 `install-browser`。
   - 若 `playwright-cli` 不可用，先按其安装/降级方案处理；不能直接改用无证据的手工描述。

3. **解析页面路径**
   - **C 端 H5（功能名 → 路由）**：用户未给出完整 URL 时，**REQUIRED SUB-SKILL:** Use `codewiki-h5`。先 `list_codewiki_repos` / `search_wiki` / `get_wiki_route_reference`（会话未注册则执行 `codewiki-h5/scripts/resolve_h5_routes.py`），唯一确认仓与 path，再用环境变量中的 H5 源站拼全量 URL（仍不含 token）。路由不唯一则停止并列出候选，禁止猜测后 `goto`。
   - **Shadow / onion-backstage**：目标页面属于 `Shadow APP运营平台`、`onion-backstage` 或测试描述出现菜单名时，**REQUIRED SUB-SKILL:** Use `shadow-path`。必须先定位 `一级菜单 / 二级菜单 / 三级菜单 / 路径`，再打开页面。页面打开后必须用 `snapshot` 或 `document.body.innerText` 验证页面内容与菜单路径一致。

4. **准备业务测试数据**
   - **REQUIRED SUB-SKILL:** Use `ops-ass`。
   - 按 `ops-ass/SKILL.md` 执行：根据你的业务场景造数。本套件不附带造数脚本、账号或登录实现。

5. **执行 Web UI 自动化**
   - 使用 `playwright-cli` 打开目标测试环境页面。
   - **C 端 H5（强制）**：打开业务 H5（不含后台、不含运营平台）时：
     1. 若还没有完整 URL：必须已完成第 3 步 `codewiki-h5`，使用其输出的 `rawUrl`。
     2. 用户身份和登录态按 `ops-ass/SKILL.md` 准备，再打开页面。禁止沿用过期 `token`，禁止把 token 写进 Skill 或报告。
   - 每次关键操作后用 `snapshot`、页面文本、网络请求或 DOM 查询确认状态。
   - **需求规则必须全覆盖**：执行前对照需求/用例中的规则清单（RT/AS/BR、状态口径、展示口径）。每一条都必须给出通过或失败结论。
     - 能执行则按真实结果判定。
     - **覆盖不到一律记失败**，不得记阻塞、跳过、未执行或 Out of Scope。包括：缺造数、缺账号、缺 App 会话、缺飞书私聊、缺未上架商品、规则无对应用例、夹具未覆盖规则子项（如只测实付未测退款金额）。
     - 失败记录必须写：规则 ID、未覆盖原因、期望、实际（未执行/无法造数等）、证据（缺夹具、缺入口截图或规则原文）。
     - 仅当整次运行无法登录目标环境、无法打开任何页面时，才允许将**整轮**标为阻塞；已打开页面后漏掉的单条规则仍记失败。
   - **截图证据必须精确命中断言对象**：
     1. 截图前先将目标字段、提示、表格行或弹窗滚动到可视区，并确认目标文本实际可见。
     2. 优先截取包含目标对象及必要上下文的元素区域；使用整页截图时，目标证据也必须出现在当前画面内。
     3. 对“字段缺失 / 按钮缺失”类负向结论，截图必须完整展示该字段按设计应出现的区块，不能截页面上半部分后凭页面文本推断。
     4. 截图落盘后必须重新读取图片核对；若图片中看不到报告声称的证据，立即重截，禁止将其写入证据索引。
     5. DOM 文本、Network、Trace 可作为辅助证据，但不能替代用户明确要求的可视截图证据。
   - 对涉及菜单的页面，报告中必须记录实际使用的菜单路径。
   - 对涉及三方订单的页面，报告中必须记录本次使用的 `platform`、`orderId`、`ycSkuId` 和必要的额外参数。
   - 非电商场景额外记录：`channel`（渠道名称/ID）、上传任务 ID、Excel 文件名、支付订单号。
   - **UI 分支 / 接口迁移场景（强制）**：若弹窗或表单存在互斥选项（如「停用全部 / 停用部分」、创建/追加多种类型），且需求或用例指定了某一分支对应的新接口，则：
     1. 先读取弹窗当前默认选中项，不得默认沿用。
     2. 显式切换到用例/需求要求的分支后再提交。
     3. 用 `playwright-cli network` 断言该分支的期望 URL；禁止用另一分支的请求结果替代判定。
     4. 报告中必须写明：所选分支、默认项是否被覆盖、实际命中 URL、期望 URL。

6. **系统性 QA 或证据采集**
   - 条件：用户要求“全面测试”“页面巡检”“质量检查”“缺陷报告”“性能/安全/可访问性检查”等。
   - **REQUIRED SUB-SKILL:** Use `dogfood`。
   - 按 `dogfood` 的 6 阶段流程采集截图、trace、video、console、network 和最终报告。
   - 若只是执行明确的单条用例，可不启用 `dogfood`，但仍必须保留关键证据。

6b. **埋点 / ETS 字段验收**（与 UI 可并行，但造数在前）
   - 条件：用户给出飞书埋点表/需求埋点节，或 case 含埋点 TC。
   - 必读：`reference/ets-tracking-verify.md`；脚本：`.claude/skills/ets-tracking-verify/scripts/query_event_logs.py`。
   - 每个属性一行结论：`pass` / `attr_mismatch` / `validate_failed` / `not_triggered` / `meta_missing` / `客户端对齐 / ETS 无法验收`。
   - 优先 App 真机触发；H5 console `browserDataTrack` 只证明桥接，不能单独当 ETS 通过。
   - 产物：`web-run-*/artifacts/ets-*.json` + 字段表报告。

7. **生成 UI 自动化测试报告**
   - **REQUIRED SUB-SKILL:** Use `genr-report`。
   - 只要第 5 步已经执行 Web UI 自动化，就必须调用 `genr-report`，不能跳过。
   - 必须基于真实执行结果、截图、trace、video、console、network 和前置造数记录生成报告。
   - 若只是调试浏览器连通性、且没有执行任何自动化测试步骤，可不调用 `genr-report`，但最终回复必须说明“未执行 UI 自动化，未生成报告”。
   - 若使用 MCP Chart Server 失败，报告必须说明降级原因，不能伪造图表。

8. **输出测试结果**
   - 先给结论：通过、失败、阻塞或未执行。
   - 若失败，说明失败步骤、实际现象、期望结果、证据路径和下一步建议。
   - 需求规则未覆盖或无法执行：按**失败**输出，不要写成阻塞。
   - 仅整轮无法进入测试环境时，才说明阻塞点；不要伪造通过。

## 造数与用户身份

需要造数、解析用户或准备登录态时，只读 `ops-ass/SKILL.md`。

根据你的业务场景造数。本套件不附带造数脚本、洋葱账号或登录实现。报告可写 `userId`，不要输出手机号、密码或 token。

## 子 Skill 调用规则

| 子 Skill | 触发条件 | 必须发生在 |
| --- | --- | --- |
| `playwright-cli` | 所有 Web UI 自动化、页面操作、截图、表单填写、网络/console 检查 | 第 2 步开始 |
| `codewiki-h5` | C 端 H5 测试且输入是功能名/页面名、缺少完整 URL | 打开 H5 前（第 3 步） |
| `shadow-path` | 运营平台、菜单层级 | 打开后台页面前 |
| `ops-ass` | 需要造数、解析用户或登录态。按该 Skill：根据你的业务场景造数 | UI / 埋点触发前 |
| `ets-tracking-verify`（+ `reference/ets-tracking-verify.md`） | 飞书埋点表、ETS 实时日志、事件属性字段验收；依赖业务态时先造数 | 造数与触发之后、出字段结论时 |
| `dogfood` | 系统性 QA、页面巡检、缺陷发现、性能/安全/可访问性检查、正式测试报告 | 页面可访问且前置数据准备完成后 |
| `genr-report` | UI 自动化报告、可视化报告、测试交付报告、图表化测试结果 | Web UI 自动化执行后、最终输出前 |

## 禁止事项

- 禁止未按 `ops-ass/SKILL.md` 准备业务数据就执行依赖夹具的 UI 自动化。
- 禁止未使用 `shadow-path` 就猜测 `onion-backstage` 菜单路由。
- 禁止 C 端 H5 在用户只给功能名时跳过 `codewiki-h5`、凭记忆或历史报告猜 path；禁止用后端 API path 冒充 H5 页面 path。
- 禁止只凭页面打不开就判定功能失败；必须先确认登录态、环境、菜单路径和网络请求。
- 禁止沿用过期 `token`。登录态按 `ops-ass/SKILL.md` 准备，不要把 token 写进 Skill。
- 禁止在 Skill 中内置洋葱账号或造数脚本。
- 禁止在终端、报告或 Skill 中输出明文密码、token、Cookie、Authorization。
- 禁止把线上数据写入测试环境前不做验证。
- 禁止测试失败时只给“失败”结论，必须给出证据和可复现步骤。
- 禁止将需求已写明但未执行/无法执行的规则记为阻塞、跳过或未覆盖；必须记失败。
- 禁止引用未显示断言对象的截图；截图与结论不一致时必须重截或将该结论标记为“缺少截图证据”。
- 禁止用页面完整文本抓取结果冒充截图证据；文本证据与图片证据必须在报告中区分标注。
- 禁止执行了 Web UI 自动化后不调用 `genr-report`。
- 禁止未执行测试或缺少证据时调用 `genr-report` 生成通过报告。
- 禁止在「接口替换 / 路由迁移」类用例中，沿用弹窗默认选项却断言另一分支接口；例如默认「停用全部」时不得据此判定「停用部分 / partStop」是否已切换。
- 禁止已有会话能用时，换新 session 名再 `install-browser`。Playwright 不用系统 Chrome.app；本机 `~/Library/Caches/ms-playwright` 已有对应 Chromium 时不得因换 session 或沙箱空缓存重复下载。
- 禁止在报告、日志、Skill 中输出数据库 URI、密码、手机号。
- 禁止埋点验收时未重拉最新飞书埋点表、仍用旧字段清单；依赖特定业务态时，先按 `ops-ass/SKILL.md` 准备数据再断言。
- 禁止把 ETS `meta_missing` 写成客户端未上报；禁止把错误 `scene`/`pageName` 的同名事件当通过；禁止仅凭 H5 console bridge 判定 ETS 通过。

## UI 分支 → Network 断言（接口迁移专用）

当需求形如「旧接口 A → 新接口 B」，且页面同一入口下有多个模式时，按分支建映射表再执行：

| UI 分支 | 期望 Network | 不得用其替代判定的结果 |
|---|---|---|
| 停用部分 | `.../redeemCodebatch/partStop`（或需求写明的新路径） | 停用全部打到的旧批次接口 |
| 停用全部 | 需求单独给出的全部停用接口；未给出则单独记录，不冒充 partStop | 停用部分的 partStop |
| 查询 / 追加 / 创建 | 需求对应新路径 | 同页其它 tab 的请求 |

执行清单：

```text
1. snapshot 确认弹窗选项与默认选中项
2. 显式 click/选择目标分支（即使看起来已选中也要复核 aria-checked / class）
3. 完成该分支必填（如停用部分需勾选具体兑换码）
4. 提交后立即 playwright-cli network，过滤旧路径关键字与新路径关键字
5. 仅当目标分支的期望 URL 出现，才判定「接口已替换」通过
```

## 页面写操作成功判定（创建 / 追加 / 停用强制）

接口迁移场景下，**「路由已切换」≠「页面功能可用」**。对配置页创建、追加、停用等写操作，必须同时满足：

| 层级 | 通过条件 | 不通过示例 |
|---|---|---|
| 路由 | Network 命中需求新路径 | 仍打旧 `/api/virtual/...` |
| 契约 | 请求 Method 正确；Response **HTTP 2xx**；业务成功字段存在（如创建返回 `id`） | 打到新路径但 **500**；页面提示「服务似乎在开小差」 |
| 页面 | 无通用失败 toast；有成功反馈或可回查到新数据 | 仅看到路由对了就判 passed |
| 证据 | 保存 Request Payload + Response Body（可脱敏）+ 页面截图 | 只有截图、没有响应体 |

强制规则：

1. **页面创建/追加/停用用例**：以「该页真实表单提交成功」为 P0 通过标准；`status!=2xx` 一律 failed，不得因「已切新路由」判 passed。
2. **出现通用失败文案**（如「服务似乎在开小差」）时：必须展开失败请求的 Response `message`/`code` 写入报告；禁止只记 toast。
3. **关键表单分支至少各跑一条成功路径**（例：创建链接=是/否；一码一用/一码多用；不同申请用途）。只跑造数用的单一组合不算页面创建已覆盖。
4. **纯接口用例（ITC-xxx 接口测试）不得替代页面创建结论**：
   - API 用例可用手写合法 body 验证注入/转换逻辑；
   - 页面用例必须用前端实际组包；二者 payload 不一致时，以页面失败为准记缺陷，并反哺 API 增加「前端组包」回归。
5. **推荐执行顺序**：先 UI 打通一条创建成功并固化 Request Payload 为 golden fixture → 再用该 fixture 跑 API 专项（createdBy 等），避免 API 假绿、页面 500。

```text
页面创建最小通过清单：
1. 按用例填完必填（含目标分支选项）
2. 点击生成/提交
3. network：新路径 + status 2xx + response 含批次 id（或约定成功字段）
4. 页面无失败 toast；可选：查询页/审批页回查到新批次
5. 落盘：request.json + response.json + 结果截图
任一环节失败 → 该创建用例 failed，不得降级为「路由通过」
```

## 最小执行模板

当用户要求执行 Web UI 自动化时，按这个模板行动：

```text
1. 读取 web-cli 总入口。
2. 读取并遵循 playwright-cli。
3. 若是 C 端 H5 且只有功能名，读取并遵循 codewiki-h5：查路由并拼全量 URL。
4. 若是 Shadow/onion-backstage 页面，读取并遵循 shadow-path。
5. 需要业务数据或登录态时，读取 ops-ass/SKILL.md：根据你的业务场景造数。
5b. 若是埋点/ETS 验收：reference/ets-tracking-verify.md；每个字段一行结论。
6. 打开测试环境页面并执行 UI 自动化步骤。C 端 H5 的用户身份按 ops-ass 准备后再打开。
7. 若用户要求全面 QA，读取并遵循 dogfood 采集完整证据。
8. 自动化执行后，必须读取并遵循 genr-report 生成图表化 UI 自动化测试报告。
9. 输出测试结论、关键证据和阻塞/缺陷信息。
```
