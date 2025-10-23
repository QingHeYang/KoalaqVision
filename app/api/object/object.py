from fastapi import APIRouter

from app.services.vector_service import vector_service
from app.utils.response import success, Timer
from app.utils.exceptions import NotFoundError, InternalError

router = APIRouter(prefix="/api/object/object", tags=["object-object"])

@router.get("/list")
async def list_objects():
    """列出所有物品，包含图片数量统计"""
    timer = Timer()

    try:
        objects = vector_service.list_objects()

        data = {
            "total": len(objects),
            "objects": objects
        }

        return success(data, f"Found {len(objects)} objects", timer.elapsed())

    except Exception as e:
        raise InternalError(f"Failed to list objects: {str(e)}")

@router.get("/{object_id}")
async def get_object(object_id: str):
    """查询某个物品的所有图片"""
    timer = Timer()

    try:
        images = vector_service.get_by_object_id(object_id)

        if not images:
            raise NotFoundError("Object", object_id)

        data = {
            "object_id": object_id,
            "image_count": len(images),
            "images": images
        }

        return success(data, f"Object {object_id} has {len(images)} images", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to get object: {str(e)}")

@router.delete("/{object_id}")
async def delete_object(object_id: str):
    """删除某个物品的所有图片"""
    timer = Timer()

    try:
        count = vector_service.delete_by_object_id(object_id)

        if count == 0:
            raise NotFoundError("Object", object_id)

        data = {
            "object_id": object_id,
            "deleted_count": count
        }

        return success(data, f"Deleted {count} images for object {object_id}", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to delete object: {str(e)}")
