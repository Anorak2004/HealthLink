"""
HealthLink Gateway API 效果追踪路由
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from config.database_switch import get_database
from packages.schemas.models import Outcome, Patient, Intervention
from packages.schemas.requests import OutcomeCreateRequest
from packages.schemas.responses import (
    OutcomeResponse, 
    OutcomeCreateResponse, 
    OutcomeListResponse,
    PaginationMeta
)
from ..middleware import get_current_user, get_request_id
from ..exceptions import NotFoundException

router = APIRouter()

@router.post("/", response_model=OutcomeCreateResponse)
async def create_outcome(
    request: OutcomeCreateRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建效果记录"""
    
    # 验证患者存在
    patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", request.patient_id)
    
    # 验证干预记录（如果提供）
    intervention_id = None
    if request.intervention_id:
        intervention = db.query(Intervention).filter(
            Intervention.intervention_id == request.intervention_id
        ).first()
        if intervention:
            intervention_id = intervention.id
    
    # 创建效果记录
    outcome = Outcome(
        outcome_id=str(uuid.uuid4()),
        patient_id=patient.id,
        intervention_id=intervention_id,
        followup_day=request.followup_day,
        measurement_date=request.measurement_date,
        adherence_score=request.adherence_score,
        adherence_details=request.adherence_details,
        clinical_metrics=request.clinical_metrics,
        emergency_visits=request.emergency_visits,
        hospitalizations=request.hospitalizations,
        direct_cost=request.direct_cost,
        indirect_cost=request.indirect_cost,
        qaly_score=request.qaly_score,
        patient_satisfaction=request.patient_satisfaction,
        quality_of_life=request.quality_of_life,
        data_source=request.data_source,
        measurement_metadata=request.measurement_metadata
    )
    
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    
    return OutcomeCreateResponse(
        request_id=request_id,
        data=OutcomeResponse.from_orm(outcome)
    )

@router.get("/", response_model=OutcomeListResponse)
async def list_outcomes(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    patient_id: Optional[str] = Query(None, description="患者ID筛选"),
    intervention_id: Optional[str] = Query(None, description="干预ID筛选"),
    followup_day_min: Optional[int] = Query(None, ge=0, description="随访天数最小值"),
    followup_day_max: Optional[int] = Query(None, ge=0, description="随访天数最大值"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """查询效果列表"""
    
    query = db.query(Outcome)
    
    if patient_id:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            query = query.filter(Outcome.patient_id == patient.id)
        else:
            return OutcomeListResponse(
                request_id=request_id,
                data=[],
                meta=PaginationMeta(page=page, size=size, total=0, pages=0, has_next=False, has_prev=False)
            )
    
    if intervention_id:
        intervention = db.query(Intervention).filter(
            Intervention.intervention_id == intervention_id
        ).first()
        if intervention:
            query = query.filter(Outcome.intervention_id == intervention.id)
    
    if followup_day_min is not None:
        query = query.filter(Outcome.followup_day >= followup_day_min)
    
    if followup_day_max is not None:
        query = query.filter(Outcome.followup_day <= followup_day_max)
    
    # 按测量日期倒序排列
    query = query.order_by(Outcome.measurement_date.desc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * size
    outcomes = query.offset(offset).limit(size).all()
    
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return OutcomeListResponse(
        request_id=request_id,
        data=[OutcomeResponse.from_orm(outcome) for outcome in outcomes],
        meta=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )