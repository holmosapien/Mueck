from __future__ import annotations

import datetime
import requests

from slack_sdk.web import WebClient

from lib.context import MueckContext
from lib.slack_integration import SlackIntegration
from lib.tensor_art import TensorArtJob

from lib.models.slack_event import SlackEventRecord
from lib.models.tensor_art import TensorArtImage
from lib.store.slack_event import SlackEventStore

class SlackEvent:
    @classmethod
    def from_event_body(cls, context: MueckContext, event_body: dict) -> SlackEvent:
        app_id = event_body["api_app_id"]
        timestamp = event_body["event"]["ts"]

        integration = SlackIntegration.from_app_id(context, app_id)

        if not integration:
            raise Exception("Slack integration not found.")

        created = datetime.datetime.now()

        slack_event_record = SlackEventRecord(
            id=0,
            slack_integration_id=integration.id,
            event=event_body,
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

    def __init__(self, context: MueckContext, slack_event_record: SlackEventRecord, store: SlackEventStore = None):
        self.context = context
        self.record = slack_event_record

        if store is None:
            store = SlackEventStore(context)

        self.store = store
        self.tensor_art_job = None

    @property
    def id(self) -> int:
        return self.record.id

    @property
    def slack_integration_id(self) -> int:
        return self.record.slack_integration_id

    @property
    def event(self) -> dict:
        return self.record.event

    @property
    def channel(self) -> str:
        return self.event["event"]["channel"]

    @property
    def thread_ts(self) -> str:
        if "thread_ts" in self.event["event"]:
            return self.event["event"]["thread_ts"]
        else:
            return self.event["event"]["event_ts"]

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

            prompt = self.__extract_prompt_from_event()

            job = TensorArtJob(self.context, prompt=prompt)

            job.execute()

            self.record.tensor_art_request_id = self.store.save_tensor_art_request(self.id, job)

        self.tensor_art_job = job

    def update_tensor_art_request_status(self, status: str):
        self.store.update_tensor_art_request_status(self.tensor_art_request_id, status)

    def save_images(self):
        for image in self.tensor_art_job.images:
            url = image.url

            r = requests.get(url)

            basename = f"{image.image_id}.png"
            filename = f"{self.context.download_path}/{basename}"

            with open(filename, "wb") as fp:
                fp.write(r.content)

            image.filename = filename

            self.store.save_tensor_art_image(self.tensor_art_request_id, image)

    def reply_with_images(self):
        integration = SlackIntegration.from_id(self.context, self.slack_integration_id)
        access_token = integration.access_token

        client = WebClient(token=access_token)

        file_uploads = [
            {
                "file": image.filename,
                "title": image.image_id,
            } for image in self.tensor_art_job.images
        ]

        response = client.files_upload_v2(
            file_uploads=file_uploads,
            channel=self.channel,
            thread_ts=self.thread_ts,
            initial_comment="Here is your requested image.",
        )

        print(response)

    def mark_event_as_processed(self):
        self.store.mark_event_as_processed(self.id)

    def __extract_prompt_from_event(self) -> str:
        integration = SlackIntegration.from_id(self.context, self.slack_integration_id)
        bot_user_id = integration.bot_user_id

        prompt = ""

        for block in self.event["event"]["blocks"]:
            if block["type"] == "rich_text":
                for element in block["elements"]:
                    if element["type"] == "rich_text_section":
                        for text in element["elements"]:
                            if text["type"] == "user" and text["user_id"] != bot_user_id:
                                prompt += text['user_id']
                            elif text["type"] == "text":
                                prompt += text["text"]

        return prompt