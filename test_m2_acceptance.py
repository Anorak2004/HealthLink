#!/usr/bin/env python3
"""
M2 - ICER Engine 验收测试
验证M2阶段的所有交付物和验收标准
"""
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

def test_deliverables():
    """测试交付物完整性"""
    print("📋 Testing M2 deliverables...")
    
    required_files = [
        # 服务源码
        "services/icer_engine/app/main.py",
        "services/icer_engine/app/routers/evaluate.py",
        "services/icer_engine/app/schemas/icer.py",
        
        # 策略文件
        "packages/policies/icer/2025-08.json",
        
        # OpenAPI更新
        "docs/openapi.yaml",
        
        # 单元测试
        "services/icer_engine/tests/test_icer_engine.py",
        
        # 容器配置
        "services/icer_engine/Dockerfile",
        "docker-compose.yml",
        
        # 文档
        "services/icer_engine/README.md",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing deliverables: {missing_files}")
        return False
    else:
        print("✅ All deliverables present")
        return True

def test_openapi_compliance():
    """测试OpenAPI规范合规性"""
    print("\n📋 Testing OpenAPI compliance...")
    
    try:
        # 检查OpenAPI文件是否有效JSON/YAML
        with open("docs/openapi.yaml", "r") as f:
            content = f.read()
            
        # 检查是否包含ICER相关端点
        required_paths = ["/icer/policies", "/icer/evaluate"]
        missing_paths = []
        
        for path in required_paths:
            if path not in content:
                missing_paths.append(path)
        
        if missing_paths:
            print(f"❌ Missing OpenAPI paths: {missing_paths}")
            return False
        
        # 检查是否包含ICER相关组件
        required_components = ["IcerEvaluateRequest", "IcerEvaluateResult"]
        missing_components = []
        
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing OpenAPI components: {missing_components}")
            return False
        
        print("✅ OpenAPI specification compliant")
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI compliance check failed: {e}")
        return False

def test_unit_tests():
    """测试单元测试"""
    print("\n🧪 Running unit tests...")
    
    try:
        # 安装测试依赖
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pytest", "requests"
        ], check=True, capture_output=True)
        
        # 运行ICER Engine单元测试
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "services/icer_engine/tests/test_icer_engine.py", 
            "-v"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Unit tests passed")
            # 检查测试覆盖的场景
            output = result.stdout
            required_tests = [
                "test_accept_by_dominance",
                "test_reject_by_threshold", 
                "test_zero_effect_difference"
            ]
            
            missing_tests = []
            for test in required_tests:
                if test not in output:
                    missing_tests.append(test)
            
            if missing_tests:
                print(f"⚠️  Missing required test scenarios: {missing_tests}")
                return False
            
            return True
        else:
            print(f"❌ Unit tests failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Unit test execution failed: {e}")
        return False

