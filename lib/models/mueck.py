import datetime

from pydantic import BaseModel

class ImageRequest(BaseModel):
    prompt: str
    user_id: str

class RawImageRequest(ImageRequest):
    request_id: int
    processed: bool
    created: datetime.datetime

class ParsedImageRequest(RawImageRequest):
    width: int
    height: int
    count: int

class ImageRequestFilter(BaseModel):
    request_ids: list[int] = []
    user_ids: list[str] = []

class ImageRequests(BaseModel):
    requests: list[RawImageRequest | ParsedImageRequest]