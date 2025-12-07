# ArgoCD Quick Start

Get ArgoCD up and running in 5 minutes!

## Prerequisites

- Kubernetes cluster with kubectl access
- GitHub repository with chess-lamp code

## Installation (3 Steps)

### 1. Install ArgoCD

```bash
./deploy/install-argocd.sh
```

Save the admin password that's displayed!

### 2. Access ArgoCD UI

```bash
# Port forward (in a separate terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser: https://localhost:8080
# Login: admin / <password-from-step-1>
```

### 3. Create Application

```bash
kubectl apply -f argocd/application.yaml
```

## Verify It Works

```bash
# Check application status
kubectl get applications -n argocd

# Check if pods are running
kubectl get pods -n chess-lamp

# View in ArgoCD UI
# Go to https://localhost:8080 and click on "chess-lamp"
```

## Test the Workflow

1. Make a small code change
2. Push to `main` branch
3. Watch GitHub Actions build and push image
4. ArgoCD will automatically sync within 3 minutes (or instantly with webhook)

## That's It! 🎉

Your deployment is now GitOps-enabled. Every code push will:
- Build and push image to GHCR
- Update Git with new image tag
- ArgoCD automatically syncs to Kubernetes

## Need Help?

- Full setup guide: `deploy/ARGOCD_SETUP.md`
- Migration details: `ARGOCD_MIGRATION.md`
- Approach explanation: `ARGOCD_APPROACH.md`
