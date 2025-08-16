#!/usr/bin/env python3
"""
HealthLink 简化启动脚本
避免复杂的CLI依赖，直接启动服务
"""
import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def init_database():
    """初始化数据库"""
    try:
        from config.database_switch import init_database
        print("🔧 Initializing database...")
        init_database()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def create_sample_data():
    """创建示例数据"""
    try:
        from sqlalchemy.orm import sessionmaker
        from config.database_switch import create_database_engine, get_config
        from packages.schemas.models import Patient, ICERPolicy
        from datetime import datetime, date
        
        print("📝 Creating sample data...")
        
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
        
        print("✅ Sample data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def start_server():
    """启动服务器"""
    try:
        import uvicorn
        from config.database_switch import get_config
        
        config = get_config()
        gateway_config = config.get('gateway', {})
        
        host = gateway_config.get('host', '0.0.0.0')
        port = gateway_config.get('port', 8000)
        
        print("🚀 Starting HealthLink Gateway API...")
        print(f"📡 Server will be available at: http://{host}:{port}")
        print(f"📚 API documentation: http://{host}:{port}/docs")
        print(f"🏥 Health check: http://{host}:{port}/health")
        print()
        
        uvicorn.run(
            "services.gateway_api.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🏥 HealthLink - AI驱动的共病管理平台")
    print("=" * 50)
    print()
    
    # 初始化数据库
    if not init_database():
        sys.exit(1)
    
    print()
    
    # 创建示例数据
    if not create_sample_data():
        print("⚠️  Warning: Failed to create sample data, but continuing...")
    
    print()
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()