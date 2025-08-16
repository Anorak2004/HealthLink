"""
HealthLink Gateway API 异常处理
统一错误响应格式
"""
import traceback
from typing import Union

import structlog
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from packages.schemas.responses import ErrorResponse, ErrorDetail

logger = structlog.get_logger()

class HealthLinkException(Exception):
    """HealthLink自定义异常基类"""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(HealthLinkException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field} if field else {}
        )

class NotFoundException(HealthLinkException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )

class ConflictException(HealthLinkException):
    """资源冲突异常"""
    
    def __init__(self, message: str, resource: str = None):
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource} if resource else {}
        )

class ExternalServiceException(HealthLinkException):
    """外部服务异常"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service}
        )

class BusinessLogicException(HealthLinkException):
    """业务逻辑异常"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="BUSINESS_LOGIC_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

def setup_exception_handlers(app: FastAPI) -> None:
    """设置异常处理器"""
    
    @app.exception_handler(HealthLinkException)
    async def healthlink_exception_handler(request: Request, exc: HealthLinkException):
        """处理自定义异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            "HealthLink exception occurred",
            request_id=request_id,
            error_code=exc.code,
            error_message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
        
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                field=exc.details.get('field')
            )
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.warning(
            "HTTP exception occurred",
            request_id=request_id,
            status_code=exc.status_code,
            detail=exc.detail
        )
        
        # 映射HTTP状态码到错误代码
        error_code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE"
        }
        
        error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
        
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code=error_code,
                message=str(exc.detail)
            )
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 提取第一个验证错误
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_error.get('loc', []))
        message = first_error.get('msg', 'Validation error')
        
        logger.warning(
            "Request validation failed",
            request_id=request_id,
            field=field,
            message=message,
            errors=exc.errors()
        )
        
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=f"Validation failed for field '{field}': {message}",
                field=field
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """处理Pydantic验证异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 提取第一个验证错误
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_error.get('loc', []))
        message = first_error.get('msg', 'Validation error')
        
        logger.warning(
            "Pydantic validation failed",
            request_id=request_id,
            field=field,
            message=message,
            errors=exc.errors()
        )
        
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=f"Data validation failed for field '{field}': {message}",
                field=field
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """处理数据库异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            "Database error occurred",
            request_id=request_id,
            error=str(exc),
            error_type=type(exc).__name__
        )
        
        # 不暴露具体的数据库错误信息
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code="DATABASE_ERROR",
                message="A database error occurred. Please try again later."
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        logger.error(
            "Unexpected error occurred",
            request_id=request_id,
            error=str(exc),
            error_type=type(exc).__name__,
            traceback=traceback.format_exc()
        )
        
        error_response = ErrorResponse(
            request_id=request_id,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again later."
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )