from lib.context import MueckContext

class SlackAuthorizationStore:
    def __init__(self, context: MueckContext):
        self.context = context

    def save_slack_oauth_state(self, account_id: str, slack_client_id: str) -> int:
        query = """
            INSERT INTO
                slack_oauth_state
            (
                account_id,
                slack_client_id
            ) VALUES (
                %s,
                %s
            )
            RETURNING
                id
        """

        state_id = None

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (account_id, slack_client_id))

                for row in cursor:
                    state_id = row[0]

        return state_id

    def redeem_authorization_state(self, state_id: int):
        query = """
            UPDATE
                slack_oauth_state
            SET
                redeemed = NOW()
            WHERE
                id = %s
        """

        with self.context.dbh.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (state_id,))