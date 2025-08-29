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
            f"dbname={database_name} " +
            f"user={database_user} " +
            f"password={database_password} " +
            f"host={database_host} " +
            f"port={database_port}"
        )

        if tls_ca and tls_certificate and tls_private_key:
            connection_params += (
                f" sslmode=require" +
                f" sslrootcert={tls_ca}" +
                f" sslcert={tls_certificate}" +
                f" sslkey={tls_private_key}"
            )

        self.pool = ConnectionPool(conninfo=connection_params)