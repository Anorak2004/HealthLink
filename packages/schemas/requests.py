"""
HealthLink API 请求模型
Pydantic 模型用于API请求验证
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# 枚举类型定义
class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"

class TriageLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ApprovalStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

class ExecutionStatusEnum(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InterventionTypeEnum(str, Enum):
    MEDICATION = "medication"
    LIFESTYLE = "lifestyle"
    EDUCATION = "education"
    MONITORING = "monitoring"

# 基础请求模型
class BaseRequest(BaseModel):
    """基础请求模型"""
    request_id: Optional[str] = Field(None, description="请求ID，用于幂等性")

# 患者相关请求
class PatientCreateRequest(BaseRequest):
    """创建患者请求"""
    patient_id: str = Field(..., min_length=1, max_length=50, description="患者业务ID")
    name: str = Field(..., min_length=1, max_length=100, description="患者姓名")
    gender: Optional[GenderEnum] = Field(None, description="性别")
    birth_date: Optional[date] = Field(None, description="出生日期")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱地址")
    medical_record_number: Optional[str] = Field(None, max_length=50, description="病历号")
    primary_doctor_id: Optional[str] = Field(None, max_length=50, description="主治医生ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展元数据")

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PatientUpdateRequest(BaseModel):
    """更新患者请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    primary_doctor_id: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# 筛查相关请求
class ScreeningCreateRequest(BaseRequest):
    """创建筛查请求"""
    patient_id: str = Field(..., description="患者ID")
    input_text: Optional[str] = Field(None, description="NLP输入文本")
    input_audio_base64: Optional[str] = Field(None, description="ASR音频数据(base64编码)")
    input_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="输入元数据")

    @validator('input_text', 'input_audio_base64')
    def validate_input(cls, v, values):
        # 至少需要提供文本或音频输入之一
        if not v and not values.get('input_text') and not values.get('input_audio_base64'):
            raise ValueError('Must provide either input_text or input_audio_base64')
        return v

class ScreeningTriageRequest(BaseModel):
    """筛查分诊请求"""
    force_retriage: Optional[bool] = Field(False, description="是否强制重新分诊")
    triage_override: Optional[TriageLevelEnum] = Field(None, description="手动覆盖分诊级别")
    notes: Optional[str] = Field(None, max_length=1000, description="分诊备注")

# ICER相关请求
class ICERPolicyCreateRequest(BaseRequest):
    """创建ICER策略请求"""
    policy_id: str = Field(..., min_length=1, max_length=50, description="策略ID")
    version: str = Field(..., min_length=1, max_length=20, description="策略版本")
    threshold_per_daly: float = Field(..., gt=0, description="DALY阈值(元)")
    policy_data: Dict[str, Any] = Field(..., description="策略数据")
    description: Optional[str] = Field(None, description="策略描述")
    source: Optional[str] = Field(None, max_length=200, description="策略来源")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    expiry_date: Optional[datetime] = Field(None, description="失效日期")
    is_default: Optional[bool] = Field(False, description="是否为默认策略")

class ICEREvaluationRequest(BaseRequest):
    """ICER评估请求"""
    intervention_cost: float = Field(..., ge=0, description="干预成本(元)")
    intervention_effectiveness: float = Field(..., gt=0, description="干预效果(DALY saved)")
    population_size: Optional[int] = Field(None, gt=0, description="目标人群规模")
    time_horizon: Optional[int] = Field(5, gt=0, le=30, description="时间跨度(年)")
    policy_version: Optional[str] = Field(None, description="指定策略版本")
    cohort_id: Optional[str] = Field(None, max_length=50, description="人群标识")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="计算元数据")

# 干预相关请求
class InterventionCreateRequest(BaseRequest):
    """创建干预请求"""
    patient_id: str = Field(..., description="患者ID")
    screening_id: Optional[str] = Field(None, description="关联筛查ID")
    intervention_type: InterventionTypeEnum = Field(..., description="干预类型")
    intervention_plan: Dict[str, Any] = Field(..., description="干预计划详情")
    priority_level: Optional[str] = Field("medium", description="优先级")
    assigned_resources: Optional[List[str]] = Field(default_factory=list, description="分配资源")
    estimated_cost: Optional[float] = Field(None, ge=0, description="预估成本")
    expected_outcome: Optional[str] = Field(None, max_length=200, description="预期结果")
    auto_approve: Optional[bool] = Field(False, description="是否自动审批")

