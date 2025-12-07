#!/bin/bash
# ArgoCD Installation Script
# This script installs ArgoCD on your Kubernetes cluster

set -e

echo "🚀 Installing ArgoCD on Kubernetes cluster..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "   Please ensure kubectl is configured correctly"
    exit 1
fi

echo "✅ Kubernetes cluster connection verified"

# Create ArgoCD namespace
echo ""
echo "📦 Creating ArgoCD namespace..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
echo ""
echo "📥 Installing ArgoCD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo ""
echo "⏳ Waiting for ArgoCD to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s || {
    echo "⚠️  ArgoCD server pod not ready after 5 minutes"
    echo "   Checking pod status..."
    kubectl get pods -n argocd
    exit 1
}

echo ""
echo "✅ ArgoCD installation complete!"

# Get initial admin password
echo ""
echo "🔐 Retrieving initial admin password..."
INITIAL_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d 2>/dev/null || echo "")

if [ -z "$INITIAL_PASSWORD" ]; then
    echo "⚠️  Could not retrieve initial admin password (may need to wait a bit longer)"
    echo "   You can retrieve it later with:"
    echo "   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ArgoCD Admin Credentials"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Username: admin"
    echo "  Password: $INITIAL_PASSWORD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "⚠️  IMPORTANT: Save this password! You'll need it to log in to ArgoCD UI."
    echo ""
fi

# Check if ArgoCD server is accessible
echo "🌐 Checking ArgoCD server access..."
ARGOCD_SERVER=$(kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || \
                kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || \
                echo "")

if [ -n "$ARGOCD_SERVER" ]; then
    echo "✅ ArgoCD server is accessible at: https://$ARGOCD_SERVER"
else
    echo ""
    echo "📋 To access ArgoCD UI, you can:"
    echo ""
    echo "   Option 1: Port forward (recommended for testing)"
    echo "   kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo "   Then open: https://localhost:8080"
    echo ""
    echo "   Option 2: Expose via NodePort or LoadBalancer"
    echo "   kubectl patch svc argocd-server -n argocd -p '{\"spec\": {\"type\": \"NodePort\"}}'"
    echo ""
fi

# Install ArgoCD CLI (optional)
echo ""
echo "💡 Optional: Install ArgoCD CLI for command-line access"
echo "   Linux:"
echo "   curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64"
echo "   chmod +x /usr/local/bin/argocd"
echo ""
echo "   macOS:"
echo "   brew install argocd"
echo ""

echo "✅ ArgoCD installation script completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Access ArgoCD UI (see instructions above)"
echo "   2. Apply the ArgoCD Application manifest:"
echo "      kubectl apply -f argocd/application.yaml"
echo "   3. Or use ArgoCD CLI to create the application"
echo ""
