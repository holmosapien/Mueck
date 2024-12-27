from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import re
import requests

from PIL import Image
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

from lib.context import MueckContext
from lib.slack_client import SlackClient
from lib.slack_integration import SlackIntegration
from lib.tensor_art import TensorArtJob

from lib.models.slack_event import SlackEventRecord
from lib.models.tensor_art import TensorArtRequestUpdate
from lib.store.slack_event import SlackEventStore

class SlackEvent:
    @classmethod
    def from_verified_event(
        cls,
        context: MueckContext,
        slack_signature: str,
        verification_string: str,
        event_body: dict
    ) -> SlackEvent:
        app_id = event_body["api_app_id"]
        channel = event_body["event"]["channel"]
        request_ts = event_body["event"]["ts"]
        event_ts = event_body["event"]["event_ts"]
        thread_ts = event_body["event"].get("thread_ts", event_ts)

        #
        # Get the Slack integration and client. We need the integration
        # so that we can store the integration ID along with the event,
        # and we need the client so we can get the signing secret that
        # we'll use to verify the payload.
        #

        slack_integration = SlackIntegration.from_app_id(context, app_id)

        if not slack_integration:
            raise Exception("Slack integration not found.")

        slack_client = SlackClient.from_id(context, slack_integration.slack_client_id)

        if not slack_client:
            raise Exception("Slack client not found.")

        valid = cls.verify_slack_signature(
            context,
            slack_signature,
            verification_string,
            slack_client.signing_secret
        )

        if not valid:
            raise Exception("Invalid event signature.")

        #
        # Now we can create the event record from the verified event.
        #

        created = datetime.datetime.now()

        slack_event_record = SlackEventRecord(
            id=0,
            slack_integration_id=slack_integration.id,
            event=event_body,
            channel=channel,
            request_ts=request_ts,
            thread_ts=thread_ts,
            tensor_art_request_id=None,
            created=created,
            processed=None
        )

        return cls(context, slack_event_record)

    @classmethod
    def from_event_body(cls, context: MueckContext, event_body: dict) -> SlackEvent:
        app_id = event_body["api_app_id"]
        channel = event_body["event"]["channel"]
        request_ts = event_body["event"]["ts"]
        event_ts = event_body["event"]["event_ts"]
        thread_ts = event_body["event"].get("thread_ts", event_ts)

        integration = SlackIntegration.from_app_id(context, app_id)

        if not integration:
            raise Exception("Slack integration not found.")

        created = datetime.datetime.now()

        slack_event_record = SlackEventRecord(
            id=0,
            slack_integration_id=integration.id,
            event=event_body,
            channel=channel,
            request_ts=request_ts,
            thread_ts=thread_ts,
            tensor_art_request_id=None,
            created=created,
            processed=None
        )

        return cls(context, slack_event_record)

    @classmethod
    def from_next_unprocessed(cls, context: MueckContext) -> SlackEvent:
        store = SlackEventStore(context)

        slack_event_record = store.get_next_unprocessed_event()

        if not slack_event_record:
            return None

        return cls(context, slack_event_record, store=store)

    @staticmethod
    def verify_slack_signature(context: MueckContext, slack_signature: str, verification_string: str, signing_secret: str) -> bool:

        #
        # Calculate the signature and see how it compares to what Slack sent.
        #

        computed_signature = "v0=" + hmac.new(
            key=bytes(signing_secret.encode("utf-8")),
            msg=verification_string.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        valid = hmac.compare_digest(slack_signature, computed_signature)

        if not valid:
            context.logger.error(
                f"Invalid signature: " +
                f"slack_signature={slack_signature}, " +
                f"computed_signature={computed_signature}"
            )

            return False

        # context.logger.debug(f"Signature verified: slack_signature={slack_signature}, computed_signature={computed_signature}")

        return True

    def __init__(self, context: MueckContext, slack_event_record: SlackEventRecord, store: SlackEventStore = None):
        self.context = context
        self.record = slack_event_record

        if store is None:
            store = SlackEventStore(context)

        self.store = store

        self.tensor_art_job = None

        self.__slack_integration = None
        self.__slack_client = None

    @property
    def id(self) -> int:
        return self.record.id

    @property
    def slack_integration_id(self) -> int:
        return self.record.slack_integration_id

    @property
    def slack_integration(self) -> SlackIntegration:
        if not self.__slack_integration:
            integration = SlackIntegration.from_id(self.context, self.slack_integration_id)

            self.__slack_integration = integration

        return self.__slack_integration

    @property
    def event(self) -> dict:
        return self.record.event

    @property
    def channel(self) -> str:
        return self.record.channel

    @property
    def thread_ts(self) -> str:
        return self.record.thread_ts

    @property
    def slack_client(self) -> WebClient:
        if not self.__slack_client:
            self.__slack_client = WebClient(token=self.slack_integration.access_token)

        return self.__slack_client

    @property
    def tensor_art_request_id(self) -> int:
        return self.record.tensor_art_request_id

    def save_event(self):
        slack_event_record = self.store.save_event(self.record)

        self.record = slack_event_record

    def process_event(self):
        if self.record.tensor_art_request_id:
            # Resume a job already in progress.

            job_id = self.store.get_tensor_art_job_id(self.tensor_art_request_id)
            job = TensorArtJob(self.context, job_id=job_id)
        else:
            # Start a new job.

            (prompt, seed) = self.__extract_prompt_from_event()

            job = TensorArtJob(self.context, prompt=prompt, seed=seed)

            job.execute()

            self.record.tensor_art_request_id = self.store.save_tensor_art_request(self.id, job)

            self.reply_with_status(job.status)

        self.tensor_art_job = job

    def update_tensor_art_request(self, update: TensorArtRequestUpdate):
        self.store.update_tensor_art_request(self.tensor_art_request_id, update)

    def save_images(self):
        for image in self.tensor_art_job.images:
            url = image.url

            r = requests.get(url)

            basename = f"{image.image_id}.png"
            filename = f"{self.context.download_path}/{basename}"

            with open(filename, "wb") as fp:
                fp.write(r.content)

            seed = self.__get_image_seed(filename)

            image.filename = filename
            image.seed = seed

            self.store.save_tensor_art_image(self.tensor_art_request_id, image)

    def reply_with_status(self, status: str):
        client = self.slack_client

        if status == "created":
            emoji = "eyes"
        elif status == "queued":
            emoji = "hourglass_flowing_sand"
        elif status == "running":
            emoji = "runner"
        elif status == "complete":
            emoji = "white_check_mark"
        else:
            emoji = "question"

        try:
            client.reactions_add(
                channel=self.channel,
                name=emoji,
                timestamp=self.record.request_ts,
            )
        except SlackApiError:
            self.context.logger.error("Failed to add reaction to message.")

    def reply_with_images(self):
        client = self.slack_client

        file_uploads = [
            {
                "file": image.filename,
                "title": f"seed:{image.seed}",
            } for image in self.tensor_art_job.images
        ]

        response = client.files_upload_v2(
            file_uploads=file_uploads,
            channel=self.channel,
            thread_ts=self.thread_ts,
        )

    def mark_event_as_processed(self):
        self.store.mark_event_as_processed(self.id)

    def __extract_prompt_from_event(self) -> tuple[str, int]:
        bot_user_id = self.slack_integration.bot_user_id

        prompt = ""
        seed = -1

        for block in self.event["event"]["blocks"]:
            if block["type"] == "rich_text":
                for element in block["elements"]:
                    if element["type"] == "rich_text_section":
                        for text in element["elements"]:
                            if text["type"] == "user" and text["user_id"] != bot_user_id:
                                prompt += text['user_id']
                            elif text["type"] == "text":
                                #
                                # See if the user has embedded the image seed in the prompt.
                                #

                                if "style" in text and "code" in text["style"] and text["style"]["code"]:
                                    m = re.match(r"^seed:(\d+)$", text["text"])

                                    if m:
                                        seed = m.group(1)

                                        continue

                                prompt += text["text"]

        return (prompt, seed)

    def __get_image_seed(self, filename: str) -> str:
        try:
            image = Image.open(filename)

            image.load()

            prompt = json.loads(image.info["prompt"])
        except Exception as e:
            self.context.logger.error(f"Failed to extract metadata from image: {e}", exc_info=True)

            return 0

        seed = 0

        try:
            for key in prompt:
                if "inputs" in prompt[key] and "seed" in prompt[key]["inputs"]:
                    seed = prompt[key]["inputs"]["seed"]
        except Exception as e:
            self.context.logger.error(f"Failed to parse image metadata: {e}", exc_info=True)

        return seed