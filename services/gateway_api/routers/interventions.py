"""
HealthLink Gateway API 干预管理路由
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from config.database_switch import get_database
from packages.schemas.models import Intervention, Patient, Screening
from packages.schemas.requests import (
    InterventionCreateRequest, 
    InterventionApprovalRequest,
    InterventionExecutionRequest
)
from packages.schemas.responses import (
    InterventionResponse, 
    InterventionCreateResponse, 
    InterventionListResponse,
    InterventionApprovalResponse,
    PaginationMeta
)
from ..middleware import get_current_user, get_request_id
from ..exceptions import NotFoundException

router = APIRouter()

@router.post("/", response_model=InterventionCreateResponse)
async def create_intervention(
    request: InterventionCreateRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建干预记录"""
    
    # 验证患者存在
    patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", request.patient_id)
    
    # 验证筛查记录（如果提供）
    screening_id = None
    if request.screening_id:
        screening = db.query(Screening).filter(
            Screening.screening_id == request.screening_id
        ).first()
        if screening:
            screening_id = screening.id
    
    # 创建干预记录
    intervention = Intervention(
        intervention_id=str(uuid.uuid4()),
        patient_id=patient.id,
        screening_id=screening_id,
        intervention_type=request.intervention_type,
        intervention_plan=request.intervention_plan,
        priority_level=request.priority_level,
        assigned_resources=request.assigned_resources,
        estimated_cost=request.estimated_cost,
        expected_outcome=request.expected_outcome,
        approval_status="auto_approved" if request.auto_approve else "pending"
    )
    
    if request.auto_approve:
        intervention.approved_by = current_user.get("user_id", "system")
        intervention.approved_at = datetime.now()
    
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    
    return InterventionCreateResponse(
        request_id=request_id,
        data=InterventionResponse.from_orm(intervention)
    )

@router.get("/", response_model=InterventionListResponse)
async def list_interventions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    patient_id: Optional[str] = Query(None, description="患者ID筛选"),
    intervention_type: Optional[str] = Query(None, description="干预类型筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    execution_status: Optional[str] = Query(None, description="执行状态筛选"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """查询干预列表"""
    
    query = db.query(Intervention)
    
    if patient_id:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            query = query.filter(Intervention.patient_id == patient.id)
        else:
            return InterventionListResponse(
                request_id=request_id,
                data=[],
                meta=PaginationMeta(page=page, size=size, total=0, pages=0, has_next=False, has_prev=False)
            )
    
    if intervention_type:
        query = query.filter(Intervention.intervention_type == intervention_type)
    
    if approval_status:
        query = query.filter(Intervention.approval_status == approval_status)
    
    if execution_status:
        query = query.filter(Intervention.execution_status == execution_status)
    
    # 按创建时间倒序排列
    query = query.order_by(Intervention.created_at.desc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * size
    interventions = query.offset(offset).limit(size).all()
    
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return InterventionListResponse(
        request_id=request_id,
        data=[InterventionResponse.from_orm(intervention) for intervention in interventions],
        meta=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.post("/{intervention_id}:approve", response_model=InterventionApprovalResponse)
async def approve_intervention(
    intervention_id: str = Path(..., description="干预ID"),
    request: InterventionApprovalRequest = ...,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """审批干预"""
    
    intervention = db.query(Intervention).filter(
        Intervention.intervention_id == intervention_id
    ).first()
    
    if not intervention:
        raise NotFoundException("Intervention", intervention_id)
    
    # 更新审批信息
    intervention.approval_status = request.approval_status
    intervention.approved_by = request.approved_by
    intervention.approved_at = datetime.now()
    intervention.approval_notes = request.approval_notes
    
    # 如果有修改的计划，更新计划
    if request.modified_plan:
        intervention.intervention_plan = request.modified_plan
    
    db.commit()
    db.refresh(intervention)
    
    return InterventionApprovalResponse(
        request_id=request_id,
        data=InterventionResponse.from_orm(intervention)
    )