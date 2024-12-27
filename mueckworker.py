import time

from lib.context import MueckContext
from lib.slack_event import SlackEvent
from lib.models.tensor_art import TensorArtRequestUpdate

STATUS_MESSAGES = {
    "created": "Your request has been received.",
    "queued": "Your request has been queued for processing.",
    "running": "Your request is now running.",
    "complete": "Your image is ready.",
    "error": "There was an error processing your request."
}

class MueckWorker:
    def __init__(self):
        self.context = MueckContext()

    def run(self):
        self.context.logger.info("Mueck worker started.")

        # We use this so we only print the "no events to process" message once.

        sleeping = False

        while True:
            event = SlackEvent.from_next_unprocessed(self.context)

            if not event:
                if not sleeping:
                    self.context.logger.info("No events to process. Sleeping.")

                    sleeping = True

                time.sleep(10)

                continue

            self.context.logger.info(f"Processing event_id={event.id}")

            event.process_event()

            self.__wait_for_job_completion(event)

            event.save_images()
            event.reply_with_images()
            event.mark_event_as_processed()

            sleeping = False

    def __wait_for_job_completion(self, event: SlackEvent):
        job_id = event.tensor_art_job.id

        while True:
            previous_status = event.tensor_art_job.status

            status = event.tensor_art_job.get_status()
            credits = event.tensor_art_job.credits

            if status != previous_status:
                self.context.logger.info(f"job_id={job_id}, previous_status={previous_status}, status={status}")

                update = TensorArtRequestUpdate(
                    status=status,
                    credits=credits,
                )

                event.reply_with_status(status)
                event.update_tensor_art_request(update)

                if status == "complete":
                    return

                time.sleep(5)

if __name__ == "__main__":
    worker = MueckWorker()

    worker.run()