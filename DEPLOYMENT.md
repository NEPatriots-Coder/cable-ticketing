# Deployment Guide

Complete guide for deploying the Cable Ticketing System to CoreWeave (Kubernetes) or DigitalOcean App Platform.

---

## CoreWeave (Kubernetes + Helm)

### Prerequisites

1. CoreWeave account with kubectl access configured
2. Helm installed
3. Container registry (Docker Hub, GHCR, etc.)

```bash
kubectl version --client
helm version
kubectl get nodes  # Verify CoreWeave connection
```

### Step 1: Build and Push Docker Images

```bash
cd ticketing_app

# Docker Hub
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest ./backend
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest ./frontend
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest
```

### Step 2: Configure Helm Values

Create `helm-values-coreweave.yaml`:

```yaml
backend:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend
    tag: latest
    pullPolicy: Always
  service:
    type: ClusterIP
    port: 5000
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
  env:
    secretKey: "CHANGE-THIS-TO-RANDOM-SECURE-STRING"
    databaseUrl: "sqlite:///ticketing.db"
    appUrl: "http://YOUR_COREWEAVE_IP"
    sendgridFromEmail: "noreply@yourdomain.com"

frontend:
  image:
    repository: YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend
    tag: latest
    pullPolicy: Always
  service:
    type: LoadBalancer
    port: 80
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

secrets:
  twilioAccountSid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  twilioAuthToken: "your_twilio_auth_token_here"
  twilioPhoneNumber: "+1234567890"
  sendgridApiKey: "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

persistence:
  enabled: true
  storageClass: "ceph-block"
  accessMode: ReadWriteOnce
  size: 2Gi

nodeSelector:
  node.coreweave.cloud/cpu: "true"

ingress:
  enabled: false
```

### Step 3: Deploy

```bash
# Create namespace
kubectl create namespace cable-ticketing

# Deploy
helm install cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing

# Monitor
kubectl get pods -w -n cable-ticketing
kubectl logs -f deployment/cable-ticketing-backend -n cable-ticketing
```

### Step 4: Access the App

```bash
# Get LoadBalancer IP
kubectl get service cable-ticketing-frontend -n cable-ticketing

# Update APP_URL with actual IP, then upgrade
helm upgrade cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing
```

### Useful Kubernetes Commands

```bash
# Logs
kubectl logs -f deployment/cable-ticketing-backend -n cable-ticketing

# Restart
kubectl rollout restart deployment/cable-ticketing-backend -n cable-ticketing

# Scale
kubectl scale deployment/cable-ticketing-backend --replicas=3 -n cable-ticketing

# Resource usage
kubectl top pods -n cable-ticketing

# Delete everything
helm uninstall cable-ticketing -n cable-ticketing
kubectl delete namespace cable-ticketing
```

### Optional: Add PostgreSQL

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --set auth.username=ticketing \
  --set auth.password=CHANGE_THIS \
  --set auth.database=ticketing \
  --set persistence.storageClass=ceph-block \
  --namespace cable-ticketing

# Update helm values:
# backend.env.databaseUrl: "postgresql://ticketing:CHANGE_THIS@postgres-postgresql:5432/ticketing"
```

### Optional: Enable HTTPS

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Then enable ingress in helm values
```

---

## DigitalOcean App Platform

### Prerequisites

- DigitalOcean account
- `doctl` CLI installed and authenticated

```bash
brew install doctl  # macOS
doctl auth init
```

### Step 1: Deploy

```bash
cd ticketing_app
doctl apps create --spec .do/app.yaml
```

### Step 2: Monitor

```bash
doctl apps list
doctl apps logs <app-id> --type BUILD --follow
```

### Step 3: Access

```bash
# Get app URL from the list output
doctl apps list
# Visit: https://your-app-url.ondigitalocean.app/
```

### Key Configuration Notes

- DigitalOcean handles `/api` routing to backend at the platform level
- Frontend nginx does NOT need proxy config (unlike Docker Compose)
- Environment variables are set in `.do/app.yaml`, not `.env`
- SQLite data resets on redeploy -- use DigitalOcean Managed PostgreSQL for persistence

### App.yaml Structure

The `.do/app.yaml` file configures:
- **Backend service**: Python/Flask with Gunicorn
- **Frontend service**: Static site with nginx
- **Database**: Optional PostgreSQL (`databases` section)
- **Environment variables**: Resend API key, sender email, etc.

### Useful Commands

```bash
doctl apps list                              # List all apps
doctl apps get <app-id>                      # App details
doctl apps logs <app-id> --type RUN --follow # Runtime logs
doctl apps update <app-id> --spec .do/app.yaml # Update config
doctl apps delete <app-id>                   # Delete app
```

### Cost Estimate (DigitalOcean)

| Component | Cost/Month |
|-----------|------------|
| Backend (basic-xxs) | ~$5 |
| Frontend (basic-xxs) | ~$5 |
| PostgreSQL Dev DB | ~$15 |
| **Total** | **~$25/month** |

---

## CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to CoreWeave

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and push images
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker build -t ${{ secrets.DOCKER_USERNAME }}/cable-ticketing-backend:latest ./backend
          docker build -t ${{ secrets.DOCKER_USERNAME }}/cable-ticketing-frontend:latest ./frontend
          docker push ${{ secrets.DOCKER_USERNAME }}/cable-ticketing-backend:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/cable-ticketing-frontend:latest

      - name: Deploy to CoreWeave
        run: |
          echo "${{ secrets.KUBECONFIG }}" > kubeconfig
          export KUBECONFIG=kubeconfig
          helm upgrade --install cable-ticketing ./helm-chart \
            -f helm-values-coreweave.yaml \
            --namespace cable-ticketing
```

---

## Troubleshooting

### Pods not starting (Kubernetes)
```bash
kubectl describe pod POD_NAME -n cable-ticketing
# Common: image pull errors, resource limits, missing secrets
```

### 404 errors (DigitalOcean)
- Verify both components deployed: `doctl apps get <app-id>`
- Check routes in app.yaml (backend: `/api`, frontend: `/`)
- Check build logs: `doctl apps logs <app-id> --type BUILD`

### SMS/Email not working
```bash
# Kubernetes
kubectl get secret cable-ticketing-secrets -n cable-ticketing -o yaml
kubectl logs deployment/cable-ticketing-backend -n cable-ticketing | grep -i email

# DigitalOcean
doctl apps logs <app-id> --type RUN | grep -i email
```

### Database connection issues
```bash
# Kubernetes: check PVC
kubectl get pvc -n cable-ticketing

# DigitalOcean: verify DATABASE_URL
doctl apps get <app-id> | grep DATABASE
```
