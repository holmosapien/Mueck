from typing import List, Optional

from lib.context import MueckContext
from lib.models.generated_image import GeneratedImage

class ImageGenerator:
    def __init__(self, context: MueckContext):
        self.context = context

        self.model_vendor: ModelVendor = None
        self.id: Optional[str] = None
        self.token: Optional[str] = None
        self.prompt: str = ""
        self.status: Optional[str] = None
        self.credits: float = 0.0
        self.seed: int = -1
        self.images = List[GeneratedImage]