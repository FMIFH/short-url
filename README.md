# Short URL Service

A high-performance, scalable URL shortening service built with FastAPI, featuring distributed caching with Redis Sentinel, persistent storage with Cassandra, and production-ready deployment options for both Docker Compose and Kubernetes.

## Features

- **URL Shortening**: Convert long URLs into short, shareable links using HashIDs
- **High Availability**: Redis Sentinel for automatic failover and high availability
- **Scalable Architecture**: Stateless application design with horizontal scaling support
- **Distributed Storage**: Cassandra for persistent, distributed URL mappings
- **Production Ready**: Load balancing with NGINX, health checks, and auto-scaling
- **Cloud Native**: Kubernetes deployment with HPA (Horizontal Pod Autoscaler)
- **Fast Redirects**: Permanent (301) redirects with minimal latency
- **CORS Enabled**: Ready for frontend integration

## Architecture

### Components

- **FastAPI Application**: Stateless REST API server
- **Redis Cluster**: Master-replica setup with 3 Sentinel nodes for HA
- **Cassandra**: Distributed NoSQL database for URL mappings
- **NGINX**: Reverse proxy and load balancer
- **Kubernetes**: Orchestration with auto-scaling capabilities

### How It Works

1. **URL Shortening**:
   - POST request to `/shorten` with original URL
   - Redis counter atomically incremented
   - Counter encoded using HashIDs with custom salt
   - Short code stored in Cassandra with original URL
   - Returns short URL: `{BASE_URL}/{short_code}`

2. **URL Redirection**:
   - GET request to `/{short_code}`
   - Query Cassandra for original URL
   - Return 301 permanent redirect to original URL
   - Return 404 if short code not found

3. **High Availability**:
   - Redis Sentinel monitors master and replicas
   - Automatic failover if master fails
   - Application reconnects to new master transparently
   - Cassandra provides distributed data persistence

## Prerequisites

### For Docker Compose
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### For Kubernetes
- Kubernetes cluster 1.24+
- kubectl configured
- Docker for building images
- 4GB RAM minimum across nodes
- 20GB disk space

## Quick Start

### Environment Configuration

Create a `.env` file in the root directory:

```env
# Redis Configuration
REDIS_HOST=redis-master
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password
REDIS_SENTINEL_HOSTS=redis-sentinel-1:26379,redis-sentinel-2:26379,redis-sentinel-3:26379
REDIS_MASTER_NAME=mymaster

# Cassandra Configuration
CASSANDRA_HOST=cassandra
CASSANDRA_PORT=9042
CASSANDRA_CLUSTER_NAME=short-url-cluster
CASSANDRA_DC=dc1
CASSANDRA_KEYSPACE=short_url

# Application Configuration
SALT=your_random_salt_string
URL=http://localhost
```

### Docker Compose Deployment

1. **Start the services**:
```bash
docker-compose up -d
```

2. **Verify services are running**:
```bash
docker-compose ps
```

3. **Check logs**:
```bash
docker-compose logs -f app
```

4. **Scale application instances**:
```bash
docker-compose up -d --scale app=5
```

The service will be available at `http://localhost`

### Kubernetes Deployment

1. **Build and tag the Docker image**:
```bash
docker build -t short-url-app:latest .
```

2. **Update configuration** (optional):
   - Edit `k8s/configmap.yaml` for non-sensitive config
   - Edit `k8s/secret.yaml` for sensitive data (base64 encoded)

3. **Deploy to Kubernetes**:
```bash
# Using PowerShell script
.\k8s\deploy.ps1

# Or using bash script
./k8s/deploy.sh

# Or manually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/cassandra.yaml
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

4. **Check deployment status**:
```bash
kubectl get pods -n short-url
kubectl get svc -n short-url
```

5. **Port forward for local testing**:
```bash
kubectl port-forward -n short-url svc/short-url-app 8000:8000
```

## API Usage

### Health Check

Check if the service is healthy:

```bash
curl -X GET http://localhost/health
```

**Response**: `204 No Content` (healthy) or `503 Service Unavailable`

### Shorten URL

Create a short URL:

```bash
curl -X POST http://localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"originalUrl": "https://www.example.com/very/long/url/path"}'
```

**Response**:
```json
{
  "short_url": "http://localhost/aBcD123"
}
```

### Redirect to Original URL

Access the short URL:

```bash
curl -L http://localhost/aBcD123
```

Returns a 301 redirect to the original URL.

## API Documentation

Once the service is running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost/docs`
- **ReDoc**: `http://localhost/redoc`

