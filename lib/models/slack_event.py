from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SlackEventRecord(BaseModel):
    id: int
    slack_integration_id: int
    event: dict
    created: datetime
    processed: Optional[datetime]