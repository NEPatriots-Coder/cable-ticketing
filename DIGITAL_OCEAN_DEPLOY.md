# Digital Ocean Deployment Guide

## Stop Your Current App

### Option 1: Via Web Dashboard
1. Go to https://cloud.digitalocean.com/apps
2. Click on your `cable-ticketing` app
3. Click **Settings** tab
4. Scroll to bottom → Click **Destroy App**
5. Type app name to confirm

### Option 2: Via CLI
```bash
# List your apps to get the ID
doctl apps list

# Delete the app (replace <app-id> with actual ID)
doctl apps delete <app-id>
```

---

## Deploy Correctly (Without GitHub)

Your current deployment failed because the `app.yaml` had placeholder GitHub repo paths. Here's how to deploy directly:

### Step 1: Install doctl (if not already installed)
```bash
# Install doctl
brew install doctl  # macOS
# or download from: https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate
doctl auth init
```

### Step 2: Create the App from Your Local Code
```bash
# Navigate to your project directory
cd /sessions/loving-exciting-heisenberg/mnt/ticketing_app

# Create the app using the updated app.yaml
doctl apps create --spec .do/app.yaml
```

This will:
- Upload your code directly from your local machine
- Build both frontend and backend
- Deploy them with proper routing

### Step 3: Monitor the Deployment
```bash
# Get your app ID
doctl apps list

# Watch the deployment logs
doctl apps logs <app-id> --type BUILD --follow
```

### Step 4: Get Your App URL
```bash
# Once deployed, get the URL
doctl apps list
```

Look for the "Default Ingress" URL - that's your app's public URL!

---

## Why the 404 Error Happened

Your previous deployment showed successful backend build but 404 errors because:

1. **GitHub repo was placeholder**: `YOUR_GITHUB_USERNAME/cable-ticketing` doesn't exist
2. **Digital Ocean couldn't fetch code**: Failed silently or used cached/empty data
3. **Frontend likely didn't deploy**: Only backend built successfully

---

## Alternative: Push to GitHub First

If you prefer GitHub integration:

### Step 1: Create GitHub Repo
```bash
# Initialize git in your project
cd /sessions/loving-exciting-heisenberg/mnt/ticketing_app
git init
git add .
git commit -m "Initial commit - Cable Ticketing App"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/cable-ticketing.git
git branch -M main
git push -u origin main
```

### Step 2: Update app.yaml
Edit `.do/app.yaml` and add back the github section:
```yaml
services:
  - name: backend
    github:
      repo: YOUR_ACTUAL_USERNAME/cable-ticketing
      branch: main
      deploy_on_push: true
    source_dir: backend
    # ... rest of config
```

### Step 3: Deploy
```bash
doctl apps create --spec .do/app.yaml
```

---

## Quick Reference Commands

```bash
# List all apps
doctl apps list

# Get app details
doctl apps get <app-id>

# View logs
doctl apps logs <app-id> --type RUN --follow

# Update app (after code changes)
doctl apps update <app-id> --spec .do/app.yaml

# Delete app
doctl apps delete <app-id>
```

---

## Testing Your Deployment

Once deployed successfully, you should be able to:

1. **Access Frontend**: `https://your-app-url.ondigitalocean.app/`
2. **Test Backend API**: `https://your-app-url.ondigitalocean.app/api/health`
3. **Login**: Use credentials from seed_users.py
   - Username: `LZL01-ICS-LW`
   - Password: `demo123`

---

## Troubleshooting

### Still getting 404?
- Check both components are deployed: `doctl apps get <app-id>`
- Verify routes in app.yaml (backend: `/api`, frontend: `/`)
- Check build logs for errors: `doctl apps logs <app-id> --type BUILD`

### Environment variables not loading?
- Digital Ocean loads env vars from app.yaml directly
- No need for .env file in production
- Check current env vars: `doctl apps get <app-id> | grep -A 20 envs`

### Database issues?
- SQLite works but data resets on redeploy
- Consider upgrading to Digital Ocean Managed PostgreSQL for production
- Update DATABASE_URL in app.yaml accordingly
