from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from PIL import Image
import io

from app.services.face_service import face_service
from app.utils.response import success
from app.utils.exceptions import ValidationError, InternalError

router = APIRouter(prefix="/api/face/match", tags=["face-match"])

@router.post("/file")
async def recognize_face_file(
    file: UploadFile = File(...),
    save_temp: bool = Form(False),
    person_ids: Optional[str] = Form(None),
    confidence: float = Form(0.75),
    top_k: int = Form(10),
    enable_liveness: bool = Form(True)
):
    """文件人脸识别（1:N 匹配）

    Args:
        file: 人脸图片文件
        save_temp: 是否保存临时文件
        person_ids: 限定搜索范围的人员ID列表（逗号分隔），为空则搜索全部
        confidence: 置信度阈值（人脸识别推荐 0.75 以上）
        top_k: 返回的最大匹配人数

    Returns:
        按 person_id 分组的匹配结果，每个人包含多张人脸图片
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 解析 person_ids
        person_id_list = None
        if person_ids:
            person_id_list = [id.strip() for id in person_ids.split(",")]

        result = face_service.match_face(
            image_source=image,
            save_temp=save_temp,
            person_ids=person_id_list,
            confidence=confidence,
            top_k=top_k,
            enable_liveness=enable_liveness
        )

        # Extract processing time from result
        processing_time = None
        if "processing_time" in result and "total" in result["processing_time"]:
            processing_time = result["processing_time"]["total"]

        message = f"Found {result.get('total_matches', 0)} matching persons"
        return success(result, message, processing_time)

    except ValueError as e:
        # 人脸检测失败等业务错误
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Face recognition failed: {str(e)}")

@router.post("/url")
async def recognize_face_url(
    url: str = Form(...),
    save_temp: bool = Form(False),
    person_ids: Optional[str] = Form(None),
    confidence: float = Form(0.75),
    top_k: int = Form(10),
    enable_liveness: bool = Form(True)
):
    """URL人脸识别（1:N 匹配）

    Args:
        url: 人脸图片URL
        save_temp: 是否保存临时文件
        person_ids: 限定搜索范围的人员ID列表（逗号分隔），为空则搜索全部
        confidence: 置信度阈值（人脸识别推荐 0.75 以上）
        top_k: 返回的最大匹配人数

    Returns:
        按 person_id 分组的匹配结果，每个人包含多张人脸图片
    """
    try:
        # 解析 person_ids
        person_id_list = None
        if person_ids:
            person_id_list = [id.strip() for id in person_ids.split(",")]

        result = face_service.match_face(
            image_source=url,
            save_temp=save_temp,
            person_ids=person_id_list,
            confidence=confidence,
            top_k=top_k,
            enable_liveness=enable_liveness
        )

        # Extract processing time from result
        processing_time = None
        if "processing_time" in result and "total" in result["processing_time"]:
            processing_time = result["processing_time"]["total"]

        message = f"Found {result.get('total_matches', 0)} matching persons"
        return success(result, message, processing_time)

    except ValueError as e:
        # 人脸检测失败等业务错误
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Face recognition failed: {str(e)}")
