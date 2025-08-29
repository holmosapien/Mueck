import json
import re
import requests
import uuid

from typing import List, Optional

from lib.context import MueckContext

from lib.generators.base import ImageGenerator
from lib.models.generated_image import GeneratedImage, ModelVendor

FLUX_CHECKPOINT = "757279507095956705"
FLUX_PONY_CHECKPOINT = "763947005736342551"
OBLIVIOUS_MIX_ILLUSTRIOUS_CHECKPOINT = "808939700149555823"
STABLE_DIFFUSION_35_CHECKPOINT = "808211415430243917"

class TensorArtJob(ImageGenerator):
    def __init__(
        self,
        context: MueckContext,
        prompt: Optional[str] = None,
        seed: Optional[int] = -1,
        job_id: Optional[str] = None,
    ):
        super().__init__(context)

        self.model_vendor = ModelVendor.tensor_art

        self.api_key = context.tensorart_api_key
        self.endpoint = context.tensorart_endpoint

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.queue_position: int = 0
        self.queue_length: int = 0

        if job_id:
            self.id = job_id
            self.status = "pending"

        if prompt:
            self.prompt = prompt

    def execute(self):
        if not self.prompt:
            raise ValueError("Prompt is required to create a job.")

        url = f"{self.endpoint}/v1/jobs"
        request_id = str(uuid.uuid4())

        body = {
            "request_id": request_id,
            "stages": [
                {
                    "type": "INPUT_INITIALIZE",
                    "inputInitialize": {
                        "count": 1,
                        "seed": self.seed,
                    }
                },
                {
                    "type": "DIFFUSION",
                    "diffusion": {
                        "cfgScale": 1.5,
                        "clipSkip": 1,
                        "guidance": 3.5,
                        "height": 1536,
                        "prompts": [
                            {
                                "text": self.prompt,
                            },
                        ],
                        "sampler": "Euler a",
                        "sdVae": "Automatic",
                        "sd_model": FLUX_PONY_CHECKPOINT,
                        "steps": 20,
                        "width": 1024,
                    }
                }
            ]
        }

        r = requests.post(url, headers=self.headers, json=body)

        response = r.json()

        self.context.logger.debug(f"response={response}")

        self.id = response["job"]["id"]
        self.status = "created" # response["job"]["status"]

        return

    def get_status(self) -> str:
        if not self.id:
            raise ValueError("Job ID is required to get a job.")

        url = f"{self.endpoint}/v1/jobs/{self.id}"
        r = requests.get(url, headers=self.headers)

        response = r.json()
        status = response["job"]["status"]

        if status == "CREATED":
            self.__parse_created_job(response)
        elif status == "WAITING":
            self.__parse_queued_job(response)
        elif status == "RUNNING":
            self.__parse_running_job(response)
        elif status == "SUCCESS":
            self.__parse_successful_job(response)
        else:
            self.status = "queued"

        return self.status

    def __parse_created_job(self, response):
        self.id = response["job"]["id"]
        self.status = "created"

    def __parse_queued_job(self, response):
        self.id = response["job"]["id"]
        self.status = "queued"
        self.credits = response["job"]["credits"]

        queue_position = 0
        queue_length = 0

        if "waitingInfo" in response["job"] and "queueRank" in response["job"]["waitingInfo"]:
            queue_position = response["job"]["waitingInfo"]["queueRank"]
            queue_length = response["job"]["waitingInfo"]["queueLen"]

        self.queue_position = queue_position
        self.queue_length = queue_length

    def __parse_running_job(self, response):
        self.id = response["job"]["id"]
        self.status = "running"
        self.credits = response["job"]["credits"]

    def __parse_successful_job(self, response):
        self.id = response["job"]["id"]
        self.status = "complete"
        self.credits = response["job"]["credits"]

        success_info = response["job"]["successInfo"]
        images = success_info["images"]
        meta_map = success_info["imageExifMetaMap"]

        self.images: List[GeneratedImage] = []

        for image in images:
            image_id = image["id"]
            url = image["url"]
            seed = 0
            width = 0
            height = 0

            if image_id in meta_map:
                meta_info = meta_map[image_id]["meta"]
                image_size = meta_info["ImageSize"]
                seed = meta_info["Seed"]

                m = re.match(r"^(\d+)x(\d+)$", image_size)

                if m:
                    width = int(m.group(1))
                    height = int(m.group(2))

            image_record = GeneratedImage(
                image_id=image_id,
                url=url,
                seed=seed,
                width=width,
                height=height,
            )

            self.images.append(image_record)