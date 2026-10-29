---
name: shadow-path
description: Use when testing Shadow APP运营平台 or onion-backstage pages, resolving menu hierarchy, executing playwright-cli cases that mention menus such as 三方订单管理、通用三方、抖店、渠道投放, or when ops-ass/造数工具 cannot produce needed fixtures and data must be queried from Shadow backend menus.
---

# Shadow 运营平台路径导航

## 使用规则

当测试用例、需求或页面地址涉及 `<shadow-test-host>/shadow/#/`、旧版 Shadow 运营平台、用户管理、商品中心、订单管理、售后管理、退款管理、发货管理、配置管理等场景时，先按本节查找菜单路径，再执行 `playwright-cli`。

1. 根据用例中的页面、模块或菜单名，在下方表格定位 `一级菜单 / 二级菜单 / 三级菜单 / 路径`。
2. 若 `路径` 非空，优先直接访问：`https://<shadow-test-host>{路径}`。
3. 若用户提供 stage/online 环境，将 host 替换为对应 Shadow host，路径保持不变。
4. 页面打开后必须用 `snapshot` 或 `document.body.innerText` 验证页面内容与菜单层级一致，再开始执行用例步骤。
5. 本节路径来自旧版 Shadow 菜单接口，和下方 `# Shadow APP运营平台路径导航` 的 `/onion-backstage` 路径不是同一套路由，不要混用。

## 造数不可用时的取数兜底（强制）

当 `ops-ass`（脚本 / 接口 / Redis 特殊场景）**无法造出或验收**用例所需数据时，本 Skill 作为取数兜底，**禁止**因造数工具能力不足直接记失败或跳过断言。

```text
1. 明确缺什么数据（用户资产、订单号、退款状态、服务期、商品配置、洋葱币余额等）
2. 在下方「快速路径 / 菜单层级」选对应 Shadow 或 onion-backstage 菜单
3. playwright-cli 打开路径 → 用 userId / 手机号 / 订单号查询
4. snapshot 或抓 Network 保存证据到 web-run-*/artifacts/
5. 将取到的字段回填用例夹具，再继续 UI / 埋点步骤
```

| 需要的数据 | 优先菜单（Shadow） | 路径 |
| --- | --- | --- |
| 用户资料 / 洋葱币 / 资产核对 | 用户管理 / 用户信息 | `/shadow/#/shadow-admin/user-management` |
| 服务期 | 用户管理 / 服务期管理 | `/shadow/#/server-management/list` |
| 订单详情 / 支付状态 | 订单管理 / 订单管理 | `/shadow/#/shadow-admin/search` |
| 退款状态 | 退款管理 / 自动退款管理 | `/shadow/#/after-sales/refund-auto-v2` |
| 售后单 | 售后管理 / 售后管理 | `/shadow/#/after-sales/afterSales` |
| 发货 / 物流 | 发货管理 / 发货管理 | `/shadow/#/delivery` |
| 组合商品 / SKU | 商品中心 / 组合商品或 SKU 管理 | 见下方快速路径表 |
| 三方电商/非电商订单（后台查） | onion-backstage：通用三方 / 三方数据管理 | 见下文 onion-backstage 表 |

规则：

- 先造数、后 Shadow；只有造数链路失败或能力覆盖不到时才兜底取数。
- 页面可见字段优先；不够再用 Shadow 登录态请求后台 API，响应摘要入证据。
- 报告中写明：数据来源 = `ops-ass` 或 `shadow-path:<菜单路径>`，避免 silently 混用未标注来源的夹具。

## 快速路径

