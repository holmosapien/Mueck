from pydantic import BaseModel
from typing import Optional

class TensorArtImage(BaseModel):
    image_id: str
    url: str
    filename: Optional[str] = None
    seed: int
    file_size: int
    width: int
    height: int