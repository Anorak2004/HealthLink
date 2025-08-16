"""
HealthLink Gateway API 健康检查路由
"""
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database_switch import get_database
from packages.schemas.responses import HealthCheckResponse

router = APIRouter()

@router.get("/", response_model=HealthCheckResponse)
@router.get("/ready", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_database)):
    """健康检查端点"""
    
    # 检查数据库连接
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    # 检查外部服务状态（占位）
    external_services = {
        "nlp_api": "healthy",  # 实际应该调用NLP API检查
        "asr_api": "healthy",  # 实际应该调用ASR API检查
    }
    
    # 确定整体状态
    overall_status = "healthy" if database_status == "healthy" else "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0-mvp",
        database=database_status,
        external_services=external_services
    )

@router.get("/live")
async def liveness_check():
    """存活检查端点（简单版本）"""
    return {"status": "alive", "timestamp": datetime.now()}

@router.get("/metrics")
async def metrics():
    """Prometheus指标端点（占位）"""
    # 这里应该返回Prometheus格式的指标
    # 暂时返回简单的JSON格式
    return {
        "healthlink_requests_total": 0,
        "healthlink_request_duration_seconds": 0.0,
        "healthlink_active_connections": 0,
        "timestamp": datetime.now()
    }