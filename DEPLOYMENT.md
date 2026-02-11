# CoreWeave Deployment Guide

Complete guide for deploying the Cable Ticketing System to CoreWeave's Kubernetes platform.

## Prerequisites

1. **CoreWeave Account**
   - Sign up at https://cloud.coreweave.com
   - Have kubectl access configured

2. **Required Tools**
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

   # Install helm
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

   # Verify installations
   kubectl version --client
   helm version
   ```

3. **Container Registry**
   - Docker Hub (free)
   - GitHub Container Registry
   - Or CoreWeave's registry

## Step 1: Configure CoreWeave Access

### Get kubeconfig from CoreWeave

```bash
# Download your kubeconfig from CoreWeave dashboard
# Save it to ~/.kube/config or a custom location

# Test connection
kubectl get nodes

# You should see CoreWeave nodes listed
```

### Set namespace (optional)

```bash
# Create a namespace for your app
kubectl create namespace cable-ticketing

# Set as default
kubectl config set-context --current --namespace=cable-ticketing
```

## Step 2: Build and Push Docker Images

### Option A: Docker Hub

```bash
# Login to Docker Hub
docker login

# Build images
cd ticketing_app
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest ./backend
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest ./frontend

# Push images
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest
```

### Option B: GitHub Container Registry

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Build and tag
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/cable-ticketing-backend:latest ./backend
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/cable-ticketing-frontend:latest ./frontend

# Push
docker push ghcr.io/YOUR_GITHUB_USERNAME/cable-ticketing-backend:latest
docker push ghcr.io/YOUR_GITHUB_USERNAME/cable-ticketing-frontend:latest
```

## Step 3: Configure Helm Values for CoreWeave

Create `helm-values-coreweave.yaml`:

```yaml
# Image configuration
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
    # For production, use PostgreSQL
    databaseUrl: "sqlite:///ticketing.db"
    # Or: postgresql://user:pass@postgres-service:5432/ticketing
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

# Secrets - REPLACE WITH YOUR ACTUAL VALUES
secrets:
  twilioAccountSid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  twilioAuthToken: "your_twilio_auth_token_here"
  twilioPhoneNumber: "+1234567890"
  sendgridApiKey: "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Persistence for SQLite database
persistence:
  enabled: true
  storageClass: "ceph-block"  # CoreWeave default
  accessMode: ReadWriteOnce
  size: 2Gi

# Node selector for CoreWeave CPU nodes
nodeSelector:
  node.coreweave.cloud/cpu: "true"

# Ingress (optional - if you want a domain)
ingress:
  enabled: false
  # Enable if you have a domain:
  # enabled: true
  # className: "nginx"
  # hosts:
  #   - host: cable-tickets.yourdomain.com
  #     paths:
  #       - path: /
  #         pathType: Prefix
```

## Step 4: Deploy to CoreWeave

### Deploy with Helm

```bash
# From the ticketing_app directory
helm install cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing

# Check deployment status
kubectl get pods -n cable-ticketing
kubectl get services -n cable-ticketing
```

### Monitor deployment

```bash
# Watch pods come up
kubectl get pods -w -n cable-ticketing

# Check pod logs if issues
kubectl logs -f deployment/cable-ticketing-backend -n cable-ticketing
kubectl logs -f deployment/cable-ticketing-frontend -n cable-ticketing

# Check events
kubectl get events -n cable-ticketing --sort-by='.lastTimestamp'
```

## Step 5: Access Your Application

### Get the LoadBalancer IP

```bash
kubectl get service cable-ticketing-frontend -n cable-ticketing

# Output will show EXTERNAL-IP
# Example: 207.x.x.x
```

### Test the application

```bash
# Get the IP
export APP_IP=$(kubectl get service cable-ticketing-frontend -n cable-ticketing -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Open in browser
echo "Access your app at: http://$APP_IP"

# Or use curl to test
curl http://$APP_IP
```

### Update APP_URL after getting IP

```bash
# Edit your helm values file
# Update backend.env.appUrl to: http://YOUR_ACTUAL_IP

# Upgrade deployment
helm upgrade cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing
```

## Step 6: Production Setup (Optional but Recommended)

### Add PostgreSQL Database

Create `postgres-values.yaml`:

