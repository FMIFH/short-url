# Kubernetes Deployment Script for Short-URL Service

Write-Host "🚀 Deploying Short-URL to Kubernetes..." -ForegroundColor Green

# Check if kubectl is available
if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ kubectl not found. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# Check if NGINX Ingress Controller is installed
Write-Host "🔍 Checking for NGINX Ingress Controller..." -ForegroundColor Yellow
$ingressController = kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller 2>$null
if (!$ingressController) {
    Write-Host "📦 Installing NGINX Ingress Controller..." -ForegroundColor Yellow
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
    Write-Host "⏳ Waiting for Ingress Controller to be ready..." -ForegroundColor Yellow
    kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s
    Write-Host "✅ NGINX Ingress Controller installed" -ForegroundColor Green
} else {
    Write-Host "✅ NGINX Ingress Controller already installed" -ForegroundColor Green
}

# Check if Metrics Server is installed
Write-Host "🔍 Checking for Metrics Server..." -ForegroundColor Yellow
$metricsServer = kubectl get deployment metrics-server -n kube-system 2>$null
if (!$metricsServer) {
    Write-Host "📦 Installing Metrics Server..." -ForegroundColor Yellow
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    # Patch for Docker Desktop
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
    Write-Host "✅ Metrics Server installed" -ForegroundColor Green
} else {
    Write-Host "✅ Metrics Server already installed" -ForegroundColor Green
}

# Build Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -t short-url-app:latest .

# Docker Desktop uses images from local Docker daemon automatically
$context = kubectl config current-context
Write-Host "🔍 Using Kubernetes context: $context" -ForegroundColor Cyan

# Apply Kubernetes manifests in order
Write-Host "📝 Creating namespace..." -ForegroundColor Yellow
kubectl apply -f k8s/namespace.yaml

Write-Host "⚙️  Creating ConfigMap and Secret..." -ForegroundColor Yellow
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

Write-Host "💾 Deploying Cassandra..." -ForegroundColor Yellow
kubectl apply -f k8s/cassandra.yaml

Write-Host "🔴 Deploying Redis (Master, Replicas, Sentinels)..." -ForegroundColor Yellow
kubectl apply -f k8s/redis.yaml

Write-Host "🌐 Deploying Application..." -ForegroundColor Yellow
kubectl apply -f k8s/app-deployment.yaml

Write-Host "📊 Creating HorizontalPodAutoscaler..." -ForegroundColor Yellow
kubectl apply -f k8s/hpa.yaml

Write-Host "🌍 Creating Ingress..." -ForegroundColor Yellow
kubectl apply -f k8s/ingress.yaml

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Check status with:" -ForegroundColor Cyan
Write-Host "   kubectl get pods -n short-url"
Write-Host "   kubectl get hpa -n short-url"
Write-Host ""
Write-Host "📈 Watch HPA in action:" -ForegroundColor Cyan
Write-Host "   kubectl get hpa -n short-url --watch"
Write-Host ""
Write-Host "🔍 View logs:" -ForegroundColor Cyan
Write-Host "   kubectl logs -n short-url -l app=short-url-app -f"
Write-Host ""
Write-Host "⚠️  Note: Wait for Cassandra to be ready (60-90 seconds) before app pods start" -ForegroundColor Yellow
