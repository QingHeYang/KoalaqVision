"""
统一API响应格式

Keep it simple, stupid! - Linus风格
"""

from typing import Any, Optional
from datetime import datetime
import time


# 错误代码 - 只定义真正需要的
class ErrorCode:
    # 通用错误
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # 人脸相关
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    LIVENESS_FAILED = "LIVENESS_FAILED"

    # 物品相关
    NO_OBJECT_DETECTED = "NO_OBJECT_DETECTED"

    # 数据库
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"


def success(data: Any, message: str = None, processing_time: float = None) -> dict:
    """
    成功响应

    简单直接，没有花里胡哨的东西
    """
    response = {
        "success": True,
        "data": data
    }

    if message:
        response["message"] = message

    if processing_time is not None:
        response["processing_time"] = round(processing_time, 3)

    response["timestamp"] = datetime.now().isoformat()

    return response


def error(code: str, message: str, details: dict = None) -> dict:
    """
    错误响应

    清晰的错误信息，方便调试
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        },
        "timestamp": datetime.now().isoformat()
    }

    if details:
        response["error"]["details"] = details

    return response


def paginated(items: list, total: int, limit: int, offset: int) -> dict:
    """
    分页响应

    只返回必要的分页信息
    """
    return {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(items)) < total
        },
        "timestamp": datetime.now().isoformat()
    }


class Timer:
    """简单计时器"""

    def __init__(self):
        self.start = time.time()

    def elapsed(self) -> float:
        """返回耗时（秒）"""
        return round(time.time() - self.start, 3)