from fastapi import APIRouter

from app.services.vector_service import vector_service
from app.utils.response import success, Timer
from app.utils.exceptions import NotFoundError, InternalError
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/face/person", tags=["face-person"])

@router.get("/list")
async def list_persons():
    """列出所有人员，包含人脸图片数量统计

    Returns:
        所有人员列表，每个人员包含:
        - person_id: 人员ID
        - image_count: 该人员的人脸图片数量
    """
    timer = Timer()

    try:
        # 复用 vector_service.list_objects()
        # 数据库中 object_id 对应 person_id
        persons = vector_service.list_objects()

        # 将 object_id 重命名为 person_id，语义更清晰
        for person in persons:
            person["person_id"] = person.pop("object_id")

        data = {
            "total": len(persons),
            "persons": persons
        }

        return success(data, f"Found {len(persons)} persons", timer.elapsed())

    except Exception as e:
        raise InternalError(f"Failed to list persons: {str(e)}")

@router.get("/{person_id}")
async def get_person(person_id: str):
    """查询某个人员的所有人脸图片

    Args:
        person_id: 人员ID

    Returns:
        该人员的所有人脸图片信息
    """
    timer = Timer()

    try:
        # 复用 vector_service.get_by_object_id()
        images = vector_service.get_by_object_id(person_id)

        if not images:
            raise NotFoundError("Person", person_id)

        # 将 object_id 重命名为 person_id
        for image in images:
            image["person_id"] = image.pop("object_id", person_id)
            # 如果有 img_object_url，重命名为 img_face_url
            if "img_object_url" in image:
                image["img_face_url"] = image.pop("img_object_url")

        data = {
            "person_id": person_id,
            "face_count": len(images),
            "faces": images
        }

        return success(data, f"Person {person_id} has {len(images)} faces", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to get person: {str(e)}")

@router.delete("/{person_id}")
async def delete_person(person_id: str):
    """删除某个人员的所有人脸图片（包括物理文件）

    Args:
        person_id: 人员ID

    Returns:
        删除结果，包含删除的图片数量
    """
    timer = Timer()

    try:
        # vector_service.delete_by_object_id 现在会同时删除数据库记录和物理文件
        count = vector_service.delete_by_object_id(person_id)

        if count == 0:
            raise NotFoundError("Person", person_id)

        data = {
            "person_id": person_id,
            "deleted_count": count
        }

        return success(data, f"Deleted {count} faces for person {person_id}", timer.elapsed())

    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(f"Failed to delete person: {str(e)}")

@router.get("/stats/summary")
async def get_stats():
    """获取人脸库统计信息

    Returns:
        统计信息，包含:
        - total_faces: 总人脸数
        - total_persons: 总人数
        - vector_dimension: 向量维度
    """
    timer = Timer()

    try:
        stats = vector_service.get_stats()

        # 重命名字段，更符合人脸识别语义
        data = {
            "total_faces": stats.get("total_images", 0),
            "total_persons": stats.get("total_objects", 0),
            "vector_dimension": stats.get("vector_dimension")
        }

        return success(data, "Statistics retrieved successfully", timer.elapsed())

    except Exception as e:
        raise InternalError(f"Failed to get statistics: {str(e)}")
