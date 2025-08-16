"""
HealthLink Gateway API ICER评估路由
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from config.database_switch import get_database
from packages.schemas.models import ICERPolicy, ICEREvaluation
from packages.schemas.requests import ICERPolicyCreateRequest, ICEREvaluationRequest
from packages.schemas.responses import (
    ICERPolicyResponse, 
    ICERPolicyCreateResponse, 
    ICERPolicyListResponse,
    ICEREvaluationResponse,
    ICEREvaluationCreateResponse,
    PaginationMeta
)
from ..middleware import get_current_user, get_request_id
from ..exceptions import NotFoundException, ConflictException

router = APIRouter()

@router.post("/policies", response_model=ICERPolicyCreateResponse)
async def create_icer_policy(
    request: ICERPolicyCreateRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """创建ICER策略"""
    
    # 检查策略ID是否已存在
    existing_policy = db.query(ICERPolicy).filter(
        ICERPolicy.policy_id == request.policy_id,
        ICERPolicy.version == request.version
    ).first()
    
    if existing_policy:
        raise ConflictException(
            message=f"ICER policy {request.policy_id} version {request.version} already exists",
            resource="icer_policy"
        )
    
    # 如果设置为默认策略，先取消其他默认策略
    if request.is_default:
        db.query(ICERPolicy).filter(
            ICERPolicy.version == request.version,
            ICERPolicy.is_default == True
        ).update({"is_default": False})
    
    # 创建策略记录
    policy = ICERPolicy(
        policy_id=request.policy_id,
        version=request.version,
        threshold_per_daly=request.threshold_per_daly,
        policy_data=request.policy_data,
        description=request.description,
        source=request.source,
        effective_date=request.effective_date,
        expiry_date=request.expiry_date,
        is_default=request.is_default
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return ICERPolicyCreateResponse(
        request_id=request_id,
        data=ICERPolicyResponse.from_orm(policy)
    )

@router.get("/policies", response_model=ICERPolicyListResponse)
async def list_icer_policies(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    version: Optional[str] = Query(None, description="版本筛选"),
    is_active: Optional[bool] = Query(None, description="是否活跃"),
    is_default: Optional[bool] = Query(None, description="是否默认"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """查询ICER策略列表"""
    
    query = db.query(ICERPolicy)
    
    if version:
        query = query.filter(ICERPolicy.version == version)
    
    if is_active is not None:
        query = query.filter(ICERPolicy.is_active == is_active)
    
    if is_default is not None:
        query = query.filter(ICERPolicy.is_default == is_default)
    
    # 按创建时间倒序排列
    query = query.order_by(ICERPolicy.created_at.desc())
    
    # 分页
    total = query.count()
    offset = (page - 1) * size
    policies = query.offset(offset).limit(size).all()
    
    pages = (total + size - 1) // size
    has_next = page < pages
    has_prev = page > 1
    
    return ICERPolicyListResponse(
        request_id=request_id,
        data=[ICERPolicyResponse.from_orm(policy) for policy in policies],
        meta=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    )

@router.post("/evaluate", response_model=ICEREvaluationCreateResponse)
async def evaluate_icer(
    request: ICEREvaluationRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """执行ICER评估"""
    
    # 获取策略
    if request.policy_version:
        policy = db.query(ICERPolicy).filter(
            ICERPolicy.version == request.policy_version,
            ICERPolicy.is_active == True
        ).first()
    else:
        # 使用默认策略
        policy = db.query(ICERPolicy).filter(
            ICERPolicy.is_default == True,
            ICERPolicy.is_active == True
        ).first()
    
    if not policy:
        raise NotFoundException("ICER Policy", request.policy_version or "default")
    
    # 计算ICER值
    icer_value = request.intervention_cost / request.intervention_effectiveness
    threshold_used = policy.threshold_per_daly
    
    # 做出决策
    decision = "cost_effective" if icer_value <= threshold_used else "not_cost_effective"
    
    # 创建评估记录
    evaluation = ICEREvaluation(
        evaluation_id=str(uuid.uuid4()),
        policy_id=policy.id,
        intervention_cost=request.intervention_cost,
        intervention_effectiveness=request.intervention_effectiveness,
        population_size=request.population_size,
        time_horizon=request.time_horizon,
        icer_value=icer_value,
        threshold_used=threshold_used,
        decision=decision,
        calculation_metadata=request.metadata,
        cohort_id=request.cohort_id
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return ICEREvaluationCreateResponse(
        request_id=request_id,
        data=ICEREvaluationResponse.from_orm(evaluation)
    )

@router.get("/policies/{policy_id}", response_model=ICERPolicyCreateResponse)
async def get_icer_policy(
    policy_id: str = Path(..., description="策略ID"),
    version: Optional[str] = Query(None, description="版本"),
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
):
    """获取ICER策略详情"""
    
    query = db.query(ICERPolicy).filter(ICERPolicy.policy_id == policy_id)
    
    if version:
        query = query.filter(ICERPolicy.version == version)
    else:
        # 获取最新版本
        query = query.order_by(ICERPolicy.created_at.desc())
    
    policy = query.first()
    
    if not policy:
        identifier = f"{policy_id}:{version}" if version else policy_id
        raise NotFoundException("ICER Policy", identifier)
    
    return ICERPolicyCreateResponse(
        request_id=request_id,
        data=ICERPolicyResponse.from_orm(policy)
    )