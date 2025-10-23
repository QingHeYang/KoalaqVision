import json
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from pathlib import Path

from app.database.weaviate_client import weaviate_client
from app.models.object_data import ObjectData, ImageSearchResponse
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class VectorService:
    """向量数据库服务 - 支持 ObjectData 和 FaceData"""

    def __init__(self):
        self.weaviate_wrapper = weaviate_client  # 保存wrapper引用
        self.client = None  # 实际的Weaviate客户端
        self.collection_name = None  # 动态设置，从 weaviate_client 获取

    def _delete_physical_files(self, img_url: str, img_object_url: str):
        """删除物理文件

        Args:
            img_url: 原图URL路径（如 /images/upload/xxx.jpg）
            img_object_url: Object/Face图URL路径（如 /images/upload/xxx_object.png）
        """
        def _url_to_path(url: str) -> Optional[Path]:
            """将URL转换为文件系统路径"""
            if not url:
                return None
            # /images/upload/... → data/upload/...
            # /images/temp/... → data/temp/...
            if url.startswith("/images/"):
                return Path(url.replace("/images/", "data/", 1))
            return None

        # 删除原图
        if img_url:
            img_path = _url_to_path(img_url)
            if img_path and img_path.exists():
                try:
                    img_path.unlink()
                    logger.debug(f"Deleted file: {img_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {img_path}: {e}")

        # 删除object/face图
        if img_object_url:
            obj_path = _url_to_path(img_object_url)
            if obj_path and obj_path.exists():
                try:
                    obj_path.unlink()
                    logger.debug(f"Deleted file: {obj_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {obj_path}: {e}")
    
    def initialize(self):
        """初始化服务"""
        try:
            # 获取实际的Weaviate客户端，而不是wrapper
            self.client = self.weaviate_wrapper.get_client()
            # 动态获取 collection_name
            self.collection_name = self.weaviate_wrapper.collection_name
            logger.info(f"VectorService initialized (collection: {self.collection_name})")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}")
            raise
    
    def add_image(self, image_data: Union[ObjectData, 'FaceData']) -> str:
        """
        添加图片到向量数据库（支持 ObjectData 和 FaceData）

        Args:
            image_data: 图片数据（ObjectData 或 FaceData）

        Returns:
            图片ID
        """
        try:
            if not self.client:
                self.initialize()

            # 检查向量有效性
            if not image_data.feature_vector or not isinstance(image_data.feature_vector, list):
                raise ValueError("Invalid feature vector: must be a non-empty list")

            # 检查向量中是否有 NaN 或 None
            import math
            for i, val in enumerate(image_data.feature_vector):
                if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                    raise ValueError(f"Invalid value in feature vector at index {i}: {val}")

            # 检查向量维度兼容性
            current_vector_dim = len(image_data.feature_vector)
            db_vector_dim = self.weaviate_wrapper.get_vector_dimension()

            if db_vector_dim is not None and db_vector_dim != current_vector_dim:
                error_msg = (
                    f"Vector dimension mismatch! "
                    f"Database expects {db_vector_dim}D vectors, "
                    f"but current model outputs {current_vector_dim}D vectors. "
                    f"\n\nPlease run: python scripts/reset_database.py to clear the database and recreate collection."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 准备数据
            # Weaviate需要RFC3339格式的日期 (带时区)
            from datetime import timezone
            created_at_rfc3339 = image_data.created_at.replace(tzinfo=timezone.utc).isoformat()

            # 基础字段（ObjectData 和 FaceData 共有）
            data_object = {
                "image_id": image_data.image_id,
                "object_id": getattr(image_data, 'object_id', None) or getattr(image_data, 'person_id', None),
                "img_url": image_data.img_url or "",
                "img_object_url": getattr(image_data, 'img_object_url', None) or getattr(image_data, 'img_face_url', None) or "",
                "custom_data": json.dumps(image_data.custom_data) if image_data.custom_data else "{}",
                "created_at": created_at_rfc3339
            }

            # FaceData 特有字段
            if self.collection_name == "FaceData" and hasattr(image_data, 'face_bbox'):
                data_object["face_bbox"] = json.dumps(image_data.face_bbox) if image_data.face_bbox else "[]"
                data_object["face_score"] = image_data.face_score or 0.0
                data_object["face_landmarks"] = json.dumps(image_data.face_landmarks) if hasattr(image_data, 'face_landmarks') and image_data.face_landmarks else "[]"
            
            # 添加到Weaviate (兼容v4和legacy API)
            if hasattr(self.client, 'collections'):
                # v4 API
                try:
                    collection = self.client.collections.get(self.collection_name)
                    result = collection.data.insert(
                        properties=data_object,
                        vector=image_data.feature_vector
                    )
                except Exception as e:
                    logger.error(f"V4 API error: {e}")
                    raise  # 不使用fallback，直接抛出错误以便调试
            else:
                # Legacy API - direct batch call without context manager
                self.client.batch.add_data_object(
                    data_object=data_object,
                    class_name=self.collection_name,
                    vector=image_data.feature_vector
                )
                # Execute batch
                self.client.batch.flush()
                result = image_data.image_id
            
            logger.info(f"Image added to vector database: {image_data.image_id}")
            return image_data.image_id
            
        except Exception as e:
            logger.error(f"Error adding image to vector database: {e}")
            raise
    
    def search_similar(self, feature_vector: List[float], 
                      top_k: int = 10,
                      threshold: float = 0.7,
                      filter_object_id: Optional[str] = None) -> List[ImageSearchResponse]:
        """
        搜索相似图片
        
        Args:
            feature_vector: 查询向量
            top_k: 返回结果数量
            threshold: 相似度阈值
            filter_object_id: 按object_id过滤
            
        Returns:
            相似图片列表
        """
        try:
            if not self.client:
                self.initialize()
            
            # 检查客户端类型并使用相应的API
            if hasattr(self.client, 'query'):
                # Legacy API (weaviate.Client)
                # 查询更多结果，因为会根据threshold过滤
                query_limit = min(top_k * 3, 100)  # 查询3倍的结果，最多100个
                query = self.client.query.get(
                    self.collection_name,
                    ["image_id", "object_id", "img_url", "img_object_url", "custom_data"]
                ).with_near_vector({
                    "vector": feature_vector,
                    "certainty": 0.0  # 设为0.0以获取所有结果，后面手动过滤
                }).with_limit(query_limit).with_additional("certainty")
                
                # 添加过滤条件
                if filter_object_id:
                    query = query.with_where({
                        "path": ["object_id"],
                        "operator": "Equal",
                        "valueText": filter_object_id
                    })
                
                # 执行查询
                result = query.do()
                
                # 处理结果
                responses = []
                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])

                    for item in items:
                        # 获取相似度
                        certainty = item.get("_additional", {}).get("certainty", 0)

                        # 根据threshold过滤
                        if certainty < threshold:
                            continue

                        # 解析custom_data
                        custom_data = {}
                        if item.get("custom_data"):
                            try:
                                custom_data = json.loads(item["custom_data"])
                            except:
                                pass

                        responses.append(ImageSearchResponse(
                            image_id=item.get("image_id", ""),
                            object_id=item.get("object_id", ""),
                            similarity=certainty,
                            img_url=item.get("img_url") or None,
                            img_object_url=item.get("img_object_url") or None,
                            custom_data=custom_data
                        ))
            
            elif hasattr(self.client, 'collections'):
                # V4 API (WeaviateClient)
                collection = self.client.collections.get(self.collection_name)

                # 查询更多结果，因为会根据threshold过滤
                query_limit = min(top_k * 3, 100)  # 查询3倍的结果，最多100个

                # 执行查询 - 根据是否有过滤条件分别调用
                if filter_object_id:
                    from weaviate.classes.query import Filter
                    result = collection.query.near_vector(
                        near_vector=feature_vector,
                        limit=query_limit,
                        filters=Filter.by_property("object_id").equal(filter_object_id),
                        return_metadata=["distance"]
                    )
                else:
                    result = collection.query.near_vector(
                        near_vector=feature_vector,
                        limit=query_limit,
                        return_metadata=["distance"]
                    )
                
                # 处理结果
                responses = []
                for item in result.objects:
                    # v4 API中distance转换为similarity
                    # Weaviate 使用 Cosine Distance [0, 2]，需要转换为 Cosine Similarity [0, 1]
                    # Cosine Similarity = 1 - (Cosine Distance / 2)
                    distance = item.metadata.distance if hasattr(item.metadata, 'distance') else 2.0
                    similarity = 1 - (distance / 2)

                    # 根据threshold过滤
                    if similarity < threshold:
                        continue

                    # 解析custom_data
                    custom_data = {}
                    if item.properties.get("custom_data"):
                        try:
                            custom_data = json.loads(item.properties["custom_data"])
                        except:
                            pass

                    responses.append(ImageSearchResponse(
                        image_id=item.properties.get("image_id", ""),
                        object_id=item.properties.get("object_id", ""),
                        similarity=similarity,
                        img_url=item.properties.get("img_url") or None,
                        img_object_url=item.properties.get("img_object_url") or None,
                        custom_data=custom_data
                    ))
            else:
                raise Exception("Unknown Weaviate client type")
            
            # 限制返回结果数量不超过top_k
            responses = responses[:top_k]

            logger.info(f"Found {len(responses)} similar images (threshold: {threshold})")
            return responses
            
        except Exception as e:
            logger.error(f"Error searching similar images: {e}")
            raise
    
    def get_by_image_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        根据图片ID获取数据
        
        Args:
            image_id: 图片ID
            
        Returns:
            图片数据
        """
        try:
            if not self.client:
                self.initialize()
            
            # 检查客户端类型
            if hasattr(self.client, 'query'):
                # Legacy API
                # 根据 collection 类型查询不同字段
                query_fields = ["image_id", "object_id", "img_url", "img_object_url", "custom_data", "created_at"]
                if self.collection_name == "FaceData":
                    query_fields.extend(["face_bbox", "face_score", "face_landmarks"])

                result = self.client.query.get(
                    self.collection_name,
                    query_fields
                ).with_where({
                    "path": ["image_id"],
                    "operator": "Equal",
                    "valueText": image_id
                }).with_limit(1).do()

                # 处理结果
                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    if items:
                        item = items[0]
                        # 解析custom_data
                        if item.get("custom_data"):
                            try:
                                item["custom_data"] = json.loads(item["custom_data"])
                            except:
                                pass
                        return item
            
            elif hasattr(self.client, 'collections'):
                # V4 API
                from weaviate.classes.query import Filter
                collection = self.client.collections.get(self.collection_name)

                result = collection.query.fetch_objects(
                    filters=Filter.by_property("image_id").equal(image_id),
                    limit=1
                )

                if result.objects:
                    item = result.objects[0]
                    # 转换为字典格式
                    data = {
                        "image_id": item.properties.get("image_id"),
                        "object_id": item.properties.get("object_id"),
                        "img_url": item.properties.get("img_url"),
                        "img_object_url": item.properties.get("img_object_url"),
                        "created_at": item.properties.get("created_at"),
                        "custom_data": item.properties.get("custom_data")
                    }

                    # FaceData 特有字段
                    if self.collection_name == "FaceData":
                        data["face_bbox"] = item.properties.get("face_bbox", "[]")
                        data["face_score"] = item.properties.get("face_score", 0)
                        data["face_landmarks"] = item.properties.get("face_landmarks", "[]")

                    # 解析custom_data
                    if data.get("custom_data"):
                        try:
                            data["custom_data"] = json.loads(data["custom_data"])
                        except:
                            pass
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting image by ID: {e}")
            return None
    
    def delete_by_image_id(self, image_id: str) -> bool:
        """
        删除图片（包括数据库记录和物理文件）

        Args:
            image_id: 图片ID

        Returns:
            是否成功
        """
        try:
            if not self.client:
                self.initialize()

            # 先获取图片信息（用于删除物理文件）
            img_data = self.get_by_image_id(image_id)
            if not img_data:
                logger.warning(f"Image not found: {image_id}")
                return False

            # 删除物理文件
            self._delete_physical_files(
                img_data.get("img_url"),
                img_data.get("img_object_url")
            )

            # 检查客户端类型
            if hasattr(self.client, 'query'):
                # Legacy API
                result = self.client.query.get(
                    self.collection_name, ["image_id"]
                ).with_where({
                    "path": ["image_id"],
                    "operator": "Equal",
                    "valueText": image_id
                }).with_limit(1).with_additional("id").do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    if items:
                        uuid = items[0]["_additional"]["id"]
                        self.client.data_object.delete(uuid, class_name=self.collection_name)
                        logger.info(f"Deleted image (DB + files): {image_id}")
                        return True

            elif hasattr(self.client, 'collections'):
                # V4 API
                from weaviate.classes.query import Filter
                collection = self.client.collections.get(self.collection_name)

                # 先查询
                result = collection.query.fetch_objects(
                    filters=Filter.by_property("image_id").equal(image_id),
                    limit=1
                )

                if result.objects:
                    # 删除对象 - 使用 delete_by_id
                    collection.data.delete_by_id(result.objects[0].uuid)
                    logger.info(f"Deleted image (DB + files): {image_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            return False

    def delete_by_object_id(self, object_id: str) -> int:
        """
        按object_id批量删除图片（包括数据库记录和物理文件）

        Args:
            object_id: 物品ID

        Returns:
            删除数量
        """
        try:
            if not self.client:
                self.initialize()

            # 先获取所有图片信息（用于删除物理文件）
            images = self.get_by_object_id(object_id)
            if not images:
                logger.info(f"No images found for object_id: {object_id}")
                return 0

            # 删除所有物理文件
            for img in images:
                self._delete_physical_files(
                    img.get("img_url"),
                    img.get("img_object_url")
                )

            deleted_count = 0

            if hasattr(self.client, 'query'):
                # Legacy API
                result = self.client.query.get(
                    self.collection_name, ["image_id"]
                ).with_where({
                    "path": ["object_id"],
                    "operator": "Equal",
                    "valueText": object_id
                }).with_additional("id").do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    for item in items:
                        uuid = item["_additional"]["id"]
                        self.client.data_object.delete(uuid, class_name=self.collection_name)
                        deleted_count += 1

            elif hasattr(self.client, 'collections'):
                # V4 API
                from weaviate.classes.query import Filter
                collection = self.client.collections.get(self.collection_name)

                # 查询所有匹配的对象
                result = collection.query.fetch_objects(
                    filters=Filter.by_property("object_id").equal(object_id)
                )

                # 批量删除
                for obj in result.objects:
                    collection.data.delete_by_id(obj.uuid)
                    deleted_count += 1

            logger.info(f"Deleted {deleted_count} images (DB + files) for object_id: {object_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting images by object_id: {e}")
            return 0

    def list_images(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        列表查询（分页）

        Args:
            limit: 每页数量
            offset: 偏移量

        Returns:
            图片列表和分页信息
        """
        try:
            if not self.client:
                self.initialize()

            results = []
            total = 0

            if hasattr(self.client, 'query'):
                # Legacy API - 不支持offset，只能用limit
                result = self.client.query.get(
                    self.collection_name,
                    ["image_id", "object_id", "img_url", "img_object_url", "custom_data", "created_at"]
                ).with_limit(limit + offset).do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    # 手动实现offset
                    items = items[offset:offset + limit]

                    for item in items:
                        # 解析custom_data
                        if item.get("custom_data"):
                            try:
                                item["custom_data"] = json.loads(item["custom_data"])
                            except:
                                pass
                        results.append(item)

                    # 获取总数（近似）
                    total = len(items) + offset

            elif hasattr(self.client, 'collections'):
                # V4 API
                collection = self.client.collections.get(self.collection_name)

                result = collection.query.fetch_objects(
                    limit=limit,
                    offset=offset
                )

                for item in result.objects:
                    data = {
                        "image_id": item.properties.get("image_id"),
                        "object_id": item.properties.get("object_id"),
                        "img_url": item.properties.get("img_url"),
                        "img_object_url": item.properties.get("img_object_url"),
                        "created_at": item.properties.get("created_at"),
                        "custom_data": item.properties.get("custom_data")
                    }
                    # 解析custom_data
                    if data.get("custom_data"):
                        try:
                            data["custom_data"] = json.loads(data["custom_data"])
                        except:
                            pass
                    results.append(data)

                # 获取总数（通过aggregate）
                total = len(results) + offset

            return {
                "items": results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": len(results) == limit
            }

        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "has_more": False}

    def get_by_object_id(self, object_id: str) -> List[Dict[str, Any]]:
        """
        根据object_id查询所有图片

        Args:
            object_id: 物品ID

        Returns:
            图片列表
        """
        try:
            if not self.client:
                self.initialize()

            results = []

            if hasattr(self.client, 'query'):
                # Legacy API
                result = self.client.query.get(
                    self.collection_name,
                    ["image_id", "object_id", "img_url", "img_object_url", "custom_data", "created_at"]
                ).with_where({
                    "path": ["object_id"],
                    "operator": "Equal",
                    "valueText": object_id
                }).do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    for item in items:
                        # 解析custom_data
                        if item.get("custom_data"):
                            try:
                                item["custom_data"] = json.loads(item["custom_data"])
                            except:
                                pass
                        results.append(item)

            elif hasattr(self.client, 'collections'):
                # V4 API
                from weaviate.classes.query import Filter
                collection = self.client.collections.get(self.collection_name)

                result = collection.query.fetch_objects(
                    filters=Filter.by_property("object_id").equal(object_id)
                )

                for item in result.objects:
                    data = {
                        "image_id": item.properties.get("image_id"),
                        "object_id": item.properties.get("object_id"),
                        "img_url": item.properties.get("img_url"),
                        "img_object_url": item.properties.get("img_object_url"),
                        "created_at": item.properties.get("created_at"),
                        "custom_data": item.properties.get("custom_data")
                    }
                    # 解析custom_data
                    if data.get("custom_data"):
                        try:
                            data["custom_data"] = json.loads(data["custom_data"])
                        except:
                            pass
                    results.append(data)

            logger.info(f"Found {len(results)} images for object_id: {object_id}")
            return results

        except Exception as e:
            logger.error(f"Error getting images by object_id: {e}")
            return []

    def list_objects(self) -> List[Dict[str, Any]]:
        """
        列出所有物品，包含图片数量统计

        Returns:
            物品列表，每个包含object_id和image_count
        """
        try:
            if not self.client:
                self.initialize()

            objects_dict = {}

            if hasattr(self.client, 'query'):
                # Legacy API
                result = self.client.query.get(
                    self.collection_name,
                    ["object_id"]
                ).with_limit(10000).do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    for item in items:
                        obj_id = item.get("object_id")
                        if obj_id:
                            objects_dict[obj_id] = objects_dict.get(obj_id, 0) + 1

            elif hasattr(self.client, 'collections'):
                # V4 API
                collection = self.client.collections.get(self.collection_name)
                result = collection.query.fetch_objects(limit=10000)

                for obj in result.objects:
                    obj_id = obj.properties.get("object_id")
                    if obj_id:
                        objects_dict[obj_id] = objects_dict.get(obj_id, 0) + 1

            # 转换为列表格式
            objects = [
                {"object_id": obj_id, "image_count": count}
                for obj_id, count in objects_dict.items()
            ]

            # 按image_count降序排序
            objects.sort(key=lambda x: x["image_count"], reverse=True)

            logger.info(f"Found {len(objects)} objects")
            return objects

        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def get_object_count(self) -> int:
        """获取object数量（图片总数）"""
        stats = self.get_stats()
        return stats.get("total_images", 0)

    def get_face_count(self) -> int:
        """获取face数量（图片总数）"""
        stats = self.get_stats()
        return stats.get("total_images", 0)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        try:
            if not self.client:
                self.initialize()

            stats = {
                "total_images": 0,
                "total_objects": 0,
                "vector_dimension": self.weaviate_wrapper.get_vector_dimension()
            }

            if hasattr(self.client, 'query'):
                # Legacy API
                # 获取总图片数
                result = self.client.query.aggregate(self.collection_name).with_meta_count().do()

                if result and "data" in result and "Aggregate" in result["data"]:
                    agg_data = result["data"]["Aggregate"].get(self.collection_name, [])
                    if agg_data:
                        stats["total_images"] = agg_data[0].get("meta", {}).get("count", 0)

                # 获取唯一object_id数量（需要遍历）
                all_objects = self.client.query.get(
                    self.collection_name, ["object_id"]
                ).with_limit(10000).do()

                if all_objects and "data" in all_objects and "Get" in all_objects["data"]:
                    items = all_objects["data"]["Get"].get(self.collection_name, [])
                    unique_objects = set(item["object_id"] for item in items)
                    stats["total_objects"] = len(unique_objects)

            elif hasattr(self.client, 'collections'):
                # V4 API
                collection = self.client.collections.get(self.collection_name)

                # 获取总数（通过fetch_objects）
                result = collection.query.fetch_objects(limit=10000)
                stats["total_images"] = len(result.objects)

                # 获取唯一object_id
                unique_objects = set(obj.properties.get("object_id") for obj in result.objects)
                stats["total_objects"] = len(unique_objects)

            logger.info(f"Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_images": 0, "total_objects": 0, "vector_dimension": None}

# 单例实例
vector_service = VectorService()