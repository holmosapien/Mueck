import civitai
import json

from typing import List, Optional

from lib.context import MueckContext
from lib.generators.base import GeneratedImage, ImageGenerator
from lib.models.generated_image import ModelVendor

CYBERREALISTIC_PONY_CHECKPOINT = "urn:air:sdxl:checkpoint:civitai:443821@2071650"
PONY_CHECKPOINT = "urn:air:sdxl:checkpoint:civitai:257749@290640"

class CivitAI(ImageGenerator):
    def __init__(
        self,
        context: MueckContext,
        prompt: Optional[str] = None,
        seed: Optional[int] = -1,
        job_id: Optional[str] = None,
        token: Optional[str] = None,
    ):
        super().__init__(context)

        self.model_vendor = ModelVendor.civitai

        if job_id:
            self.id = job_id
            self.status = "pending"

        if token:
            self.token = token

        if prompt:
            self.prompt = prompt

    def execute(self):
        if not self.prompt:
            raise ValueError("Prompt is required to create a job.")

        request = {
            "model": CYBERREALISTIC_PONY_CHECKPOINT,
            "params": {
                "cfgScale": 3.5,
                "clipSkip": 2,
                "height": 1024,
                "prompt": self.prompt,
                "scheduler": "EulerA",
                "steps": 20,
                "width": 832,
            }
        }

        response = civitai.image.create(request)

        # self.context.logger.debug(json.dumps(response, indent=4))

        self.token = response["token"]
        self.status = "created"

        for job in response["jobs"]:
            self.id = job["jobId"]
            self.credits = job["cost"]

    def get_status(self) -> str:
        if not self.token:
            raise ValueError("Token is required to get a job.")

        response = civitai.jobs.get(token=self.token)

        # self.context.logger.debug(json.dumps(response, indent=4))

        for job in response["jobs"]:
            self.credits = job["cost"]

            scheduled = job["scheduled"]

            if scheduled:
                self.status = "running"
            else:
                self.__parse_job_result(job["result"])

        return self.status

    def __parse_job_result(self, result):
        self.images: List[GeneratedImage] = []

        for image in result:
            available = image["available"]

            if available:
                self.status = "complete"

                image_id = image["blobKey"]
                url = image["blobUrl"]
                seed = image["seed"]
                width = 0
                height = 0

                image_record = GeneratedImage(
                    image_id=image_id,
                    url=url,
                    seed=seed,
                    width=width,
                    height=height,
                )

                self.images.append(image_record)
            else:
                self.context.logger.debug(f"Unexpected status: image_id={image_id}, available={available}")
