import json
import os
import uvicorn

from fastapi import FastAPI, Request
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
def get_slack_access_token(code: str, state: str) -> None:
    authorization = SlackAuthorization(context)

    authorization.exchange_code_for_token(code, state)

    return "", 204

@app.post("/api/v1/mueck/slack-event")
async def post_slack_event(request: Request) -> None:
    raw_payload = await request.body()
    event_body = json.loads(raw_payload)
    event_type = event_body["type"]

    if event_type == "url_verification":
        challenge = event_body.get("challenge")

        return {
            "challenge": challenge,
        }

    #
    # This will generate a Slack event without verifying the signature.
    #
    #
    # slack_event = SlackEvent.from_event_body(context, event_body)
    #

    #
    # First we need to assemble the string that's used to verify the signature.
    #

    slack_signature = request.headers.get("X-Slack-Signature")
    timestamp_header = request.headers.get("X-Slack-Request-Timestamp")

    verification_string = f"v0:{timestamp_header}:{raw_payload.decode()}"

    #
    # Send everything we need to verify and process the event:
    #
    # - The signature as computed by Slack
    # - Our interpretation of the verification string
    # - The event body, as a dictionary
    #

    slack_event = SlackEvent.from_verified_event(
        context,
        slack_signature,
        verification_string,
        event_body
    )

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