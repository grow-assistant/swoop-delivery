# Golf Course Delivery System - Deployment Guide

This guide provides comprehensive instructions for deploying the Golf Course Delivery System, which is based on DoorDash's DeepRed dispatch algorithm adapted for golf course food and beverage deliveries.

## System Overview

The system consists of:
- **FastAPI Backend**: RESTful API with WebSocket support for real-time tracking
- **PostgreSQL Database**: Persistent storage for orders, assets, and metrics
- **Redis**: Caching and background task queue
- **Celery**: Background task processing
- **Docker**: Containerization for consistent deployments
- **Kubernetes**: Orchestration for production deployment
- **Prometheus/Grafana**: Monitoring and visualization

## Prerequisites

- Docker and Docker Compose installed
- Kubernetes cluster (for production)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd golf-course-delivery
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)

## Production Deployment

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t golf-delivery-api:latest .

# Tag for your registry
docker tag golf-delivery-api:latest your-registry/golf-delivery-api:latest

# Push to registry
docker push your-registry/golf-delivery-api:latest
```

### 2. Configure Kubernetes Secrets

Create a `k8s/secrets.yaml` file:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: golf-delivery-secrets
  namespace: golf-delivery
type: Opaque
stringData:
  database-url: "postgresql://user:pass@postgres-host:5432/golf_delivery"
  redis-url: "redis://redis-host:6379"
  sentry-dsn: "https://your-sentry-dsn"
  secret-key: "your-secret-key"
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Set up ingress
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n golf-delivery
kubectl logs -f deployment/golf-delivery-api -n golf-delivery
```

### 4. Database Migrations

```bash
# Run migrations in a Kubernetes job
kubectl run --rm -it migration-job \
  --image=your-registry/golf-delivery-api:latest \
  --env="DATABASE_URL=<your-database-url>" \
  --command -- alembic upgrade head
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automates:

1. **Testing**: Runs unit tests and linting
2. **Building**: Creates and pushes Docker images
3. **Deployment**: Deploys to Kubernetes on merge to main

### Setup GitHub Secrets

Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DOCKER_REGISTRY_USERNAME`
- `DOCKER_REGISTRY_PASSWORD`

## Monitoring and Observability

### Prometheus Metrics

The application exposes metrics at `/metrics`:
- Request count and latency
- Order processing metrics
- Asset utilization
- System health

### Grafana Dashboards

Import the provided dashboards from `monitoring/grafana/dashboards/`:
- System Overview
- Order Processing
- Asset Performance
- API Performance

### Logging

Logs are structured JSON format and can be aggregated using:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- CloudWatch Logs (AWS)
- Stackdriver (GCP)

## API Endpoints

### Orders
- `POST /api/orders` - Create new order
- `GET /api/orders` - List all orders
- `GET /api/orders/{order_id}` - Get specific order
- `POST /api/orders/{order_id}/dispatch` - Dispatch order to asset
- `POST /api/orders/{order_id}/complete` - Mark order as completed

### Assets
- `GET /api/assets` - List all delivery assets
- `GET /api/assets/{asset_id}` - Get specific asset
- `POST /api/assets/{asset_id}/location` - Update asset location
- `POST /api/assets/{asset_id}/status` - Update asset status

### WebSocket
- `ws://localhost:8000/ws` - Real-time updates for orders and assets

## Scaling Considerations

1. **Horizontal Scaling**: Increase API replicas in Kubernetes
2. **Database Connection Pooling**: Configure connection limits
3. **Redis Clustering**: For high-throughput environments
4. **Load Balancing**: Use Kubernetes service mesh (Istio)
5. **CDN**: For static assets and API caching

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   kubectl logs -f deployment/golf-delivery-api -n golf-delivery
   # Check DATABASE_URL in secrets
   ```

2. **Redis Connection Issues**
   ```bash
   kubectl exec -it deployment/golf-delivery-api -n golf-delivery -- redis-cli ping
   ```

3. **Pod Crashes**
   ```bash
   kubectl describe pod <pod-name> -n golf-delivery
   kubectl logs <pod-name> -n golf-delivery --previous
   ```

### Health Checks

- Liveness: `GET /`
- Readiness: `GET /`
- Metrics: `GET /metrics`

## Backup and Recovery

### Database Backups

```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql $DATABASE_URL < backup_20240120_120000.sql
```

### Disaster Recovery

1. Regular automated backups to S3
2. Multi-region database replication
3. Point-in-time recovery enabled
4. Regular disaster recovery drills

## Security Considerations

1. **API Authentication**: Implement JWT tokens
2. **HTTPS Only**: Enforce SSL/TLS
3. **Network Policies**: Restrict pod-to-pod communication
4. **Secrets Management**: Use Kubernetes secrets or AWS Secrets Manager
5. **Regular Updates**: Keep dependencies updated

## Performance Optimization

1. **Database Indexing**: Add indexes for frequently queried fields
2. **Caching Strategy**: Use Redis for hot data
3. **Query Optimization**: Monitor slow queries
4. **Connection Pooling**: Configure optimal pool sizes
5. **Load Testing**: Regular performance testing with k6 or Locust

## Support

For issues or questions:
1. Check the logs first
2. Review this documentation
3. Check GitHub Issues
4. Contact the development team

Remember to always test changes in staging before deploying to production!