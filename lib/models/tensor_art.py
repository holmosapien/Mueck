from pydantic import BaseModel
from typing import Optional

class TensorArtImage(BaseModel):
    image_id: str
    url: str
    filename: Optional[str] = None
    seed: int
    width: int
    height: int
    seed: int

class TensorArtRequestUpdate(BaseModel):
    status: Optional[str] = None
    credits: Optional[float] = None