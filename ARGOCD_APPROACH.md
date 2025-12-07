# ArgoCD Deployment Approach

This document explains how your deployment approach would change if you installed ArgoCD.

## Understanding "Source of Truth"

**Important distinction:**

- **GitHub (Git Repository)** = Source of truth for **WHAT to deploy**
  - Contains Kubernetes manifests (deployment.yaml, service.yaml, etc.)
  - Contains image tags (which version to deploy)
  - ArgoCD reads from here to know the desired state
  
- **GHCR (Container Registry)** = Source of truth for **THE ARTIFACTS**
  - Stores the actual Docker images
  - Where Kubernetes pulls images from
  - Not the source of truth for deployment configuration

**In GitOps with ArgoCD:**
- **Git (GitHub repo)** tells ArgoCD **what** to deploy (manifests + image tags)
- **GHCR** provides **the actual images** to deploy
- ArgoCD syncs from Git → Kubernetes, and Kubernetes pulls images from GHCR

**Example:**
```
Git (GitHub) says: "Deploy image ghcr.io/user/chess-lamp:main-abc1234"
         ↓
ArgoCD reads Git and applies manifests
         ↓
Kubernetes pulls image from GHCR using the tag from Git
```

So when we say "Git is the source of truth," we mean Git is the source of truth for **deployment configuration**, while GHCR is the source of truth for **the artifacts themselves**.

## Current Setup (Without ArgoCD)

Your current deployment flow:

```
┌─────────────────┐
│  GitHub Actions │
│  (CI Pipeline)  │
└────────┬────────┘
         │
         │ 1. Build & Push Image
         │    to GHCR
         ▼
┌─────────────────┐
│  GHCR Registry  │
│  (Image Store)  │
└────────┬────────┘
         │
         │ 2. Polling Script
         │    (on k8s-control)
         │    Detects new image
         ▼
┌─────────────────┐
│  Kubernetes     │
│  (kubectl apply)│
│  imagePullPolicy│
│  = Always       │
└─────────────────┘
```

**Current Components:**
- ✅ GitHub Actions builds and pushes to GHCR
- ✅ Polling script on `k8s-control` node detects image changes
- ✅ Kubernetes deployment uses `imagePullPolicy: Always`
- ⚠️ Manual/script-based deployment coordination
- ⚠️ No GitOps workflow (manifests not in Git as source of truth)

## ArgoCD Approach (With ArgoCD)

With ArgoCD, your deployment flow becomes:

```
┌─────────────────┐
│  GitHub Actions │
│  (CI Pipeline)  │
└────────┬────────┘
         │
         │ 1. Build & Push Image
         │    to GHCR
         ▼
┌─────────────────┐
│  GHCR Registry  │
│  (Image Store)  │
└────────┬────────┘
         │
         │ 2. Update Image Tag
         │    in Git Repo
         │    (via GitHub Action)
         ▼
┌─────────────────┐
│  Git Repository │
│  (Source of     │
│   Truth)        │
└────────┬────────┘
         │
         │ 3. ArgoCD Detects
         │    Git Changes
         │    (Polling or Webhook)
         ▼
┌─────────────────┐
│  ArgoCD         │
│  (GitOps Engine)│
└────────┬────────┘
         │
         │ 4. Sync to Cluster
         │    (kubectl apply)
         ▼
┌─────────────────┐
│  Kubernetes     │
│  Cluster        │
└─────────────────┘
```

## Key Changes

### 1. **Git as Source of Truth**

**Current:** Kubernetes manifests might be applied directly or via scripts.

**With ArgoCD:** 
- Kubernetes manifests live in your Git repository
- ArgoCD watches the Git repo for changes
- Git becomes the single source of truth for your cluster state

**Example Structure:**
```
chess-lamp/
├── .github/
│   └── workflows/
│       └── k8s-deploy.yml
├── k8s/                          # ← New: Git-based manifests
│   ├── chess-lamp-deployment.yaml
│   └── kustomization.yaml        # ← Optional: For image tag management
└── argocd/                       # ← New: ArgoCD Application definition
    └── application.yaml
```

