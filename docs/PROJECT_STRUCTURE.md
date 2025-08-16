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
    gateway_api/             # API网关服务 (重命名为Python兼容)
    gateway-api/             # 原始目录 (可删除)
    icer_engine/             # ICER评估微服务 ✅ M2完成
      app/
        main.py              # FastAPI应用
        routers/
          evaluate.py        # ICER评估路由
        schemas/
          icer.py            # ICER数据模型
      tests/
        test_icer_engine.py  # 单元测试
      Dockerfile             # Docker镜像
      requirements.txt       # 依赖文件
      README.md              # 服务文档
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
  
  # 启动和测试脚本
  start_server.py          # Gateway API启动脚本
  start_icer_engine.py     # ICER Engine启动脚本
  start_all_services.py    # 完整系统启动脚本
  test_icer_integration.py # ICER Engine集成测试
  quality_check.py         # 质量检查脚本
  quick_test.py            # 快速测试脚本
```