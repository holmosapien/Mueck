import logging
import os
import torch
import uuid

from diffusers import StableDiffusion3Pipeline
from huggingface_hub import login

from lib.models.mueck import ParsedImageRequest

logger = logging.getLogger("mueck")

class ImageGenerator:
    def __init__(self):
        output_directory = os.getenv("MUECK_OUTPUT_DIRECTORY")

        if not output_directory:
            raise Exception("MUECK_OUTPUT_DIRECTORY environment variable not set.")

        self.output_directory = output_directory
        self.sd_pipe = self.initialize()

    def initialize(self):
        cuda_available = torch.cuda.is_available()

        if not cuda_available:
            raise Exception("CUDA is not enabled in PyTorch.")

        access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN")

        if not access_token:
            raise Exception("Hugging Face access token not found.")

        login(token=access_token)

        pipe = StableDiffusion3Pipeline.from_pretrained(
            "stabilityai/stable-diffusion-3.5-medium",
            torch_dtype=torch.bfloat16
        )

        pipe = pipe.to("cuda")

        return pipe

    def generate_image(self, request: ParsedImageRequest) -> list[str]:
        prompt = request.prompt
        width = request.width
        height = request.height
        count = request.count

        logger.info(f"Generating {count} images ({height} x {width}) with prompt={prompt}")

        filenames = []

        for i in range(count):
            image = self.sd_pipe(
                prompt,
                width=width,
                height=height,
                num_inference_steps=40,
                guidance_scale=4.5,
            ).images[0]

            filename = self.generate_filename()

            image.save(filename)

            filenames.append(filename)

        return filenames

    def generate_filename(self) -> str:
        basename = uuid.uuid4().hex + ".png"
        filename = os.path.join(self.output_directory, basename)

        return filename