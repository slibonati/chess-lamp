# ArgoCD Setup Guide

This guide walks you through setting up ArgoCD for GitOps deployment of chess-lamp.

## Prerequisites

- Kubernetes cluster with kubectl access
- GitHub repository with chess-lamp code
- GitHub Actions enabled (for CI/CD)

## Step 1: Install ArgoCD

### Option A: Using the Installation Script (Recommended)

```bash
# From your k8s-control node or any machine with kubectl access
cd /path/to/chess-lamp
./deploy/install-argocd.sh
```

The script will:
- Create the `argocd` namespace
- Install ArgoCD components
- Wait for ArgoCD to be ready
- Display the initial admin password

### Option B: Manual Installation

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Step 2: Access ArgoCD UI

### Option 1: Port Forward (Recommended for Testing)

```bash
# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open in browser: https://localhost:8080
# Username: admin
# Password: (from Step 1)
```

### Option 2: Expose via NodePort

```bash
# Change service type to NodePort
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'

# Get the NodePort
kubectl get svc argocd-server -n argocd

# Access via: https://<node-ip>:<nodeport>
```

### Option 3: Expose via LoadBalancer (Cloud)

```bash
# Change service type to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get the LoadBalancer IP
kubectl get svc argocd-server -n argocd

# Access via: https://<loadbalancer-ip>
```

## Step 3: Install ArgoCD CLI (Optional but Recommended)

### Linux

```bash
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

### macOS

```bash
brew install argocd
```

### Verify Installation

```bash
argocd version --client
```

## Step 4: Login to ArgoCD

### Via CLI

```bash
# Get ArgoCD server address
ARGOCD_SERVER=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' || \
                kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || \
                echo "localhost:8080")

# Login (if using port-forward, use localhost:8080)
argocd login $ARGOCD_SERVER --insecure

# Or if using port-forward:
argocd login localhost:8080 --insecure
```

### Via UI

1. Open ArgoCD UI in browser
2. Username: `admin`
3. Password: (from Step 1)

## Step 5: Create ArgoCD Application

### Option A: Using kubectl (Recommended)

```bash
# Apply the ArgoCD Application manifest
kubectl apply -f argocd/application.yaml

# Verify application was created
kubectl get applications -n argocd

# Check application status
kubectl describe application chess-lamp -n argocd
```

### Option B: Using ArgoCD CLI

```bash
argocd app create chess-lamp \
  --repo https://github.com/slibonati/chess-lamp \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace chess-lamp \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### Option C: Using ArgoCD UI

1. Go to ArgoCD UI
2. Click **"New App"**
3. Fill in:
   - **Application Name**: `chess-lamp`
   - **Project Name**: `default`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: `https://github.com/slibonati/chess-lamp`
   - **Revision**: `main`
   - **Path**: `k8s`
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `chess-lamp`
4. Click **"Create"**

## Step 6: Verify Deployment

### Check ArgoCD Application Status

```bash
# Via CLI
argocd app get chess-lamp

# Via kubectl
kubectl get application chess-lamp -n argocd -o yaml

# Check sync status
kubectl get application chess-lamp -n argocd -o jsonpath='{.status.sync.status}'
```

### Check Kubernetes Resources

```bash
# Check if namespace was created
kubectl get namespace chess-lamp

# Check deployment
kubectl get deployment -n chess-lamp

# Check pods
kubectl get pods -n chess-lamp

# Check service
kubectl get svc -n chess-lamp
```

### View in ArgoCD UI

1. Go to ArgoCD UI
2. Click on `chess-lamp` application
3. You should see:
   - **Sync Status**: Synced
   - **Health Status**: Healthy
   - All resources (Namespace, Deployment, Service, etc.)

## Step 7: Configure Secrets (If Needed)

If you need to set secrets for the application:

```bash
# Create or update secrets
kubectl create secret generic chess-lamp-secrets \
  --from-literal=lichess_token='YOUR_TOKEN' \
  --from-literal=govee_api_key='YOUR_KEY' \
  --from-literal=govee_device_mac='YOUR_MAC' \
  --from-literal=govee_device_ip='YOUR_IP' \
  -n chess-lamp \
  --dry-run=client -o yaml | kubectl apply -f -
```

Or edit the ConfigMap if you prefer:

```bash
kubectl edit configmap chess-lamp-config -n chess-lamp
```

## Step 8: Test the GitOps Workflow

### Trigger a Deployment

1. Make a small change to the code (e.g., update a comment)
2. Push to `main` branch
3. GitHub Actions will:
   - Build and push new image to GHCR
   - Update `k8s/chess-lamp-deployment.yaml` with new image tag
   - Commit and push the change to Git
4. ArgoCD will:
   - Detect the Git change (within sync interval, default 3 minutes)
   - Sync the new image tag to Kubernetes
   - Rollout the new deployment

### Monitor the Deployment

```bash
# Watch ArgoCD application
argocd app watch chess-lamp

# Or check status
argocd app get chess-lamp

# Watch Kubernetes pods
kubectl get pods -n chess-lamp -w

# Check rollout status
kubectl rollout status deployment/chess-lamp -n chess-lamp
```

## Step 9: (Optional) Remove Polling Script

If you were using a polling script before, you can now remove it:

```bash
# Remove cron job
crontab -e
# Delete the line with poll-update.sh

# Or remove the script
rm /path/to/poll-update.sh
```

## Troubleshooting

### ArgoCD Application Not Syncing

```bash
# Check application status
kubectl get application chess-lamp -n argocd -o yaml

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=50

# Force sync
argocd app sync chess-lamp
```

### Image Pull Errors

```bash
# Check if image exists
docker pull ghcr.io/slibonati/chess-lamp:main-<sha>

# Check image pull secrets
kubectl get secrets -n chess-lamp

# If using private GHCR, create image pull secret:
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PAT \
  -n chess-lamp
```

### Pod Not Starting

```bash
# Check pod logs
kubectl logs -n chess-lamp -l app=chess-lamp

# Check pod events
kubectl describe pod -n chess-lamp -l app=chess-lamp

# Check deployment
kubectl describe deployment chess-lamp -n chess-lamp
```

### ArgoCD Can't Access Git Repository

If your repository is private, you need to configure Git credentials:

```bash
# Create Git secret
kubectl create secret generic github-repo-secret \
  --from-literal=type=git \
  --from-literal=url=https://github.com/slibonati/chess-lamp \
  --from-literal=password=YOUR_GITHUB_TOKEN \
  -n argocd

# Update application to use secret
# Edit argocd/application.yaml and add:
# source:
#   repoURL: ...
#   path: k8s
#   passwordRef:
#     secretName: github-repo-secret
#     key: password
```

## Useful Commands

### ArgoCD CLI

```bash
# List applications
argocd app list

# Get application details
argocd app get chess-lamp

# Sync application
argocd app sync chess-lamp

# Delete application
argocd app delete chess-lamp

# Watch application
argocd app watch chess-lamp
```

### kubectl

```bash
# Get ArgoCD applications
kubectl get applications -n argocd

# Describe application
kubectl describe application chess-lamp -n argocd

# Get application logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

## Next Steps

1. ✅ ArgoCD is installed and running
2. ✅ Application is created and syncing
3. ✅ Test the GitOps workflow
4. 🔄 Monitor deployments via ArgoCD UI
5. 📚 Learn more: https://argo-cd.readthedocs.io/

## Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [GitOps Principles](https://www.gitops.tech/)
