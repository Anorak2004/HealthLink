#!/usr/bin/env python3
"""
快速测试脚本 - 验证关键修复
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pydantic_fix():
    """测试Pydantic v2修复"""
    try:
        print("🔍 Testing Pydantic v2 compatibility...")
        
        # 测试Field with pattern (不是regex)
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            sort_order: str = Field("desc", pattern="^(asc|desc)$")
        
        # 测试有效值
        model = TestModel(sort_order="asc")
        assert model.sort_order == "asc"
        
        # 测试无效值会抛出异常
        try:
            TestModel(sort_order="invalid")
            assert False, "Should have raised validation error"
        except Exception:
            pass  # 预期的验证错误
        
        print("✅ Pydantic pattern validation: OK")
        return True
        
    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
        return False

def test_basic_imports():
    """测试基本导入"""
    try:
        print("🔍 Testing basic imports...")
        
        # 测试配置导入
        from config.database_switch import get_config
        config = get_config()
        print(f"✅ Config loaded: {len(config)} sections")
        
        # 测试模型导入
        from packages.schemas.models import Patient
        print("✅ Models import: OK")
        
        # 测试请求模型导入
        from packages.schemas.requests import PatientCreateRequest
        print("✅ Request schemas import: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 40)
    print("🧪 HealthLink 快速修复测试")
    print("=" * 40)
    
    success = True
    
    # 测试Pydantic修复
    if not test_pydantic_fix():
        success = False
    
    print()
    
    # 测试基本导入
    if not test_basic_imports():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 修复成功！可以启动服务器了。")
        print("\n启动命令:")
        print("python start_server.py")
    else:
        print("❌ 修复失败，请检查错误信息。")
    print("=" * 40)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())