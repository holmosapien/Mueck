from __future__ import annotations

from lib.context import MueckContext
from lib.models.slack_authorization import SlackOAuthState
from lib.models.slack_client import SlackClientRecord
from lib.store.slack_client import SlackClientStore

def verify_slack_event() -> bool:
    return True

class SlackClient:
    @classmethod
    def from_id(cls, context, slack_client_id: int) -> SlackClient:
        store = SlackClientStore(context)
        record = store.get_slack_client_by_id(slack_client_id)

        return cls(context, record)

    @classmethod
    def from_authorization_state(cls, context, state_record: SlackOAuthState) -> SlackClient:
        state_id = state_record.state_id
        account_id = state_record.account_id
        slack_client_id = state_record.slack_client_id

        store = SlackClientStore(context)
        record = store.get_slack_client_by_authorization_state(state_id, account_id, slack_client_id)

        if not record:
            raise Exception(f"Could not find state_id={state_id}, account_id={account_id}, slack_client_id={slack_client_id}")

        return cls(context, record)

    def __init__(self, context: MueckContext, record: SlackClientRecord):
        self.context = context
        self.record = record

    @property
    def id(self) -> int:
        return self.record.id

    @property
    def api_client_id(self) -> str:
        return self.record.api_client_id

    @property
    def api_client_secret(self) -> str:
        return self.record.api_client_secret

    @property
    def signing_secret(self) -> str:
        return self.record.signing_secret