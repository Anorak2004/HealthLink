"""
HealthLink 数据模型定义
SQLAlchemy ORM 模型，支持 SQLite/MySQL 切换
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class Patient(Base, TimestampMixin):
    """患者模型"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)  # 业务ID
    name = Column(String(100), nullable=False)
    gender = Column(String(10))  # M/F/Other
    birth_date = Column(DateTime)
    phone = Column(String(20))
    email = Column(String(100))
    
    # 医疗信息
    medical_record_number = Column(String(50), unique=True)
    primary_doctor_id = Column(String(50))
    
    # 元数据
    metadata_json = Column(JSON, default=dict)  # 扩展字段
    is_active = Column(Boolean, default=True)
    
    # 关系
    screenings = relationship("Screening", back_populates="patient")
    interventions = relationship("Intervention", back_populates="patient")
    outcomes = relationship("Outcome", back_populates="patient")
    
    __table_args__ = (
        Index('idx_patient_active', 'is_active'),
        Index('idx_patient_doctor', 'primary_doctor_id'),
    )

class Screening(Base, TimestampMixin):
    """筛查记录模型"""
    __tablename__ = "screenings"
    
    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # 输入数据
    input_text = Column(Text)  # NLP输入文本
    input_audio_path = Column(String(500))  # ASR音频文件路径
    input_metadata = Column(JSON, default=dict)
    
    # NLP结果
    nlp_entities = Column(JSON, default=list)  # 提取的实体
    nlp_confidence = Column(Float)
    nlp_model_version = Column(String(50))
    
    # ASR结果
    asr_transcript = Column(Text)  # 转写文本
    asr_confidence = Column(Float)
    asr_keywords = Column(JSON, default=list)  # 识别的关键词
    
    # 筛查结果
    triage_level = Column(String(20))  # low/medium/high
    triage_score = Column(Float)
    risk_factors = Column(JSON, default=list)
    
    # 状态
    status = Column(String(20), default="pending")  # pending/completed/failed
    processed_at = Column(DateTime)
    
    # 关系
    patient = relationship("Patient", back_populates="screenings")
    interventions = relationship("Intervention", back_populates="screening")
    
    __table_args__ = (
        Index('idx_screening_patient', 'patient_id'),
        Index('idx_screening_status', 'status'),
        Index('idx_screening_triage', 'triage_level'),
    )

class ICERPolicy(Base, TimestampMixin):
    """ICER策略模型"""
    __tablename__ = "icer_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(50), unique=True, index=True, nullable=False)
    version = Column(String(20), nullable=False)  # 如 "2025-08"
    
    # 策略内容
    threshold_per_daly = Column(Float, nullable=False)  # 元/DALY阈值
    policy_data = Column(JSON, nullable=False)  # 完整策略JSON
    
    # 元数据
    description = Column(Text)
    source = Column(String(200))  # 策略来源
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 关系
    evaluations = relationship("ICEREvaluation", back_populates="policy")
    
    __table_args__ = (
        Index('idx_icer_policy_active', 'is_active'),
        Index('idx_icer_policy_version', 'version'),
        UniqueConstraint('version', 'is_default', name='uq_default_policy_per_version'),
    )

class ICEREvaluation(Base, TimestampMixin):
    """ICER评估记录模型"""
    __tablename__ = "icer_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(50), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("icer_policies.id"), nullable=False)
    
    # 输入参数
    intervention_cost = Column(Float, nullable=False)
    intervention_effectiveness = Column(Float, nullable=False)  # DALY saved
    population_size = Column(Integer)
    time_horizon = Column(Integer)  # 年
    
    # 计算结果
    icer_value = Column(Float, nullable=False)  # 计算出的ICER值
    threshold_used = Column(Float, nullable=False)  # 使用的阈值
    decision = Column(String(20), nullable=False)  # cost_effective/not_cost_effective
    
    # 元数据
    calculation_metadata = Column(JSON, default=dict)
    cohort_id = Column(String(50))  # 人群标识
    
    # 关系
    policy = relationship("ICERPolicy", back_populates="evaluations")
    interventions = relationship("Intervention", back_populates="icer_evaluation")
    
    __table_args__ = (
        Index('idx_icer_eval_policy', 'policy_id'),
        Index('idx_icer_eval_decision', 'decision'),
        Index('idx_icer_eval_cohort', 'cohort_id'),
    )

