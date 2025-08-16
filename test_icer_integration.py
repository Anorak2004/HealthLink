#!/usr/bin/env python3
"""
ICER Engine 集成测试脚本
验证ICER Engine的完整功能
"""
import sys
import json
import time
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

ICER_ENGINE_URL = "http://localhost:8090"

def test_health_check():
    """测试健康检查"""
    try:
        print("🔍 Testing ICER Engine health check...")
        response = requests.get(f"{ICER_ENGINE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data['status']}")
            print(f"📊 Service: {data['service']}")
            print(f"🔖 Version: {data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_get_policies():
    """测试获取策略信息"""
    try:
        print("\n🔍 Testing policy retrieval...")
        response = requests.get(f"{ICER_ENGINE_URL}/v1/icer/policies", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Policy version: {data['version']}")
            print(f"📊 Default threshold: {data['threshold']}")
            print(f"👥 Cohorts: {list(data['cohorts'].keys())}")
            return True
        else:
            print(f"❌ Policy retrieval failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Policy retrieval failed: {e}")
        return False

def test_icer_evaluation():
    """测试ICER评估"""
    try:
        print("\n🔍 Testing ICER evaluation...")
        
        # 测试数据：干预成本效果比较好的情况
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
            },
            "uncertainty": {
                "samples": 100  # 小样本快速测试
            }
        }
        
        response = requests.post(
            f"{ICER_ENGINE_URL}/v1/icer/evaluate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ICER evaluation successful")
            print(f"📊 ICER value: {data.get('icer_value')}")
            print(f"🎯 Decision: {data.get('decision')}")
            print(f"💰 Net benefit: {data.get('net_benefit')}")
            print(f"🎲 CEAC probability: {data.get('ceac_prob_accept')}")
            print(f"📋 Policy version: {data.get('policy_version')}")
            
            # 验证必需字段
            required_fields = [
                'dominance', 'decision', 'net_benefit', 
                'policy_version', 'threshold_used', 
                'assumptions', 'evaluated_at'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
                return False
            
            return True
        else:
            print(f"❌ ICER evaluation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ICER evaluation failed: {e}")
        return False

def test_dominance_scenarios():
    """测试支配性场景"""
    try:
        print("\n🔍 Testing dominance scenarios...")
        
        # 简单支配接受场景
        dominance_data = {
            "comparator": {
                "cost": 10000,
                "effect": 1.0,
                "effect_unit": "QALY"
            },
            "intervention": {
                "cost": 9000,   # 成本更低
                "effect": 1.1,  # 效果更好
                "effect_unit": "QALY"
            }
        }
        
        response = requests.post(
            f"{ICER_ENGINE_URL}/v1/icer/evaluate",
            json=dominance_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('dominance') == 'simple' and data.get('decision') == 'accept':
                print("✅ Simple dominance (accept) scenario: PASSED")
                return True
            else:
                print(f"❌ Simple dominance scenario failed: {data}")
                return False
        else:
            print(f"❌ Dominance test failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Dominance test failed: {e}")
        return False

def test_custom_threshold():
    """测试自定义阈值"""
    try:
        print("\n🔍 Testing custom threshold...")
        
        threshold_data = {
            "comparator": {
                "cost": 10000,
                "effect": 1.0,
                "effect_unit": "QALY"
            },
            "intervention": {
                "cost": 15000,
                "effect": 1.2,
                "effect_unit": "QALY"
            },
            "threshold": {
                "value": 50000,
                "unit": "CNY_per_QALY",
                "source": "literature"
            }
        }
        
        response = requests.post(
            f"{ICER_ENGINE_URL}/v1/icer/evaluate",
            json=threshold_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('threshold_used') == 50000:
                print("✅ Custom threshold scenario: PASSED")
                print(f"📊 Used threshold: {data.get('threshold_used')}")
                return True
            else:
                print(f"❌ Custom threshold not applied: {data}")
                return False
        else:
            print(f"❌ Custom threshold test failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Custom threshold test failed: {e}")
        return False

def test_api_documentation():
    """测试API文档可访问性"""
    try:
        print("\n🔍 Testing API documentation...")
        
        # 测试OpenAPI文档
        response = requests.get(f"{ICER_ENGINE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation accessible")
            return True
        else:
            print(f"❌ API documentation not accessible: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 ICER Engine 集成测试")
    print("=" * 60)
    print(f"🎯 Target URL: {ICER_ENGINE_URL}")
    print()
    
    # 等待服务启动
    print("⏳ Waiting for service to start...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Policy Retrieval", test_get_policies),
        ("ICER Evaluation", test_icer_evaluation),
        ("Dominance Scenarios", test_dominance_scenarios),
        ("Custom Threshold", test_custom_threshold),
        ("API Documentation", test_api_documentation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！ICER Engine 运行正常。")
        return 0
    else:
        print("❌ 部分测试失败，请检查服务状态。")
        return 1

if __name__ == "__main__":
    sys.exit(main())