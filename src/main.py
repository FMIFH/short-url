import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from redis import Redis
from redis.sentinel import Sentinel

from src.database import CassandraDB
from src.models import ShortenURLRequest
from src.settings import redis_settings, setup_logging
from src.url_repository import URLRepository

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application initialization...")

    # Initialize Redis (with Sentinel support if configured)
    if redis_settings.sentinel_hosts:
        logger.info(f"Connecting to Redis via Sentinel: {redis_settings.sentinel_hosts}")
        sentinel_nodes = [
            tuple(host.split(':')) if ':' in host else (host, 26379)
            for host in redis_settings.sentinel_hosts.split(',')
        ]
        # Convert port strings to integers
        sentinel_nodes = [(host, int(port)) for host, port in sentinel_nodes]

        sentinel = Sentinel(
            sentinel_nodes,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            password=redis_settings.password,
            sentinel_kwargs={'socket_connect_timeout': 2.0}
        )
        # master_for returns a Redis client that automatically reconnects to new master after failover
        app.state.redis = sentinel.master_for(
            redis_settings.master_name,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            password=redis_settings.password,
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError]
        )
        logger.info(f"Connected to Redis master via Sentinel: {redis_settings.master_name}")
    else:
        logger.info(f"Connecting to Redis at {redis_settings.host}:{redis_settings.port}")
        app.state.redis = Redis(
            host=redis_settings.host,
            port=redis_settings.port,
            password=redis_settings.password,
        )

    app.state.redis.set("counter", 14000000, nx=True)

    # Initialize Cassandra
    logger.info("Initializing Cassandra connection...")
    app.state.cassandra = CassandraDB()
    app.state.cassandra.connect()
    logger.info("Cassandra connection established")

    # Initialize URL Repository
    app.state.url_repository = URLRepository(app.state.cassandra)
    logger.info("Application initialization completed successfully")

    yield

    logger.info("Shutting down application...")
    app.state.redis.close()
    logger.info("Redis connection closed")
    app.state.cassandra.close()
    logger.info("Cassandra connection closed")
    logger.info("Application shutdown completed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection functions
def get_redis() -> Redis:
    return app.state.redis


def get_url_repository() -> URLRepository:
    return app.state.url_repository


@app.get(
    "/health",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "API is healthy"},
        503: {"description": "Service unavailable"}
    },
    tags=["Health Check"],
)
async def health(
    redis: Redis = Depends(get_redis),
    url_repository: URLRepository = Depends(get_url_repository),
):
    """
    Health check endpoint that verifies connectivity to Redis and Cassandra.
    Returns 204 if healthy, 503 if any dependency is unavailable.
    """
    logger.debug("Health check endpoint called")
    try:
        # Verify Redis connectivity
        redis.ping()
        logger.debug("Redis health check passed")

        # Verify Cassandra connectivity
        url_repository.cassandra.get_session().execute("SELECT now() FROM system.local")
        logger.debug("Cassandra health check passed")

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@app.post("/shorten")
async def shorten_url(
    request: ShortenURLRequest,
    redis: Redis = Depends(get_redis),
    url_repository: URLRepository = Depends(get_url_repository),
):
    logger.info(f"Shortening URL: {request.original_url}")
    counter = redis.incr("counter")
    logger.debug(f"Counter incremented to: {counter}")
    short_url = url_repository.create_short_url(request.original_url, counter)
    logger.info(f"Created short URL: {short_url}")
    return {"short_url": short_url}


@app.get("/{short_code}")
async def redirect_url(
    short_code: str, url_repository: URLRepository = Depends(get_url_repository)
):
    logger.info(f"Redirect request for short code: {short_code}")
    original_url = url_repository.get_original_url(short_code)
    if not original_url:
        logger.warning(f"Short code not found: {short_code}")
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    logger.info(f"Redirecting to: {original_url}")
    return RedirectResponse(
        url=original_url, status_code=status.HTTP_301_MOVED_PERMANENTLY
    )
