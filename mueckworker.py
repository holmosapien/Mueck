import requests
import time

from lib.context import MueckContext
from lib.slack_event import SlackEvent
from lib.tensor_art import TensorArtJob

class MueckWorker:
    def __init__(self):
        self.context = MueckContext()

    def run(self):
        self.context.logger.info("Mueck worker started.")

        while True:
            event = SlackEvent.from_next_unprocessed(self.context)

            if not event:
                self.context.logger.info("No events to process. Sleeping for 10 seconds.")

                time.sleep(10)

                continue

            self.context.logger.info(f"Processing event_id={event.id}")

            event.process_event()

            self.__wait_for_job_completion(event)

            event.save_images()
            event.reply_with_images()
            event.mark_event_as_processed()

    def __wait_for_job_completion(self, event: SlackEvent):
        job_id = event.tensor_art_job.id
        previous_status = event.tensor_art_job.status

        while True:
            status = event.tensor_art_job.get_job_status()

            self.context.logger.info(f"job_id={job_id}, status={status}")

            if status == "complete":
                return
            else:
                if previous_status is None or status != previous_status:
                    event.update_tensor_art_request_status(status)

                time.sleep(5)

if __name__ == "__main__":
    worker = MueckWorker()

    worker.run()