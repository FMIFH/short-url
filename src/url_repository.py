import logging
from datetime import datetime

from hashids import Hashids

from src.database import CassandraDB
from src.settings import app_settings

logger = logging.getLogger(__name__)


class URLRepository:
    def __init__(self, cassandra: CassandraDB):
        self.cassandra = cassandra
        self.hasher = Hashids(
            salt=app_settings.salt,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

    def create_short_url(self, original_url: str, counter: int) -> str:
        """Create a short URL and store the mapping"""
        logger.debug(f"Encoding counter {counter} to short code")
        short_code = self.hasher.encode(counter)
        short_url = f"{app_settings.url}/{short_code}"
        logger.debug(f"Generated short code: {short_code}")

        query = """
            INSERT INTO url_mappings (short_code, original_url, created_at)
            VALUES (?, ?, ?)
        """
        with self.cassandra.session_scope() as session:
            prepared = session.prepare(query)
            session.execute(prepared, (short_code, original_url, datetime.now()))

        logger.info(f"URL mapping stored: {short_code} -> {original_url}")
        return short_url

    def get_original_url(self, short_code: str) -> str | None:
        """Retrieve the original URL from a short code"""
        logger.debug(f"Retrieving original URL for short code: {short_code}")
        query = "SELECT original_url FROM url_mappings WHERE short_code = ?"
        with self.cassandra.session_scope() as session:
            prepared = session.prepare(query)
            result = session.execute(prepared, (short_code,))
            row = result.one()
            if row:
                logger.debug(f"Found original URL: {row.original_url}")
                return row.original_url
            else:
                logger.debug(f"No mapping found for short code: {short_code}")
                return None
