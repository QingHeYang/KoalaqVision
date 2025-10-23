from fastapi import APIRouter, UploadFile, File, Form
from PIL import Image
import io

from app.services.object_service import object_service
from app.services.vector_service import vector_service
from app.utils.response import success, error, Timer
from app.utils.exceptions import ValidationError, InternalError
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/object/train", tags=["object-train"])

@router.post("/file")
async def train_file(
    file: UploadFile = File(...),
    object_id: str = Form(...),
    save_files: bool = Form(True)
):
    """单文件训练入库"""
    timer = Timer()

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        result = object_service.add_image(
            image_source=image,
            object_id=object_id,
            save_files=save_files,
            custom_data={}
        )

        data = {
            "image_id": result.image_id,
            "object_id": result.object_id,
            "img_url": result.img_url,
            "img_object_url": result.img_object_url
        }

        return success(data, "Image added successfully", timer.elapsed())

    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Failed to process image: {str(e)}")

@router.post("/url")
async def train_url(
    url: str = Form(...),
    object_id: str = Form(...),
    save_files: bool = Form(True)
):
    """单URL训练入库"""
    timer = Timer()

    try:
        result = object_service.add_image(
            image_source=url,
            object_id=object_id,
            save_files=save_files,
            custom_data={}
        )

        data = {
            "image_id": result.image_id,
            "object_id": result.object_id,
            "img_url": result.img_url,
            "img_object_url": result.img_object_url
        }

        return success(data, "Image added successfully", timer.elapsed())

    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise InternalError(f"Failed to process URL: {str(e)}")

@router.delete("/clear")
async def clear_all_vectors():
    """
    Clear all vectors from the database

    WARNING: This will delete ALL stored image features!
    Use with caution - this operation cannot be undone.
    """
    timer = Timer()

    try:
        # Get collection stats before clearing
        collection_name = vector_service.collection_name
        stats_before = {
            "collection": collection_name,
            "count_before": vector_service.get_object_count()
        }

        logger.warning(f"🚨 Clearing all vectors from collection: {collection_name}")

        # Clear the collection
        vector_service.weaviate_wrapper.clear_collection()

        # Get count after clearing (should be 0)
        stats_after = {
            "count_after": vector_service.get_object_count()
        }

        data = {
            **stats_before,
            **stats_after,
            "cleared": stats_before["count_before"]
        }

        logger.success(f"✅ Cleared {data['cleared']} vectors from {collection_name}")

        return success(
            data,
            f"Successfully cleared {data['cleared']} vectors",
            timer.elapsed()
        )

    except Exception as e:
        logger.error(f"❌ Failed to clear vectors: {e}")
        raise InternalError(f"Failed to clear vectors: {str(e)}")

