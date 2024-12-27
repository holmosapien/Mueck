import json
import re
import requests
import uuid

from typing import List, Optional

from lib.context import MueckContext

from lib.models.tensor_art import TensorArtImage

class TensorArtJob:
    def __init__(
        self,
        context: MueckContext,
        prompt: Optional[str] = None,
        job_id: Optional[str] = None,
    ):
        self.context = context

        self.api_key = context.tensorart_api_key
        self.endpoint = context.tensorart_endpoint

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.id: Optional[str] = None
        self.prompt: str = ""
        self.status: Optional[str] = None
        self.credits: float = 0.0
        self.width: int = 0
        self.height: int = 0
        self.seed: int = 0
        self.queue_position: int = 0
        self.queue_length: int = 0
        self.images = List[TensorArtImage]

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
                        "seed": -1,
                    }
                },
                {
                    "type": "DIFFUSION",
                    "diffusion": {
                        "cfgScale": 1,
                        "clipSkip": 1,
                        "guidance": 3.5,
                        "height": 1536,
                        "lora": {
                            "items": [
                            {
                                "loraModel": "793264151850916361",
                                "weight": 0.8,
                            },
                            {
                                "loraModel": "785002322695696514",
                                "weight": 0.7,
                            }
                            ]
                        },
                        "prompts": [
                            {
                                "text": self.prompt,
                            },
                        ],
                        "sampler": "Euler a",
                        "sdVae": "Automatic",
                        "sd_model": "757279507095956705",
                        "steps": 20,
                        "width": 1024,
                    }
                }
            ]
        }

        r = requests.post(url, headers=self.headers, json=body)

        response = r.json()

        print(response)

        self.id = response["job"]["id"]
        self.status = "pending" # response["job"]["status"]

        return

    def get_job_status(self) -> str:
        if not self.id:
            raise ValueError("Job ID is required to get a job.")

        url = f"{self.endpoint}/v1/jobs/{self.id}"
        r = requests.get(url, headers=self.headers)

        response = r.json()
        status = response["job"]["status"]

        if status in ["CREATED", "WAITING"]:
            self.__parse_pending_job(response)
        elif status == "RUNNING":
            self.__parse_running_job(response)
        elif status == "SUCCESS":
            self.__parse_successful_job(response)
        else:
            self.status = "pending"

        return self.status

    def __parse_pending_job(self, response):
        job_id = response["job"]["id"]
        status = "pending"
        credits = response["job"]["credits"]

        queue_position = 0
        queue_length = 0

        if "waitingInfo" in response["job"] and "queueRank" in response["job"]["waitingInfo"]:
            queue_position = response["job"]["waitingInfo"]["queueRank"]
            queue_length = response["job"]["waitingInfo"]["queueLen"]

        self.id = job_id
        self.status = status
        self.credits = credits
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

        self.images: List[TensorArtImage] = []

        for image in images:
            image_id = image["id"]
            url = image["url"]
            seed = 0
            file_size = 0
            width = 0
            height = 0

            if image_id in meta_map:
                meta_info = meta_map[image_id]["meta"]
                raw_file_size = meta_info["FileSize"]
                image_size = meta_info["ImageSize"]
                seed = meta_info["Seed"]

                m = re.match(r"^(\d+) kB$", raw_file_size)

                if m:
                    file_size = int(m.group(1))

                m = re.match(r"^(\d+)x(\d+)$", image_size)

                if m:
                    width = int(m.group(1))
                    height = int(m.group(2))

            image_record = TensorArtImage(
                image_id=image_id,
                url=url,
                seed=seed,
                file_size=file_size,
                width=width,
                height=height,
            )

            self.images.append(image_record)