| 场景 | 一级菜单 | 二级菜单 | 三级菜单 | 路径 |
|---|---|---|---|---|
| 关于 | 关于 | - | - | `/shadow/#/` |
| 用户信息 | 用户管理 | 用户信息 | - | `/shadow/#/shadow-admin/user-management` |
| 发币/退款余额核对（门禁） | 用户管理 | 用户信息 | - | `/shadow/#/shadow-admin/user-management`（断言洋葱币到账/不回收时必查；退款另查退款管理） |
| 服务期管理 | 用户管理 | 服务期管理 | - | `/shadow/#/server-management/list` |
| 菜单配置管理 | 工具管理 | 菜单配置管理 | - | `/shadow/#/shadow-admin/menu-config` |
| 组合商品管理 | 商品中心 | 组合商品管理 | - | `/shadow/#/combination-product-management` |
| 组合商品管理（新） | 商品中心 | 组合商品管理（新） | - | `/shadow/#/shadow-admin/sku-group-good-manage` |
| 组合商品分组管理 | 商品中心 | 组合商品分组管理 | - | `/shadow/#/shadow-admin/commodity-CommodityGroups?type=list&from=commodityGroup` |
| 单品SKU | 商品中心 | SKU管理 | 单品SKU | `/shadow/#/shadow-admin/sku-management-single` |
| 组合SKU | 商品中心 | SKU管理 | 组合SKU | `/shadow/#/sku-management-combile` |
| 订单管理 | 订单管理 | 订单管理 | - | `/shadow/#/shadow-admin/search` |
| 发票管理 | 发票管理 | 发票管理 | - | `/shadow/#/shadow-admin/invoices-management` |
| 售后管理 | 售后管理 | 售后管理 | - | `/shadow/#/after-sales/afterSales` |
| 自动退款管理 | 退款管理 | 自动退款管理 | - | `/shadow/#/after-sales/refund-auto-v2` |
| 发货管理 | 发货管理 | 发货管理 | - | `/shadow/#/delivery` |
| 权限管理 | 配置管理 | 权限管理 | - | `/shadow/#/shadow-admin/authManagement` |
| 申请功能权限 | 配置管理 | 申请功能权限 | - | `/shadow/#/shadow-admin/apply-permission` |

## Shadow 运营平台菜单层级表

| 字段 | 内容 |
|---|---|
| 页面 URL | https://<shadow-test-host>/shadow/#/ |
| 菜单来源 | https://<shadow-test-host>/api/shadow-user/menu-config/menus?platform=shadow |
| 提取方式 | 使用测试环境登录态打开旧版 Shadow 页面后，通过菜单接口读取 `menus` 树并按 `children` 扁平化 |
| 一级菜单数 | 21 |
| 表格行数 | 108 |

## 菜单层级

