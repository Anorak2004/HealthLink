# HealthLink — AI IDE 规则文档（工程/安全/评测）

版本：v1.0（2025-08-16）

## 1. 代码与提交规则
- 分支：`main`（保护）、`feat/*`、`fix/*`、`chore/*`
- 提交：Conventional Commits（`feat: ...`/`fix: ...`/`docs: ...`）
- PR：原子改动；包含说明、测试与自测命令；CI 绿灯才可合并
- 风格与静态检查：Python（black/isort/ruff/mypy）、前端（eslint/prettier）、OpenAPI（spectral）
- pre-commit 强制：本地或 CI 均需通过

## 2. API/Schema 规则
- REST：复数资源、动作用 `:action`、分页/排序参数标准化
- 版本：破坏性变更升 `/v2`；Schema 增量变化需向后兼容
- 错误：统一 `error.code/message/request_id`
- 幂等：非幂等 POST 支持 `Idempotency-Key`
- 契约优先：先改 `docs/openapi.yaml` 再改实现，必须过 spectral

## 3. 安全/合规
- 鉴权：JWT/OAuth2；最小权限（例：`patient.read`, `intervention.write`）
- 数据保护：PII 脱敏；日志禁敏感明文；导出需二次确认
- 机密：由 KMS/环境变量管理；禁止入库
- 审计：所有跨边界动作记录操作者、时间、资源与请求 ID
- 保留：默认 180 天；遵守数据删除与访问审计

## 4. 可观测性
- 追踪：`X-Request-Id` + W3C `traceparent`
- 指标：每个服务暴露 `/metrics`；关键业务指标入看板
- 日志：JSON 结构化，含级别/时间/服务/trace/user/org（脱敏）

## 5. 测试策略
- 单元：核心逻辑与边界
- 契约：基于 OpenAPI 的客户端校验
- 集成：docker compose e2e
- 数据：NLP/ASR 基准评测；报告 F1/召回/误报率
- 回滚：策略/模型变更附回滚脚本与对比报告

## 6. 版本与发布
- 语义化版本：`MAJOR.MINOR.PATCH`
- 灰度：策略/模型按 cohort 灰度；服务滚动与一键回滚
- 变更记录：自动 CHANGELOG；策略文件目录化与元数据

## 7. AI IDE 使用规则
- 单模块改动；输出必须包含变更清单、diff 摘要、自测命令、更新文件列表
- 禁止引入未审计脚本；第三方模型与服务需列出许可与地域
- 严禁上传真实数据；仅用脱敏/合成样例

## 8. 升级触发条件（替代 → 正式）
- NLP：F1 ≥ 0.82 且误差分布稳定
- ASR：召回 ≥ 80%、误报 ≤ 10%、合规明确
- 图谱：≥2 机构 RWD，边权置信度达标
- ICER：RWD 校准差达标，允许从规则转概率更新
- 联邦：机构与审计就绪后切换“模拟→真实”