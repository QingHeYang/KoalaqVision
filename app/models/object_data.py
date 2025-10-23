from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class ObjectData(BaseModel):
    """物品数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "object_id": "product_123",
                "img_url": "https://example.com/image.jpg",
                "img_object_url": "https://example.com/image_processed.png",
                "feature_vector": [0.1, 0.2, 0.3],
                "custom_data": {"brand": "Nike", "category": "shoes"}
            }
        }
    )

    # 基础字段
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="图片唯一ID")
    object_id: str = Field(..., description="所属物品ID，外部传入")

    # 图片链接
    img_url: Optional[str] = Field(None, description="原始图片URL")
    img_object_url: Optional[str] = Field(None, description="抠图后的图片URL")

    # 特征向量
    feature_vector: List[float] = Field(..., description="特征向量，1280维")

    # 自定义数据
    custom_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义JSON数据")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class ImageUploadRequest(BaseModel):
    """图片上传请求模型"""
    object_id: str = Field(..., description="物品ID")
    save_original: bool = Field(True, description="是否保存原图")
    save_processed: bool = Field(True, description="是否保存抠图后的图片")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="自定义数据")

class ImageSearchRequest(BaseModel):
    """图片搜索请求模型"""
    top_k: int = Field(10, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(0.7, ge=0, le=1, description="相似度阈值")
    filter_object_id: Optional[str] = Field(None, description="按object_id过滤")

class ImageSearchResponse(BaseModel):
    """图片搜索响应模型"""
    image_id: str
    object_id: str
    similarity: float
    img_url: Optional[str]
    img_object_url: Optional[str]
    custom_data: Optional[Dict[str, Any]]

    @field_serializer('similarity')
    def serialize_similarity(self, value: float) -> float:
        """格式化相似度为2位小数"""
        return round(value, 2)