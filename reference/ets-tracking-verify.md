# Web CLI · ETS 埋点验收（含 Redis 造数联动）

用户要求验证埋点、ETS 实时日志、事件属性、飞书埋点表时使用。与独立技能 `.claude/skills/ets-tracking-verify/` 配合。依赖特定业务态时，先按 `ops-ass/SKILL.md` 准备数据。

## 何时启用

- 飞书需求 / 埋点表（sheets）验收客户端事件与属性
- case 中含 `enter*` / `click*` / `click_PaySceneEntrance` 等埋点 TC
- 需要先把用户拨到「第 N 天 / 已打卡 / 活动结束」再触发埋点

## 强制顺序

```text
Task Progress:
- [ ] 1. 解析埋点表（事件名 + 每个属性）
- [ ] 2. 确认 env / userId / deviceId（onion-cli）
- [ ] 3. 若埋点依赖活动态 → Redis 特殊场景造数并 API 验收
- [ ] 4. 确认 ETS 事件元数据已注册
- [ ] 5. 准备设备通道（ensure_bluestacks_adb + device_ui doctor）
- [ ] 6. App 自执行触发埋点（截图留证）；不可用时再退人工/H5
- [ ] 7. query_event_logs.py 查实时日志（含 data 属性）
- [ ] 8. 按字段出 pass / mismatch / meta_missing / not_triggered / validate_failed；失败回 6
```

### 1. 解析埋点表

优先飞书表 URL（PRD「数据埋点」节常链到 sheets）：

```bash
lark-cli sheets +workbook-info --url '<表格URL>' --as bot
lark-cli sheets +csv-get --url '<表格URL>' --sheet-id '<sheetId>' --as bot --range 'A1:O80' --format json
```

抽取：事件英文名、`category`、属性英文名、枚举值、是否必填。同一事件多行属性合并成一条期望。

**以表为准**：表更新后必须重拉；不要沿用旧 PRD 多出来的字段（例：表已删 `scene`/`currentDay` 则以表为准）。前端实现应与表对齐；若不一致，报告里同时写「表期望」与「客户端实际载荷」。

### 2. 用户与设备

```bash
onion-cli auth status --verify
onion-cli user detail <userId>
onion-cli user device list <userId>
```

记录在线 `deviceId`。实时日志里顶层 `userId` 常为空，靠 `data.u_user` / `device` 关联。

### 3. 业务态准备（埋点依赖活动态时）

按 `ops-ass/SKILL.md`：根据你的业务场景造数。准备完成并用业务读接口验收后，再打开页面触发埋点。本套件不附带造数脚本。

### 4. ETS 元数据

```bash
onion-cli ets event list --name <eventName>
```

- 空 / 409「事件名不存在」→ 字段结论统一 **`meta_missing`**（无法验收），**禁止**写成「客户端未触发」。
- 客户端 console 可见 `browserDataTrack` 只能证明「页面发了桥接」，不能替代 ETS 元数据与实时日志。

### 5. 触发（优先设备自执行）

| 方式 | 用途 | 注意 |
| --- | --- | --- |
| **BlueStacks / 真机 ADB 自执行（推荐）** | Agent 自动点 App 写入 ETS 实时流 | 先 `ensure_bluestacks_adb.sh`，再用 `device_ui.py`；细则见 `ets-tracking-verify/reference/device-control.md` |
| App 人工点击 | 设备不可控时 | 操作后立刻查（窗口短） |
| H5 + `playwright-cli` | 看 console bridge、核对前端载荷是否与表一致 | Web 常**不进** App 设备实时流 → ETS 可能 `not_triggered` |

自执行入口：

```bash
SKILL=.claude/skills/ets-tracking-verify
bash "$SKILL/scripts/ensure_bluestacks_adb.sh"
python3 "$SKILL/scripts/device_ui.py" doctor
python3 "$SKILL/scripts/device_ui.py" launch
python3 "$SKILL/scripts/device_ui.py" tap-text --text '知道了' --optional
# 再按埋点 TC 走到目标页点击，截图后立刻 query_event_logs.py
```

C 端 H5：按 `ops-ass/SKILL.md` 准备用户和登录态后再打开；可加 `fromPageName=` 便于验曝光属性。

### 6. 查实时日志（必须带属性）

`onion-cli ets real-time logs` 只有摘要。属性级验收：

```bash
SCRIPT=.claude/skills/ets-tracking-verify/scripts/query_event_logs.py

python3 "$SCRIPT" \
  --user-id <userId> \
  --device-id <deviceId> \
  --event-name <event1> \
  --event-name <event2> \
  --expect '{"<event1>":{"pageName":"..."},"<event2>":{"button":"day2"}}'
```

扫流：`--scan --keyword threeDay --keyword Checkin`。

### 7. 字段判定（每个属性一行）

| 判定 | 条件 |
| --- | --- |
| `meta_missing` | ETS 无事件名 / 409 |
| `not_triggered` | 事件存在，但无该用户/设备近期日志 |
| `attr_mismatch` | 有日志，关键属性与期望不符 |
| `validate_failed` | 属性命中但 `status=false` / `validateFailList` 非空 |
| `pass` | 命中期望且 `status=true`（无期望属性时：有日志且 status=true） |
| `客户端对齐 / ETS 无法验收` | 前端载荷与表一致，但 ETS meta_missing 或 Web 未进设备流 |

**禁止**把同名事件错误 `scene`/`pageName` 当成通过（如宝藏卡 `shop-baozang-commonCard` ≠ 打卡页）。

## 与 web-cli 总流程的衔接

1. `web-cli` 识别「埋点验收」→ 读本 reference + `ets-tracking-verify`。
2. 需要活动态 → `ops-ass/SKILL.md`。
3. `ensure_bluestacks_adb` + `device_ui.py` 自执行触发（失败再退 `playwright-cli` / 人工）。
4. 字段结果写入 `web-run-*/artifacts/` 与报告；UI 主流程若同时跑了，仍走 `genr-report`。

## 输出模板

```markdown
### 埋点验收（<env> / <userId>）

造数：Redis … → activityDay=N / completed=[…]（证据路径）

| 事件 | 字段 | 期望 | 实测 | 判定 |
|------|------|------|------|------|
| … | pageName | … | … | pass / … |

结论：通过 / 未通过
风险：meta_missing / 实时窗口空 / Web 未进 App 流 …
```

## 禁止

- 未拉最新埋点表就用旧字段清单验收。
- 未 Redis/API 验收活动态就断言依赖状态的埋点属性。
- 只看事件名不看属性；或把错误 scene 的同名事件当通过。
- 把 `meta_missing` 写成客户端未上报。
- 在报告中输出生产密码、全量无关 key、明文 token。
