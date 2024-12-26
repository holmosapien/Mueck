import json
import requests

from datetime import datetime
from urllib.parse import urlencode

from lib.context import MueckContext
from lib.models.slack_authorization import SlackOAuthState
from lib.models.slack_integration import SlackIntegrationRecord
from lib.slack_client import SlackClient
from lib.slack_integration import SlackIntegration
from lib.store.slack_authorization import SlackAuthorizationStore

class SlackAuthorization:
    def __init__(self, context: MueckContext, store=None):
        self.context = context

        if store is None:
            store = SlackAuthorizationStore(context)

        self.store = store

    def get_slack_redirect_link(self, account_id, slack_client_id) -> str:
        state_id = self.store.save_slack_oauth_state(account_id, slack_client_id)

        state = SlackOAuthState(
            state_id=state_id,
            account_id=account_id,
            slack_client_id=slack_client_id,
        )

        bot_scopes = ",".join([
            "app_mentions:read",
            "chat:write",
        ])

        slack_client = SlackClient.from_id(self.context, slack_client_id)

        params = {
            "client_id": slack_client.api_client_id,
            "scope": bot_scopes,
            "user_scope": "",
            "redirect_uri": f"https://{self.context.listener_hostname}/api/v1/mueck/slack-authorization",
            "state": state.model_dump_json()
        }

        url = "https://slack.com/oauth/v2/authorize?" + urlencode(params)

        return url

    def exchange_code_for_token(self, code: str, state: str) -> str:
        state_obj = json.loads(state)
        state_record = SlackOAuthState(**state_obj)

        state_id = state_record.state_id
        account_id = state_record.account_id
        slack_client_id = state_record.slack_client_id

        client = SlackClient.from_authorization_state(self.context, state_record)

        if not client:
            raise Exception(f"Could not find state_id={state_id}, account_id={account_id}, slack_client_id={slack_client_id}")

        token = self.__get_slack_token(account_id, client, code)

        self.store.redeem_authorization_state(state_id)

        return token

    def __get_slack_token(self, account_id: int, client: SlackClient, code: str) -> str:
        params = {
            "client_id": client.api_client_id,
            "client_secret": client.api_client_secret,
            "code": code
        }

        url = "https://slack.com/api/oauth.v2.access?" + urlencode(params)

        r = requests.post(url)

        response = r.json()

        access_token = response["access_token"]
        bot_user_id = response["bot_user_id"]
        app_id = response["app_id"]
        team_id = response["team"]["id"]
        team_name = response["team"]["name"]

        integration_record = SlackIntegrationRecord(
            id=0,
            account_id=account_id,
            slack_client_id=client.id,
            team_id=team_id,
            team_name=team_name,
            bot_user_id=bot_user_id,
            access_token=access_token,
            app_id=app_id,
            created=datetime.now(),
        )

        integration = SlackIntegration(self.context, integration_record)

        integration.create_integration()

        return access_token