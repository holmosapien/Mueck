import os
import psycopg

from psycopg.rows import dict_row

from lib.models.mueck import (
    ImageRequest,
    ParsedImageRequest,
    RawImageRequest,
    ImageRequestFilter
)

class QueueStore:
    def __init__(self):
        self.dbh = self.connect()

    def connect(self) -> psycopg.connection:
        hostname = os.getenv("MUECK_DB_HOSTNAME")
        port = os.getenv("MUECK_DB_PORT")
        username = os.getenv("MUECK_DB_USERNAME")
        password = os.getenv("MUECK_DB_PASSWORD")
        database = os.getenv("MUECK_DB_DATABASE")

        connection_string = "host=%s port=%s user=%s password=%s dbname=%s" % (
            hostname,
            port,
            username,
            password,
            database
        )

        dbh = psycopg.connect(connection_string, row_factory=dict_row)

        return dbh

    def queue_request(self, request: ImageRequest) -> RawImageRequest:
        image_request = None

        with self.dbh.cursor() as cursor:
            query = """
                INSERT INTO
                    request_queue
                (
                    prompt,
                    user_id,
                    processed
                ) VALUES (
                    %s,
                    %s,
                    %s
                )
                RETURNING
                    id,
                    created
            """

            cursor.execute(query, (request.prompt, request.user_id, False))

            row = cursor.fetchone()

            request_id = row["id"]
            created = row["created"]

            image_request = RawImageRequest(
                request_id=request_id,
                prompt=request.prompt,
                processed=False,
                user_id=request.user_id,
                created=created
            )

        self.dbh.commit()

        return image_request

    def get_request(self, request_id) -> RawImageRequest | ParsedImageRequest:
        filters = ImageRequestFilter(request_ids=[request_id])
        requests = self.get_requests(filters=filters, include_processed=True)

        if len(requests) == 0:
            return None

        return requests[0]

    def get_requests(
        self,
        filters: ImageRequestFilter = None,
        include_processed=False
    ) -> list[RawImageRequest | ParsedImageRequest]:
        where = []
        values = []

        if filters is not None:
            if filters.request_ids:
                w = self.generate_placeholders("rq.id", filters.request_ids)

                where.append(w)
                values.extend(filters.request_ids)

            if filters.user_ids:
                w = self.generate_placeholders("rq.user_id", filters.user_ids)

                where.append(w)
                values.extend(filters.user_ids)

        if not include_processed:
            where.append("rq.processed = %s")
            values.append(False)

        if len(where) == 0:
            where.append("1 = 1")

        query = f"""
            SELECT
                rq.id AS request_id,
                rq.prompt AS raw_prompt,
                rp.prompt,
                rp.width,
                rp.height,
                rp.count,
                rq.processed,
                rq.user_id,
                rq.created
            FROM
                request_queue rq
            LEFT JOIN
                request_parameter rp
            ON
                rq.id = rp.request_id
            WHERE
                {" AND ".join(where)}
        """

        queue = []

        with self.dbh.cursor() as cursor:
            cursor.execute(query, values)

            for row in cursor:
                parsed_prompt = row["prompt"]

                if parsed_prompt:
                    request = ParsedImageRequest(
                        request_id=row["request_id"],
                        prompt=parsed_prompt,
                        width=row["width"],
                        height=row["height"],
                        count=row["count"],
                        processed=row["processed"],
                        user_id=row["user_id"],
                        created=row["created"]
                    )
                else:
                    request = RawImageRequest(
                        request_id=row["request_id"],
                        prompt=row["raw_prompt"],
                        processed=row["processed"],
                        user_id=row["user_id"],
                        created=row["created"]
                    )

                queue.append(request)

        return queue

    def add_request_parameters(self, parsed_request: ParsedImageRequest) -> ParsedImageRequest:
        with self.dbh.cursor() as cursor:
            query = """
                INSERT INTO
                    request_parameter
                (
                    request_id,
                    prompt,
                    width,
                    height,
                    count
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """

            cursor.execute(query, (
                parsed_request.request_id,
                parsed_request.prompt,
                parsed_request.width,
                parsed_request.height,
                parsed_request.count
            ))

        self.dbh.commit()

        return parsed_request

    def complete_request(self, request: ParsedImageRequest, filenames: list[str]):
        query = """
            INSERT INTO
                request_filename
            (
                request_id,
                filename
            ) VALUES (
                %s,
                %s
            )
        """

        with self.dbh.cursor() as cursor:
            request_id = request.request_id

            for filename in filenames:
                cursor.execute(query, (request_id, filename))

            query = """
                UPDATE
                    request_queue
                SET
                    processed = %s
                WHERE
                    id = %s
            """

            cursor.execute(query, (True, request_id))

        self.dbh.commit()

    def generate_placeholders(self, column, values) -> str:
        placeholders = ["%s" for _ in values]

        p = ", ".join(placeholders)

        where = f"{column} IN ({p})"

        return where