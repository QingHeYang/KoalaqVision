from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from PIL import Image
import io

from app.services.object_service import object_service
from app.utils.response import success
from app.utils.exceptions import ValidationError, InternalError

router = APIRouter(prefix="/api/object/match", tags=["object-match"])

@router.post("/file")
async def match_file(
    file: UploadFile = File(...),
    save_temp: bool = Form(False),
    object_ids: Optional[str] = Form(None),
    confidence: float = Form(0.7),
    top_k: int = Form(10)
):
    """文件匹配"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        object_id_list = None
        if object_ids:
            object_id_list = [id.strip() for id in object_ids.split(",")]

        result = object_service.match_image(
            image_source=image,
            save_temp=save_temp,
            object_ids=object_id_list,
            confidence=confidence,
            top_k=top_k
        )

        # Extract processing time from result
        processing_time = None
        if "processing_time" in result and "total" in result["processing_time"]:
            processing_time = result["processing_time"]["total"]

        message = f"Found {result.get('total_matches', 0)} matches"
        return success(result, message, processing_time)

    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Failed to match image: {str(e)}")

@router.post("/url")
async def match_url(
    url: str = Form(...),
    save_temp: bool = Form(False),
    object_ids: Optional[str] = Form(None),
    confidence: float = Form(0.7),
    top_k: int = Form(10)
):
    """URL匹配"""
    try:
        object_id_list = None
        if object_ids:
            object_id_list = [id.strip() for id in object_ids.split(",")]

        result = object_service.match_image(
            image_source=url,
            save_temp=save_temp,
            object_ids=object_id_list,
            confidence=confidence,
            top_k=top_k
        )

        # Extract processing time from result
        processing_time = None
        if "processing_time" in result and "total" in result["processing_time"]:
            processing_time = result["processing_time"]["total"]

        message = f"Found {result.get('total_matches', 0)} matches"
        return success(result, message, processing_time)

    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Failed to match URL: {str(e)}")
