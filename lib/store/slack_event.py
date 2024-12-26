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
                        created=row[3],
                        processed=row[4],
                    )

        return slack_event_record

    def save_tensor_art_request(self, slack_integration_id: int, job: TensorArtJob) -> int:
        query = """
            INSERT INTO
                tensor_art_request
            (
                slack_integration_id,
                job_id,
                prompt,
                job_status,
                credits
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id
        """

        tensor_request_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    slack_integration_id,
                    job.id,
                    job.prompt,
                    job.status,
                    job.credits
                ))

                for row in cursor:
                    tensor_request_id = row[0]

        if not tensor_request_id:
            raise ValueError("Failed to save tensor art request.")

        return tensor_request_id

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