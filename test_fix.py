#!/usr/bin/env python3
"""
测试修复后的代码
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    try:
        print("🔍 Testing imports...")
        
        # 测试基础导入
        from config.database_switch import get_config, init_database
        print("✅ Database config import: OK")
        
        from packages.schemas.models import Patient, ICERPolicy
        print("✅ Models import: OK")
        
        from packages.schemas.requests import PatientCreateRequest
        print("✅ Request schemas import: OK")
        
        from packages.schemas.responses import PatientResponse
        print("✅ Response schemas import: OK")
        
        # 测试FastAPI应用创建
        from services.gateway_api.main import create_app
        print("✅ FastAPI app creation: OK")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """测试配置加载"""
    try:
        print("\n🔍 Testing configuration...")
        
        from config.database_switch import get_config
        config = get_config()
        
        print(f"✅ Config loaded with {len(config)} sections")
        print(f"📊 Database type: {config.get('database', {}).get('type', 'unknown')}")
        print(f"🤖 AI model provider: {config.get('ai_models', {}).get('nlp', {}).get('provider', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_database():
    """测试数据库初始化"""
    try:
        print("\n🔍 Testing database initialization...")
        
        from config.database_switch import init_database
        engine = init_database()
        
        print(f"✅ Database initialized: {engine.url}")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 HealthLink 修复测试")
    print("=" * 50)
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试配置
    if not test_config():
        success = False
    
    # 测试数据库
    if not test_database():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！可以启动服务器了。")
        print("\n启动命令:")
        print("python start_server.py")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())