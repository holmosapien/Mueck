import os
import uvicorn

from fastapi import FastAPI, Body
from typing import Any

from lib.context import MueckContext
from lib.slack_authorization import SlackAuthorization
from lib.slack_event import SlackEvent

app = FastAPI()

context = MueckContext()

@app.get("/api/v1/mueck/slack-redirect-link")
def get_slack_redirect_link(account_id: int, slack_client_id: int) -> dict:
    authorization = SlackAuthorization(context)

    return {
        "redirect_link": authorization.get_slack_redirect_link(account_id, slack_client_id)
    }

@app.get("/api/v1/mueck/slack-authorization")
def get_slack_access_token(code: str, state: str) -> dict:
    authorization = SlackAuthorization(context)

    access_token = authorization.exchange_code_for_token(code, state)

    return "", 204

@app.post("/api/v1/mueck/slack-event")
def post_slack_event(payload: Any = Body(None)) -> None:
    event_type = payload["type"]

    if event_type == "url_verification":
        challenge = payload.get("challenge")

        return {
            "challenge": challenge,
        }

    slack_event = SlackEvent.from_event_body(context, payload)

    slack_event.save_event()

    return "", 204

if __name__ == "__main__":
    certificate = os.environ.get("MUECK_TLS_CERTIFICATE")
    private_key = os.environ.get("MUECK_TLS_PRIVATE_KEY")

    if certificate and private_key:
        uvicorn.run(
            app,
            host=None,
            port=11030,
            ssl_certfile=certificate,
            ssl_keyfile=private_key
        )
    else:
        uvicorn.run(app, host=None, port=11030)