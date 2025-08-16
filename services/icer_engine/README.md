# ICER Engine

独立的成本效果比评估微服务，提供ICER/INB评估与策略版本查询功能。

## 功能特性

- **ICER评估**: 计算增量成本效果比
- **支配性分析**: 检测简单支配和扩展支配关系
- **净效益计算**: 基于支付意愿阈值计算净效益
- **不确定性分析**: 概率敏感性分析和CEAC曲线
- **策略管理**: 版本化的阈值策略配置
- **多视角分析**: 支持社会、支付方、提供方视角

## 快速开始

### 本地运行

```bash
cd services/icer_engine

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8090
```

### Docker运行

```bash
# 构建镜像
docker build -t icer-engine .

# 运行容器
docker run -p 8090:8090 -v $(pwd)/../../packages/policies:/app/../packages/policies:ro icer-engine
```

### 使用Docker Compose

```bash
# 从项目根目录
docker-compose up -d icer_engine
```

## API接口

### 健康检查

```bash
curl http://localhost:8090/health
```

### 获取策略信息

```bash
curl http://localhost:8090/v1/icer/policies
```

### ICER评估

#### 基本评估

```bash
curl -s -X POST http://localhost:8090/v1/icer/evaluate \
  -H 'Content-Type: application/json' \
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

#### 带不确定性分析的评估

```bash
curl -s -X POST http://localhost:8090/v1/icer/evaluate \
  -H 'Content-Type: application/json' \
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
    },
    "uncertainty": {
      "se_cost_0": 1000,
      "se_cost_1": 1200,
      "se_eff_0": 0.08,
      "se_eff_1": 0.11,
      "samples": 1000
    }
  }'
```

#### 自定义阈值评估

```bash
curl -s -X POST http://localhost:8090/v1/icer/evaluate \
  -H 'Content-Type: application/json' \
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
    },
    "threshold": {
      "value": 50000,
      "unit": "CNY_per_QALY",
      "source": "literature"
    },
    "perspective": "societal"
  }'
```

## 响应示例

### 成功评估响应

```json
{
  "icer_value": 6666.67,
  "icer_unit": "CNY_per_QALY",
  "dominance": "none",
  "decision": "accept",
  "net_benefit": 4233.33,
  "ceac_prob_accept": 0.85,
  "policy_version": "2025-08",
  "threshold_used": 37446.0,
  "assumptions": {
    "perspective": "payer",
    "threshold_unit": "CNY_per_QALY",
    "effect_unit": "QALY",
    "note": "Demo贴现略过；真实实现请基于年度序列贴现"
  },
  "evaluated_at": "2025-08-16T11:38:00Z"
}
```

### 简单支配响应

```json
{
  "icer_value": null,
  "icer_unit": null,
  "dominance": "simple",
  "decision": "accept",
  "net_benefit": 4100.0,
  "ceac_prob_accept": null,
  "policy_version": "2025-08",
  "threshold_used": 37446.0,
  "assumptions": {
    "perspective": "payer",
    "threshold_unit": "CNY_per_QALY"
  },
  "evaluated_at": "2025-08-16T11:38:00Z"
}
```

## 测试

### 运行单元测试

```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest tests/ -v
```

### 测试覆盖的场景

- ✅ 健康检查
- ✅ 策略信息获取
- ✅ 简单支配接受
- ✅ 简单支配拒绝
- ✅ 基于阈值接受
- ✅ 基于阈值拒绝
- ✅ 零效果差异边界情况
- ✅ 不确定性分析
- ✅ 自定义阈值
- ✅ 无效请求处理
- ✅ 响应字段完整性

## 配置

### 策略文件

策略文件位于 `packages/policies/icer/2025-08.json`：

```json
{
  "version": "2025-08",
  "threshold": 37446.0,
  "cohorts": {
    "default": { "threshold": 37446.0 },
    "elderly": { "threshold": 36000.0 },
    "low_income": { "threshold": 40000.0 }
  },
  "updated_at": "2025-08-16T11:38:00Z",
  "notes": "阈值示例；请根据政策/文献/支付意愿调查更新并审计。"
}
```

### 环境变量

- `PORT`: 服务端口 (默认: 8090)
- `HOST`: 绑定地址 (默认: 0.0.0.0)

## 技术实现

### 核心算法

1. **支配性检查**: 比较成本和效果的组合关系
2. **ICER计算**: ΔC/ΔE (增量成本/增量效果)
3. **净效益**: λ×ΔE - ΔC (阈值×增量效果 - 增量成本)
4. **决策规则**: 基于ICER与阈值比较或净效益正负

### 不确定性分析

- 蒙特卡洛抽样
- 成本效果可接受曲线 (CEAC)
- 概率敏感性分析

### 限制说明

- 当前版本未实现时序贴现（需要年度序列数据）
- PSA为简化实现，未考虑参数间相关性
- 扩展支配分析待后续版本实现

## 集成说明

### 与Gateway API集成

ICER Engine可以作为独立服务运行，也可以通过Gateway API进行代理访问。

### 服务发现

- 健康检查: `GET /health`
- OpenAPI文档: `GET /docs`
- 服务信息: `GET /`

## 开发指南

### 代码结构

```
services/icer_engine/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用
│   ├── routers/
│   │   ├── __init__.py
│   │   └── evaluate.py      # ICER评估路由
│   └── schemas/
│       ├── __init__.py
│       └── icer.py          # 数据模型
├── tests/
│   ├── __init__.py
│   └── test_icer_engine.py  # 单元测试
├── Dockerfile
├── requirements.txt
└── README.md
```

### 添加新功能

1. 在 `schemas/icer.py` 中定义数据模型
2. 在 `routers/evaluate.py` 中实现业务逻辑
3. 在 `tests/test_icer_engine.py` 中添加测试用例
4. 更新API文档和README

## 许可证

MIT License - 详见项目根目录 LICENSE 文件