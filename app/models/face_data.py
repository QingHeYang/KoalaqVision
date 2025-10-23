from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class FaceData(BaseModel):
    """人脸数据模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "person_id": "person_001",
                "img_url": "/images/upload/person_001/xxxxx.jpg",
                "img_face_url": "/images/upload/person_001/xxxxx_face.jpg",
                "feature_vector": [0.1, 0.2, 0.3],
                "face_bbox": [57.5, 96.5, 235.5, 318.0],
                "face_score": 0.865,
                "custom_data": {"name": "张三", "department": "研发部"}
            }
        }
    )

    # 基础字段
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="图片唯一ID")
    person_id: str = Field(..., description="所属人员ID，外部传入")

    # 图片链接
    img_url: Optional[str] = Field(None, description="原始图片URL")
    img_face_url: Optional[str] = Field(None, description="人脸区域图片URL")

    # 特征向量
    feature_vector: List[float] = Field(..., description="特征向量，512维")

    # 人脸信息
    face_bbox: Optional[List[float]] = Field(None, description="人脸位置 [x1, y1, x2, y2]")
    face_score: Optional[float] = Field(None, description="人脸检测置信度")
    face_landmarks: Optional[List[List[float]]] = Field(None, description="人脸关键点坐标")

    # 自定义数据
    custom_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义JSON数据")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class FaceUploadRequest(BaseModel):
    """人脸上传请求模型"""
    person_id: str = Field(..., description="人员ID")
    save_original: bool = Field(True, description="是否保存原图")
    save_face: bool = Field(True, description="是否保存人脸图片")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="自定义数据")


class FaceSearchRequest(BaseModel):
    """人脸搜索请求模型"""
    top_k: int = Field(10, ge=1, le=100, description="返回结果数量")
    threshold: float = Field(0.75, ge=0, le=1, description="相似度阈值（人脸识别推荐0.75以上）")
    filter_person_id: Optional[str] = Field(None, description="按person_id过滤")


class FaceSearchResponse(BaseModel):
    """人脸搜索响应模型"""
    image_id: str
    person_id: str
    similarity: float
    img_url: Optional[str]
    img_face_url: Optional[str]
    face_bbox: Optional[List[float]]
    face_score: Optional[float]
    custom_data: Optional[Dict[str, Any]]

    @field_serializer('similarity')
    def serialize_similarity(self, value: float) -> float:
        """格式化相似度为2位小数"""
        return round(value, 2)

    @field_serializer('face_score')
    def serialize_face_score(self, value: Optional[float]) -> Optional[float]:
        """格式化人脸检测置信度为2位小数"""
        return round(value, 2) if value is not None else None

    @field_serializer('face_bbox')
    def serialize_face_bbox(self, value: Optional[List[float]]) -> Optional[List[float]]:
        """格式化人脸位置坐标为2位小数"""
        return [round(v, 2) for v in value] if value is not None else None
