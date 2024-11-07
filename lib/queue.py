from lib.models.mueck import ImageRequest, RawImageRequest, ParsedImageRequest
from lib.store.queue import QueueStore

class ImageQueue:
    def __init__(self, store=None):
        if store is None:
            store = QueueStore()

        self.store = store

    def queue_request(self, request: ImageRequest) -> RawImageRequest:
        return self.store.queue_request(request)

    def get_request(self, request_id: int) -> RawImageRequest | ParsedImageRequest:
        return self.store.get_request(request_id)

    def get_requests(self, include_processed=False) -> list[RawImageRequest | ParsedImageRequest]:
        return self.store.get_requests(include_processed=include_processed)

    def add_request_parameters(self, request: ParsedImageRequest):
        return self.store.add_request_parameters(request)

    def complete_request(self, request: ParsedImageRequest, filenames: list[str]):
        self.store.complete_request(request, filenames)