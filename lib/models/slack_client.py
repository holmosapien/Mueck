from datetime import datetime
from pydantic import BaseModel

class SlackClientRecord(BaseModel):
    id: int
    api_client_id: str
    api_client_secret: str
    signing_secret: str
    name: str
    created: datetime