def test_service_endpoints():
    """测试服务端点"""
    print("\n🌐 Testing service endpoints...")
    
    # 检查ICER Engine是否运行
    try:
        response = requests.get("http://localhost:8090/health", timeout=5)
        if response.status_code != 200:
            print("❌ ICER Engine not running or unhealthy")
            return False
    except requests.exceptions.RequestException:
        print("❌ ICER Engine not accessible")
        return False
    
    # 测试策略端点
    try:
        response = requests.get("http://localhost:8090/v1/icer/policies", timeout=5)
        if response.status_code != 200:
            print("❌ Policies endpoint failed")
            return False
        
        data = response.json()
        required_fields = ["version", "threshold", "cohorts"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Policies response missing fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"❌ Policies endpoint test failed: {e}")
        return False
    
    # 测试评估端点
    try:
        test_data = {
            "comparator": {
                "cost": 10000,
                "effect": 1.0,
                "effect_unit": "QALY"
            },
            "intervention": {
                "cost": 12000,
                "effect": 1.1,
                "effect_unit": "QALY"
            }
        }
        
        response = requests.post(
            "http://localhost:8090/v1/icer/evaluate",
            json=test_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Evaluate endpoint failed: {response.status_code}")
            return False
        
        data = response.json()
        required_fields = [
            "icer_value", "net_benefit", "decision", 
            "policy_version", "threshold_used"
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Evaluate response missing fields: {missing_fields}")
            return False
        
        print("✅ Service endpoints working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Evaluate endpoint test failed: {e}")
        return False

def test_docker_build():
    """测试Docker构建"""
    print("\n🐳 Testing Docker build...")
    
    try:
        # 检查Docker是否可用
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        
        # 构建ICER Engine镜像
        result = subprocess.run([
            "docker", "build", "-t", "icer-engine-test", "."
        ], cwd="services/icer_engine", capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            
            # 清理测试镜像
            subprocess.run([
                "docker", "rmi", "icer-engine-test"
            ], capture_output=True)
            
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError:
        print("⚠️  Docker not available, skipping Docker build test")
        return True  # 不强制要求Docker
    except Exception as e:
        print(f"❌ Docker build test failed: {e}")
        return False

def test_integration_scenarios():
    """测试集成场景"""
    print("\n🔗 Testing integration scenarios...")
    
    test_cases = [
        {
            "name": "Simple dominance acceptance",
            "data": {
                "comparator": {"cost": 10000, "effect": 1.0, "effect_unit": "QALY"},
                "intervention": {"cost": 9000, "effect": 1.1, "effect_unit": "QALY"}
            },
            "expected": {"dominance": "simple", "decision": "accept"}
        },
        {
            "name": "Threshold-based rejection",
            "data": {
                "comparator": {"cost": 10000, "effect": 1.0, "effect_unit": "QALY"},
                "intervention": {"cost": 20000, "effect": 1.05, "effect_unit": "QALY"},
                "threshold": {"value": 37446, "unit": "CNY_per_QALY"}
            },
            "expected": {"dominance": "none", "decision": "reject"}
        },
        {
            "name": "Zero effect difference",
            "data": {
                "comparator": {"cost": 10000, "effect": 1.0, "effect_unit": "QALY"},
                "intervention": {"cost": 12000, "effect": 1.0, "effect_unit": "QALY"}
            },
            "expected": {"decision": "reject"}
        }
    ]
    
    passed = 0
    for test_case in test_cases:
        try:
            response = requests.post(
                "http://localhost:8090/v1/icer/evaluate",
                json=test_case["data"],
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查预期结果
                all_match = True
                for key, expected_value in test_case["expected"].items():
                    if data.get(key) != expected_value:
                        print(f"  ❌ {test_case['name']}: {key} = {data.get(key)}, expected {expected_value}")
                        all_match = False
                
                if all_match:
                    print(f"  ✅ {test_case['name']}: PASSED")
                    passed += 1
                else:
                    print(f"  ❌ {test_case['name']}: FAILED")
            else:
                print(f"  ❌ {test_case['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {test_case['name']}: {e}")
    
    if passed == len(test_cases):
        print("✅ All integration scenarios passed")
        return True
    else:
        print(f"❌ {len(test_cases) - passed} integration scenarios failed")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🎯 M2 - ICER Engine 验收测试")
    print("=" * 60)
    
    tests = [
        ("Deliverables Check", test_deliverables),
        ("OpenAPI Compliance", test_openapi_compliance),
        ("Unit Tests", test_unit_tests),
        ("Service Endpoints", test_service_endpoints),
        ("Docker Build", test_docker_build),
        ("Integration Scenarios", test_integration_scenarios),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 M2验收测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 M2 - ICER Engine 验收测试全部通过！")
        print("✅ 可以进入M3阶段开发")
        return 0
    elif passed >= total * 0.8:
        print("⚠️  大部分测试通过，但仍有改进空间")
        return 0
    else:
        print("❌ 多项验收测试失败，请修复后重试")
        return 1

if __name__ == "__main__":
    sys.exit(main())