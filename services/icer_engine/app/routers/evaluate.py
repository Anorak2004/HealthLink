"""
ICER Engine 评估路由
提供ICER/INB评估和策略查询功能
"""
import os
import json
import math
import time
import random
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from ..schemas.icer import EvaluateRequest, EvaluateResult, PolicyResponse

router = APIRouter(tags=["icer"])

def load_policy() -> Dict[str, Any]:
    """加载ICER策略文件"""
    # 构建策略文件路径
    current_file = Path(__file__)
    policy_path = current_file.parent.parent.parent.parent.parent / "packages" / "policies" / "icer" / "2025-08.json"
    
    if not policy_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ICER policy file not found"
        )
    
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid policy file format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load policy: {str(e)}"
        )

@router.get("/icer/policies", response_model=PolicyResponse)
def get_policies():
    """获取ICER策略信息"""
    policy = load_policy()
    return PolicyResponse(**policy)

@router.post("/icer/evaluate", response_model=EvaluateResult)
def evaluate_icer(req: EvaluateRequest):
    """执行ICER评估"""
    
    # 1. 加载策略与阈值
    policy = load_policy()
    version = policy.get("version", "unknown")
    
    if req.threshold:
        threshold_value = req.threshold.value
        threshold_unit = req.threshold.unit
    else:
        # 使用默认阈值
        threshold_value = policy.get("threshold", 37446.0)
        threshold_unit = "CNY_per_QALY"
    
    # 2. 提取成本和效果数据
    c0, e0 = req.comparator.cost, req.comparator.effect
    c1, e1 = req.intervention.cost, req.intervention.effect
    
    # 计算增量成本和增量效果
    delta_cost = c1 - c0
    delta_effect = e1 - e0
    
    # 3. 支配性分析
    dominance = "none"
    decision = "inconclusive"
    icer_value = None
    
    # 简单支配检查 (使用小的容差处理浮点数比较)
    eps = 1e-10
    
    if (delta_cost <= eps and delta_effect >= -eps) and (delta_cost < -eps or delta_effect > eps):
        # 干预组成本更低且效果更好（或相等）
        dominance = "simple"
        decision = "accept"
        icer_value = None
    elif (delta_cost >= -eps and delta_effect <= eps) and (delta_cost > eps or delta_effect < -eps):
        # 干预组成本更高且效果更差（或相等）
        dominance = "simple"
        decision = "reject"
        icer_value = None
    else:
        # 无简单支配关系
        dominance = "none"
        
        if abs(delta_effect) < 1e-12:
            # 效果差异极小，无法计算ICER
            if delta_cost > 0:
                icer_value = float('inf')
                decision = "reject"
            elif delta_cost < 0:
                icer_value = float('-inf')
                decision = "accept"
            else:
                icer_value = 0.0
                decision = "inconclusive"
        else:
            # 计算ICER
            icer_value = delta_cost / delta_effect
            
            # 基于阈值做决策
            if delta_effect > 0:
                # 效果增加
                decision = "accept" if icer_value <= threshold_value else "reject"
            elif delta_effect < 0:
                # 效果减少
                decision = "reject" if delta_cost >= 0 else "inconclusive"
            else:
                decision = "inconclusive"
    
    # 4. 计算净效益 (INB)
    net_benefit = threshold_value * delta_effect - delta_cost
    
    # 5. 不确定性分析 (简化的概率敏感性分析)
    ceac_prob = None
    uncertainty = req.uncertainty
    
    if uncertainty and uncertainty.samples and uncertainty.samples > 0:
        accepts = 0
        samples = min(uncertainty.samples, 5000)  # 限制最大抽样次数
        
        for _ in range(samples):
            # 简化的蒙特卡洛抽样
            # 为成本和效果添加随机噪声
            noise_c0 = random.gauss(0, uncertainty.se_cost_0 or 0.0)
            noise_c1 = random.gauss(0, uncertainty.se_cost_1 or 0.0)
            noise_e0 = random.gauss(0, uncertainty.se_eff_0 or 0.0)
            noise_e1 = random.gauss(0, uncertainty.se_eff_1 or 0.0)
            
            # 计算抽样后的增量值
            dc_sample = (c1 + noise_c1) - (c0 + noise_c0)
            de_sample = (e1 + noise_e1) - (e0 + noise_e0)
            
            # 计算抽样后的净效益
            inb_sample = threshold_value * de_sample - dc_sample
            
            if inb_sample > 0:
                accepts += 1
        
        ceac_prob = accepts / float(samples)
    
    # 6. 构建假设条件
    assumptions = {
        "perspective": req.perspective,
        "threshold_unit": threshold_unit,
        "effect_unit": req.intervention.effect_unit,
        "note": "Demo贴现略过；真实实现请基于年度序列贴现"
    }
    
    if req.discount:
        assumptions["cost_discount_rate"] = str(req.discount.cost_rate)
        assumptions["effect_discount_rate"] = str(req.discount.effect_rate)
    
    # 7. 返回结果
    return EvaluateResult(
        icer_value=icer_value if dominance == "none" else None,
        icer_unit=threshold_unit if dominance == "none" and icer_value is not None else None,
        dominance=dominance,
        decision=decision,
        net_benefit=net_benefit,
        ceac_prob_accept=ceac_prob,
        policy_version=version,
        threshold_used=threshold_value,
        assumptions=assumptions,
        evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )