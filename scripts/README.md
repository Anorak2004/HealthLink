# HealthLink 启动脚本说明

## 可用脚本

### 1. start_server.py (推荐)
**用途**: 一键启动HealthLink服务，自动处理数据库初始化和示例数据创建

**特点**:
- 兼容性最好，避免rich版本冲突
- 自动初始化数据库
- 自动创建示例数据
- 直接启动API服务

**使用方法**:
```bash
python start_server.py
```

### 2. quick_test.py
**用途**: 快速验证关键修复和基本功能

**特点**:
- 测试Pydantic v2兼容性
- 验证基本导入功能
- 轻量级，运行快速

**使用方法**:
```bash
python quick_test.py
```

### 3. test_fix.py
**用途**: 完整的功能测试 (需要rich版本兼容)

**特点**:
- 全面测试所有导入
- 测试配置加载
- 测试数据库初始化
- 测试FastAPI应用创建

**使用方法**:
```bash
python test_fix.py
```

### 4. healthlink.cli (传统方式)
**用途**: 完整的CLI工具集

**特点**:
- 丰富的命令行功能
- 需要rich版本兼容
- 适合开发和运维

**使用方法**:
```bash
python -m healthlink.cli serve
python -m healthlink.cli init-db
python -m healthlink.cli create-sample-data
```

## 推荐启动流程

### 首次使用
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 快速测试 (可选)
python quick_test.py

# 3. 启动服务
python start_server.py
```

### 开发环境
```bash
# 使用CLI工具 (如果兼容)
python -m healthlink.cli serve --reload

# 或使用简化启动脚本
python start_server.py
```

### 生产环境
```bash
# 使用Docker
docker-compose up -d gateway-api

# 或直接启动
python start_server.py
```

## 故障排除

如果遇到问题，请参考 [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)