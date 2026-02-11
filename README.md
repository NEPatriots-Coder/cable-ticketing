# 🔌 Cable Ticketing System

A Jira-like ticketing application specifically designed for managing cable requests. Built with React frontend, Flask backend, and fully containerized with Docker and Kubernetes support.

## Features

- **Bidirectional Ticketing**: Create and manage cable requests between teams
- **SMS & Email Notifications**: Automatic notifications via Twilio and SendGrid
- **Approve/Reject Workflow**: One-click approve/reject links in notifications
- **Real-time Dashboard**: View ticket status and statistics
- **User Management**: Simple authentication and role management
- **Mobile-Friendly**: Responsive design works on all devices
- **Cloud-Native**: Fully containerized with Kubernetes/Helm support

## Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database management
- **SQLite** (dev) / **PostgreSQL** (prod)
- **Twilio** - SMS notifications
- **SendGrid** - Email notifications

### Frontend
- **React** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **CSS3** - Styling

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Local development orchestration
- **Helm** - Kubernetes package manager
- **Kubernetes** - Container orchestration (CoreWeave)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Twilio account (for SMS)
- SendGrid account (for email)

### 1. Clone and Setup

```bash
cd ticketing_app

# Copy environment file
cp backend/.env.example backend/.env

# Edit backend/.env with your credentials
# - Add Twilio credentials
# - Add SendGrid API key
# - Update APP_URL if needed
```

### 2. Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

### 3. Create Your First User

Navigate to http://localhost:3000 and click **Register**.

Fill in:
- Username
- Email
- Phone (with country code, e.g., +12025551234)
- Password

### 4. Create a Ticket

1. Log in
2. Fill out the cable request form
3. Assign to another user
4. The assignee receives SMS + Email with approve/reject links!

## Configuration

### Backend Environment Variables

Edit `backend/.env`:

```bash
# Flask
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///ticketing.db
# For PostgreSQL: postgresql://user:password@postgres:5432/ticketing

# Twilio (SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid (Email)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# App URL (for notification links)
APP_URL=http://localhost:3000
```

### Getting API Keys

**Twilio** (SMS):
1. Sign up at https://www.twilio.com
2. Get a phone number ($1/month)
3. Copy Account SID, Auth Token, and Phone Number
4. Cost: ~$0.0075 per SMS

**SendGrid** (Email):
1. Sign up at https://sendgrid.com
2. Create an API key
3. Free tier: 100 emails/day

## Development

### Run Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Backend runs at http://localhost:5000

### Run Frontend Locally

```bash
cd frontend
npm install
npm start
```

Frontend runs at http://localhost:3000

## Deployment to CoreWeave (Kubernetes)

### Prerequisites

- CoreWeave account
- `kubectl` configured for CoreWeave
- `helm` installed
- Docker images built and pushed to a registry

### 1. Build and Push Docker Images

```bash
# Build images
docker build -t your-registry/cable-ticketing-backend:latest ./backend
docker build -t your-registry/cable-ticketing-frontend:latest ./frontend

# Push to registry (Docker Hub, GCR, ECR, etc.)
docker push your-registry/cable-ticketing-backend:latest
docker push your-registry/cable-ticketing-frontend:latest
```

### 2. Configure Helm Values

Create `helm-values-production.yaml`:

```yaml
backend:
  image:
    repository: your-registry/cable-ticketing-backend
    tag: latest
  env:
    secretKey: "CHANGE-THIS-TO-RANDOM-STRING"
    databaseUrl: "sqlite:///ticketing.db"  # Or PostgreSQL URL
    appUrl: "https://your-domain.com"
    sendgridFromEmail: "noreply@yourdomain.com"

frontend:
  image:
    repository: your-registry/cable-ticketing-frontend
    tag: latest
  service:
    type: LoadBalancer  # Or NodePort for CoreWeave

secrets:
  twilioAccountSid: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  twilioAuthToken: "your_auth_token"
  twilioPhoneNumber: "+1234567890"
  sendgridApiKey: "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: cable-tickets.your-domain.com
      paths:
        - path: /
          pathType: Prefix
```

### 3. Deploy with Helm

