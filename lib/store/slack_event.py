import json

from typing import Optional

from lib.context import MueckContext
from lib.tensor_art import TensorArtJob

from lib.models.slack_event import SlackEventRecord
from lib.models.tensor_art import TensorArtImage

class SlackEventStore:
    def __init__(self, context: MueckContext):
        self.context = context

    def save_event(self, slack_event_record: SlackEventRecord) -> SlackEventRecord:
        query = """
            INSERT INTO
                slack_event
            (
                slack_integration_id,
                event,
                created
            ) VALUES (
                %s,
                %s,
                NOW()
            )
            RETURNING
                id,
                created
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    slack_event_record.slack_integration_id,
                    json.dumps(slack_event_record.event),
                ))

                for row in cursor:
                    slack_event_record.id = row[0]
                    slack_event_record.created = row[1]

        return slack_event_record

    def get_next_unprocessed_event(self) -> Optional[SlackEventRecord]:
        query = """
            SELECT
                id,
                slack_integration_id,
                event,
                tensor_art_request_id,
                created,
                processed
            FROM
                slack_event
            WHERE
                processed IS NULL
            ORDER BY
                created ASC
            LIMIT
                1
        """

        slack_event_record = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)

                for row in cursor:
                    slack_event_record = SlackEventRecord(
                        id=row[0],
                        slack_integration_id=row[1],
                        event=row[2],
                        tensor_art_request_id=row[3],
                        created=row[4],
                        processed=row[5],
                    )

        return slack_event_record

    def get_tensor_art_job_id(self, tensor_art_request_id: int) -> str:
        query = """
            SELECT
                job_id
            FROM
                tensor_art_request
            WHERE
                id = %s
        """

        job_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (tensor_art_request_id,))

                for row in cursor:
                    job_id = row[0]

        if not job_id:
            raise ValueError(f"Failed to retrieve job ID for tensor_art_request_id={tensor_art_request_id}.")

        return job_id

    def save_tensor_art_request(self, slack_event_id: int, job: TensorArtJob) -> int:
        query = """
            INSERT INTO
                tensor_art_request
            (
                job_id,
                prompt,
                job_status,
                credits
            ) VALUES (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id
        """

        tensor_art_request_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    job.id,
                    job.prompt,
                    job.status,
                    job.credits
                ))

                for row in cursor:
                    tensor_art_request_id = row[0]

        if not tensor_art_request_id:
            raise ValueError("Failed to save tensor art request.")

        query = """
            UPDATE
                slack_event
            SET
                tensor_art_request_id = %s
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    tensor_art_request_id,
                    slack_event_id,
                ))

        return tensor_art_request_id

    def update_tensor_art_request_status(self, tensor_art_request_id: int, status: str):
        query = """
            UPDATE
                tensor_art_request
            SET
                job_status = %s
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    status,
                    tensor_art_request_id,
                ))

    def save_tensor_art_image(self, tensor_art_request_id: int, image: TensorArtImage):
        query = """
            INSERT INTO
                tensor_art_image
            (
                tensor_art_request_id,
                filename,
                width,
                height
            ) VALUES (
                %s,
                %s,
                %s,
                %s
            )
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    tensor_art_request_id,
                    image.filename,
                    image.width,
                    image.height
                ))

    def mark_event_as_processed(self, slack_event_id: int):
        query = """
            UPDATE
                slack_event
            SET
                processed = NOW()
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (slack_event_id,))