| 序号 | 一级菜单 | 二级菜单 | 三级菜单 | 路径 |
|---:|---|---|---|---|
| 1 | 关于 | - | - | `/shadow/#/` |
| 2 | 封控管理 | 用户行为日志 | - | `/shadow/#/shadow-admin/login-management/login-log` |
| 3 | 封控管理 | 封禁列表 | - | `/shadow/#/shadow-admin/login-management/ban-list` |
| 4 | 封控管理 | 校验管理 | - | `/shadow/#/shadow-admin/login-management/verify-list` |
| 5 | 封控管理 | 下单白名单列表 | - | `/shadow/#/shadow-admin/login-management/order-white-list` |
| 6 | 用户管理 | 用户信息 | - | `/shadow/#/shadow-admin/user-management` |
| 7 | 用户管理 | 用户功能权限配置 | - | `/shadow/#/shadow-admin/user-feature-config` |
| 8 | 用户管理 | 用户注销查询 | - | `/shadow/#/shadow-admin/user-logout-search` |
| 9 | 用户管理 | 手机号绑定历史查询 | - | `/shadow/#/bindPhone-history` |
| 10 | 用户管理 | 批量创建用户 | - | `/shadow/#/multi-create-user` |
| 11 | 用户管理 | 批量用户奖励 | - | `/shadow/#/shadow-admin/multi-set-reward/list` |
| 12 | 用户管理 | 批量发代金券 | - | `/shadow/#/HandselVoucherPro` |
| 13 | 用户管理 | 批量发送消息 | - | `/shadow/#/multi-send-message-new` |
| 14 | 用户管理 | 禁闭室 | - | `/shadow/#/shadow-admin/disable-room` |
| 15 | 用户管理 | 禁言用户管理 | - | `/shadow/#/disable-send-msg-account-manage` |
| 16 | 用户管理 | 服务期管理 | - | `/shadow/#/server-management/list` |
| 17 | 投诉管理 | 微信商户投诉 | - | `/shadow/#/shadow-admin/complaintManage` |
| 18 | 投诉管理 | 支付宝商户投诉 | - | `/shadow/#/shadow-admin/alipayComplaintManage` |
| 19 | 虚拟资产管理 | 兑换码管理 | - | `/shadow/#/redeem-code` |
| 20 | 虚拟资产管理 | 兑换码审批 | - | `/shadow/#/redeem-code-list` |
| 21 | 虚拟资产管理 | 体验券管理 | - | `/shadow/#/experience-ticket` |
| 22 | 虚拟资产管理 | 社群代金券管理 | - | `/shadow/#/CommunityVoucher/list` |
| 23 | 工具管理 | 平板锁机工具 | - | `/shadow/#/shadow-admin/locking` |
| 24 | 工具管理 | 用户分层工具 | - | `/shadow/#/shadow-admin/layering` |
| 25 | 工具管理 | 订单分层工具 | 订单分层配置 | `/shadow/#/shadow-admin/orderLayering` |
| 26 | 工具管理 | 订单分层工具 | 批量录入订单 | `/shadow/#/shadow-admin/enterOrderInfo` |
| 27 | 工具管理 | 短信管理 | - | `/shadow/#/shortMessage/list` |
| 28 | 工具管理 | 授权配置管理 | - | `/shadow/#/shadow-admin/authorization-manager-list` |
| 29 | 工具管理 | 授权日志 | - | `/shadow/#/shadow-admin/authorization-log` |
| 30 | 工具管理 | 权益更新策略 | - | `/shadow/#/shadow-admin/authStrategy` |
| 31 | 工具管理 | 短链接管理 | - | `/shadow/#/shadow-admin/short-link` |
| 32 | 工具管理 | 注册入口管理 | - | `/shadow/#/shadow-admin/register-entry` |
| 33 | 工具管理 | productId管理 | - | `/shadow/#/shadow-admin/productId-list` |
| 34 | 工具管理 | 体验券reason管理 | - | `/shadow/#/experience-ticket/reason` |
| 35 | 工具管理 | 日志平台管理 | - | `/shadow/#/shadow-admin/journal-platform` |
| 36 | 工具管理 | 文件工具 | - | `/shadow/#/uploadFile` |
| 37 | 工具管理 | 对象存储管理 | - | `/shadow/#/shadow-admin/yc-oss/bucket` |
| 38 | 工具管理 | 审批事件消息管理 | - | `/shadow/#/approveMessageManagement` |
| 39 | 工具管理 | 用户type管理 | - | `/shadow/#/userTypeManagement` |
| 40 | 工具管理 | 数据导出任务中心 | - | `/shadow/#/shadow-admin/download-center` |
| 41 | 工具管理 | 菜单配置管理 | - | `/shadow/#/shadow-admin/menu-config` |
| 42 | 内容审核管理 | 昵称审核管理 | - | `/shadow/#/NickNameManage` |
| 43 | 内容审核管理 | 好友昵称审核管理 | - | `/shadow/#/FriendNickName` |
| 44 | 内容审核管理 | 昵称机审拒绝 | - | `/shadow/#/NickNameAiReject` |
| 45 | 内容审核管理 | 洋葱敏感词管理 | - | `/shadow/#/SensitiveWord` |
| 46 | 商品中心 | 组合商品管理 | - | `/shadow/#/combination-product-management` |
| 47 | 商品中心 | 组合商品管理（新） | - | `/shadow/#/shadow-admin/sku-group-good-manage` |
| 48 | 商品中心 | 组合商品类目管理 | - | `/shadow/#/shadow-admin/combination-good-kind-management` |
| 49 | 商品中心 | 组合商品分组管理 | - | `/shadow/#/shadow-admin/commodity-CommodityGroups?type=list&from=commodityGroup` |
| 50 | 商品中心 | IOS商品价格管理 | - | `/shadow/#/shadow-admin/ios-amount-config` |
| 51 | 商品中心 | 鸿蒙商品价格管理 | - | `/shadow/#/shadow-admin/harmony-amount-config` |
| 52 | 商品中心 | SKU管理 | 单品SKU | `/shadow/#/shadow-admin/sku-management-single` |
| 53 | 商品中心 | SKU管理 | 组合SKU | `/shadow/#/sku-management-combile` |
| 54 | 商品中心 | SKU管理 | 组合SKU(新) | `/shadow/#/shadow-admin/sku-management-combine` |
| 55 | 商品中心 | 积分商品管理 | - | `/shadow/#/shadow-admin/integral_commodity_list` |
| 56 | 商品中心 | 商品快照 | - | `/shadow/#/shadow-admin/CommodityList` |
| 57 | 营销工具 | 商品直降 | - | `/shadow/#/shadow-admin/good-price-drop` |
| 58 | 营销工具 | 续购 | - | `/shadow/#/shadow-admin/xugou-good-price-drop` |
| 59 | 营销工具 | 保价 | - | `/shadow/#/shadow-admin/marking-tool-protect-price` |
| 60 | 营销工具 | 随单赠品 | - | `/shadow/#/shadow-admin/marking-tool-free-gift` |
| 61 | 营销工具 | 单后赠品 | - | `/shadow/#/shadow-admin/marking-tool-gift` |
| 62 | 营销工具 | 补差价 | - | `/shadow/#/shadow-admin/marking-diff-price` |
| 63 | 营销工具 | 补差价补充优惠 | - | `/shadow/#/shadow-admin/diff-price-supplemental-discount` |
| 64 | 库存管理 | 安全库存监控 | - | `/shadow/#/warehouse/safetyStockMonitor` |
| 65 | 库存管理 | SKU总库存 | - | `/shadow/#/warehouse/stockList` |
| 66 | 库存管理 | 分仓库存 | - | `/shadow/#/warehouse/warehouseStock` |
| 67 | 库存管理 | 库存校验记录 | - | `/shadow/#/warehouse/skuStockCheck` |
| 68 | 库存管理 | 周转率看板 | - | `/shadow/#/warehouse/turnoverRate` |
| 69 | 订单管理 | 订单管理 | - | `/shadow/#/shadow-admin/search` |
| 70 | 订单管理 | 积分订单管理 | - | `/shadow/#/shadow-admin/integral-order` |
| 71 | 订单管理 | 公域多胎策略查询 | - | `/shadow/#/shadow-admin/multi-child-order-query` |
| 72 | 发票管理 | 发票管理 | - | `/shadow/#/shadow-admin/invoices-management` |
| 73 | 售后管理 | 售后管理 | - | `/shadow/#/after-sales/afterSales` |
| 74 | 售后管理 | 退货管理 | - | `/shadow/#/after-sales/returnGoods` |
| 75 | 售后管理 | 以旧换新 | - | `/shadow/#/oldDeviceExchangeNew` |
| 76 | 售后管理 | 硬件验机管理 | - | `/shadow/#/after-sales/inspection` |
| 77 | 售后管理 | 硬件验机查询 | - | `/shadow/#/after-sales/inspectionQuery` |
| 78 | 售后管理 | 维修管理 | - | `/shadow/#/after-sales/repair` |
| 79 | 售后管理 | 换货管理 | - | `/shadow/#/after-sales/exchange` |
| 80 | 退款管理 | 非自动退款管理 | - | `/shadow/#/after-sales/refund-v2` |
| 81 | 退款管理 | 自动退款管理 | - | `/shadow/#/after-sales/refund-auto-v2` |
| 82 | 退款管理 | 批量退款管理 | - | `/shadow/#/after-sales/refund-batch` |
| 83 | 仓储管理 | 出库管理 | - | `/shadow/#/warehouse/outboundDeliveryManagement` |
| 84 | 仓储管理 | 出库时效监控 | - | `/shadow/#/warehouse/outboundMonitor` |
| 85 | 仓储管理 | 入库管理 | - | `/shadow/#/warehouse/warehousingManagement` |
| 86 | 仓储管理 | 采购管理 | - | `/shadow/#/warehouse/procurementManagement/list` |
| 87 | 仓储管理 | 出入库看板 | - | `/shadow/#/warehouse/inoutDashboard` |
| 88 | 发货管理 | 发货管理 | - | `/shadow/#/delivery` |
| 89 | 发货管理 | 发货策略 | - | `/shadow/#/delivery/deliveryStrategy` |
| 90 | 发货管理 | 发货申请 | - | `/shadow/#/delivery/apply` |
| 91 | 发货管理 | 物流拦截记录 | - | `/shadow/#/delivery/intercept` |
| 92 | 分佣系统 | 分佣规则管理 | - | `/shadow/#/shadow-admin/commission-rule-list` |
| 93 | 供应链基础数据 | 快递编码映射 | - | `/shadow/#/delivery/expressConfig` |
| 94 | 供应链基础数据 | 常用地址管理 | - | `/shadow/#/delivery/addressManage` |
| 95 | 供应链基础数据 | 成本承担部门 | - | `/shadow/#/delivery/costDepartment` |
| 96 | 供应链基础数据 | 供应商管理 | - | `/shadow/#/shadow-admin/supplierManage` |
| 97 | 应用管理 | 包更新管理 | - | `/shadow/#/apk-upload-manage` |
| 98 | 应用管理 | 渠道打包管理 | - | `/shadow/#/apk-channel` |
| 99 | 应用管理 | 投放渠道管理 | - | `/shadow/#/serving-channel` |
| 100 | 应用管理 | 打包列表管理 | - | `/shadow/#/pack-management` |
| 101 | 应用管理 | iOS审核开关管理 | - | `/shadow/#/pay-management` |
| 102 | 平板管理 | 平板管理 | - | `/shadow/#/shadow-admin/pad-fixed-price-detail` |
| 103 | 平板管理 | 一口价平板 | - | `/shadow/#/shadow-admin/pad-fixed-price-list` |
| 104 | 平板管理 | 一口价平板-补发授权 | - | `/shadow/#/shadow-admin/pad-fixed-price-course` |
| 105 | 配置管理 | 成员管理 | - | `/shadow/#/shadow-admin/shadow-users` |
| 106 | 配置管理 | 权限管理 | - | `/shadow/#/shadow-admin/authManagement` |
| 107 | 配置管理 | 权限配置管理 | - | `/shadow/#/shadow-admin/permission/config` |
| 108 | 配置管理 | 申请功能权限 | - | `/shadow/#/shadow-admin/apply-permission` |

