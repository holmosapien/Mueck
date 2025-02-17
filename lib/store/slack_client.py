from typing import Optional

from lib.context import MueckContext
from lib.models.slack_client import SlackClientRecord

class SlackClientStore:
    def __init__(self, context: MueckContext):
        self.context = context

    def get_slack_client_by_id(self, slack_client_id: int) -> Optional[SlackClientRecord]:
        query = """
            SELECT
                id,
                api_client_id,
                api_client_secret,
                signing_secret,
                name,
                created
            FROM
                slack_client
            WHERE
                id = %s
        """

        slack_client_record = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (slack_client_id,))

                for row in cursor:
                    slack_client_record = SlackClientRecord(
                        id=row[0],
                        api_client_id=row[1],
                        api_client_secret=row[2],
                        signing_secret=row[3],
                        name=row[4],
                        created=row[5]
                    )

        return slack_client_record

    def get_slack_client_by_authorization_state(self, state_id: int, account_id: int, slack_client_id: int) -> Optional[SlackClientRecord]:
        query = """
            SELECT
                c.id,
                c.api_client_id,
                c.api_client_secret,
                c.signing_secret,
                c.name,
                c.created
            FROM
                slack_oauth_state os
            JOIN
                slack_client c ON os.slack_client_id = c.id
            WHERE
                os.id = %s AND
                os.account_id = %s AND
                os.slack_client_id = %s AND
                os.redeemed IS NULL
            ORDER BY
                os.created DESC
            LIMIT
                1
        """

        slack_client_record = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (state_id, account_id, slack_client_id,))

                for row in cursor:
                    slack_client_record = SlackClientRecord(
                        id=row[0],
                        api_client_id=row[1],
                        api_client_secret=row[2],
                        signing_secret=row[3],
                        name=row[4],
                        created=row[5]
                    )

        return slack_client_record