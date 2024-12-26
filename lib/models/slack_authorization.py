from pydantic import BaseModel

class SlackOAuthState(BaseModel):
    state_id: int
    account_id: int
    slack_client_id: int