# Shadow APP运营平台路径导航

## 使用规则

当测试用例、需求或页面地址涉及 `<shadow-test-host>/onion-backstage`、APP运营平台、菜单层级、通用三方、抖店、三方订单管理等场景时，先按本 Skill 查找菜单路径，再执行 `playwright-cli`。

1. 根据用例中的页面、模块或菜单名，在下方表格定位 `一级菜单 / 二级菜单 / 三级菜单 / 路径`。
2. 若 `路径` 非空，优先直接访问：`https://<shadow-test-host>{路径}`。
3. 若用户提供 stage/online 环境，将 host 替换为对应 Shadow host，路径保持不变。
4. 若 `路径` 为 `-`，说明该行是分组节点，不是可直接访问页面；应点击对应菜单层级展开，再选择其子菜单。
5. 页面打开后必须用 `snapshot` 或 `document.body.innerText` 验证面包屑/页面内容与菜单层级一致，再开始执行用例步骤。

## 执行用例时的强制注意

- 不要把 APP运营平台路由误改为 `#/shadow-admin/...`。例如「通用三方」正确路径是 `/onion-backstage/revenue/channelManager/commonOrder`；「三方数据管理」正确路径是 `/onion-backstage/revenue/channelManager/outerDataManager`。
- 通用三方页面默认 Tab 是「电商平台」。测非电商时必须先点「非电商平台」Tab，再断言列表。
- 非电商订单造数入口是「三方数据管理」上传，不是通用三方页本身。
- 不要仅凭目标 URL 加载失败就判定功能不可达；先用本表确认菜单路径，再访问完整 URL。
- 若需要读取菜单配置，优先使用已加载页面和本 Skill 表格；原生 `fetch` 未携带 `ShadowAuthorization` / `Authorization` 可能返回 401，不能把这种手动探针 401 当作登录失败。
- 对菜单相关用例，报告中必须记录实际使用的菜单路径和打开后的面包屑。

