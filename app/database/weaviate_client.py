import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from typing import Optional
from app.config.settings import settings
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class WeaviateClient:
    """Weaviate数据库客户端"""

    def __init__(self):
        self.client: Optional[weaviate.Client] = None
        self.collection_name = None  # 将在 connect() 时根据 app_mode 设置
    
    def connect(self):
        """连接到Weaviate"""
        try:
            # 根据 app_mode 设置 collection_name
            from app.services.pipeline_factory import get_pipeline
            pipeline = get_pipeline()
            self.collection_name = pipeline.get_collection_name()
            logger.info(f"Using collection: {self.collection_name} (app_mode={settings.app_mode})")

            # 连接到Weaviate
            # 从URL解析端口
            import re
            url_parts = re.match(r'http://([^:]+):(\d+)', settings.weaviate_url)
            host = url_parts.group(1) if url_parts else "localhost"
            port = int(url_parts.group(2)) if url_parts else 10769

            self.client = weaviate.connect_to_local(
                host=host,
                port=port,
                grpc_port=50050
            )

            logger.info(f"Connected to Weaviate at {settings.weaviate_url}")

            # 初始化collection
            self.setup_collection()
            
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            # 降级到简单客户端
            try:
                self.client = weaviate.Client(url=settings.weaviate_url)
                logger.info("Using legacy Weaviate client")
                self.setup_collection_legacy()
            except Exception as e2:
                logger.error(f"Failed to create legacy client: {e2}")
                raise
    
    def setup_collection(self):
        """设置Weaviate collection (v4版本)"""
        try:
            # 检查collection是否存在
            if self.client.collections.exists(self.collection_name):
                logger.info(f"Collection {self.collection_name} already exists")
                return

            # 根据 collection 类型定义属性
            if self.collection_name == "FaceData":
                # 人脸数据 collection
                properties = [
                    Property(name="image_id", data_type=DataType.TEXT),
                    Property(name="object_id", data_type=DataType.TEXT),  # 对应 person_id
                    Property(name="img_url", data_type=DataType.TEXT),
                    Property(name="img_object_url", data_type=DataType.TEXT),  # 对应 img_face_url
                    Property(name="face_bbox", data_type=DataType.TEXT),  # JSON string
                    Property(name="face_score", data_type=DataType.NUMBER),
                    Property(name="face_landmarks", data_type=DataType.TEXT),  # JSON string
                    Property(name="custom_data", data_type=DataType.TEXT),  # JSON string
                    Property(name="created_at", data_type=DataType.DATE),
                ]
            else:
                # 物品数据 collection (ObjectData)
                properties = [
                    Property(name="image_id", data_type=DataType.TEXT),
                    Property(name="object_id", data_type=DataType.TEXT),
                    Property(name="img_url", data_type=DataType.TEXT),
                    Property(name="img_object_url", data_type=DataType.TEXT),
                    Property(name="custom_data", data_type=DataType.TEXT),  # JSON string
                    Property(name="created_at", data_type=DataType.DATE),
                ]

            # 创建collection
            self.client.collections.create(
                name=self.collection_name,
                properties=properties,
                vectorizer_config=Configure.Vectorizer.none(),  # 我们自己提供向量
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                    ef=200,
                    ef_construction=200,
                    max_connections=32
                )
            )

            logger.info(f"Collection {self.collection_name} created successfully")

        except Exception as e:
            logger.error(f"Error setting up collection: {e}")
    
    def setup_collection_legacy(self):
        """设置Weaviate collection (legacy版本)"""
        try:
            # 检查schema是否存在
            schema = self.client.schema.get()
            exists = any(cls["class"] == self.collection_name for cls in schema.get("classes", []))

            if exists:
                logger.info(f"Collection {self.collection_name} already exists")
                return

            # 根据 collection 类型定义属性
            if self.collection_name == "FaceData":
                # 人脸数据 collection
                properties = [
                    {"name": "image_id", "dataType": ["text"]},
                    {"name": "object_id", "dataType": ["text"]},  # 对应 person_id
                    {"name": "img_url", "dataType": ["text"]},
                    {"name": "img_object_url", "dataType": ["text"]},  # 对应 img_face_url
                    {"name": "face_bbox", "dataType": ["text"]},  # JSON string
                    {"name": "face_score", "dataType": ["number"]},
                    {"name": "face_landmarks", "dataType": ["text"]},  # JSON string
                    {"name": "custom_data", "dataType": ["text"]},
                    {"name": "created_at", "dataType": ["date"]},
                ]
            else:
                # 物品数据 collection (ObjectData)
                properties = [
                    {"name": "image_id", "dataType": ["text"]},
                    {"name": "object_id", "dataType": ["text"]},
                    {"name": "img_url", "dataType": ["text"]},
                    {"name": "img_object_url", "dataType": ["text"]},
                    {"name": "custom_data", "dataType": ["text"]},
                    {"name": "created_at", "dataType": ["date"]},
                ]

            # 创建schema
            class_obj = {
                "class": self.collection_name,
                "properties": properties,
                "vectorizer": "none",  # 我们自己提供向量
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {
                    "distance": "cosine",
                    "ef": 200,
                    "efConstruction": 200,
                    "maxConnections": 32
                }
            }

            self.client.schema.create_class(class_obj)
            logger.info(f"Collection {self.collection_name} created successfully")

        except Exception as e:
            logger.error(f"Error setting up legacy collection: {e}")
    
    def close(self):
        """关闭连接"""
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed")
            except:
                pass
            finally:
                self.client = None  # 清空引用，下次get_client会重新连接
    
    def get_client(self):
        """获取客户端实例"""
        if not self.client:
            self.connect()
        return self.client

    def get_vector_dimension(self) -> Optional[int]:
        """
        获取当前collection的向量维度

        Returns:
            向量维度，如果collection为空则返回None
        """
        try:
            import requests
            # 使用REST API查询第一个对象
            url = f"{settings.weaviate_url}/v1/objects"
            params = {
                "class": self.collection_name,
                "limit": 1,
                "include": "vector"
            }
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                objects = data.get("objects", [])

                if objects and "vector" in objects[0]:
                    dimension = len(objects[0]["vector"])
                    logger.info(f"Current vector dimension: {dimension}")
                    return dimension
                else:
                    logger.info("Collection is empty, no vector dimension constraint yet")
                    return None
            else:
                logger.warning(f"Failed to query objects: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting vector dimension: {e}")
            return None

    def clear_collection(self):
        """清空collection中的所有数据，但保留collection结构"""
        try:
            if not self.client:
                self.connect()

            deleted_count = 0

            # 检查客户端类型
            if hasattr(self.client, 'collections'):
                # V4 API - 删除所有对象
                collection = self.client.collections.get(self.collection_name)

                # 获取所有对象并删除
                result = collection.query.fetch_objects(limit=10000)
                for obj in result.objects:
                    collection.data.delete_by_id(obj.uuid)
                    deleted_count += 1

                logger.info(f"Cleared {deleted_count} objects from collection {self.collection_name}")
                return deleted_count
            else:
                # Legacy API - 批量删除
                result = self.client.query.get(
                    self.collection_name, ["image_id"]
                ).with_limit(10000).with_additional("id").do()

                if result and "data" in result and "Get" in result["data"]:
                    items = result["data"]["Get"].get(self.collection_name, [])
                    for item in items:
                        uuid = item["_additional"]["id"]
                        self.client.data_object.delete(uuid, class_name=self.collection_name)
                        deleted_count += 1

                logger.info(f"Cleared {deleted_count} objects from collection {self.collection_name}")
                return deleted_count

        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def delete_collection(self):
        """删除collection（用于重置数据库）"""
        try:
            if not self.client:
                self.connect()

            # 检查客户端类型
            if hasattr(self.client, 'collections'):
                # V4 API
                if self.client.collections.exists(self.collection_name):
                    self.client.collections.delete(self.collection_name)
                    logger.info(f"Collection {self.collection_name} deleted")
                    return True
            else:
                # Legacy API
                schema = self.client.schema.get()
                exists = any(cls["class"] == self.collection_name for cls in schema.get("classes", []))
                if exists:
                    self.client.schema.delete_class(self.collection_name)
                    logger.info(f"Collection {self.collection_name} deleted")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

# 单例实例
weaviate_client = WeaviateClient()