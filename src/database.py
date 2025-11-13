import logging
from contextlib import contextmanager

from cassandra.cluster import Cluster, Session

from src.settings import cassandra_settings

logger = logging.getLogger(__name__)


class CassandraDB:
    def __init__(self):
        self.cluster = None
        self.session = None

    def connect(self):
        """Establish connection to Cassandra cluster"""
        logger.info(f"Connecting to Cassandra cluster at {cassandra_settings.host}:{cassandra_settings.port}")
        self.cluster = Cluster(
            [cassandra_settings.host],
            port=cassandra_settings.port
        )
        self.session = self.cluster.connect()
        logger.info("Cassandra session established")
        self._create_keyspace()
        self.session.set_keyspace(cassandra_settings.keyspace)
        logger.info(f"Using keyspace: {cassandra_settings.keyspace}")
        self._create_tables()

    def get_session(self) -> Session:
        """Get the active Cassandra session"""
        if not self.session:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.session

    @contextmanager
    def session_scope(self):
        """Context manager for database session"""
        if not self.session:
            raise RuntimeError("Database not connected. Call connect() first.")

        yield self.session

    def _create_keyspace(self):
        """Create keyspace if it doesn't exist"""
        logger.info(f"Creating keyspace if not exists: {cassandra_settings.keyspace}")
        query = f"""
            CREATE KEYSPACE IF NOT EXISTS {cassandra_settings.keyspace}
            WITH replication = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """
        self.session.execute(query)
        logger.info("Keyspace ready")

    def _create_tables(self):
        """Create tables if they don't exist"""
        logger.info("Creating tables if not exist")
        # Table to store URL mappings
        query = """
            CREATE TABLE IF NOT EXISTS url_mappings (
                short_code TEXT PRIMARY KEY,
                original_url TEXT,
                created_at TIMESTAMP
            )
        """
        self.session.execute(query)
        logger.info("Tables ready")

    def close(self):
        """Close the connection"""
        if self.cluster:
            logger.info("Closing Cassandra cluster connection")
            self.cluster.shutdown()
            logger.info("Cassandra cluster connection closed")
