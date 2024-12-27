import os

from lib.database import DatabasePool
from lib.logging import setup_logger

class MueckContext:
    def __init__(self):
        self.dbh = DatabasePool()
        self.logger = setup_logger()

        self.listener_hostname = os.getenv("MUECK_LISTENER_HOSTNAME")
        self.tensorart_endpoint = os.getenv("TENSORART_ENDPOINT")
        self.tensorart_api_key = os.getenv("TENSORART_API_KEY")
        self.download_path = os.getenv("MUECK_DOWNLOAD_PATH")