```yaml
# Using Bitnami PostgreSQL chart
persistence:
  enabled: true
  size: 10Gi
  storageClass: ceph-block

auth:
  username: ticketing
  password: CHANGE_THIS_PASSWORD
  database: ticketing

primary:
  resources:
    requests:
      memory: 512Mi
      cpu: 500m
```

Deploy PostgreSQL:

```bash
# Add Bitnami repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install postgres bitnami/postgresql \
  -f postgres-values.yaml \
  --namespace cable-ticketing

# Update your app's helm values
# backend.env.databaseUrl: "postgresql://ticketing:CHANGE_THIS_PASSWORD@postgres-postgresql:5432/ticketing"

# Upgrade your app
helm upgrade cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing
```

### Enable HTTPS with Ingress

```bash
# Install nginx ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Update helm-values-coreweave.yaml:
# ingress.enabled: true
# ingress.hosts[0].host: your-domain.com

# Upgrade
helm upgrade cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing
```

## Useful Commands

### View logs
```bash
# Backend logs
kubectl logs -f deployment/cable-ticketing-backend -n cable-ticketing

# Frontend logs
kubectl logs -f deployment/cable-ticketing-frontend -n cable-ticketing
```

### Restart pods
```bash
kubectl rollout restart deployment/cable-ticketing-backend -n cable-ticketing
kubectl rollout restart deployment/cable-ticketing-frontend -n cable-ticketing
```

### Update secrets
```bash
# Edit secrets directly
kubectl edit secret cable-ticketing-secrets -n cable-ticketing

# Or upgrade helm with new values
helm upgrade cable-ticketing ./helm-chart \
  -f helm-values-coreweave.yaml \
  --namespace cable-ticketing
```

### Scale deployment
```bash
# Scale up
kubectl scale deployment/cable-ticketing-backend --replicas=3 -n cable-ticketing

# Or update helm values and upgrade
```

### Check resource usage
```bash
kubectl top pods -n cable-ticketing
kubectl top nodes
```

### Delete deployment
```bash
# Delete everything
helm uninstall cable-ticketing -n cable-ticketing

# Delete namespace
kubectl delete namespace cable-ticketing
```

## Troubleshooting

### Pods not starting

```bash
# Describe pod to see events
kubectl describe pod POD_NAME -n cable-ticketing

# Common issues:
# - Image pull errors (check image names)
# - Resource limits (adjust in helm values)
# - Missing secrets (verify secrets are set)
```

### Can't access application

```bash
# Check service
kubectl get svc cable-ticketing-frontend -n cable-ticketing

# Check if LoadBalancer IP is assigned
# If pending, CoreWeave might need time or there's a quota issue

# Check frontend pod logs
kubectl logs deployment/cable-ticketing-frontend -n cable-ticketing
```

### Database connection issues

```bash
# Check if using correct service name
# For PostgreSQL: postgres-postgresql:5432
# For SQLite: make sure PVC is mounted

# Check PVC status
kubectl get pvc -n cable-ticketing
```

### SMS/Email not working

```bash
# Check secrets are set correctly
kubectl get secret cable-ticketing-secrets -n cable-ticketing -o yaml

# Check backend logs for errors
kubectl logs deployment/cable-ticketing-backend -n cable-ticketing | grep -i twilio
kubectl logs deployment/cable-ticketing-backend -n cable-ticketing | grep -i sendgrid
```

## Cost Optimization

CoreWeave charges for:
- **Compute**: CPU/Memory usage
- **Storage**: Persistent volumes
- **Network**: LoadBalancer and data transfer

Tips:
1. Use appropriate resource limits (don't over-provision)
2. Use autoscaling for variable workloads
3. Delete unused deployments
4. Use SQLite for small deployments (no separate DB costs)
5. Consider NodePort instead of LoadBalancer if behind VPN

## CI/CD Integration

### GitHub Actions Example

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

## Support

For CoreWeave-specific issues:
- CoreWeave Docs: https://docs.coreweave.com
- CoreWeave Support: support@coreweave.com
- CoreWeave Slack: https://coreweave.slack.com

For app issues:
- Check application logs
- Review README.md troubleshooting section
- Verify all secrets are configured correctly

---

**Happy Deploying! 🚀**
