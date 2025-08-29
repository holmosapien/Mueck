from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ModelVendor(str, Enum):
    tensor_art = "tensor_art"
    civitai = "civitai"

class ImageGenerationRequest(BaseModel):
    id: Optional[int] = None
    model_vendor: ModelVendor
    job_id: str
    token: Optional[str] = None

class ImageGenerationRequestUpdate(BaseModel):
    status: Optional[str] = None
    credits: Optional[float] = None

class GeneratedImage(BaseModel):
    image_id: str
    url: str
    filename: Optional[str] = None
    seed: int
    width: int
    height: int
    seed: int