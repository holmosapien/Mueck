from typing import Optional

from lib.context import MueckContext
from lib.models.slack_integration import SlackIntegrationFilter, SlackIntegrationRecord

class SlackIntegrationStore:
    def __init__(self, context: MueckContext):
        self.context = context

    def save_slack_integration(self, record: SlackIntegrationRecord) -> int:
        query = """
            INSERT INTO
                slack_integration
            (
                account_id,
                slack_client_id,
                team_id,
                team_name,
                bot_user_id,
                app_id,
                access_token
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

        values = [
            record.account_id,
            record.slack_client_id,
            record.team_id,
            record.team_name,
            record.bot_user_id,
            record.app_id,
            record.access_token
        ]

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)

                integration_id = None

                for row in cursor:
                    integration_id = row[0]

        return integration_id

    def get_slack_integration(self, integration_filter: SlackIntegrationFilter) -> Optional[SlackIntegrationRecord]:
        where = []
        values = []

        if integration_filter.slack_integration_id:
            where.append(f"id = %s")
            values.append(integration_filter.slack_integration_id)

        if integration_filter.app_id:
            where.append(f"app_id = %s")
            values.append(integration_filter.app_id)

        query = f"""
            SELECT
                id,
                account_id,
                slack_client_id,
                team_id,
                team_name,
                bot_user_id,
                app_id,
                access_token,
                created
            FROM
                slack_integration
            WHERE
                {" AND ".join(where)}
        """

        slack_integration_record = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)

                for row in cursor:
                    slack_integration_id = row[0]
                    account_id = row[1]
                    slack_client_id = row[2]
                    team_id = row[3]
                    team_name = row[4]
                    bot_user_id = row[5]
                    app_id = row[6]
                    access_token = row[7]
                    created = row[8]

                    slack_integration_record = SlackIntegrationRecord(
                        id=slack_integration_id,
                        account_id=account_id,
                        slack_client_id=slack_client_id,
                        team_id=team_id,
                        team_name=team_name,
                        bot_user_id=bot_user_id,
                        app_id=app_id,
                        access_token=access_token,
                        created=created
                    )

        return slack_integration_record