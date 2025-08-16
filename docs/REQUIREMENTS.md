# HealthLink — AI IDE 需求文档（用于分模块构建）
版本：v1.0（2025-08-16）

## 一、项目概述
- 目标：面向社区慢病共病管理，构建“1 平台 + 2 端 + 3 层服务”的可扩展系统：
  - 1 平台：AI 驱动的共病管理云平台
  - 2 端：患者小程序、医生工作台
  - 3 层服务：智能筛查 → 个性化干预 → 效果追踪
- 理论框架：安德森健康服务利用模型（倾向性 / 易得性 / 需要性）
- 当前策略：优先交付 MVP，接受“简化替代方案”，保持可插拔升级路线。

## 二、范围（M1–M5 必须，M6–M12 逐步）
- M1 Schemas & Gateway（REST 规范、JWT 鉴权、分页/错误模型、幂等键）
- M2 ICER Engine（阈值=37446 元/DALY 可配置；支持 cohort 覆盖）
- M3 Screening Service（NLP + ASR 关键词的初筛）
- M4 Intervention Service（画像→资源匹配→分层响应，接入 ICER 决策）
- M5 Outcomes Service（依从性/急诊/成本/QALY 指标回流）
- M6 NLP Service（规则 + HF Pipeline；后续可切换 BioBERT/临床模型）
- M7 ASR + Keywords（云 ASR + 热词 + 复核通道）
- M8 KG-Comorbidity（动态共病图谱）
- M9 Workflow Orchestrator（有状态编排，人工批准）
- M10 FL-Connector（模拟聚合→真实联邦切换）
- M11 前端应用（医生端 Web、患者小程序）
- M12 Data-Ingest & 合规治理（脱敏、审计、策略灰度）

## 三、功能性需求（摘取关键）
1. **REST API**：遵循 OpenAPI 3.0；资源复数命名、分页与排序、统一错误模型。
2. **ICER 决策**：输入方案与人群参数，输出 `icer_value/threshold/decision`；策略文件版本化。
3. **筛查**：接收 NLP 实体与 ASR 关键词，生成 triage（低/中/高），触发干预。
4. **干预**：根据（倾向/易得/需要）画像与资源约束生成干预计划；接入 ICER 进行经济性约束；支持人工批准。
5. **追踪**：记录依从性、急诊/再入院、成本与 QALY 指标；提供人群与个体查询；反哺策略更新。
6. **NLP/ASR**：NLP 先规则+Pipeline；ASR 先云转写+热词白名单+低置信度复核。
7. **图谱**：提供疾病对的风险倍数/证据查询；夜间任务按 RWD 校正边权（占位）。
8. **编排**：S1→S2→S3 图式流程；支持重试/超时/人工批准和回放。
9. **联邦**：接口与真实 FL 对齐，支持“模拟/真实”后端可切换。
10. **前端**：医生端优先，呈现筛查/干预/追踪；患者端提供随访与提醒。

## 四、非功能需求
- **安全与合规**：JWT/OAuth2；最小权限；审计日志；PII 脱敏；数据保留策略。
- **工程规范**：pre-commit（black/isort/ruff/mypy、eslint/prettier、spectral）；CI 必须绿色。
- **可观测性**：X-Request-Id、Traceparent；Prometheus 指标；结构化日志。
- **质量**：单测覆盖关键逻辑；契约测试与 e2e 回放；语义化版本管理。
- **性能目标（MVP）**：P95 API < 300ms；并发 < 50；错误率 < 0.5%。

## 五、按模块的验收标准（DoD）示例
- **M1**：`/v1/patients` 与 `/v1/icer/evaluate` 可用；OpenAPI 与实现一致；错误模型统一；CI 通过。
- **M2**：ICER 策略 JSON 可版本化与热更新；审计包含策略版本；单元测试覆盖规则分支。
- **M3**：输入模拟 EMR/语音转写可得到 triage；与 M4 对接成功；事件链路可回放。
- **M4**：干预决策包含资源匹配与 ICER 结果；人工批准流可用；可追溯决策来源。
- **M5**：可查询个体/人群成效；生成最小看板数据；推动策略更新事件（占位）。

## 六、AI IDE 提示词模板（每模块通用）
> 目标：实现 {模块名} 的 {功能}。  
> 约束：遵循 `docs/openapi.yaml`；Python 3.11 + FastAPI；使用 Pydantic；lint 必须通过。  
> 产出：代码、测试、README、OpenAPI 片段；更新 docker 与 compose。  
> 验证：提供 curl 示例、自测命令与 DoD 检查项。  
> 风险：列出可回滚方案与数据迁移脚本（若涉及）。

（具体到 M1–M5 的详细提示词可参考上一轮分模块计划。）

## 七、接口基线（节选）
- `GET/POST /v1/patients`
- `POST /v1/icer/evaluate`，`GET /v1/icer/policies`（版本化）
- `POST /v1/screenings`，`POST /v1/screenings/<built-in function id>:triage`
- `POST /v1/interventions`，`POST /v1/interventions/<built-in function id>:approve`
- `GET /v1/outcomes`（支持 patient_id）

## 八、里程碑
- 周 1：M1–M2
- 周 2：M3–M4
- 周 3：M5 + NLP/ASR 原型（M6–M7）
- 周 4：图谱/编排（M8–M9）
- 周 5–6：联邦/前端/治理（M10–M12）