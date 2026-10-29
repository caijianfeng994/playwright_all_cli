---
name: genr-report
description: Use when generating Web UI automation test reports from playwright-cli, dogfood, console, network, screenshot, trace, video, or execution-result artifacts.
---

# Web UI 自动化测试报告生成

本 Skill 用于在 Web UI 自动化测试完成后，基于测试执行结果和证据产物生成结构化报告，并使用 `@antv/mcp-server-chart` 生成可视化图表。

必须先完成 `web-cli` 总入口中的页面测试、前置造数、菜单校验和证据采集，再执行本 Skill。禁止在没有执行结果或证据的情况下生成“看起来完整”的报告。

## 输入产物

优先读取以下产物：

- `dogfood` 生成的 `report.md`、`screenshots/`、`traces/`、`videos/`、`storage/`
- `playwright-cli` 生成的 snapshot、screenshot、trace、video、console、network 输出
- Playwright 执行结果：通过数、失败数、跳过数、耗时、失败用例、错误堆栈
- 三方订单场景的前置数据：`platform`、`orderId`、`ycSkuId`、额外参数、造数结果
- Shadow 后台页面的菜单路径与页面验证结果

若关键输入缺失，先返回阻塞说明，不要继续生成报告。

## 报告输出目录

默认输出到：

```text
web-output/reports/{label}_{YYYYMMDD_HHMMSS}/
├── report.md
├── report.html
├── charts/
│   ├── pass-rate.*
│   ├── issue-severity.*
│   └── issue-category.*
└── evidence-index.json
```

`label` 使用测试目标或页面名称，非字母数字和连字符替换为 `_`。

## MCP Chart Server 配置

使用以下 MCP 连接配置加载图表工具：

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient(
    {
        "mcp-server-chart": {
            "command": "npx",
            "args": ["-y", "@antv/mcp-server-chart"],
            "transport": "stdio",
        }
    }
)
mcp_tools = asyncio.run(mcp_client.get_tools())
```

使用工具前先打印或记录可用工具名，优先选择可渲染图表的工具，例如 `render_chart`、`generate_chart`、`chart`、`pie`、`column`、`bar`、`line`。不要假设固定工具名一定存在。

## 严格流程

1. **汇总测试结果**
   - 统计 `total`、`passed`、`failed`、`skipped`、`duration`。
   - 归类缺陷严重程度：`Critical`、`High`、`Medium`、`Low`、`Info`。
   - 归类问题类型：功能、接口、Console、Network、性能、安全、可访问性、数据准备、环境阻塞。

2. **建立证据索引**
   - 记录每个缺陷对应的截图、trace、video、console、network 文件路径。
   - 每个截图在写入索引前必须重新读取并核对，确认图片中直接可见该缺陷所依赖的字段、数值、提示或完整功能区块。
   - 为每条截图证据记录 `assertion`（要证明的结论）和 `visibleEvidence`（图片中实际可见内容）；两者不一致时不得引用。
   - 对负向结论（字段缺失、按钮缺失、无提示），截图必须完整覆盖该元素按设计应出现的区块，并用 DOM 文本或 snapshot 辅助确认。
   - 文本抓取、Network、Trace 与截图分别标注证据类型，禁止用文本证据路径冒充图片证据。
   - 三方订单场景必须记录 `platform`、`orderId`、`ycSkuId` 和造数验证结果。
   - 非电商场景必须额外记录 `channel`、上传任务 ID、Excel 文件名，以及造数页路径 `outerDataManager`。
   - C 端 H5 场景必须记录 CodeWiki `repo`、检索功能名、拼出的 path（无 token）和打开后的 `location.pathname`。

3. **生成图表数据**
   - 通过率图：`passed`、`failed`、`skipped`。
   - 缺陷严重程度图：按 severity 聚合。
   - 缺陷类型图：按 category 聚合。
   - 如有性能数据，生成耗时或接口延迟趋势图。

4. **调用 MCP 生成图表**
   - 使用 `@antv/mcp-server-chart` 渲染图表。
   - 每个图表调用失败时，只降级该图表，不影响其他图表。
   - MCP 完全不可用时，报告必须明确写出“图表 MCP 不可用”，并保留原始统计表。

5. **生成 `report.md`**
   - 先写结论：通过、失败、阻塞或未执行。
   - 写执行摘要、范围、环境、数据准备、结果统计、**需求规则覆盖表**、缺陷清单、证据索引、风险与建议。
   - 不要把 token、Cookie、Authorization、密码写入报告。

6. **生成 `report.html`**
   - 嵌入或引用 MCP 生成的图表。
   - 保留与 `report.md` 一致的结论、统计、缺陷和证据链接。
   - HTML 中的资源路径必须使用相对路径，便于整体目录上传或归档。

7. **最终校验**
   - 确认 `report.md` 和 `report.html` 都存在。
   - 确认图表文件或图表降级说明存在。
   - 确认证据路径可访问。
   - 逐条打开报告引用的截图，确认目标证据位于画面内且清晰可读；截图只显示页面顶部、错误页面、遮罩或无关区域时必须重截。
   - 确认报告没有把“DOM 文本中存在/缺失”写成“截图中可见/不可见”；若没有合格图片，应明确标注“仅有文本证据，缺少截图证据”。
   - 确认报告中没有明文敏感信息。

## 推荐图表规格

通过率图：

```json
{
  "type": "pie",
  "title": "UI 自动化执行结果",
  "data": [
    {"status": "通过", "value": 0},
    {"status": "失败", "value": 0},
    {"status": "跳过", "value": 0}
  ],
  "angleField": "value",
  "colorField": "status"
}
```

缺陷严重程度图：

```json
{
  "type": "column",
  "title": "缺陷严重程度分布",
  "data": [
    {"severity": "Critical", "count": 0},
    {"severity": "High", "count": 0},
    {"severity": "Medium", "count": 0},
    {"severity": "Low", "count": 0},
    {"severity": "Info", "count": 0}
  ],
  "xField": "severity",
  "yField": "count"
}
```

## 报告结论规则

- 所有用例通过、无失败、且需求规则清单全部判定通过：结论为 `通过`。
- 存在失败断言、页面错误、接口错误、关键流程不可用，或**需求规则未覆盖/无法执行**：结论为 `失败`。
- 仅当整轮无法登录、无法打开目标环境，导致一条规则都未开始执行：结论为 `阻塞`。
- 需求规则缺夹具、缺 App、缺通知通道、缺库存数据：记该规则/用例如 **失败**，禁止记阻塞或跳过。
- 未实际执行自动化步骤且用户未要求跑用例：结论为 `未执行`，不能写成通过。

报告中必须有「需求规则覆盖表」：规则 ID、对应 TC、结果（通过/失败）、失败原因。表中不得出现「未执行」「阻塞」「跳过」。

## 禁止事项

- 禁止跳过测试执行直接生成报告。
- 禁止无证据编造缺陷、通过率或性能数据。
- 禁止把未覆盖的需求规则写成阻塞、跳过或 Out of Scope；必须列入失败项。
- 禁止将未显示断言对象的截图关联到缺陷，包括目标区块在折叠区域、页面下方或当前 viewport 之外的情况。
- 禁止截图文件存在但未人工核对内容就写入报告或 `evidence-index.json`。
- 禁止仅凭 `document.body.innerText` 得出“截图已证明”的结论。
- 禁止在报告中输出明文密码、token、Cookie、Authorization。
- 禁止 MCP 图表生成失败后吞掉错误；必须在报告中说明降级。
- 禁止只有图表没有文字结论；报告必须可独立阅读。