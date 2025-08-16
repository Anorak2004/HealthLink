"""
ICER Engine 数据模型
定义ICER评估的请求和响应结构
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Literal
from datetime import datetime

class Arm(BaseModel):
    """干预臂或对照臂"""
    cost: float = Field(ge=0, description="成本（元）")
    effect: float = Field(description="效果值（QALY或DALY）")
    effect_unit: Literal["QALY", "DALY", "OTHER"] = Field(default="QALY", description="效果单位")

class Threshold(BaseModel):
    """阈值配置"""
    value: float = Field(gt=0, description="阈值数值")
    unit: Literal["CNY_per_QALY", "CNY_per_DALY"] = Field(description="阈值单位")
    source: Literal["policy", "literature", "WTP_survey", "config"] = Field(
        default="config", description="阈值来源"
    )

class Discount(BaseModel):
    """贴现率配置"""
    cost_rate: float = Field(default=0.03, ge=0, le=1, description="成本贴现率")
    effect_rate: float = Field(default=0.03, ge=0, le=1, description="效果贴现率")

class Uncertainty(BaseModel):
    """不确定性分析参数"""
    se_cost_0: Optional[float] = Field(None, ge=0, description="对照组成本标准误")
    se_cost_1: Optional[float] = Field(None, ge=0, description="干预组成本标准误")
    se_eff_0: Optional[float] = Field(None, ge=0, description="对照组效果标准误")
    se_eff_1: Optional[float] = Field(None, ge=0, description="干预组效果标准误")
    corr: Optional[float] = Field(None, ge=-1, le=1, description="成本效果相关系数")
    samples: int = Field(default=0, ge=0, le=10000, description="蒙特卡洛抽样次数")

class EvaluateRequest(BaseModel):
    """ICER评估请求"""
    comparator: Arm = Field(description="对照臂")
    intervention: Arm = Field(description="干预臂")
    perspective: Literal["societal", "payer", "provider"] = Field(
        default="payer", description="分析视角"
    )
    threshold: Optional[Threshold] = Field(None, description="自定义阈值")
    discount: Optional[Discount] = Field(None, description="贴现率配置")
    uncertainty: Optional[Uncertainty] = Field(None, description="不确定性分析参数")
    equity_weights: Optional[Dict[str, float]] = Field(None, description="公平性权重")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comparator": {
                    "cost": 10000,
                    "effect": 0.8,
                    "effect_unit": "QALY"
                },
                "intervention": {
                    "cost": 12000,
                    "effect": 1.1,
                    "effect_unit": "QALY"
                },
                "perspective": "payer",
                "uncertainty": {
                    "samples": 1000
                }
            }
        }
    )

class EvaluateResult(BaseModel):
    """ICER评估结果"""
    icer_value: Optional[float] = Field(None, description="ICER值")
    icer_unit: Optional[str] = Field(None, description="ICER单位")
    dominance: Literal["simple", "extended", "none"] = Field(
        default="none", description="支配关系"
    )
    decision: Literal["accept", "reject", "inconclusive"] = Field(
        default="inconclusive", description="决策结果"
    )
    net_benefit: Optional[float] = Field(None, description="净效益")
    ceac_prob_accept: Optional[float] = Field(None, description="成本效果可接受曲线概率")
    policy_version: Optional[str] = Field(None, description="使用的策略版本")
    threshold_used: Optional[float] = Field(None, description="使用的阈值")
    assumptions: Dict[str, str] = Field(default_factory=dict, description="假设条件")
    evaluated_at: str = Field(description="评估时间")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "icer_value": 6666.67,
                "icer_unit": "CNY_per_QALY",
                "dominance": "none",
                "decision": "accept",
                "net_benefit": 4233.33,
                "ceac_prob_accept": 0.85,
                "policy_version": "2025-08",
                "threshold_used": 37446.0,
                "assumptions": {
                    "perspective": "payer",
                    "threshold_unit": "CNY_per_QALY"
                },
                "evaluated_at": "2025-08-16T11:38:00Z"
            }
        }
    )

class PolicyResponse(BaseModel):
    """策略响应"""
    version: str = Field(description="策略版本")
    threshold: float = Field(description="默认阈值")
    cohorts: Dict[str, Dict[str, float]] = Field(description="人群特定阈值")
    updated_at: str = Field(description="更新时间")
    notes: str = Field(description="备注说明")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "2025-08",
                "threshold": 37446.0,
                "cohorts": {
                    "default": {"threshold": 37446.0},
                    "elderly": {"threshold": 36000.0},
                    "low_income": {"threshold": 40000.0}
                },
                "updated_at": "2025-08-16T11:38:00Z",
                "notes": "阈值示例；请根据政策/文献/支付意愿调查更新并审计。"
            }
        }
    )