import json

from typing import Optional

from lib.context import MueckContext

from lib.generators.base import ImageGenerator
from lib.models.slack_event import SlackEventRecord
from lib.models.generated_image import GeneratedImage, ImageGenerationRequest, ImageGenerationRequestUpdate

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
                se.id,
                se.slack_integration_id,
                se.event,
                se.channel,
                se.request_ts,
                se.thread_ts,
                ir.id AS image_generation_request_id,
                se.created,
                se.processed
            FROM
                slack_event se
            LEFT JOIN
                image_generation_request ir
            ON
                se.id = ir.slack_event_id
            WHERE
                se.processed IS NULL
            ORDER BY
                se.created ASC
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
                        image_generation_request_id=row[6],
                        created=row[7],
                        processed=row[8],
                    )

        return slack_event_record

    def get_image_generation_request(self, image_generation_request_id: int) -> ImageGenerationRequest:
        query = """
            SELECT
                model_vendor,
                job_id,
                token
            FROM
                image_generation_request
            WHERE
                id = %s
        """

        image_generation_request = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (image_generation_request_id,))

                for row in cursor:
                    image_generation_request = ImageGenerationRequest(
                        id=image_generation_request_id,
                        model_vendor=row[0],
                        job_id=row[1],
                        token=row[2],
                    )

        if not image_generation_request:
            raise ValueError(f"Failed to retrieve image_generation_request_id={image_generation_request_id}.")

        return image_generation_request

    def save_image_generation_request(self, slack_event_id: int, image_generator: ImageGenerator) -> int:
        query = """
            INSERT INTO
                image_generation_request
            (
                slack_event_id,
                model_vendor,
                prompt,
                job_id,
                token,
                status,
                credits
            ) VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id
        """

        image_generation_request_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    slack_event_id,
                    image_generator.model_vendor,
                    image_generator.prompt,
                    image_generator.id,
                    image_generator.token,
                    image_generator.status,
                    image_generator.credits
                ))

                for row in cursor:
                    image_generation_request_id = row[0]

        if not image_generation_request_id:
            raise ValueError("Failed to save image generation request.")

        return image_generation_request_id

    def update_image_generation_request(self, image_generation_request_id: int, update: ImageGenerationRequestUpdate):
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

        values.append(image_generation_request_id)

        query = f"""
            UPDATE
                image_generation_request
            SET
                {', '.join(updates)}
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)

    def save_generated_image(self, image_generation_request_id: int, image: GeneratedImage):
        query = """
            INSERT INTO
                generated_image
            (
                image_generation_request_id,
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
                    image_generation_request_id,
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