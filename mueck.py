import os
import uvicorn

from fastapi import FastAPI

from lib.log_handler import setup_logger
from lib.models.mueck import (
    ImageRequests,
    ImageRequest,
    RawImageRequest,
    ParsedImageRequest
)
from lib.queue import ImageQueue

logger = setup_logger()
app = FastAPI()

@app.post("/api/v1/mueck/request")
def create_request(request: ImageRequest) -> RawImageRequest:
    image_queue = ImageQueue()

    raw_request = image_queue.queue_request(request)

    return raw_request

@app.get("/api/v1/mueck/requests")
def get_requests(include_processed=False) -> ImageRequests:
    image_queue = ImageQueue()

    requests = image_queue.get_requests(include_processed=include_processed)
    response = ImageRequests(requests=requests)

    return response

@app.get("/api/v1/mueck/request/{request_id}")
def get_request(request_id: int) -> RawImageRequest | ParsedImageRequest:
    image_queue = ImageQueue()

    return image_queue.get_request(request_id)

if __name__ == "__main__":
    certificate = os.environ.get("MUECK_SSL_CERTIFICATE")
    private_key = os.environ.get("MUECK_SSL_PRIVATE_KEY")

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