class Intervention(Base, TimestampMixin):
    """干预记录模型"""
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    screening_id = Column(Integer, ForeignKey("screenings.id"))
    icer_evaluation_id = Column(Integer, ForeignKey("icer_evaluations.id"))
    
    # 干预内容
    intervention_type = Column(String(50), nullable=False)  # medication/lifestyle/education
    intervention_plan = Column(JSON, nullable=False)  # 具体干预计划
    priority_level = Column(String(20))  # high/medium/low
    
    # 资源匹配
    assigned_resources = Column(JSON, default=list)  # 分配的资源
    estimated_cost = Column(Float)
    expected_outcome = Column(String(200))
    
    # 审批状态
    approval_status = Column(String(20), default="pending")  # pending/approved/rejected/auto_approved
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # 执行状态
    execution_status = Column(String(20), default="planned")  # planned/in_progress/completed/cancelled
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 关系
    patient = relationship("Patient", back_populates="interventions")
    screening = relationship("Screening", back_populates="interventions")
    icer_evaluation = relationship("ICEREvaluation", back_populates="interventions")
    outcomes = relationship("Outcome", back_populates="intervention")
    
    __table_args__ = (
        Index('idx_intervention_patient', 'patient_id'),
        Index('idx_intervention_status', 'approval_status', 'execution_status'),
        Index('idx_intervention_type', 'intervention_type'),
    )

class Outcome(Base, TimestampMixin):
    """效果追踪模型"""
    __tablename__ = "outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    outcome_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    intervention_id = Column(Integer, ForeignKey("interventions.id"))
    
    # 追踪时间点
    followup_day = Column(Integer, nullable=False)  # 干预后第几天
    measurement_date = Column(DateTime, nullable=False)
    
    # 依从性指标
    adherence_score = Column(Float)  # 0-1
    adherence_details = Column(JSON, default=dict)
    
    # 临床指标
    clinical_metrics = Column(JSON, default=dict)  # 血压、血糖等
    emergency_visits = Column(Integer, default=0)
    hospitalizations = Column(Integer, default=0)
    
    # 经济指标
    direct_cost = Column(Float)  # 直接医疗成本
    indirect_cost = Column(Float)  # 间接成本
    qaly_score = Column(Float)  # 质量调整生命年
    
    # 主观指标
    patient_satisfaction = Column(Float)  # 1-5分
    quality_of_life = Column(Float)  # 生活质量评分
    
    # 元数据
    data_source = Column(String(50))  # manual/ehr/survey/device
    measurement_metadata = Column(JSON, default=dict)
    
    # 关系
    patient = relationship("Patient", back_populates="outcomes")
    intervention = relationship("Intervention", back_populates="outcomes")
    
    __table_args__ = (
        Index('idx_outcome_patient', 'patient_id'),
        Index('idx_outcome_intervention', 'intervention_id'),
        Index('idx_outcome_followup', 'followup_day'),
        Index('idx_outcome_date', 'measurement_date'),
    )

class AuditLog(Base, TimestampMixin):
    """审计日志模型"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), index=True, nullable=False)
    
    # 操作信息
    action = Column(String(50), nullable=False)  # create/read/update/delete
    resource_type = Column(String(50), nullable=False)  # patient/screening/intervention
    resource_id = Column(String(50))
    
    # 用户信息
    user_id = Column(String(50))
    user_role = Column(String(50))
    organization_id = Column(String(50))
    
    # 请求信息
    ip_address = Column(String(45))  # IPv6支持
    user_agent = Column(String(500))
    endpoint = Column(String(200))
    method = Column(String(10))
    
    # 结果信息
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # 数据变更
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    __table_args__ = (
        Index('idx_audit_request', 'request_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_created', 'created_at'),
    )