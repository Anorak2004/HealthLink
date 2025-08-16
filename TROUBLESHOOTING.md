# HealthLink 故障排除指南

## 常见问题及解决方案

### 1. Pydantic版本兼容性问题

**错误信息**: `regex` is removed. use `pattern` instead

**解决方案**: 
- 已修复：将所有 `regex=` 参数替换为 `pattern=`
- 如果仍有问题，检查是否有其他文件使用了 `regex` 参数

### 2. 依赖冲突问题

**错误信息**: 
```
anaconda-cloud-auth 0.1.4 requires pydantic<2.0, but you have pydantic 2.11.7
streamlit 1.30.0 requires rich<14,>=10.14.0, but you have rich 14.1.0
```

**解决方案**:
```bash
# 方案1: 使用兼容版本的requirements.txt
pip install -r requirements.txt --force-reinstall

# 方案2: 创建新的虚拟环境
conda create -n healthlink python=3.11
conda activate healthlink
pip install -r requirements.txt

# 方案3: 忽略依赖冲突 (不推荐)
pip install -r requirements.txt --no-deps
```

### 3. 模块导入路径问题

**错误信息**: `ModuleNotFoundError: No module named 'services.gateway-api'`

**解决方案**: 
- 已修复：重命名为 `services.gateway_api`
- Python不支持模块名中的连字符

### 4. 数据库初始化失败

**错误信息**: `sqlite3.OperationalError: no such table`

**解决方案**:
```bash
# 删除现有数据库文件
rm -f data/healthlink.db

# 重新初始化
python start_server.py
```

### 5. 端口占用问题

**错误信息**: `OSError: [Errno 48] Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 杀死进程或使用其他端口
python start_server.py --port 8001
```

## 快速诊断

### 运行诊断脚本

```bash
# 快速测试关键功能
python quick_test.py

# 完整测试 (如果rich版本兼容)
python test_fix.py
```

### 检查环境

```bash
# 检查Python版本
python --version  # 应该是 3.11+

# 检查已安装的包
pip list | grep -E "(pydantic|fastapi|rich)"

# 检查项目结构
ls -la services/
```

## 启动方式选择

### 推荐方式 (兼容性最好)
```bash
python start_server.py
```

### 传统方式 (需要rich版本兼容)
```bash
python -m healthlink.cli serve
```

### Docker方式
```bash
docker-compose up -d gateway-api
```

## 开发环境设置

### 创建干净的虚拟环境

```bash
# 使用conda
conda create -n healthlink python=3.11
conda activate healthlink
pip install -r requirements.txt

# 使用venv
python -m venv healthlink_env
source healthlink_env/bin/activate  # Linux/macOS
# 或
healthlink_env\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 验证安装

```bash
python quick_test.py
```

## 生产环境注意事项

1. **数据库切换**: 编辑 `config/settings.yaml` 将数据库类型从 `sqlite` 改为 `mysql`
2. **安全配置**: 设置真实的JWT密钥和加密密钥
3. **日志配置**: 调整日志级别和输出路径
4. **监控配置**: 启用Prometheus指标收集

## ICER Engine 相关问题

### 6. ICER Engine启动失败

**错误信息**: `ModuleNotFoundError: No module named 'app'`

**解决方案**:
```bash
# 确保在正确目录启动
cd services/icer_engine
python -m uvicorn app.main:app --port 8090

# 或使用启动脚本
python start_icer_engine.py
```

### 7. 策略文件未找到

**错误信息**: `ICER policy file not found`

**解决方案**:
```bash
# 检查策略文件是否存在
ls -la packages/policies/icer/2025-08.json

# 如果不存在，创建策略文件
mkdir -p packages/policies/icer
# 复制示例策略文件或重新运行初始化
```

### 8. ICER评估计算错误

**错误信息**: 评估结果不符合预期

**解决方案**:
- 检查输入数据的单位是否一致
- 确认成本和效果值为正数
- 验证阈值设置是否正确
- 查看响应中的assumptions字段了解计算假设

### 9. Docker服务间通信失败

**错误信息**: `Connection refused` 或 `Service unavailable`

**解决方案**:
```bash
# 检查Docker网络
docker network ls
docker network inspect healthlink_healthlink

# 重启Docker Compose
docker-compose down
docker-compose up -d

# 检查服务状态
docker-compose ps
```

## 获取帮助

如果问题仍未解决：

1. 检查 `logs/healthlink.log` 文件中的详细错误信息
2. 运行诊断脚本：
   - `python quick_test.py` - 快速诊断
   - `python test_icer_integration.py` - ICER Engine集成测试
   - `python test_m2_acceptance.py` - M2验收测试
3. 查看项目文档和API文档：
   - Gateway API: http://localhost:8000/docs
   - ICER Engine: http://localhost:8090/docs
4. 提交Issue时请包含：
   - Python版本
   - 操作系统
   - 完整的错误堆栈
   - `pip list` 输出
   - 相关服务的日志输出