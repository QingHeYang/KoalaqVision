from fastapi import APIRouter, Query

from app.services.vector_service import vector_service
from app.utils.response import success, paginated, Timer
from app.utils.exceptions import NotFoundError, InternalError

router = APIRouter(prefix="/api/object/image", tags=["object-image"])

@router.get("/list")
async def list_images(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """图片列表（分页）"""
    timer = Timer()

    try:
        result = vector_service.list_images(limit=limit, offset=offset)

        # Extract items and total from result
        items = result.get("images", [])
        total = result.get("total", 0)

        return paginated(items, total, limit, offset)

    except Exception as e:
        raise InternalError(f"Failed to list images: {str(e)}")

@router.get("/stats")
async def get_stats():
    """图片统计信息"""
    timer = Timer()

    try:
        stats = vector_service.get_stats()
        return success(stats, "Statistics retrieved successfully", timer.elapsed())

    except Exception as e:
        raise InternalError(f"Failed to get statistics: {str(e)}")

@router.get("/{image_id}")
async def get_image(image_id: str):
    """查询单张图片"""
    timer = Timer()

    try:
        result = vector_service.get_by_image_id(image_id)
        if not result:
            raise NotFoundError("Image", image_id)

        return success(result, f"Image {image_id} retrieved", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to get image: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """删除单张图片"""
    timer = Timer()

    try:
        result = vector_service.delete_by_image_id(image_id)
        if not result:
            raise NotFoundError("Image", image_id)

        return success({"image_id": image_id}, f"Image {image_id} deleted successfully", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to delete image: {str(e)}")
