# ArgoCD Migration Summary

This document summarizes the changes made to migrate from polling-based deployment to ArgoCD GitOps.

## What Changed

### 1. New Files Created

- **`deploy/install-argocd.sh`** - ArgoCD installation script
- **`argocd/application.yaml`** - ArgoCD Application definition
- **`k8s/chess-lamp-deployment.yaml`** - Kubernetes manifests (moved from `.github/k8s/`)
- **`deploy/ARGOCD_SETUP.md`** - Setup guide
- **`ARGOCD_MIGRATION.md`** - This file

### 2. Updated Files

- **`.github/workflows/k8s-deploy.yml`** - Now updates Git with image tags
  - Added step to update `k8s/chess-lamp-deployment.yaml` with new image tag
  - Added step to commit and push changes to Git
  - Changed permissions to include `contents: write`

### 3. Deployment Flow Change

**Before (Polling-based):**
```
GitHub Actions → GHCR → Polling Script → kubectl apply
```

**After (GitOps with ArgoCD):**
```
GitHub Actions → GHCR → Update Git → ArgoCD detects → Auto-sync to K8s
```

## Migration Steps

### Step 1: Install ArgoCD

```bash
./deploy/install-argocd.sh
```

### Step 2: Create ArgoCD Application

```bash
kubectl apply -f argocd/application.yaml
```

### Step 3: Verify Setup

```bash
# Check ArgoCD application
kubectl get applications -n argocd

# Check if it synced
argocd app get chess-lamp
```

### Step 4: Test the Workflow

1. Make a code change
2. Push to `main` branch
3. Watch GitHub Actions workflow
4. Verify ArgoCD syncs the new image

### Step 5: (Optional) Remove Polling Script

If you were using a polling script:

```bash
# Remove from crontab
crontab -e
# Delete the polling script entry
```

## Key Differences

| Aspect | Before | After |
|--------|--------|-------|
| **Image Detection** | Polling script checks GHCR | GitHub Actions updates Git |
| **Deployment Trigger** | Manual or cron-based | Automatic (Git push) |
| **Source of Truth** | Cluster state | Git repository |
| **Rollback** | Manual kubectl | Git revert + auto-sync |
| **Visibility** | kubectl commands | ArgoCD UI dashboard |
| **Change Detection** | Polling delay (5+ min) | Webhook-based (instant) |
| **Drift Detection** | Manual checks | Automatic (self-heal) |

## Configuration

### Image Tag Format

The workflow now uses commit SHA-based tags:
- Format: `ghcr.io/slibonati/chess-lamp:main-<commit-sha>`
- Example: `ghcr.io/slibonati/chess-lamp:main-abc1234`

### Image Pull Policy

Changed from `Always` to `IfNotPresent` since we're using specific tags now.

### ArgoCD Sync Policy

- **Automated sync**: Enabled
- **Self-heal**: Enabled (corrects manual changes)
- **Prune**: Enabled (removes resources deleted from Git)
- **Sync interval**: Default (3 minutes, or instant with webhook)

## Troubleshooting

### ArgoCD Not Syncing

1. Check application status:
   ```bash
   kubectl get application chess-lamp -n argocd
   ```

2. Check ArgoCD logs:
   ```bash
   kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
   ```

3. Force sync:
   ```bash
   argocd app sync chess-lamp
   ```

### GitHub Actions Not Updating Git

1. Check workflow permissions (needs `contents: write`)
2. Verify the workflow is running
3. Check workflow logs for errors

### Image Not Found

1. Verify image was pushed to GHCR
2. Check image tag in `k8s/chess-lamp-deployment.yaml`
3. Verify GHCR authentication if using private repo

## Rollback Plan

If you need to rollback to the previous approach:

1. Keep the old workflow file (`.github/workflows/k8s-deploy-simple.yml`)
2. Remove ArgoCD application:
   ```bash
   kubectl delete application chess-lamp -n argocd
   ```
3. Re-enable polling script or use direct kubectl deployment

## Benefits

✅ **GitOps**: Git is the source of truth  
✅ **Audit Trail**: All changes tracked in Git  
✅ **Easy Rollback**: Revert Git commit  
✅ **Visual Dashboard**: ArgoCD UI  
✅ **Automatic Sync**: No manual intervention  
✅ **Self-Healing**: Corrects manual changes  
✅ **Multi-Environment**: Easy to extend  

## Next Steps

1. Monitor first few deployments
2. Set up ArgoCD webhook for instant sync (optional)
3. Configure notifications (Slack, email, etc.)
4. Set up multiple environments (dev, staging, prod)

## Support

- ArgoCD Documentation: https://argo-cd.readthedocs.io/
- Setup Guide: `deploy/ARGOCD_SETUP.md`
- Approach Explanation: `ARGOCD_APPROACH.md`
