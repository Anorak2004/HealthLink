"""
HealthLink Gateway API 中间件
处理请求ID、日志、认证、限流等
"""
import time
import uuid
import json
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

import structlog
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import JWTError, jwt

from packages.schemas.responses import ErrorResponse, ErrorDetail

logger = structlog.get_logger()

class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成或获取请求ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # 添加到请求状态
        request.state.request_id = request_id
        
        # 调用下一个中间件
        response = await call_next(request)
        
        # 添加到响应头
        response.headers["X-Request-ID"] = request_id
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 获取请求信息
        request_id = getattr(request.state, 'request_id', 'unknown')
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求开始
        logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(
                "Request completed",
                request_id=request_id,
                method=method,
                url=url,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求错误
            logger.error(
                "Request failed",
                request_id=request_id,
                method=method,
                url=url,
                error=str(e),
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # 重新抛出异常
            raise

class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""
    
    # 不需要认证的路径
    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/health/",
        "/health/ready",
        "/health/live"
    }
    
    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or "your-secret-key-here"  # 从配置获取
        self.algorithm = "HS256"
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否需要认证
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # 开发模式跳过认证
        if self._is_development_mode():
            # 设置模拟用户信息
            request.state.user = {
                "user_id": "dev_user",
                "role": "admin",
                "organization_id": "dev_org"
            }
            return await call_next(request)
        
        # 获取认证信息
        authorization = request.headers.get("Authorization")
        if not authorization:
            return self._create_auth_error("Missing authorization header")
        
        try:
            # 解析JWT token
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return self._create_auth_error("Invalid authorization scheme")
            
            # 验证token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 设置用户信息
            request.state.user = {
                "user_id": payload.get("sub"),
                "role": payload.get("role", "user"),
                "organization_id": payload.get("org"),
                "permissions": payload.get("permissions", [])
            }
            
            return await call_next(request)
            
        except (ValueError, JWTError) as e:
            return self._create_auth_error(f"Invalid token: {str(e)}")
    
    def _is_exempt_path(self, path: str) -> bool:
        """检查路径是否免认证"""
        return path in self.EXEMPT_PATHS or path.startswith("/health")
    
    def _is_development_mode(self) -> bool:
        """检查是否为开发模式"""
        # 这里应该从配置读取
        return True  # MVP阶段暂时返回True
    
    def _create_auth_error(self, message: str) -> JSONResponse:
        """创建认证错误响应"""
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="AUTHENTICATION_FAILED",
                message=message
            )
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.dict()
        )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, config: Dict[str, Any]):
        super().__init__(app)
        rate_limit_config = config.get('gateway', {}).get('rate_limit', {})
        self.requests_per_minute = rate_limit_config.get('requests_per_minute', 100)
        self.burst = rate_limit_config.get('burst', 20)
        
        # 使用内存存储（生产环境应使用Redis）
        self.clients = defaultdict(lambda: deque())
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查限流
        if not self._is_allowed(client_id):
            return self._create_rate_limit_error()
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID，其次使用IP
        user = getattr(request.state, 'user', None)
        if user and user.get('user_id'):
            return f"user:{user['user_id']}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # 获取客户端请求记录
        requests = self.clients[client_id]
        
        # 清理过期记录
        while requests and requests[0] < minute_ago:
            requests.popleft()
        
        # 检查是否超过限制
        if len(requests) >= self.requests_per_minute:
            return False
        
        # 记录当前请求
        requests.append(now)
        
        return True
    
    def _create_rate_limit_error(self) -> JSONResponse:
        """创建限流错误响应"""
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response.dict(),
            headers={"Retry-After": "60"}
        )

# 依赖注入函数
def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前用户信息"""
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def get_request_id(request: Request) -> str:
    """获取请求ID"""
    return getattr(request.state, 'request_id', 'unknown')