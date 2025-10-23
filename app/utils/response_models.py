"""
统一的 API 响应模型和工具类

提供标准化的成功响应、错误响应和相关工具函数
"""

from typing import Optional, Dict, Any, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import time

T = TypeVar('T')


class ErrorCode(str, Enum):
    """标准化错误代码"""
    # 验证错误
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # 资源错误
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # 业务错误
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
    LIVENESS_CHECK_FAILED = "LIVENESS_CHECK_FAILED"
    NO_OBJECT_DETECTED = "NO_OBJECT_DETECTED"

    # 数据库错误
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    DATABASE_ERROR = "DATABASE_ERROR"

    # 服务错误
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # 文件错误
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"

    # 网络错误
    URL_UNREACHABLE = "URL_UNREACHABLE"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"


class ResponseMetadata(BaseModel):
    """响应元数据"""
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    processing_time: Optional[float] = Field(None, description="处理耗时（秒）")
    request_id: Optional[str] = Field(None, description="请求ID")
    version: str = Field(default="v2", description="API版本")


class ErrorDetail(BaseModel):
    """错误详细信息"""
    code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="人类可读的错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="额外的错误详情")
    field: Optional[str] = Field(None, description="出错字段（用于验证错误）")


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应模型"""
    success: bool = Field(default=True, description="操作是否成功")
    data: T = Field(..., description="业务数据")
    message: Optional[str] = Field(None, description="成功消息")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(default=False, description="操作是否成功")
    error: ErrorDetail = Field(..., description="错误信息")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")


class PaginationMetadata(BaseModel):
    """分页元数据"""
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多数据")
    page: Optional[int] = Field(None, description="当前页码")
    total_pages: Optional[int] = Field(None, description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = Field(default=True, description="操作是否成功")
    data: list[T] = Field(..., description="数据列表")
    pagination: PaginationMetadata = Field(..., description="分页信息")
    message: Optional[str] = Field(None, description="成功消息")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="响应元数据")


class ProcessingTime(BaseModel):
    """处理时间统计"""
    load: Optional[float] = Field(None, description="加载耗时")
    preprocess: Optional[float] = Field(None, description="预处理耗时")
    inference: Optional[float] = Field(None, description="推理耗时")
    postprocess: Optional[float] = Field(None, description="后处理耗时")
    database: Optional[float] = Field(None, description="数据库操作耗时")
    total: float = Field(..., description="总耗时")

    # Object模式特有
    background_removal: Optional[float] = Field(None, description="背景去除耗时")
    feature_extraction: Optional[float] = Field(None, description="特征提取耗时")
    vector_search: Optional[float] = Field(None, description="向量搜索耗时")
    result_processing: Optional[float] = Field(None, description="结果处理耗时")

    # Face模式特有
    face_detection: Optional[float] = Field(None, description="人脸检测耗时")
    liveness_detection: Optional[float] = Field(None, description="活体检测耗时")


# 工具函数
def create_success_response(
    data: Any,
    message: Optional[str] = None,
    processing_time: Optional[float] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    创建成功响应

    Args:
        data: 业务数据
        message: 成功消息
        processing_time: 处理耗时
        request_id: 请求ID

    Returns:
        标准化的成功响应字典
    """
    metadata = ResponseMetadata(
        processing_time=processing_time,
        request_id=request_id
    )

    response = SuccessResponse(
        data=data,
        message=message,
        metadata=metadata
    )

    return response.model_dump(exclude_none=True)


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    创建错误响应

    Args:
        code: 错误代码
        message: 错误信息
        details: 错误详情
        field: 出错字段
        request_id: 请求ID

    Returns:
        标准化的错误响应字典
    """
    error = ErrorDetail(
        code=code,
        message=message,
        details=details,
        field=field
    )

    metadata = ResponseMetadata(
        request_id=request_id
    )

    response = ErrorResponse(
        error=error,
        metadata=metadata
    )

    return response.model_dump(exclude_none=True)


def create_paginated_response(
    data: list,
    total: int,
    limit: int,
    offset: int,
    message: Optional[str] = None,
    processing_time: Optional[float] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    创建分页响应

    Args:
        data: 数据列表
        total: 总数量
        limit: 每页数量
        offset: 偏移量
        message: 成功消息
        processing_time: 处理耗时
        request_id: 请求ID

    Returns:
        标准化的分页响应字典
    """
    has_more = (offset + len(data)) < total
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    pagination = PaginationMetadata(
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
        page=page,
        total_pages=total_pages
    )

    metadata = ResponseMetadata(
        processing_time=processing_time,
        request_id=request_id
    )

    response = PaginatedResponse(
        data=data,
        pagination=pagination,
        message=message,
        metadata=metadata
    )

    return response.model_dump(exclude_none=True)


class APITimer:
    """API计时器上下文管理器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

    @property
    def elapsed(self) -> float:
        """获取耗时（秒）"""
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 3)
        elif self.start_time:
            return round(time.time() - self.start_time, 3)
        return 0.0