# HealthLink — 项目目录规划（Monorepo）

```
HealthLink/
  docs/
    openapi.yaml
    ADRs/
    playbooks/
    PROJECT_STRUCTURE.md
    RULES.md
    REQUIREMENTS.md
  apps/
    patient-miniapp/
    doctor-console/
    admin-ops/
  services/
    gateway-api/
    icer-engine/
    screening-service/
    intervention-service/
    outcomes-service/
    nlp-service/
    asr-keywords-service/
    kg-comorbidity-service/
    workflow-orchestrator/
    fl-connector/
    data-ingest/
  packages/
    schemas/
    clients/
    policies/
      icer/
        2025-08.json
  config/
    settings.yaml          # 主配置文件
    asr_keywords.json      # ASR关键词配置
    database_switch.py     # 数据库切换模块
    model_switch.py        # AI模型切换模块
  data/                    # SQLite数据库存储目录
  logs/                    # 日志文件目录
  models/                  # 本地AI模型存储目录 (预留)
    nlp/
    asr/
  infra/
    docker/
    k8s/
    observability/
  .github/workflows/
    ci.yml
  .env.example             # 环境变量模板
  .env                     # 环境变量文件 (git忽略)
  .pre-commit-config.yaml
  .spectral.yaml
  pyproject.toml
  README.md
  docker-compose.yml
```