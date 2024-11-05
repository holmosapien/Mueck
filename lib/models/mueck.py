import datetime

from pydantic import BaseModel

class ImageRequest(BaseModel):
    prompt: str
    user_id: str

class RawImageRequest(ImageRequest):
    request_id: int
    created: datetime.datetime

class ParsedImageRequest(RawImageRequest):
    width: int
    height: int
    count: int