## Configuration Details

### Redis Sentinel

The service supports both direct Redis connection and Redis Sentinel for high availability:

- **3 Sentinel nodes**: Monitor master and replicas
- **Automatic failover**: Promotes replica to master on failure
- **Quorum**: 2 Sentinels must agree on failover
- **Down-after-milliseconds**: 5000ms (5 seconds)

### Cassandra

- **Keyspace**: `short_url` with SimpleStrategy
- **Replication factor**: 1 (increase for production)
- **Table**: `url_mappings` with short_code as primary key
- **Columns**: short_code, original_url, created_at

### NGINX Load Balancer

- **Algorithm**: Least connections
- **Max fails**: 3 attempts before marking backend down
- **Fail timeout**: 30 seconds
- **Keepalive**: 32 connections to backends
- **Health endpoint**: `/nginx-health`

### Kubernetes Auto-scaling

The HPA scales based on:
- **CPU utilization**: Target 70%
- **Min replicas**: 1
- **Max replicas**: 10

## Development

### Local Development Setup

1. **Install Poetry**:
```bash
pip install poetry
```

2. **Install dependencies**:
```bash
poetry install
```

3. **Start dependencies** (Redis and Cassandra):
```bash
docker-compose up redis-master cassandra -d
```

4. **Run the application**:
```bash
poetry run uvicorn src.main:app --reload --port 8000
```

### Running Tests

```bash
poetry run pytest
```

## Monitoring

### Check Redis Sentinel Status

```bash
docker exec short-url-redis-sentinel-1 redis-cli -p 26379 SENTINEL masters
docker exec short-url-redis-sentinel-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
```

### Check Cassandra Status

```bash
docker exec short-url-cassandra nodetool status
docker exec short-url-cassandra cqlsh -e "SELECT COUNT(*) FROM short_url.url_mappings;"
```

### Kubernetes Monitoring

```bash
# Get pod metrics
kubectl top pods -n short-url

# Check HPA status
kubectl get hpa -n short-url

# View application logs
kubectl logs -n short-url -l app=short-url-app --tail=100 -f
```

## Performance Considerations

- **HashIDs**: Deterministic short codes with custom alphabet (62 characters)
- **Redis Counter**: Atomic increments ensure unique IDs
- **301 Redirects**: Browsers cache permanent redirects
- **Connection Pooling**: Cassandra driver manages connection pool
- **NGINX Buffering**: Reduces backend load
- **Horizontal Scaling**: Add more app instances without code changes

## Troubleshooting

### Redis Connection Issues

```bash
# Check Redis master
docker exec short-url-redis-master redis-cli ping

# Check Sentinel
docker exec short-url-redis-sentinel-1 redis-cli -p 26379 ping
```

### Cassandra Connection Issues

```bash
# Check Cassandra logs
docker logs short-url-cassandra

# Test CQL connection
docker exec short-url-cassandra cqlsh -e "DESCRIBE KEYSPACES;"
```

### Application Not Starting

```bash
# Check application logs
docker-compose logs app

# Verify environment variables
docker-compose config
```

## Security

- Use strong `REDIS_PASSWORD` in production
- Keep `SALT` secret and unique
- Enable Cassandra authentication in production
- Use TLS/SSL for external connections
- Implement rate limiting for production
- Configure network policies in Kubernetes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

- **Python 3.13**: Modern Python with performance improvements
- **FastAPI**: High-performance async web framework
- **Redis 8.2**: In-memory cache with Sentinel support
- **Cassandra 5.0**: Distributed NoSQL database
- **NGINX**: High-performance load balancer
- **Docker**: Containerization
- **Kubernetes**: Container orchestration
- **HashIDs**: Short code generation
- **Pydantic**: Data validation and settings
- **Uvicorn**: ASGI server with multiple workers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue in the GitHub repository.