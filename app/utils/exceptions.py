"""
自定义异常类

简单直接的异常处理
"""

from fastapi import HTTPException
from app.utils.response import error, ErrorCode


class APIException(HTTPException):
    """API异常基类"""

    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=error(code, message, details))


# 常用异常 - 直接定义，不要继承太多层
class NotFoundError(APIException):
    """资源不存在"""
    def __init__(self, resource: str, id: str = None):
        message = f"{resource} not found"
        if id:
            message = f"{resource} {id} not found"
        super().__init__(ErrorCode.NOT_FOUND, message, 404)


class ValidationError(APIException):
    """验证错误"""
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else None
        super().__init__(ErrorCode.VALIDATION_ERROR, message, 400, details)


class NoFaceDetectedError(APIException):
    """未检测到人脸"""
    def __init__(self):
        super().__init__(ErrorCode.NO_FACE_DETECTED, "No face detected in image", 400)


class LivenessCheckFailedError(APIException):
    """活体检测失败"""
    def __init__(self, score: float = None, reason: str = None):
        message = "Liveness check failed"
        details = {}
        if score is not None:
            details["score"] = score
        if reason:
            message = f"Liveness check failed: {reason}"
            details["reason"] = reason
        super().__init__(ErrorCode.LIVENESS_FAILED, message, 400, details)


class DimensionMismatchError(APIException):
    """向量维度不匹配"""
    def __init__(self, expected: int, actual: int):
        message = f"Vector dimension mismatch: expected {expected}D, got {actual}D"
        details = {"expected": expected, "actual": actual}
        super().__init__(ErrorCode.DIMENSION_MISMATCH, message, 400, details)


class InternalError(APIException):
    """内部错误"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(ErrorCode.INTERNAL_ERROR, message, 500)