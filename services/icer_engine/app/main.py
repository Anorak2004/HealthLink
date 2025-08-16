"""
ICER Engine 主应用
独立的ICER评估微服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import evaluate

APP_VERSION = "1.0.0"
API_PREFIX = "/v1"

# 创建FastAPI应用
app = FastAPI(
    title="ICER Engine",
    description="Independent Cost-Effectiveness Ratio Evaluation Service",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(evaluate.router, prefix=API_PREFIX)

@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "service": "ICER Engine"
    }

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "ICER Engine",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }