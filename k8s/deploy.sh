#!/bin/bash

# Kubernetes Deployment Script for Short-URL Service
set -e

echo "🚀 Deploying Short-URL to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -t short-url-app:latest .

# For local development (minikube/kind), load image
if kubectl config current-context | grep -q "minikube"; then
    echo "🔄 Loading image into minikube..."
    minikube image load short-url-app:latest
elif kubectl config current-context | grep -q "kind"; then
    echo "🔄 Loading image into kind..."
    kind load docker-image short-url-app:latest
fi

# Apply Kubernetes manifests in order
echo "📝 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "⚙️  Creating ConfigMap and Secret..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

echo "💾 Deploying Cassandra..."
kubectl apply -f k8s/cassandra.yaml

echo "🔴 Deploying Redis (Master, Replicas, Sentinels)..."
kubectl apply -f k8s/redis.yaml

echo "🌐 Deploying Application..."
kubectl apply -f k8s/app-deployment.yaml

echo "📊 Creating HorizontalPodAutoscaler..."
kubectl apply -f k8s/hpa.yaml

echo "🌍 Creating Ingress..."
kubectl apply -f k8s/ingress.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Check status with:"
echo "   kubectl get pods -n short-url"
echo "   kubectl get hpa -n short-url"
echo ""
echo "📈 Watch HPA in action:"
echo "   kubectl get hpa -n short-url --watch"
echo ""
echo "🔍 View logs:"
echo "   kubectl logs -n short-url -l app=short-url-app -f"
echo ""
echo "⚠️  Note: Wait for Cassandra to be ready (60-90 seconds) before app pods start"