### 2. **Image Tag Management**

**Current:** Using `:latest` tag with `imagePullPolicy: Always` and polling script.

**With ArgoCD (Recommended):**
- Use specific image tags (e.g., `:main-abc1234` or `:v1.2.3`)
- Update the image tag in Git (via GitHub Actions)
- ArgoCD detects the change and syncs automatically

**Option A: Direct Manifest Update**
```yaml
# k8s/chess-lamp-deployment.yaml
spec:
  containers:
  - name: chess-lamp
    image: ghcr.io/slibonati/chess-lamp:main-abc1234  # ← Specific tag
    imagePullPolicy: IfNotPresent  # ← Can use IfNotPresent
```

**Option B: Kustomize (Better for Image Updates)**
```yaml
# k8s/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

images:
  - name: ghcr.io/slibonati/chess-lamp
    newTag: main-abc1234  # ← Easy to update

resources:
  - chess-lamp-deployment.yaml
```

### 3. **GitHub Actions Workflow Changes**

**Current Workflow:**
```yaml
# .github/workflows/k8s-deploy-simple.yml
- Build & Push to GHCR
- Output message about polling script
```

**With ArgoCD Workflow:**
```yaml
# .github/workflows/k8s-deploy.yml
jobs:
  build-and-push:
    # ... existing build steps ...
    
  update-git-manifest:  # ← NEW: Update Git with new image tag
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Update image tag in k8s manifest
        run: |
          # Update kustomization.yaml or deployment.yaml
          # with new image tag from build step
          sed -i "s|image:.*chess-lamp.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}|" \
            k8s/chess-lamp-deployment.yaml
      
      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add k8s/
          git commit -m "chore: update image to ${{ github.sha }}"
          git push
```

### 4. **ArgoCD Application Definition**

You'll need to create an ArgoCD Application:

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: chess-lamp
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/slibonati/chess-lamp
    targetRevision: main
    path: k8s  # Path to your Kubernetes manifests
  
  destination:
    server: https://kubernetes.default.svc
    namespace: chess-lamp
  
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Auto-sync if cluster drifts from Git
    syncOptions:
      - CreateNamespace=true
```

### 5. **No More Polling Script**

**Current:** Polling script on `k8s-control` node checks for new images.

**With ArgoCD:**
- ❌ **Remove polling script** - No longer needed
- ✅ ArgoCD handles detection and syncing
- ✅ ArgoCD can use webhooks for instant updates (no polling delay)

### 6. **Image Change Detection**

**Current:** 
- Polling script periodically checks GHCR
- Or `imagePullPolicy: Always` with manual restarts

**With ArgoCD:**
- **Option 1: Git-based (Recommended)**
  - GitHub Actions updates Git with new image tag
  - ArgoCD detects Git change (via polling or webhook)
  - ArgoCD syncs automatically
  
- **Option 2: Image Updater (Advanced)**
  - ArgoCD Image Updater watches GHCR directly
  - Automatically updates Git when new image is detected
  - Requires additional ArgoCD component

## Migration Steps

### Step 1: Install ArgoCD

```bash
# On your k8s-control node or any machine with kubectl access
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Step 2: Move Manifests to Git

```bash
# Ensure your k8s manifests are in the repo
git add .github/k8s/chess-lamp-deployment.yaml
git commit -m "chore: add k8s manifests to Git"
git push
```

### Step 3: Create ArgoCD Application

```bash
# Apply ArgoCD Application
kubectl apply -f argocd/application.yaml

# Or use ArgoCD CLI
argocd app create chess-lamp \
  --repo https://github.com/slibonati/chess-lamp \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace chess-lamp \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### Step 4: Update GitHub Actions Workflow

Modify `.github/workflows/k8s-deploy.yml` to:
1. Build and push image (existing)
2. Update image tag in Git manifest (new)
3. Commit and push changes (new)

### Step 5: Remove Polling Script

```bash
# Remove cron job
crontab -e  # Remove the polling script entry

