from fastapi import APIRouter, Query

from app.services.vector_service import vector_service
from app.utils.response import success, paginated, Timer
from app.utils.exceptions import NotFoundError, InternalError

router = APIRouter(prefix="/api/face/image", tags=["face-image"])

@router.get("/{image_id}")
async def get_image(image_id: str):
    """根据图片ID查询人脸图片详情

    Args:
        image_id: 图片ID

    Returns:
        人脸图片详细信息
    """
    timer = Timer()

    try:
        result = vector_service.get_by_image_id(image_id)

        if not result:
            raise NotFoundError("Face image", image_id)

        # 字段重命名（语义适配）
        if "object_id" in result:
            result["person_id"] = result.pop("object_id")
        if "img_object_url" in result:
            result["img_face_url"] = result.pop("img_object_url")

        return success(result, f"Face image {image_id} retrieved", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to get face image: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """删除人脸图片

    Args:
        image_id: 图片ID

    Returns:
        删除结果
    """
    timer = Timer()

    try:
        result = vector_service.delete_by_image_id(image_id)

        if not result:
            raise NotFoundError("Face image", image_id)

        data = {
            "image_id": image_id
        }

        return success(data, f"Face image {image_id} deleted successfully", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to delete face image: {str(e)}")

@router.get("/")
async def list_images(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """分页列出人脸图片

    Args:
        limit: 每页数量（默认100）
        offset: 偏移量（默认0）

    Returns:
        分页的人脸图片列表
    """
    timer = Timer()

    try:
        result = vector_service.list_images(limit=limit, offset=offset)

        # 提取 items 和 total
        items = result.get("images", [])
        total = result.get("total", 0)

        # 字段重命名
        for item in items:
            if "object_id" in item:
                item["person_id"] = item.pop("object_id")
            if "img_object_url" in item:
                item["img_face_url"] = item.pop("img_object_url")

        return paginated(items, total, limit, offset)

    except Exception as e:
        raise InternalError(f"Failed to list face images: {str(e)}")
