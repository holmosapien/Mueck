from lib.context import MueckContext
from lib.models.slack_integration import SlackIntegrationFilter, SlackIntegrationRecord
from lib.store.slack_integration import SlackIntegrationStore

class SlackIntegration:
    @classmethod
    def from_id(cls, context: MueckContext, slack_integration_id: int):
        store = SlackIntegrationStore(context)
        filter = SlackIntegrationFilter(slack_integration_id=slack_integration_id)
        record = store.get_slack_integration(filter)

        return cls(context, record)

    @classmethod
    def from_app_id(cls, context: MueckContext, app_id: str):
        store = SlackIntegrationStore(context)
        filter = SlackIntegrationFilter(app_id=app_id)
        record = store.get_slack_integration(filter)

        return cls(context, record)

    def __init__(self, context: MueckContext, record: SlackIntegrationRecord, integration_store: SlackIntegrationStore = None):
        self.context = context
        self.record = record

        if integration_store is None:
            integration_store = SlackIntegrationStore(context)

        self.integration_store = integration_store

    @property
    def id(self) -> int:
        return self.record.id

    @property
    def bot_user_id(self) -> str:
        return self.record.bot_user_id

    @property
    def access_token(self) -> str:
        return self.record.access_token

    def create_integration(self):
        integration_id = self.integration_store.save_slack_integration(self.record)

        self.record.id = integration_id