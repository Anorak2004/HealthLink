"""
HealthLink Gateway API 患者管理路由
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from config.database_switch import get_database
from packages.schemas.models import Patient
from packages.schemas.requests import (
    PatientCreateRequest, 
    PatientUpdateRequest, 
    PatientQueryRequest
)
from packages.schemas.responses import (
    PatientResponse, 
    PatientCreateResponse, 
    PatientListResponse,
    PaginationMeta
)
from ..middleware import get_current_user, get_request_id
from ..exceptions import NotFoundException, ConflictException

router = APIRouter()

@router.post("/", response_model=PatientCreateResponse)
async def create_patient(
    request: PatientCreateRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建患者"""
    
    # 检查患者ID是否已存在
    existing_patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id
    ).first()
    
    if existing_patient:
        raise ConflictException(
            message=f"Patient with ID {request.patient_id} already exists",
            resource="patient"
        )
    
    # 创建患者记录
    patient = Patient(
        patient_id=request.patient_id,
        name=request.name,
        gender=request.gender,
        birth_date=request.birth_date,
        phone=request.phone,
        email=request.email,
        medical_record_number=request.medical_record_number,
        primary_doctor_id=request.primary_doctor_id,
        metadata_json=request.metadata
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    return PatientCreateResponse(
        request_id=request_id,
        data=PatientResponse.from_orm(patient)
    )

@router.get("/", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    patient_id: Optional[str] = Query(None, description="患者ID筛选"),
    name: Optional[str] = Query(None, description="姓名筛选"),
    primary_doctor_id: Optional[str] = Query(None, description="主治医生筛选"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    created_after: Optional[datetime] = Query(None, description="创建时间起始"),
    created_before: Optional[datetime] = Query(None, description="创建时间结束"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """查询患者列表"""
    
    # 构建查询条件
    query = db.query(Patient)
    
    if patient_id:
        query = query.filter(Patient.patient_id.ilike(f"%{patient_id}%"))
    
    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))
    
    if primary_doctor_id:
        query = query.filter(Patient.primary_doctor_id == primary_doctor_id)
    
    if is_active is not None:
        query = query.filter(Patient.is_active == is_active)
    
    if created_after:
        query = query.filter(Patient.created_at >= created_after)
    
    if created_before:
        query = query.filter(Patient.created_at <= created_before)
    
    # 排序
    if hasattr(Patient, sort_by):
        order_column = getattr(Patient, sort_by)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * size
    patients = query.offset(offset).limit(size).all()
    
    # 计算分页信息
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return PatientListResponse(
        request_id=request_id,
        data=[PatientResponse.from_orm(patient) for patient in patients],
        meta=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.get("/{patient_id}", response_model=PatientCreateResponse)
async def get_patient(
    patient_id: str = Path(..., description="患者ID"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """获取患者详情"""
    
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", patient_id)
    
    return PatientCreateResponse(
        request_id=request_id,
        data=PatientResponse.from_orm(patient)
    )

@router.put("/{patient_id}", response_model=PatientCreateResponse)
async def update_patient(
    patient_id: str = Path(..., description="患者ID"),
    request: PatientUpdateRequest = ...,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """更新患者信息"""
    
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", patient_id)
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "metadata":
            setattr(patient, "metadata_json", value)
        else:
            setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    return PatientCreateResponse(
        request_id=request_id,
        data=PatientResponse.from_orm(patient)
    )

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str = Path(..., description="患者ID"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """删除患者（软删除）"""
    
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", patient_id)
    
    # 软删除：设置为非活跃状态
    patient.is_active = False
    db.commit()
    
    return {
        "request_id": request_id,
        "success": True,
        "message": f"Patient {patient_id} has been deactivated"
    }