## 快速路径

| 场景 | 一级菜单 | 二级菜单 | 三级菜单 | 路径 |
|---|---|---|---|---|
| 通用三方订单 | 三方订单管理 | 通用三方 | - | `/onion-backstage/revenue/channelManager/commonOrder` |
| 三方数据管理（非电商上传造数） | 三方订单管理 | 三方数据管理 | - | `/onion-backstage/revenue/channelManager/outerDataManager` |
| 抖店订单 | 三方订单管理 | 抖店 | - | `/onion-backstage/revenue/channelManager/douyinOrder` |
| 微店订单 | 三方订单管理 | 微店 | - | `/onion-backstage/revenue/channelManager/douyin` |
| 掉单管理 | 三方订单管理 | 掉单管理 | - | `/onion-backstage/revenue/channelManager/droppedOrder` |
| 激活链接配置 | 三方订单管理 | 激活链接配置 | - | `/onion-backstage/revenue/channelManager/activationLinkConfig` |

## APP运营平台菜单层级表

| 字段 | 内容 |
|---|---|
| 页面 URL | https://<shadow-test-host>/onion-backstage/revenue/channelManager/commonOrder |
| 菜单来源 | https://<micro-app-host>/onion-backstage-menu/app-4c48bd3db16627172706.js |
| 提取方式 | 使用 `.claude/skills/web_cli/` 打开页面后，解析已加载的 `onion-backstage-menu` 前端包菜单数组；动态运行时菜单以当前源码可解析层级为准 |
| 一级菜单数 | 8 |
| 表格行数 | 99 |

