# Project Overview: Cable Ticketing System

## What Is This?

A **Jira-like ticketing application** specifically designed for managing **cable requests** in enterprise environments. Think of it as a simple, focused workflow tool for technicians and inventory staff to request, approve, and track cable deployments.

## The Problem It Solves

**Scenario:**
- Technician needs 100ft of Cat6 cable for a new office
- Currently: Phone call, email, or walk to inventory room
- Problem: No tracking, no accountability, chaos

**With Cable Ticketing System:**
- Technician creates ticket in web app (30 seconds)
- Inventory staff gets SMS + Email instantly
- One-click approve/reject
- Automatic status tracking
- Full audit trail

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User's Browser                        │
│                   (React Frontend - Port 3000)               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (Port 5000)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routes     │  │   Models     │  │ Notifications│      │
│  │ (API Logic)  │  │ (Database)   │  │ (SMS/Email)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌──────────┐
    │SQLite/  │    │ Twilio  │    │SendGrid  │
    │Postgres │    │  (SMS)  │    │ (Email)  │
    └─────────┘    └─────────┘    └──────────┘
```

## Key Features

### 1. Ticket Management
- Create cable requests with specifications (type, length, gauge)
- Assign to specific users
- Set priority (low, medium, high)
- Add location and notes

### 2. Approval Workflow
```
Create Ticket → Pending Approval → Approved/Rejected → In Progress → Fulfilled
```

### 3. Notifications
- **SMS**: Sent via Twilio when ticket created
- **Email**: Sent via SendGrid with formatted HTML
- **One-click approve/reject**: Links in notifications

### 4. Dashboard
- View all tickets
- Filter by created/assigned
- See real-time statistics
- Track ticket status

### 5. User Management
- Simple registration and login
- Role-based (could extend to admin/user)
- Phone + email required for notifications

## Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: Flask 3.0
- **ORM**: SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **SMS**: Twilio API
- **Email**: SendGrid API
- **Server**: Gunicorn (production WSGI)

### Frontend
- **Library**: React 18
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Styling**: Custom CSS3 (no framework dependencies)
- **Build**: Create React App
- **Server**: Nginx (production)

### DevOps
- **Containers**: Docker
- **Orchestration**: Docker Compose (local), Kubernetes (prod)
- **Package Manager**: Helm
- **Target Platform**: CoreWeave Cloud

## File Structure

```
ticketing_app/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py        # App factory
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── routes.py          # API endpoints
│   │   └── notifications.py   # SMS/Email logic
│   ├── Dockerfile             # Backend container
│   ├── requirements.txt       # Python dependencies
│   └── run.py                 # Entry point
│
├── frontend/                   # React UI
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   ├── LoginForm.js
│   │   │   ├── RegisterForm.js
│   │   │   ├── TicketForm.js
│   │   │   └── TicketList.js
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.js
│   │   │   └── ApprovalPage.js
│   │   ├── App.js             # Main app component
│   │   └── index.js           # Entry point
│   ├── public/
│   │   └── index.html
│   ├── Dockerfile             # Frontend container
│   ├── nginx.conf             # Nginx config
│   └── package.json           # Node dependencies
│
├── helm-chart/                 # Kubernetes deployment
│   ├── Chart.yaml
│   ├── values.yaml            # Configuration
│   └── templates/             # K8s manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       └── pvc.yaml
│
├── docker-compose.yml          # Local development
├── README.md                   # Main documentation
├── DEPLOYMENT.md              # CoreWeave guide
├── TESTING.md                 # Testing guide
├── quick-start.sh             # Setup script
└── .gitignore
```

## Database Schema

### Users Table
```sql
id              INTEGER PRIMARY KEY
username        VARCHAR(80) UNIQUE
email           VARCHAR(120) UNIQUE
phone           VARCHAR(20)
password_hash   VARCHAR(200)
role            VARCHAR(20)
created_at      DATETIME
```

### Tickets Table
```sql
id                INTEGER PRIMARY KEY
created_by_id     INTEGER (FK → users.id)
assigned_to_id    INTEGER (FK → users.id)
status            VARCHAR(20)
cable_type        VARCHAR(50)
cable_length      VARCHAR(20)
cable_gauge       VARCHAR(20)
location          VARCHAR(200)
notes             TEXT
priority          VARCHAR(20)
approval_token    VARCHAR(64) UNIQUE
rejection_reason  TEXT
created_at        DATETIME
updated_at        DATETIME
```

### Notifications Table
```sql
id                  INTEGER PRIMARY KEY
ticket_id           INTEGER (FK → tickets.id)
recipient_user_id   INTEGER (FK → users.id)
notification_type   VARCHAR(20)  -- 'sms' or 'email'
status              VARCHAR(20)  -- 'pending', 'sent', 'failed'
error_message       TEXT
sent_at             DATETIME
created_at          DATETIME
```

## API Endpoints

### Authentication
- `POST /api/register` - Create new user
- `POST /api/login` - Authenticate user

### Users
- `GET /api/users` - List all users
- `GET /api/users/<id>` - Get user by ID

### Tickets
- `GET /api/tickets` - List all tickets
- `GET /api/tickets/<id>` - Get ticket by ID
- `POST /api/tickets` - Create new ticket
- `PATCH /api/tickets/<id>` - Update ticket

### Approvals
- `GET /api/tickets/<id>/approve/<token>` - Approve via link
- `POST /api/tickets/<id>/reject/<token>` - Reject via link

### Dashboard
- `GET /api/dashboard/stats` - Get statistics

### Health
- `GET /api/health` - Health check

## Deployment Options

### 1. Local Development
```bash
docker-compose up
# Access: http://localhost:3000
```

### 2. CoreWeave (Kubernetes)
```bash
helm install cable-ticketing ./helm-chart
# Access via LoadBalancer IP
```

### 3. Other Kubernetes
Works on any K8s cluster (GKE, EKS, AKS, etc.)

### 4. Manual Deployment
Backend and frontend can be deployed separately to any hosting platform.

## Cost Analysis

### Development (Free)
- Docker: Free
- SQLite: Free
- Local testing: Free

### Production (Monthly)
- **CoreWeave**: ~$10-30 (CPU nodes, storage, network)
- **Twilio**: $1 phone + $0.0075 per SMS (~$5-10 for 1000 SMS)
- **SendGrid**: Free (up to 100 emails/day)
- **Total**: ~$16-45/month for small team

## Security Features

- Password hashing (werkzeug.security)
- Token-based approval links (secrets.token_urlsafe)
- Environment variable configuration (no hardcoded secrets)
- Kubernetes secrets for sensitive data
- Input validation on all endpoints
- CORS enabled for frontend-backend communication

## Scalability

**Current Design:**
- Handles 5-20 users easily
- ~100 tickets/day
- Synchronous notification sending

**For Scale (100+ users):**
- Add Celery + Redis for async notifications
- Switch to PostgreSQL
- Enable Kubernetes autoscaling
- Add caching (Redis)
- Implement rate limiting

## Future Enhancements

### Phase 1 (Easy Wins)
- [ ] PostgreSQL migration
- [ ] Ticket search/filtering
- [ ] User profile editing
- [ ] Ticket comments
- [ ] Attachment support (photos, diagrams)

### Phase 2 (Medium Effort)
- [ ] Celery for async notifications
- [ ] Real-time updates (WebSockets)
- [ ] Email reply parsing
- [ ] SMS reply parsing
- [ ] Advanced reporting

### Phase 3 (Advanced)
- [ ] Mobile app (React Native)
- [ ] Integration with inventory systems
- [ ] QR code scanning
- [ ] Barcode generation
- [ ] Analytics dashboard
- [ ] Multi-tenant support

## Learning Outcomes

By building this project, you've gained experience with:

1. **Full-Stack Development**
   - React frontend
   - Flask REST API
   - Database design

2. **DevOps**
   - Docker containerization
   - Docker Compose
   - Kubernetes deployment
   - Helm charts

3. **Cloud Platforms**
   - CoreWeave deployment
   - LoadBalancer configuration
   - Persistent storage

4. **Third-Party APIs**
   - Twilio SMS
   - SendGrid Email

5. **Best Practices**
   - Environment configuration
   - Secret management
   - API design
   - Documentation

## Use Cases Beyond Cabling

This architecture can be adapted for:
- **IT Support Tickets**: Help desk system
- **Facility Requests**: Maintenance, repairs
- **Equipment Checkout**: Borrow/return tracking
- **Inventory Management**: Stock requests
- **Approval Workflows**: Any request/approve pattern

## Performance Metrics

**Expected Performance:**
- API Response: < 200ms
- Ticket Creation: < 500ms (with notifications)
- Page Load: < 2s
- Concurrent Users: 50+
- Throughput: 100+ requests/second

## Support & Resources

- **Documentation**: README.md, DEPLOYMENT.md, TESTING.md
- **Quick Start**: ./quick-start.sh
- **Logs**: `docker-compose logs` or `kubectl logs`
- **Issues**: Check logs and troubleshooting sections

---

**Project Status**: ✅ Production Ready

**Last Updated**: February 2026

**Maintainer**: Lamar (lkennethwells@gmail.com)
