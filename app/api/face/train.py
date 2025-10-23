from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from PIL import Image
import io
import json

from app.services.face_service import face_service
from app.services.vector_service import vector_service
from app.utils.response import success, Timer
from app.utils.exceptions import ValidationError, InternalError
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/face/train", tags=["face-train"])

@router.post("/file")
async def register_face_file(
    file: UploadFile = File(...),
    person_id: str = Form(...),
    save_files: bool = Form(True),
    custom_data: Optional[str] = Form(None),
    enable_liveness: bool = Form(False)
):
    """单文件人脸注册"""
    timer = Timer()

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 解析 custom_data
        custom_dict = {}
        if custom_data:
            try:
                custom_dict = json.loads(custom_data)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format in custom_data")

        result = face_service.add_face(
            image_source=image,
            person_id=person_id,
            save_files=save_files,
            custom_data=custom_dict,
            enable_liveness=enable_liveness
        )

        data = {
            "image_id": result.image_id,
            "person_id": result.person_id,
            "img_url": result.img_url,
            "img_face_url": result.img_face_url,
            "face_bbox": [round(v, 2) for v in result.face_bbox] if result.face_bbox else None,
            "face_score": round(result.face_score, 2) if result.face_score is not None else None,
            "custom_data": result.custom_data
        }

        return success(data, "Face registered successfully", timer.elapsed())

    except ValueError as e:
        # 人脸检测失败等业务错误
        raise ValidationError(str(e))
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to register face: {str(e)}")

@router.post("/url")
async def register_face_url(
    url: str = Form(...),
    person_id: str = Form(...),
    save_files: bool = Form(True),
    custom_data: Optional[str] = Form(None),
    enable_liveness: bool = Form(False)
):
    """单URL人脸注册"""
    timer = Timer()

    try:
        # 解析 custom_data
        custom_dict = {}
        if custom_data:
            try:
                custom_dict = json.loads(custom_data)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format in custom_data")

        result = face_service.add_face(
            image_source=url,
            person_id=person_id,
            save_files=save_files,
            custom_data=custom_dict,
            enable_liveness=enable_liveness
        )

        data = {
            "image_id": result.image_id,
            "person_id": result.person_id,
            "img_url": result.img_url,
            "img_face_url": result.img_face_url,
            "face_bbox": [round(v, 2) for v in result.face_bbox] if result.face_bbox else None,
            "face_score": round(result.face_score, 2) if result.face_score is not None else None,
            "custom_data": result.custom_data
        }

        return success(data, "Face registered successfully", timer.elapsed())

    except ValueError as e:
        # 人脸检测失败等业务错误
        raise ValidationError(str(e))
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to register face: {str(e)}")

@router.delete("/clear")
async def clear_all_faces():
    """
    Clear all faces from the database

    WARNING: This will delete ALL stored face features!
    Use with caution - this operation cannot be undone.
    """
    timer = Timer()

    try:
        # Get collection stats before clearing
        collection_name = vector_service.collection_name
        stats_before = {
            "collection": collection_name,
            "count_before": vector_service.get_face_count()
        }

        logger.warning(f"🚨 Clearing all faces from collection: {collection_name}")

        # Clear the collection
        vector_service.weaviate_wrapper.clear_collection()

        # Get count after clearing (should be 0)
        stats_after = {
            "count_after": vector_service.get_face_count()
        }

        data = {
            **stats_before,
            **stats_after,
            "cleared": stats_before["count_before"]
        }

        logger.success(f"✅ Cleared {data['cleared']} faces from {collection_name}")

        return success(
            data,
            f"Successfully cleared {data['cleared']} faces",
            timer.elapsed()
        )

    except Exception as e:
        logger.error(f"❌ Failed to clear faces: {e}")
        raise InternalError(f"Failed to clear faces: {str(e)}")