class InterventionApprovalRequest(BaseModel):
    """干预审批请求"""
    approval_status: ApprovalStatusEnum = Field(..., description="审批状态")
    approved_by: str = Field(..., min_length=1, max_length=100, description="审批人")
    approval_notes: Optional[str] = Field(None, description="审批备注")
    modified_plan: Optional[Dict[str, Any]] = Field(None, description="修改后的计划")

class InterventionExecutionRequest(BaseModel):
    """干预执行状态更新请求"""
    execution_status: ExecutionStatusEnum = Field(..., description="执行状态")
    execution_notes: Optional[str] = Field(None, description="执行备注")
    actual_cost: Optional[float] = Field(None, ge=0, description="实际成本")

# 效果追踪相关请求
class OutcomeCreateRequest(BaseRequest):
    """创建效果记录请求"""
    patient_id: str = Field(..., description="患者ID")
    intervention_id: Optional[str] = Field(None, description="关联干预ID")
    followup_day: int = Field(..., ge=0, description="随访天数")
    measurement_date: datetime = Field(..., description="测量日期")
    
    # 依从性数据
    adherence_score: Optional[float] = Field(None, ge=0, le=1, description="依从性评分")
    adherence_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="依从性详情")
    
    # 临床数据
    clinical_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="临床指标")
    emergency_visits: Optional[int] = Field(0, ge=0, description="急诊次数")
    hospitalizations: Optional[int] = Field(0, ge=0, description="住院次数")
    
    # 经济数据
    direct_cost: Optional[float] = Field(None, ge=0, description="直接成本")
    indirect_cost: Optional[float] = Field(None, ge=0, description="间接成本")
    qaly_score: Optional[float] = Field(None, ge=0, description="QALY评分")
    
    # 主观数据
    patient_satisfaction: Optional[float] = Field(None, ge=1, le=5, description="患者满意度")
    quality_of_life: Optional[float] = Field(None, ge=0, le=100, description="生活质量评分")
    
    # 元数据
    data_source: Optional[str] = Field("manual", max_length=50, description="数据来源")
    measurement_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="测量元数据")

# 查询请求
class PaginationRequest(BaseModel):
    """分页请求"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")

class PatientQueryRequest(PaginationRequest):
    """患者查询请求"""
    patient_id: Optional[str] = Field(None, description="患者ID筛选")
    name: Optional[str] = Field(None, description="姓名筛选")
    primary_doctor_id: Optional[str] = Field(None, description="主治医生筛选")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")

class ScreeningQueryRequest(PaginationRequest):
    """筛查查询请求"""
    patient_id: Optional[str] = Field(None, description="患者ID筛选")
    triage_level: Optional[TriageLevelEnum] = Field(None, description="分诊级别筛选")
    status: Optional[str] = Field(None, description="状态筛选")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")

class InterventionQueryRequest(PaginationRequest):
    """干预查询请求"""
    patient_id: Optional[str] = Field(None, description="患者ID筛选")
    intervention_type: Optional[InterventionTypeEnum] = Field(None, description="干预类型筛选")
    approval_status: Optional[ApprovalStatusEnum] = Field(None, description="审批状态筛选")
    execution_status: Optional[ExecutionStatusEnum] = Field(None, description="执行状态筛选")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")

class OutcomeQueryRequest(PaginationRequest):
    """效果查询请求"""
    patient_id: Optional[str] = Field(None, description="患者ID筛选")
    intervention_id: Optional[str] = Field(None, description="干预ID筛选")
    followup_day_min: Optional[int] = Field(None, ge=0, description="随访天数最小值")
    followup_day_max: Optional[int] = Field(None, ge=0, description="随访天数最大值")
    measurement_after: Optional[datetime] = Field(None, description="测量时间起始")
    measurement_before: Optional[datetime] = Field(None, description="测量时间结束")