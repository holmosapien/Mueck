import logging

from lib.models.mueck import RawImageRequest, ParsedImageRequest

logger = logging.getLogger("mueck")

class PromptProcessor:
    def process(self, request: RawImageRequest) -> ParsedImageRequest:

        #
        # Here we'll run the prompt through the initial LLM
        # to split the prompt into two components:
        #
        # - What the user wants to see
        # - Metadata about the request, like how many copies
        #   they want to see and how big they want them to be.
        #

        logger.info(f"Processing prompt for request_id={request.request_id}, prompt={request.prompt}")

        parsed_request = ParsedImageRequest(
            request_id=request.request_id,
            prompt=request.prompt,
            width=512,
            height=512,
            count=1,
            processed=False,
            user_id=request.user_id,
            created=request.created
        )

        return parsed_request