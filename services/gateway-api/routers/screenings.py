"""
HealthLink Gateway API 筛查管理路由
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from config.database_switch import get_database
from packages.schemas.models import Screening, Patient
from packages.schemas.requests import ScreeningCreateRequest, ScreeningTriageRequest
from packages.schemas.responses import (
    ScreeningResponse, 
    ScreeningCreateResponse, 
    ScreeningListResponse,
    ScreeningTriageResponse,
    PaginationMeta
)
from ..middleware import get_current_user, get_request_id
from ..exceptions import NotFoundException

router = APIRouter()

@router.post("/", response_model=ScreeningCreateResponse)
async def create_screening(
    request: ScreeningCreateRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建筛查记录"""
    
    # 验证患者存在
    patient = db.query(Patient).filter(
        Patient.patient_id == request.patient_id
    ).first()
    
    if not patient:
        raise NotFoundException("Patient", request.patient_id)
    
    # 创建筛查记录
    screening = Screening(
        screening_id=str(uuid.uuid4()),
        patient_id=patient.id,
        input_text=request.input_text,
        input_metadata=request.input_metadata,
        status="pending"
    )
    
    # 如果有音频数据，保存到文件（简化实现）
    if request.input_audio_base64:
        # 这里应该解码base64并保存音频文件
        # 暂时只记录有音频输入
        screening.input_audio_path = f"audio/{screening.screening_id}.wav"
    
    db.add(screening)
    db.commit()
    db.refresh(screening)
    
    return ScreeningCreateResponse(
        request_id=request_id,
        data=ScreeningResponse.from_orm(screening)
    )

@router.get("/", response_model=ScreeningListResponse)
async def list_screenings(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    patient_id: Optional[str] = Query(None, description="患者ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    triage_level: Optional[str] = Query(None, description="分诊级别筛选"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """查询筛查列表"""
    
    query = db.query(Screening)
    
    if patient_id:
        # 通过患者ID查找
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if patient:
            query = query.filter(Screening.patient_id == patient.id)
        else:
            # 患者不存在，返回空结果
            return ScreeningListResponse(
                request_id=request_id,
                data=[],
                meta=PaginationMeta(page=page, size=size, total=0, pages=0, has_next=False, has_prev=False)
            )
    
    if status:
        query = query.filter(Screening.status == status)
    
    if triage_level:
        query = query.filter(Screening.triage_level == triage_level)
    
    # 按创建时间倒序排列
    query = query.order_by(Screening.created_at.desc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * size
    screenings = query.offset(offset).limit(size).all()
    
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return ScreeningListResponse(
        request_id=request_id,
        data=[ScreeningResponse.from_orm(screening) for screening in screenings],
        meta=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.post("/{screening_id}:triage", response_model=ScreeningTriageResponse)
async def triage_screening(
    screening_id: str = Path(..., description="筛查ID"),
    request: ScreeningTriageRequest = ...,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """执行筛查分诊"""
    
    screening = db.query(Screening).filter(
        Screening.screening_id == screening_id
    ).first()
    
    if not screening:
        raise NotFoundException("Screening", screening_id)
    
    # 如果有手动覆盖，直接使用
    if request.triage_override:
        screening.triage_level = request.triage_override
        screening.triage_score = 1.0  # 手动分诊给满分
    else:
        # 这里应该调用NLP/ASR服务进行自动分诊
        # MVP阶段使用简化逻辑
        if screening.input_text:
            # 简单的关键词匹配逻辑
            high_risk_keywords = ["胸痛", "呼吸困难", "心悸", "昏厥"]
            medium_risk_keywords = ["头晕", "乏力", "水肿"]
            
            text = screening.input_text.lower()
            if any(keyword in text for keyword in high_risk_keywords):
                screening.triage_level = "high"
                screening.triage_score = 0.8
            elif any(keyword in text for keyword in medium_risk_keywords):
                screening.triage_level = "medium"
                screening.triage_score = 0.6
            else:
                screening.triage_level = "low"
                screening.triage_score = 0.3
        else:
            screening.triage_level = "low"
            screening.triage_score = 0.3
    
    screening.status = "completed"
    screening.processed_at = datetime.now()
    
    db.commit()
    db.refresh(screening)
    
    return ScreeningTriageResponse(
        request_id=request_id,
        data=ScreeningResponse.from_orm(screening)
    )