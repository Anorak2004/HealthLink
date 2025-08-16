"""
ICER Engine 单元测试
测试ICER评估的各种场景
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ICER Engine"

def test_get_policies():
    """测试获取策略信息"""
    response = client.get("/v1/icer/policies")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "threshold" in data
    assert "cohorts" in data

def test_accept_by_dominance():
    """测试简单支配接受场景"""
    body = {
        "comparator": {
            "cost": 10000,
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 9000,  # 成本更低
            "effect": 1.1,  # 效果更好
            "effect_unit": "QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "accept"
    assert data["dominance"] == "simple"
    assert data["icer_value"] is None  # 简单支配时不计算ICER
    assert data["net_benefit"] is not None

def test_reject_by_dominance():
    """测试简单支配拒绝场景"""
    body = {
        "comparator": {
            "cost": 10000,
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 12000,  # 成本更高
            "effect": 0.9,   # 效果更差
            "effect_unit": "QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "reject"
    assert data["dominance"] == "simple"
    assert data["icer_value"] is None

def test_accept_by_threshold():
    """测试基于阈值的接受场景"""
    body = {
        "comparator": {
            "cost": 10000,
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 12000,  # 成本增加2000
            "effect": 1.1,   # 效果增加0.1 QALY
            "effect_unit": "QALY"
        },
        "threshold": {
            "value": 37446,
            "unit": "CNY_per_QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["dominance"] == "none"
    assert data["icer_value"] is not None
    assert abs(data["icer_value"] - 20000.0) < 0.01  # 2000/0.1 = 20000 (允许浮点数误差)
    assert data["decision"] == "accept"  # 20000 < 37446
    assert data["threshold_used"] == 37446

def test_reject_by_threshold():
    """测试基于阈值的拒绝场景"""
    body = {
        "comparator": {
            "cost": 10000,
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 20000,  # 成本增加10000
            "effect": 1.05,  # 效果增加0.05 QALY
            "effect_unit": "QALY"
        },
        "threshold": {
            "value": 37446,
            "unit": "CNY_per_QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["dominance"] == "none"
    assert data["icer_value"] is not None
    assert abs(data["icer_value"] - 200000.0) < 0.01  # 10000/0.05 = 200000 (允许浮点数误差)
    assert data["decision"] == "reject"  # 200000 > 37446

def test_zero_effect_difference():
    """测试效果差异为零的边界情况"""
    body = {
        "comparator": {
            "cost": 10000,
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 12000,  # 成本增加
            "effect": 1.0,   # 效果相同
            "effect_unit": "QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["dominance"] == "simple"  # 成本增加效果不变是简单支配
    assert data["decision"] == "reject"  # 成本增加但效果不变
    assert data["icer_value"] is None  # 简单支配时不计算ICER

def test_uncertainty_analysis():
    """测试不确定性分析"""
    body = {
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
            "se_cost_0": 1000,
            "se_cost_1": 1200,
            "se_eff_0": 0.1,
            "se_eff_1": 0.12,
            "samples": 1000
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["ceac_prob_accept"] is not None
    assert 0 <= data["ceac_prob_accept"] <= 1

def test_custom_threshold():
    """测试自定义阈值"""
    body = {
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
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    assert data["threshold_used"] == 50000
    assert data["policy_version"] is not None

def test_invalid_request():
    """测试无效请求"""
    body = {
        "comparator": {
            "cost": -1000,  # 负成本
            "effect": 1.0,
            "effect_unit": "QALY"
        },
        "intervention": {
            "cost": 12000,
            "effect": 1.1,
            "effect_unit": "QALY"
        }
    }
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 422  # 验证错误

def test_response_fields():
    """测试响应字段完整性"""
    body = {
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
    
    response = client.post("/v1/icer/evaluate", json=body)
    assert response.status_code == 200
    
    data = response.json()
    
    # 检查必需字段
    required_fields = [
        "dominance", "decision", "net_benefit", 
        "policy_version", "threshold_used", 
        "assumptions", "evaluated_at"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"