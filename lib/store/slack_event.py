import json

from typing import Optional

from lib.context import MueckContext
from lib.tensor_art import TensorArtJob

from lib.models.slack_event import SlackEventRecord
from lib.models.tensor_art import TensorArtImage, TensorArtRequestUpdate

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
                channel,
                request_ts,
                thread_ts,
                created
            ) VALUES (
                %s,
                %s,
                %s,
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
                    slack_event_record.channel,
                    slack_event_record.request_ts,
                    slack_event_record.thread_ts
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
                channel,
                request_ts,
                thread_ts,
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
                        channel=row[3],
                        request_ts=row[4],
                        thread_ts=row[5],
                        tensor_art_request_id=row[6],
                        created=row[7],
                        processed=row[8],
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
        request_query = """
            INSERT INTO
                tensor_art_request
            (
                job_id,
                prompt,
                status,
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

        event_query = """
            UPDATE
                slack_event
            SET
                tensor_art_request_id = %s
            WHERE
                id = %s
        """

        tensor_art_request_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(request_query, (
                    job.id,
                    job.prompt,
                    job.status,
                    job.credits
                ))

                for row in cursor:
                    tensor_art_request_id = row[0]

                cursor.execute(event_query, (
                    tensor_art_request_id,
                    slack_event_id,
                ))

        if not tensor_art_request_id:
            raise ValueError("Failed to save tensor art request.")

        return tensor_art_request_id

    def update_tensor_art_request(self, tensor_art_request_id: int, update: TensorArtRequestUpdate):
        updates = []
        values = []

        if update.status:
            updates.append("status = %s")
            values.append(update.status)

        if update.credits:
            updates.append("credits = %s")
            values.append(update.credits)

        if not updates:
            return

        values.append(tensor_art_request_id)

        query = f"""
            UPDATE
                tensor_art_request
            SET
                {', '.join(updates)}
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)

    def update_tensor_art_request_status(self, tensor_art_request_id: int, status: str):
        query = """
            UPDATE
                tensor_art_request
            SET
                status = %s
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
                height,
                seed
            ) VALUES (
                %s,
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
                    image.height,
                    image.seed,
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