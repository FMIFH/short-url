import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", validate_by_alias=True
    )

    # For direct connection (backwards compatible)
    host: str = Field("redis-master", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    password: str | None = Field(None, alias="REDIS_PASSWORD")

    # For Sentinel configuration
    sentinel_hosts: str | None = Field(None, alias="REDIS_SENTINEL_HOSTS")  # Comma-separated host:port
    master_name: str = Field("mymaster", alias="REDIS_MASTER_NAME")

class CassandraSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", validate_by_alias=True
    )

    host: str = Field(..., alias="CASSANDRA_HOST")
    port: int = Field(9042, alias="CASSANDRA_PORT")
    cluster_name: str = Field(..., alias="CASSANDRA_CLUSTER_NAME")
    datacenter: str = Field(..., alias="CASSANDRA_DC")
    keyspace: str = Field(..., alias="CASSANDRA_KEYSPACE")

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", validate_by_alias=True
    )

    salt: str = Field(..., alias="SALT")
    url : str = Field(..., alias="URL")

app_settings = AppSettings()
redis_settings = RedisSettings()
cassandra_settings = CassandraSettings()