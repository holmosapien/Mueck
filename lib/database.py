import os

from psycopg import Cursor
from psycopg_pool import ConnectionPool

class DatabasePool:
    def __init__(self):
        database_name = os.getenv("MUECK_DB_DATABASE")
        database_user = os.getenv("MUECK_DB_USERNAME")
        database_password = os.getenv("MUECK_DB_PASSWORD")
        database_host = os.getenv("MUECK_DB_HOSTNAME")
        database_port = os.getenv("MUECK_DB_PORT")

        tls_ca = os.getenv("MUECK_DB_CA")
        tls_certificate = os.getenv("MUECK_DB_CERTIFICATE")
        tls_private_key = os.getenv("MUECK_DB_PRIVATE_KEY")

        connection_params = (
            f"dbname={database_name} user={database_user} password={database_password} " +
            f"host={database_host} port={database_port} sslmode=require " +
            f"sslrootcert={tls_ca} sslcert={tls_certificate} sslkey={tls_private_key}"
        )

        self.pool = ConnectionPool(conninfo=connection_params)