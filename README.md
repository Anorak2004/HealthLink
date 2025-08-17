# HealthLink - AI驱动的共病管理平台

## 项目概述

HealthLink是一个面向社区慢病共病管理的AI驱动云平台，构建"1平台 + 2端 + 3层服务"的可扩展系统：

- **1平台**: AI驱动的共病管理云平台
- **2端**: 患者小程序、医生工作台  
- **3层服务**: 智能筛查 → 个性化干预 → 效果追踪

## 快速开始

### 环境要求

- Python 3.11+
- SQLite (默认) 或 MySQL 8.0+
- Docker & Docker Compose (可选)

### 快速启动 (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd HealthLink
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **测试修复** (可选)
```bash
python test_fix.py
```

4. **启动完整系统**
```bash
# 方式1: 使用Docker Compose (推荐)
docker-compose up -d

# 方式2: 分别启动服务
python start_server.py        # Gateway API (端口8000)
python start_icer_engine.py   # ICER Engine (端口8090)
```

5. **验证服务**
```bash
# 测试Gateway API
curl http://localhost:8000/health

# 测试ICER Engine
curl http://localhost:8090/health

# 运行集成测试
python test_icer_integration.py
```

### 传统安装步骤

2. **安装依赖**
```bash
pip install -e .
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

4. **初始化数据库**
```bash
python -m healthlink.cli init-db
```

5. **创建示例数据**
```bash
python -m healthlink.cli create-sample-data
```

6. **启动服务**
```bash
python -m healthlink.cli serve
```

服务启动后，访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### Docker部署

```bash
# 使用SQLite (默认)
docker-compose up -d gateway-api

# 使用MySQL
docker-compose --profile mysql up -d

# 包含监控
docker-compose --profile mysql --profile monitoring up -d
```

## API接口

### 核心接口

#### 患者管理
- `POST /api/v1/patients` - 创建患者
- `GET /api/v1/patients` - 查询患者列表
- `GET /api/v1/patients/{patient_id}` - 获取患者详情
- `PUT /api/v1/patients/{patient_id}` - 更新患者信息

#### 筛查服务
- `POST /api/v1/screenings` - 创建筛查记录
- `POST /api/v1/screenings/{screening_id}:triage` - 执行分诊
- `GET /api/v1/screenings` - 查询筛查列表

#### ICER评估
- `POST /api/v1/icer/policies` - 创建ICER策略
- `GET /api/v1/icer/policies` - 查询策略列表
- `POST /api/v1/icer/evaluate` - 执行ICER评估

#### 干预管理
- `POST /api/v1/interventions` - 创建干预计划
- `POST /api/v1/interventions/{intervention_id}:approve` - 审批干预
- `GET /api/v1/interventions` - 查询干预列表

#### 效果追踪
- `POST /api/v1/outcomes` - 创建效果记录
- `GET /api/v1/outcomes` - 查询效果列表

### 示例请求

#### 创建患者
```bash
curl -X POST "http://localhost:8000/api/v1/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P003",
    "name": "王五",
    "gender": "M",
    "birth_date": "1965-03-10",
    "phone": "13800138003",
    "email": "wangwu@example.com"
  }'
```

#### 执行ICER评估
```bash
# 通过Gateway API
curl -X POST "http://localhost:8000/api/v1/icer/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "intervention_cost": 5000.0,
    "intervention_effectiveness": 0.2,
    "population_size": 100,
    "time_horizon": 5
  }'

# 直接调用ICER Engine
curl -X POST "http://localhost:8090/v1/icer/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "comparator": {
      "cost": 10000,
      "effect": 0.8,
      "effect_unit": "QALY"
    },
    "intervention": {
      "cost": 12000,
      "effect": 1.1,
      "effect_unit": "QALY"
    }
  }'
```

## 配置说明

### 数据库切换

编辑 `config/settings.yaml`:

```yaml
database:
  type: "mysql"  # sqlite -> mysql
  mysql:
    host: "localhost"
    port: 3306
    database: "healthlink"
    username: "${MYSQL_USER}"
    password: "${MYSQL_PASSWORD}"
```

### AI模型切换

```yaml
ai_models:
  nlp:
    provider: "local"  # api -> local
    local:
      model_path: "models/nlp/clinical-bert"
      device: "cpu"
```

## 开发工具

### CLI命令

```bash
# 检查配置
python -m healthlink.cli check-config

# 健康检查
python -m healthlink.cli health-check

# 初始化数据库
python -m healthlink.cli init-db

# 创建示例数据
python -m healthlink.cli create-sample-data

# 启动服务
python -m healthlink.cli serve --reload
```

### 代码质量

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 代码格式化
black .
isort .

# 代码检查
ruff check .
mypy .

# 运行测试
pytest
```

## 项目结构

```
HealthLink/
├── config/                 # 配置文件
│   ├── settings.yaml       # 主配置
│   ├── database_switch.py  # 数据库切换
│   └── model_switch.py     # AI模型切换
├── packages/
│   └── schemas/            # 数据模型
├── services/
│   └── gateway-api/        # API网关服务
├── healthlink/             # CLI工具
├── data/                   # SQLite数据库
├── logs/                   # 日志文件
└── infra/                  # 基础设施配置
```

## MVP功能特性

### ✅ 已实现 (M1 + M2)
- [x] 统一API网关和路由
- [x] 患者管理CRUD
- [x] 独立ICER Engine微服务
- [x] ICER/INB评估与策略管理
- [x] 支配性分析和不确定性分析
- [x] 数据库抽象层 (SQLite/MySQL切换)
- [x] AI模型抽象层 (API/本地切换)
- [x] 统一错误处理和日志
- [x] 请求追踪和审计
- [x] 健康检查和监控端点
- [x] Docker容器化部署

### 🚧 开发中 (M3-M5)
- [ ] 筛查服务 (NLP/ASR集成)
- [ ] 干预决策服务
- [ ] 效果追踪服务
- [ ] 工作流编排
- [ ] 前端应用

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Pydantic
- **数据库**: SQLite (开发) / MySQL (生产)
- **缓存**: 内存 (开发) / Redis (生产)
- **监控**: Prometheus + 结构化日志
- **部署**: Docker + Docker Compose
- **AI集成**: HTTP API调用 (可切换本地模型)

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feat/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送分支 (`git push origin feat/new-feature`)
5. 创建Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: HealthLink Team
- 邮箱: HealthLink@anorakovo.site
- 文档: [项目Wiki](docs/)

---

**注意**: 这是MVP版本，部分功能仍在开发中。生产环境使用前请确保完成安全配置和性能优化。