## 菜单层级

| 序号 | 一级菜单 | 二级菜单 | 三级菜单 | 路径 |
|---:|---|---|---|---|
| 1 | 微信生态 | 小程序 | 客服回复管理 | /onion-backstage/revenue/customerNumManage |
| 2 | 微信生态 | 微信账号 | - | /onion-backstage/revenue/wechartAccount |
| 3 | App配置 | 宝藏页配置 | 发现页卡片-C端 | /onion-backstage/revenue/teasureResources/discoverCardCategory |
| 4 | App配置 | 宝藏页配置 | 发现页卡片-B端 | /onion-backstage/revenue/teasureResources/discoverCardCategoryB |
| 5 | App配置 | 宝藏页配置 | 课程管理-C端 | /onion-backstage/revenue/teasureResources/treasureCourse |
| 6 | App配置 | 宝藏页配置 | 课程管理-B端 | /onion-backstage/revenue/teasureResources/treasureBCourse |
| 7 | App配置 | 宝藏页配置 | 宝藏tab-课程推荐 | /onion-backstage/revenue/teasureResources/treasureRecommendCategory |
| 8 | App配置 | 直播配置 | - | /onion-backstage/revenue/liveConfig |
| 9 | App配置 | App付费页落地页配置 | - | /onion-backstage/revenue/paymentResource |
| 10 | App配置 | 付费介绍页商品-C端 | - | /onion-backstage/revenue/paymentGoodConfig |
| 11 | App配置 | 付费介绍页商品-B端 | - | /onion-backstage/revenue/paymentBGoodConfig |
| 12 | App配置 | 运营资源位 | 资源位曝光自查 | /onion-backstage/space-admin/operatingResources/exposureQuery |
| 13 | App配置 | 运营资源位 | Banner管理 | /onion-backstage/space-admin/operatingResources/banner |
| 14 | App配置 | 运营资源位 | 问卷调研管理 | /onion-backstage/space-admin/operatingResources/examSurvey |
| 15 | App配置 | 运营资源位 | 消息通知管理 | /onion-backstage/space-admin/operatingResources/notification |
| 16 | App配置 | 运营资源位 | 弹窗管理 | /onion-backstage/space-admin/operatingResources/popup |
| 17 | App配置 | 运营资源位 | 开屏页管理 | /onion-backstage/space-admin/operatingResources/openScreen |
| 18 | App配置 | 运营资源位 | 口令管理 | /onion-backstage/space-admin/operatingResources/configPassword |
| 19 | App配置 | 运营资源位 | 资源位策略平台 | /onion-backstage/space-admin/operatingResources/resourceNicheConfig |
| 20 | App配置 | 运营资源位 | 测试白名单 | /onion-backstage/space-admin/operatingResources/whitePeoplelist |
| 21 | App配置 | 运营资源位 | 资源位活动管理 | /onion-backstage/space-admin/operatingResources/activity |
| 22 | App配置 | 运营资源位 | 资源位黑名单管理 | /onion-backstage/space-admin/operatingResources/activityBlackList |
| 23 | App配置 | 运营资源位 | 教学区NPC管理 | /onion-backstage/space-admin/operatingResources/worldNpc |
| 24 | App配置 | 运营资源位 | 教学区NPC对白管理 | /onion-backstage/space-admin/operatingResources/npcDialogue |
| 25 | App配置 | 课程配置 | 学科上新 | /onion-backstage/revenue/courseConfig/newSubjectConfig |
| 26 | App配置 | 其他配置 | 跳转配置管理 | /onion-backstage/space-admin/other/jumpConfig |
| 27 | App配置 | 其他配置 | 后端配置后台 | /onion-backstage/space-admin/other/backstageConfig |
| 28 | App配置 | 其他配置 | 线上手术刀 | /onion-backstage/space-admin/other/mobileBugHolder |
| 29 | App配置 | 其他配置 | 诊断配置后台 | /onion-backstage/space-admin/other/mobileDiagnosisConfig |
| 30 | App配置 | 其他配置 | 旧版-xlab灰度发布控制 | /onion-backstage/revenue/other/xlabLevel |
| 31 | App配置 | 其他配置 | xlab灰度发布控制 | /onion-backstage/revenue/other/new-xlabLevel |
| 32 | App配置 | 其他配置 | 旧版-AB测试平台 | /onion-backstage/revenue/other/abTestConfig |
| 33 | App配置 | 其他配置 | AB测试平台 | /onion-backstage/revenue/other/new-abTestConfig |
| 34 | App配置 | 其他配置 | C端Pad白名单管理页 | /onion-backstage/revenue/other/clientWhiteList |
| 35 | App配置 | 其他配置 | 巡检平台告警订阅 | /onion-backstage/space-admin/other/monitorSubcripiton |
| 36 | App配置 | 其他配置 | 电销引流入口配置 | - |
| 37 | App配置 | 其他配置 | 世界观故事配置 | /onion-backstage/space-admin-next/other/world |
| 38 | App配置 | 其他配置 | 世界观专辑配置 | /onion-backstage/space-admin-next/other/worldAlbum |
| 39 | App配置 | 其他配置 | 协议配置后台 | /onion-backstage/space-admin/other/configurationConfig |
| 40 | App配置 | 其他配置 | 服务降级配置 | /onion-backstage/space-admin/other/degradationManage |
| 41 | App配置 | 其他配置 | 电销渠道活码 | /onion-backstage/revenue/other/channelId |
| 42 | App配置 | 其他配置 | EventTrigger配置 | - |
| 43 | App配置 | 弹幕管理 | 弹幕预设 | /onion-backstage/space-admin/barrage/preset |
| 44 | App配置 | 弹幕管理 | 弹幕举报处理 | /onion-backstage/space-admin/barrage/complaint |
| 45 | App配置 | 弹幕管理 | 弹幕汇总处理 | /onion-backstage/space-admin/barrage/summary |
| 46 | App配置 | 弹幕管理 | 用户管理 | /onion-backstage/space-admin/barrage/users |
| 47 | App配置 | 弹幕管理 | 热词管理 | /onion-backstage/space-admin/barrage/hotkeys |
| 48 | App配置 | 答疑管理 | 在线答疑 | /onion-backstage/study-admin/answerQuestion/online |
| 49 | App配置 | 答疑管理 | 答疑预设 | /onion-backstage/study-admin/answerQuestion/preset |
| 50 | App配置 | 答疑管理 | 题目评审 | /onion-backstage/study-admin/answerQuestion/operationReviewQuestion |
| 51 | App配置 | 答疑管理 | 回答评审 | /onion-backstage/study-admin/answerQuestion/operationReviewAnswer |
| 52 | App配置 | 答疑管理 | 加精评审 | /onion-backstage/study-admin/answerQuestion/operationReviewDigest |
| 53 | App配置 | 答疑管理 | 举报评审 | /onion-backstage/study-admin/answerQuestion/reportReview |
| 54 | App配置 | 答疑管理 | 评审记录-题目 | /onion-backstage/study-admin/answerQuestion/operationHistoryQuestion |
| 55 | App配置 | 答疑管理 | 评审记录-回答 | /onion-backstage/study-admin/answerQuestion/operationHistoryAnswer |
| 56 | App配置 | 答疑管理 | 评审记录-举报 | /onion-backstage/study-admin/answerQuestion/operationHistoryReport |
| 57 | App配置 | 学情报告 | 日志管理 | /onion-backstage/space-admin/study-report-management/log |
| 58 | IDC反馈管理 | 首页 | - | /onion-backstage/idc-admin/baskage |
| 59 | IDC反馈管理 | App反馈管理 | 反馈管理 | /onion-backstage/idc-admin/feedbacks/configList |
| 60 | IDC反馈管理 | 反馈列表 | - | - |
| 61 | 学生运营 | 运营活动管理后台 | 抽奖信息管理 | /onion-backstage/space-admin-next/activityManager/drawAddress |
| 62 | 学生运营 | 运营活动管理后台 | 成就配置管理 | /onion-backstage/space-admin-next/activityManager/achieveManage |
| 63 | 学生运营 | 洋葱TV管理后台 | 标签管理 | /onion-backstage/space-admin-next/onionTV/onionTVTag |
| 64 | 学生运营 | 洋葱TV管理后台 | 话题管理 | /onion-backstage/space-admin-next/onionTV/onionTVTopic |
| 65 | 学生运营 | 洋葱TV管理后台 | 内容管理 | /onion-backstage/space-admin-next/onionTV/onionTVContents |
| 66 | 学生运营 | 多维运营后台 | 创建目标用户 | /onion-backstage/space-admin/usersTap/tag |
| 67 | 学生运营 | 多维运营后台 | 创建用户策略 | /onion-backstage/space-admin/usersTap/strategy |
| 68 | 学生运营 | 多维运营后台 | 策略审核系统 | /onion-backstage/space-admin/usersTap/strategyAuditList |
| 69 | 学生运营 | 多维运营后台 | 创建奖励 | /onion-backstage/space-admin/usersTap/reward |
| 70 | 学生运营 | 社区运营 | 敏感词库配置 | /onion-backstage/space-admin-next/communityManager/sensitiveWords |
| 71 | 学生运营 | 社区运营 | 机审拒绝内容 | /onion-backstage/space-admin-next/communityManager/machineAudit |
| 72 | 学生运营 | 社区运营 | 安全审核后台 | /onion-backstage/space-admin-next/communityManager/securityAuditing |
| 73 | 学生运营 | 社区运营 | 高热审核后台 | /onion-backstage/space-admin-next/communityManager/hotReview |
| 74 | 学生运营 | 社区运营 | 圈子管理后台 | /onion-backstage/space-admin-next/communityManager/groupManage |
| 75 | 学生运营 | 社区运营 | 话题管理后台 | /onion-backstage/space-admin-next/communityManager/topicManager |
| 76 | 学生运营 | 社区运营 | TAB管理后台 | /onion-backstage/space-admin-next/communityManager/tabConfig |
| 77 | 学生运营 | 社区运营 | 内容管理后台 | /onion-backstage/space-admin-next/communityManager/contentsManager |
| 78 | 学生运营 | 社区运营 | 传参配置后台 | /onion-backstage/space-admin-next/communityManager/configManager |
| 79 | 学生运营 | 社区运营 | 社区黑名单 | /onion-backstage/space-admin-next/communityManager/blackUserManager |
| 80 | 学生运营 | 社区运营 | P/UGC管理后台 | /onion-backstage/space-admin-next/communityManager/pUGCManager |
| 81 | 学生运营 | 社区运营 | 社区资源位 | /onion-backstage/space-admin-next/communityManager/resourceManager |
| 82 | 学生运营 | 社区运营 | 用户信息审核后台 | /onion-backstage/space-admin-next/communityManager/userInfoManager |
| 83 | 学生运营 | 社区运营 | 社区屏蔽 | /onion-backstage/space-admin-next/communityManager/shieldingManager |
| 84 | 学生运营 | 社区运营 | 社区防沉迷 | /onion-backstage/space-admin-next/communityManager/antiAddictionWhiteListManager |
| 85 | 学生运营 | 社区运营 | 社区发帖白名单 | /onion-backstage/space-admin-next/communityManager/whiteUserManager |
| 86 | 学生运营 | 社区运营 | 举报审核后台 | /onion-backstage/space-admin-next/communityManager/reportManager |
| 87 | 渠道投放 | 检测链接 | - | /onion-backstage/revenue/channelManager/monitoringLink |
| 88 | 三方订单管理 | 微店 | - | /onion-backstage/revenue/channelManager/douyin |
| 89 | 三方订单管理 | 抖店 | - | /onion-backstage/revenue/channelManager/douyinOrder |
| 90 | 三方订单管理 | 通用三方 | - | /onion-backstage/revenue/channelManager/commonOrder |
| 91 | 三方订单管理 | 掉单管理 | - | /onion-backstage/revenue/channelManager/droppedOrder |
| 92 | 三方订单管理 | 三方数据管理 | - | /onion-backstage/revenue/channelManager/outerDataManager |
| 93 | 三方订单管理 | 激活链接配置 | - | /onion-backstage/revenue/channelManager/activationLinkConfig |
| 94 | 激励体系 | 类别管理 | - | /onion-backstage/space-admin-next/deskGameManager/categoryManager |
| 95 | 激励体系 | 物品管理 | - | /onion-backstage/space-admin-next/deskGameManager/resourceManager |
| 96 | 规划班后台 | 模板管理后台 | 模板管理 | /onion-backstage/space-admin-next/aiClassManager/templatesManage |
| 97 | 规划班后台 | 模板管理后台 | 班型管理 | /onion-backstage/space-admin-next/aiClassManager/allClassTemManage |
| 98 | 规划班后台 | 模板管理后台 | 班型管理（旧） | /onion-backstage/space-admin/aiClassManager/classTemplatesManage |
| 99 | 规划班后台 | 模板管理后台 | 定制班成就配置 | /onion-backstage/space-admin/aiClassManager/achieveManage |
