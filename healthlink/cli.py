"""
HealthLink CLI 工具
用于管理和操作HealthLink系统
"""
import os
import sys
import click
from rich.console import Console
from rich.table import Table

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.database_switch import init_database, get_config

console = Console()

@click.group()
def main():
    """HealthLink CLI - AI-driven Comorbidity Management Platform"""
    pass

@main.command()
def init_db():
    """初始化数据库"""
    try:
        console.print("🔧 Initializing database...", style="blue")
        engine = init_database()
        console.print("✅ Database initialized successfully!", style="green")
        console.print(f"📊 Database URL: {engine.url}", style="dim")
    except Exception as e:
        console.print(f"❌ Failed to initialize database: {str(e)}", style="red")
        sys.exit(1)

@main.command()
def check_config():
    """检查配置"""
    try:
        console.print("🔍 Checking configuration...", style="blue")
        config = get_config()
        
        table = Table(title="HealthLink Configuration")
        table.add_column("Section", style="cyan")
        table.add_column("Key", style="magenta")
        table.add_column("Value", style="green")
        
        for section, values in config.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    # 隐藏敏感信息
                    if any(sensitive in key.lower() for sensitive in ['password', 'key', 'secret']):
                        value = "***"
                    table.add_row(section, key, str(value))
            else:
                table.add_row(section, "", str(values))
        
        console.print(table)
        console.print("✅ Configuration loaded successfully!", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to load configuration: {str(e)}", style="red")
        sys.exit(1)

@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def serve(host, port, reload):
    """启动API服务"""
    try:
        console.print("🚀 Starting HealthLink Gateway API...", style="blue")
        console.print(f"📡 Server will be available at: http://{host}:{port}", style="green")
        console.print(f"📚 API documentation: http://{host}:{port}/docs", style="green")
        
        import uvicorn
        uvicorn.run(
            "services.gateway-api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        console.print(f"❌ Failed to start server: {str(e)}", style="red")
        sys.exit(1)

@main.command()
def create_sample_data():
    """创建示例数据"""
    try:
        console.print("📝 Creating sample data...", style="blue")
        
        from sqlalchemy.orm import sessionmaker
        from config.database_switch import create_database_engine
        from packages.schemas.models import Patient, ICERPolicy
        import json
        from datetime import datetime, date
        
        config = get_config()
        engine, SessionLocal = create_database_engine(config)
        db = SessionLocal()
        
        # 创建示例患者
        sample_patients = [
            {
                "patient_id": "P001",
                "name": "张三",
                "gender": "M",
                "birth_date": date(1960, 5, 15),
                "phone": "13800138001",
                "email": "zhangsan@example.com",
                "medical_record_number": "MR001",
                "primary_doctor_id": "DOC001"
            },
            {
                "patient_id": "P002", 
                "name": "李四",
                "gender": "F",
                "birth_date": date(1955, 8, 20),
                "phone": "13800138002",
                "email": "lisi@example.com",
                "medical_record_number": "MR002",
                "primary_doctor_id": "DOC001"
            }
        ]
        
        for patient_data in sample_patients:
            existing = db.query(Patient).filter(Patient.patient_id == patient_data["patient_id"]).first()
            if not existing:
                patient = Patient(**patient_data)
                db.add(patient)
        
        # 创建示例ICER策略
        sample_policy = {
            "policy_id": "ICER_2025",
            "version": "2025-08",
            "threshold_per_daly": 37446.0,
            "policy_data": {
                "base_threshold": 37446.0,
                "age_adjustments": {
                    "under_65": 1.0,
                    "65_to_75": 0.9,
                    "over_75": 0.8
                },
                "comorbidity_adjustments": {
                    "diabetes": 1.1,
                    "hypertension": 1.05,
                    "heart_disease": 1.2
                }
            },
            "description": "2025年ICER评估策略",
            "source": "国家卫健委",
            "effective_date": datetime(2025, 1, 1),
            "is_default": True
        }
        
        existing_policy = db.query(ICERPolicy).filter(
            ICERPolicy.policy_id == sample_policy["policy_id"],
            ICERPolicy.version == sample_policy["version"]
        ).first()
        
        if not existing_policy:
            policy = ICERPolicy(**sample_policy)
            db.add(policy)
        
        db.commit()
        db.close()
        
        console.print("✅ Sample data created successfully!", style="green")
        console.print("👥 Created 2 sample patients", style="dim")
        console.print("📋 Created 1 ICER policy", style="dim")
        
    except Exception as e:
        console.print(f"❌ Failed to create sample data: {str(e)}", style="red")
        sys.exit(1)

@main.command()
def health_check():
    """健康检查"""
    try:
        console.print("🏥 Performing health check...", style="blue")
        
        # 检查数据库连接
        from sqlalchemy.orm import sessionmaker
        from config.database_switch import create_database_engine
        
        config = get_config()
        engine, SessionLocal = create_database_engine(config)
        db = SessionLocal()
        
        db.execute("SELECT 1")
        db.close()
        
        console.print("✅ Database connection: OK", style="green")
        console.print("✅ Configuration: OK", style="green")
        console.print("🎉 System is healthy!", style="green bold")
        
    except Exception as e:
        console.print(f"❌ Health check failed: {str(e)}", style="red")
        sys.exit(1)

if __name__ == "__main__":
    main()