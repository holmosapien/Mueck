from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SlackEventRecord(BaseModel):
    id: int
    slack_integration_id: int
    event: dict
    channel: str
    request_ts: str
    thread_ts: str
    image_generation_request_id: Optional[int]
    created: datetime
    processed: Optional[datetime]