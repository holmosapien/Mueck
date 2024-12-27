from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from lib.tensor_art import TensorArtJob

class SlackEventRecord(BaseModel):
    id: int
    slack_integration_id: int
    event: dict
    tensor_art_request_id: Optional[int]
    created: datetime
    processed: Optional[datetime]