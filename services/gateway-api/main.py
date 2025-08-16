"""
HealthLink Gateway API 主服务
FastAPI 应用入口点
"""
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from config.database_switch import init_database, get_config
from packages.schemas.responses import ErrorResponse, ErrorDetail, HealthCheckResponse
from .routers import patients, screenings, icer, interventions, outcomes, health
from .middleware import (
    RequestIDMiddleware, 
    LoggingMiddleware, 
    AuthMiddleware,
    RateLimitMiddleware
)
from .exceptions import setup_exception_handlers

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("Starting HealthLink Gateway API")
    
    try:
        # 初始化数据库
        init_database()
        logger.info("Database initialized successfully")
        
        # 加载配置
        config = get_config()
        logger.info("Configuration loaded", config_keys=list(config.keys()))
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    finally:
        # 关闭时清理
        logger.info("Shutting down HealthLink Gateway API")

# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    config = get_config()
    
    app = FastAPI(
        title="HealthLink Gateway API",
        description="AI-driven Comorbidity Management Platform - Gateway Service",
        version="1.0.0-mvp",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # 添加中间件
    setup_middleware(app, config)
    
    # 添加路由
    setup_routers(app)
    
    # 设置异常处理
    setup_exception_handlers(app)
    
    return app

def setup_middleware(app: FastAPI, config: Dict[str, Any]) -> None:
    """设置中间件"""
    gateway_config = config.get('gateway', {})
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=gateway_config.get('cors_origins', ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 受信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 生产环境应该限制
    )
    
    # 自定义中间件
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware, config=config)

def setup_routers(app: FastAPI) -> None:
    """设置路由"""
    # API v1 路由
    api_prefix = "/api/v1"
    
    app.include_router(
        health.router,
        prefix="/health",
        tags=["Health Check"]
    )
    
    app.include_router(
        patients.router,
        prefix=f"{api_prefix}/patients",
        tags=["Patients"]
    )
    
    app.include_router(
        screenings.router,
        prefix=f"{api_prefix}/screenings",
        tags=["Screenings"]
    )
    
    app.include_router(
        icer.router,
        prefix=f"{api_prefix}/icer",
        tags=["ICER"]
    )
    
    app.include_router(
        interventions.router,
        prefix=f"{api_prefix}/interventions",
        tags=["Interventions"]
    )
    
    app.include_router(
        outcomes.router,
        prefix=f"{api_prefix}/outcomes",
        tags=["Outcomes"]
    )

# 创建应用实例
app = create_app()

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "HealthLink Gateway API",
        "version": "1.0.0-mvp",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    gateway_config = config.get('gateway', {})
    
    uvicorn.run(
        "main:app",
        host=gateway_config.get('host', '0.0.0.0'),
        port=gateway_config.get('port', 8000),
        reload=config.get('development', {}).get('auto_reload', False),
        log_level=config.get('logging', {}).get('level', 'info').lower()
    )