```bash
# Install
helm install cable-ticketing ./helm-chart -f helm-values-production.yaml

# Or upgrade existing deployment
helm upgrade cable-ticketing ./helm-chart -f helm-values-production.yaml

# Check status
kubectl get pods
kubectl get services
```

### 4. Access Your Application

```bash
# Get the external IP
kubectl get service cable-ticketing-frontend

# Access via LoadBalancer IP or configure DNS
```

## Helm Chart Configuration

Key values in `helm-chart/values.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of pod replicas | `1` |
| `backend.image.repository` | Backend Docker image | `cable-ticketing-backend` |
| `frontend.image.repository` | Frontend Docker image | `cable-ticketing-frontend` |
| `backend.service.type` | Backend service type | `ClusterIP` |
| `frontend.service.type` | Frontend service type | `LoadBalancer` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | Storage size | `1Gi` |
| `ingress.enabled` | Enable ingress | `false` |

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user

### Users
- `GET /api/users` - List all users
- `GET /api/users/<id>` - Get specific user

### Tickets
- `GET /api/tickets` - List all tickets
- `GET /api/tickets/<id>` - Get specific ticket
- `POST /api/tickets` - Create new ticket
- `PATCH /api/tickets/<id>` - Update ticket

### Approvals (Token-based)
- `GET /api/tickets/<id>/approve/<token>` - Approve ticket
- `GET /api/tickets/<id>/reject/<token>` - Reject ticket

### Dashboard
- `GET /api/dashboard/stats` - Get statistics

## Workflow

1. **User A** creates a cable request ticket
2. **User B** (assignee) receives **SMS + Email** with approve/reject links
3. **User B** clicks approve/reject link
4. **User A** receives notification of approval/rejection
5. If approved, **User B** can mark as "In Progress" → "Fulfilled"
6. Ticket is complete!

## Ticket Statuses

- `pending_approval` - Awaiting assignee response
- `approved` - Approved, ready to start
- `rejected` - Rejected by assignee
- `in_progress` - Work in progress
- `fulfilled` - Completed
- `closed` - Archived

## Troubleshooting

### SMS not sending
- Check Twilio credentials in `.env`
- Verify phone numbers include country code (e.g., +1234567890)
- Check Twilio account balance

### Email not sending
- Check SendGrid API key
- Verify sender email is authenticated in SendGrid
- Check SendGrid sending limits (100/day on free tier)

### Database issues
- For production, switch to PostgreSQL
- Update `DATABASE_URL` in ConfigMap/Secret

### Frontend can't reach backend
- Check `APP_URL` environment variable
- Verify backend service is running: `kubectl get svc`
- Check nginx proxy configuration in `frontend/nginx.conf`

## Production Recommendations

1. **Use PostgreSQL** instead of SQLite
   ```bash
   DATABASE_URL=postgresql://user:password@postgres:5432/ticketing
   ```

2. **Enable HTTPS** via Ingress + cert-manager
3. **Add Celery + Redis** for async notification sending
4. **Set up monitoring** (Prometheus + Grafana)
5. **Enable autoscaling** in Helm values
6. **Use managed secrets** (Kubernetes Secrets, Vault)
7. **Add authentication middleware** (OAuth, SSO)

## Project Structure

```
ticketing_app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py          # Database models
│   │   ├── routes.py          # API endpoints
│   │   └── notifications.py   # SMS/Email logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── App.js
│   │   └── index.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── helm-chart/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── secret.yaml
│       └── configmap.yaml
├── docker-compose.yml
└── README.md
```

## Contributing

This project was built for CoreWeave deployment. Feel free to fork and customize for your needs!

## License

MIT License - feel free to use for personal or commercial projects.

## Support

For issues or questions:
- Check the troubleshooting section
- Review Docker logs: `docker-compose logs`
- Review Kubernetes logs: `kubectl logs <pod-name>`

## Roadmap

- [ ] Add PostgreSQL support out of the box
- [ ] Implement Celery for async notifications
- [ ] Add file attachments to tickets
- [ ] Real-time updates with WebSockets
- [ ] Mobile app (React Native)
- [ ] Ticket comments/chat
- [ ] Advanced search and filtering
- [ ] Export reports (PDF, Excel)
- [ ] Integration with inventory systems

---

**Built with ❤️ for CoreWeave deployment**
