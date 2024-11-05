import uvicorn

from fastapi import FastAPI

from lib.database import Database
from lib.log_handler import setup_logger
from lib.models.mueck import ImageRequest, RawImageRequest

logger = setup_logger()
app = FastAPI()

@app.post("/api/v1/mueck/request")
def create_request(request: ImageRequest) -> RawImageRequest:
    database = Database()

    raw_request = database.queue_request(request)

    return raw_request

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=11030)