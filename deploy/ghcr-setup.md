# Quick GHCR Setup Guide

GitHub Container Registry (GHCR) is GitHub's built-in Docker registry. It's free and requires minimal setup.

## What is GHCR?

- **Free** Docker container registry integrated with GitHub
- No separate account needed - uses your GitHub account
- Works with GitHub Actions automatically
- Can be public or private

## First Time Setup (5 minutes)

### 1. Push Your Code

Just push this repository to GitHub. The GitHub Actions workflow will automatically:
- Build your Docker image
- Push it to `ghcr.io/YOUR_USERNAME/chess-lamp:latest`

### 2. Check the Build

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see "Build and Push Docker Image" workflow running or completed
4. Wait for it to finish (usually 2-3 minutes)

### 3. Find Your Package

After the workflow completes:

1. Go to your GitHub profile: `https://github.com/YOUR_USERNAME`
2. Click **Packages** tab (or visit `https://github.com/YOUR_USERNAME?tab=packages`)
3. You should see `chess-lamp` package

### 4. Set Package Visibility

**Important:** Choose who can pull your image.

1. Click on the `chess-lamp` package
2. Click **Package settings** (right sidebar)
3. Scroll down to **Danger Zone**
4. Click **Change visibility**
5. Choose:
   - **Public** ✅ (Recommended) - Anyone can pull, no authentication needed
   - **Private** - Only you can pull, requires authentication

**For most users:** Choose **Public** - it's easier and your code is already public anyway.

### 5. Test Pulling the Image

On your remote machine:

```bash
# If package is PUBLIC (no auth needed):
docker pull ghcr.io/YOUR_USERNAME/chess-lamp:latest

# If package is PRIVATE (auth required):
# First create a Personal Access Token:
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Generate token with 'read:packages' permission
docker login ghcr.io -u YOUR_USERNAME -p YOUR_PAT
docker pull ghcr.io/YOUR_USERNAME/chess-lamp:latest
```

## That's It!

Your image is now available at:
```
ghcr.io/YOUR_USERNAME/chess-lamp:latest
```

## Troubleshooting

### "Package not found" or "404"

- Wait a few minutes after the workflow completes
- Check that the workflow actually succeeded in Actions tab
- Verify the package name matches: `ghcr.io/YOUR_USERNAME/chess-lamp:latest`

### "Unauthorized" or "authentication required"

- Your package is private - you need to authenticate (see Step 5 above)
- Or make the package public in Package settings

### "Permission denied"

- For private packages, make sure your PAT has `read:packages` permission
- Try logging in again: `docker login ghcr.io`

## Next Steps

Once your image is available, proceed with deployment setup:
- See [CI_CD.md](../CI_CD.md) for deployment options (Watchtower, webhook, or cron)