# Or remove the script entirely
rm /path/to/poll-update.sh
```

## Benefits of ArgoCD Approach

### ✅ **GitOps Benefits**
- **Audit Trail**: All changes tracked in Git history
- **Rollback**: Easy to revert to previous Git commit
- **Collaboration**: Multiple people can review changes via PRs
- **Consistency**: Same process for all environments

### ✅ **Automation**
- **Auto-sync**: ArgoCD automatically applies Git changes
- **Self-healing**: ArgoCD corrects manual cluster changes
- **Webhook Support**: Instant updates (no polling delay)

### ✅ **Visibility**
- **ArgoCD UI**: Visual dashboard showing app status
- **Sync Status**: See what's synced vs. what's pending
- **Health Monitoring**: Built-in health checks

### ✅ **Multi-Environment**
- Easy to deploy to dev/staging/prod
- Same manifests, different configs
- Environment promotion workflows

## Comparison Table

| Aspect | Current (Polling) | With ArgoCD |
|--------|------------------|-------------|
| **Image Detection** | Polling script checks GHCR | Git-based (GitHub Actions updates Git) |
| **Deployment Trigger** | Manual or cron-based | Automatic (Git push triggers sync) |
| **Source of Truth** | Cluster state | Git repository |
| **Rollback** | Manual kubectl commands | Git revert + auto-sync |
| **Visibility** | kubectl commands | ArgoCD UI dashboard |
| **Multi-Environment** | Manual per environment | Single Git repo, multiple apps |
| **Change Detection** | Polling delay (5+ min) | Webhook-based (instant) |
| **Drift Detection** | Manual checks | Automatic (self-heal) |
| **Complexity** | Low (simple script) | Medium (requires GitOps setup) |

## When to Use ArgoCD

**Use ArgoCD if:**
- ✅ You want GitOps workflow (Git as source of truth)
- ✅ You need audit trails and change history
- ✅ You manage multiple environments
- ✅ You want visual dashboard for deployments
- ✅ You need rollback capabilities
- ✅ You want automatic drift detection

**Stick with Current Approach if:**
- ✅ Simple single-environment setup
- ✅ Minimal deployment needs
- ✅ Don't need GitOps benefits
- ✅ Want to keep it simple

## Hybrid Approach (Optional)

You can also use a **hybrid approach**:

1. **Keep GitHub Actions** for building and pushing images
2. **Use ArgoCD** for deployment (instead of polling script)
3. **Update Git** with new image tags via GitHub Actions
4. **ArgoCD syncs** automatically from Git

This gives you:
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ GitOps deployment (ArgoCD)
- ✅ No polling script needed
- ✅ Best of both worlds

## Example: Complete ArgoCD Setup

### 1. Updated GitHub Actions Workflow

```yaml
name: Build, Push, and Update Git

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - 'chess_lamp.py'
      - 'govee_lan.py'
      - 'requirements.txt'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # ← Need write for Git push
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=main-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
      
      - name: Update k8s manifest with new image
        run: |
          IMAGE_TAG="main-${{ github.sha }}"
          sed -i "s|image:.*chess-lamp.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${IMAGE_TAG}|" \
            .github/k8s/chess-lamp-deployment.yaml
      
      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .github/k8s/chess-lamp-deployment.yaml
          git commit -m "chore: update image to main-${{ github.sha }}" || exit 0
          git push
```

### 2. ArgoCD Application

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: chess-lamp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/slibonati/chess-lamp
    targetRevision: main
    path: .github/k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: chess-lamp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 3. Updated Deployment Manifest

```yaml
# .github/k8s/chess-lamp-deployment.yaml
# ... existing config ...
spec:
  containers:
  - name: chess-lamp
    image: ghcr.io/slibonati/chess-lamp:main-abc1234  # ← Will be updated by GitHub Actions
    imagePullPolicy: IfNotPresent  # ← Can change from Always
```

## Summary

**Current Approach:**
- GitHub Actions → GHCR
- Polling script detects changes
- Manual/script-based deployment

**ArgoCD Approach:**
- GitHub Actions → GHCR → Update Git
- ArgoCD watches Git
- Automatic GitOps deployment

**Key Change:** Git becomes the source of truth, and ArgoCD syncs from Git to Kubernetes automatically.
