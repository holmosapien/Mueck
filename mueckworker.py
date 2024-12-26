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
                time.sleep(10)

                continue

            self.context.logger.info(f"Processing event_id={event.id}")

            job = event.process_event()

            self.__wait_for_job_completion(job)

            event.save_images(job.images)
            event.mark_event_as_processed()

    def __wait_for_job_completion(self, job: TensorArtJob):
        previous_status = job.status

        while True:
            job.get_job()

            if job.status == "completed":
                job.save_images()

                return
            else:
                print(f"Job is in status={job.status}")

                # if job.status != previous_status:
                #     job.update_status()

                time.sleep(5)

if __name__ == "__main__":
    worker = MueckWorker()

    worker.run()