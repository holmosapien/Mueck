from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SlackIntegrationFilter(BaseModel):
    slack_integration_id: Optional[int] = None
    app_id: Optional[str] = None

class SlackIntegrationRecord(BaseModel):
    id: int
    account_id: int
    slack_client_id: int
    team_id: str
    team_name: str
    bot_user_id: str
    access_token: str
    app_id: str
    created: datetime