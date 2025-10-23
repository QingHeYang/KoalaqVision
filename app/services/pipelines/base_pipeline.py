from PIL import Image
from typing import Optional

class BasePipeline:
    """Pipeline base class"""

    def preprocess(self, image: Image.Image) -> Optional[Image.Image]:
        """Preprocess image"""
        raise NotImplementedError

    def extract_features(self, image: Image.Image, normalize: bool = True) -> Optional[list]:
        """Extract feature vector"""
        raise NotImplementedError

    def get_vector_dim(self) -> int:
        """Get vector dimension"""
        raise NotImplementedError

    def get_collection_name(self) -> str:
        """Get collection name"""
        raise NotImplementedError
