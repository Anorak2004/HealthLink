"""
HealthLink API 响应模型
Pydantic 模型用于API响应序列化
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    request_id: Optional[str] = Field(None, description="请求ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: Optional[str] = Field(None, description="错误字段")

class ErrorResponse(BaseResponse):
    """错误响应"""
    error: ErrorDetail = Field(..., description="错误详情")
    trace_id: Optional[str] = Field(None, description="追踪ID")

class SuccessResponse(BaseResponse):
    """成功响应基类"""
    success: bool = Field(True, description="操作是否成功")

# 分页响应
class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

class PaginatedResponse(SuccessResponse):
    """分页响应基类"""
    meta: PaginationMeta = Field(..., description="分页元数据")

# 患者相关响应
class PatientResponse(BaseModel):
    """患者响应"""
    id: int = Field(..., description="内部ID")
    patient_id: str = Field(..., description="患者业务ID")
    name: str = Field(..., description="患者姓名")
    gender: Optional[str] = Field(None, description="性别")
    birth_date: Optional[date] = Field(None, description="出生日期")
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    medical_record_number: Optional[str] = Field(None, description="病历号")
    primary_doctor_id: Optional[str] = Field(None, description="主治医生ID")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    is_active: bool = Field(..., description="是否活跃")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class PatientCreateResponse(SuccessResponse):
    """创建患者响应"""
    data: PatientResponse = Field(..., description="患者数据")

class PatientListResponse(PaginatedResponse):
    """患者列表响应"""
    data: List[PatientResponse] = Field(..., description="患者列表")

# 筛查相关响应
class ScreeningResponse(BaseModel):
    """筛查响应"""
    id: int = Field(..., description="内部ID")
    screening_id: str = Field(..., description="筛查业务ID")
    patient_id: int = Field(..., description="患者内部ID")
    
    # 输入数据
    input_text: Optional[str] = Field(None, description="输入文本")
    input_audio_path: Optional[str] = Field(None, description="音频文件路径")
    input_metadata: Optional[Dict[str, Any]] = Field(None, description="输入元数据")
    
    # NLP结果
    nlp_entities: Optional[List[Dict[str, Any]]] = Field(None, description="NLP实体")
    nlp_confidence: Optional[float] = Field(None, description="NLP置信度")
    nlp_model_version: Optional[str] = Field(None, description="NLP模型版本")
    
    # ASR结果
    asr_transcript: Optional[str] = Field(None, description="ASR转写文本")
    asr_confidence: Optional[float] = Field(None, description="ASR置信度")
    asr_keywords: Optional[List[str]] = Field(None, description="ASR关键词")
    
    # 筛查结果
    triage_level: Optional[str] = Field(None, description="分诊级别")
    triage_score: Optional[float] = Field(None, description="分诊评分")
    risk_factors: Optional[List[str]] = Field(None, description="风险因素")
    
    # 状态
    status: str = Field(..., description="处理状态")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class ScreeningCreateResponse(SuccessResponse):
    """创建筛查响应"""
    data: ScreeningResponse = Field(..., description="筛查数据")

class ScreeningListResponse(PaginatedResponse):
    """筛查列表响应"""
    data: List[ScreeningResponse] = Field(..., description="筛查列表")

class ScreeningTriageResponse(SuccessResponse):
    """筛查分诊响应"""
    data: ScreeningResponse = Field(..., description="更新后的筛查数据")

# ICER相关响应
class ICERPolicyResponse(BaseModel):
    """ICER策略响应"""
    id: int = Field(..., description="内部ID")
    policy_id: str = Field(..., description="策略业务ID")
    version: str = Field(..., description="策略版本")
    threshold_per_daly: float = Field(..., description="DALY阈值")
    policy_data: Dict[str, Any] = Field(..., description="策略数据")
    description: Optional[str] = Field(None, description="策略描述")
    source: Optional[str] = Field(None, description="策略来源")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    expiry_date: Optional[datetime] = Field(None, description="失效日期")
    is_active: bool = Field(..., description="是否活跃")
    is_default: bool = Field(..., description="是否为默认策略")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class ICERPolicyCreateResponse(SuccessResponse):
    """创建ICER策略响应"""
    data: ICERPolicyResponse = Field(..., description="策略数据")

class ICERPolicyListResponse(PaginatedResponse):
    """ICER策略列表响应"""
    data: List[ICERPolicyResponse] = Field(..., description="策略列表")

class ICEREvaluationResponse(BaseModel):
    """ICER评估响应"""
    id: int = Field(..., description="内部ID")
    evaluation_id: str = Field(..., description="评估业务ID")
    policy_id: int = Field(..., description="策略内部ID")
    
    # 输入参数
    intervention_cost: float = Field(..., description="干预成本")
    intervention_effectiveness: float = Field(..., description="干预效果")
    population_size: Optional[int] = Field(None, description="人群规模")
    time_horizon: Optional[int] = Field(None, description="时间跨度")
    
    # 计算结果
    icer_value: float = Field(..., description="ICER值")
    threshold_used: float = Field(..., description="使用的阈值")
    decision: str = Field(..., description="决策结果")
    
    # 元数据
    calculation_metadata: Optional[Dict[str, Any]] = Field(None, description="计算元数据")
    cohort_id: Optional[str] = Field(None, description="人群标识")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

class ICEREvaluationCreateResponse(SuccessResponse):
    """创建ICER评估响应"""
    data: ICEREvaluationResponse = Field(..., description="评估数据")

# 干预相关响应
class InterventionResponse(BaseModel):
    """干预响应"""
    id: int = Field(..., description="内部ID")
    intervention_id: str = Field(..., description="干预业务ID")
    patient_id: int = Field(..., description="患者内部ID")
    screening_id: Optional[int] = Field(None, description="筛查内部ID")
    icer_evaluation_id: Optional[int] = Field(None, description="ICER评估内部ID")
    
    # 干预内容
    intervention_type: str = Field(..., description="干预类型")
    intervention_plan: Dict[str, Any] = Field(..., description="干预计划")
    priority_level: Optional[str] = Field(None, description="优先级")
    
    # 资源匹配
    assigned_resources: Optional[List[str]] = Field(None, description="分配资源")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    expected_outcome: Optional[str] = Field(None, description="预期结果")
    
    # 审批状态
    approval_status: str = Field(..., description="审批状态")
    approved_by: Optional[str] = Field(None, description="审批人")
    approved_at: Optional[datetime] = Field(None, description="审批时间")
    approval_notes: Optional[str] = Field(None, description="审批备注")
    
    # 执行状态
    execution_status: str = Field(..., description="执行状态")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class InterventionCreateResponse(SuccessResponse):
    """创建干预响应"""
    data: InterventionResponse = Field(..., description="干预数据")

class InterventionListResponse(PaginatedResponse):
    """干预列表响应"""
    data: List[InterventionResponse] = Field(..., description="干预列表")

class InterventionApprovalResponse(SuccessResponse):
    """干预审批响应"""
    data: InterventionResponse = Field(..., description="更新后的干预数据")

# 效果追踪相关响应
class OutcomeResponse(BaseModel):
    """效果响应"""
    id: int = Field(..., description="内部ID")
    outcome_id: str = Field(..., description="效果业务ID")
    patient_id: int = Field(..., description="患者内部ID")
    intervention_id: Optional[int] = Field(None, description="干预内部ID")
    
    # 追踪时间点
    followup_day: int = Field(..., description="随访天数")
    measurement_date: datetime = Field(..., description="测量日期")
    
    # 依从性指标
    adherence_score: Optional[float] = Field(None, description="依从性评分")
    adherence_details: Optional[Dict[str, Any]] = Field(None, description="依从性详情")
    
    # 临床指标
    clinical_metrics: Optional[Dict[str, Any]] = Field(None, description="临床指标")
    emergency_visits: Optional[int] = Field(None, description="急诊次数")
    hospitalizations: Optional[int] = Field(None, description="住院次数")
    
    # 经济指标
    direct_cost: Optional[float] = Field(None, description="直接成本")
    indirect_cost: Optional[float] = Field(None, description="间接成本")
    qaly_score: Optional[float] = Field(None, description="QALY评分")
    
    # 主观指标
    patient_satisfaction: Optional[float] = Field(None, description="患者满意度")
    quality_of_life: Optional[float] = Field(None, description="生活质量评分")
    
    # 元数据
    data_source: Optional[str] = Field(None, description="数据来源")
    measurement_metadata: Optional[Dict[str, Any]] = Field(None, description="测量元数据")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class OutcomeCreateResponse(SuccessResponse):
    """创建效果响应"""
    data: OutcomeResponse = Field(..., description="效果数据")

class OutcomeListResponse(PaginatedResponse):
    """效果列表响应"""
    data: List[OutcomeResponse] = Field(..., description="效果列表")

# 健康检查响应
class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    version: str = Field(..., description="服务版本")
    database: str = Field(..., description="数据库状态")
    external_services: Dict[str, str] = Field(..., description="外部服务状态")

# 统计响应
class StatsResponse(BaseModel):
    """统计响应"""
    total_patients: int = Field(..., description="总患者数")
    total_screenings: int = Field(..., description="总筛查数")
    total_interventions: int = Field(..., description="总干预数")
    total_outcomes: int = Field(..., description="总效果记录数")
    active_interventions: int = Field(..., description="活跃干预数")
    pending_approvals: int = Field(..., description="待审批数")
    
    # 按级别统计
    triage_stats: Dict[str, int] = Field(..., description="分诊级别统计")
    intervention_type_stats: Dict[str, int] = Field(..., description="干预类型统计")
    
    # 时间范围
    stats_period: str = Field(..., description="统计周期")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")