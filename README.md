# Cable Ticketing System

A Jira-like ticketing application for managing cable requests. Built with React frontend, Flask backend, and fully containerized with Docker and Kubernetes support.

## The Problem It Solves

- Technician needs 100ft of Cat6 cable for a new office
- Currently: Phone call, email, or walk to inventory room
- Problem: No tracking, no accountability, chaos

**With this system:** Technician creates a ticket (30 seconds) -> Inventory staff gets SMS + Email instantly -> One-click approve/reject -> Automatic status tracking -> Full audit trail.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User's Browser                       │
│                   (React Frontend - Port 3000)              │
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
    │SQLite/  │    │ Twilio  │    │ Resend/  │
    │Postgres │    │  (SMS)  │    │ SendGrid │
    └─────────┘    └─────────┘    └──────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, React Router v6, Axios, CSS3 |
| Backend | Flask 3.0, SQLAlchemy, Gunicorn |
| Database | PostgreSQL (Docker/RDS), SQLite supported for local tests |
| Notifications | Resend/SendGrid (email), Twilio/AWS SNS (SMS) |
| DevOps | Docker, Docker Compose, Helm, Kubernetes |

## Quick Start

### Prerequisites

- Docker & Docker Compose (or Node.js 18+ and Python 3.11+ for local dev)
- Resend or SendGrid account (for email)
- Twilio account (for SMS, optional)

### Option A: Docker Compose

```bash
cd ticketing_app
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

docker-compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:5000
```

### Option B: Run Locally

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
# Runs at http://localhost:5000

# Frontend (separate terminal)
cd frontend
npm install
npm start
# Runs at http://localhost:3000
```

> **Note (macOS):** If port 5000 is taken by AirPlay Receiver, change the backend port to 5001 in `docker-compose.yml` and `run.py`.

### First Steps

1. Open http://localhost:3000
2. Click **Register** and create a user (username, email, phone, password)
3. Create a second user (for assigning tickets)
4. Log in and create a cable request ticket
5. The assignee receives SMS + Email with approve/reject links

## Configuration

Edit `backend/.env`:

```bash
# Flask / DB
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+psycopg2://ticketing:ticketing@postgres:5432/ticketing

# Resend (Email - primary)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=onboarding@resend.dev

# SendGrid (Email - fallback)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Twilio (SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# App URL (for notification links)
APP_URL=http://localhost:3000

# Optional: comma-separated admin emails for optics request alerts.
# If unset, all users with role=admin are notified.
OPTICS_ALERT_EMAILS=you@example.com,team@example.com
```

## Workflow

```
Create Ticket → Pending Approval → Approved/Rejected → In Progress → Fulfilled
```

1. **User A** creates a cable request ticket
2. **User B** (assignee) receives SMS + Email with approve/reject links
3. **User B** clicks approve/reject link
4. **User A** receives notification of the decision
5. If approved, **User B** marks as "In Progress" then "Fulfilled"

### Ticket Statuses

`pending_approval` → `approved` / `rejected` → `in_progress` → `fulfilled` → `closed`

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user

`/api/login` and `/api/register` return `access_token` (Bearer token).  
Use `Authorization: Bearer <token>` for mutating endpoints such as:
- `POST /api/tickets`
- `PATCH /api/tickets/<id>`
- `DELETE /api/tickets/<id>`
- `POST /api/cable-receiving`
- `POST /api/optics-requests`
- `PATCH /api/optics-requests/<id>/status`

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
- `GET /api/health` - Health check

### Inventory (New)
- `POST /api/cable-receiving` - Record inbound cable inventory (admin)
- `GET /api/cable-receiving` - List receiving records
- `GET /api/inventory/movements` - List inventory ledger movements
- `GET /api/inventory/on-hand` - View on-hand quantity by cable type/length

### Optics Requests
- `GET /api/optics-parts` - List allowed optics parts plus `Other`
- `POST /api/optics-requests` - Submit optics request (authenticated users)
- `GET /api/optics-requests` - List optics requests (users see their own, admin sees all)
- `PATCH /api/optics-requests/<id>/status` - Admin action (`approve`, `deny`, `archive`)

## Ops Safety

- Backend no longer auto-seeds users on every boot (`RUN_SEED_ON_START=false` by default).
- Docker services include health checks in `docker-compose.yml`.
- Use backup scripts:
  - `ops/postgres_backup.sh`
  - `ops/postgres_restore.sh /path/to/ticketing.dump`

## Database Schema

### Users
```sql
id, username, email, phone, password_hash, role, created_at
```

### Tickets
```sql
id, created_by_id, assigned_to_id, status, cable_type, cable_length,
cable_gauge, location, notes, priority, approval_token, rejection_reason,
created_at, updated_at
```

### Notifications
```sql
id, ticket_id, recipient_user_id, notification_type, status,
error_message, sent_at, created_at
```

## Testing

### Quick Test (Without SMS/Email)

The app works without notification services configured -- notifications fail gracefully.

1. Start the app, register two users
2. Create a ticket as User 1, assigned to User 2
3. Get the approval token from backend logs or database:
   ```bash
   docker-compose exec backend python -c "
   from app import create_app, db
   from app.models import Ticket
   app = create_app()
   with app.app_context():
       ticket = Ticket.query.first()
       if ticket:
           print(f'http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
   "
   ```
4. Visit the approval URL to approve, then complete the workflow

### API Testing with curl

```bash
# Health check
curl http://localhost:5000/api/health

# Register
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","phone":"+12025551234","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Create ticket
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"created_by_id":1,"assigned_to_id":2,"cable_type":"Cat6","cable_length":"100ft","cable_gauge":"23AWG","location":"Building A","priority":"medium"}'
```

### Test Checklist

- [ ] Users can register and login
- [ ] Tickets can be created with all fields
- [ ] Notifications are sent (if configured)
- [ ] Approval/rejection links work
- [ ] Status updates work through full lifecycle
- [ ] Dashboard shows correct stats
- [ ] Filters work (All, Created by Me, Assigned to Me)
- [ ] Responsive on mobile

## Project Structure

```
ticketing_app/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory + config
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── routes.py            # API endpoints
│   │   └── notifications.py     # SMS/Email logic
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/          # LoginForm, RegisterForm, TicketForm, TicketList
│   │   ├── pages/               # Dashboard, ApprovalPage
│   │   ├── App.js
│   │   └── index.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── helm-chart/                  # Kubernetes deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── .do/app.yaml                 # DigitalOcean config
├── docker-compose.yml
├── DEPLOYMENT.md                # Deployment guides
└── DEMO_GUIDE.md                # Demo & presentation materials
```

## Troubleshooting

### Email not sending
- Check Resend API key in `backend/.env`
- Verify sender email is valid for your Resend plan (`onboarding@resend.dev` for free tier)
- Free tier can only send to the account owner's email

### SMS not sending
- Check Twilio credentials in `backend/.env`
- Verify phone numbers include country code (+1234567890)
- Check Twilio account balance

### Frontend can't reach backend
- Check `APP_URL` environment variable
- Verify backend is running: `curl http://localhost:5000/api/health`
- Check nginx proxy config in `frontend/nginx.conf`

### Database issues
- For production, switch to PostgreSQL
- Reset local DB: `docker-compose down -v && docker-compose up -d`

## Production Recommendations

1. Use PostgreSQL instead of SQLite
2. Enable HTTPS via Ingress + cert-manager
3. Add Celery + Redis for async notification sending
4. Set up monitoring (Prometheus + Grafana)
5. Use managed secrets (Kubernetes Secrets, Vault)

## License

MIT License

---

**Maintainer:** Lamar Wells (lkennethwells@gmail.com)
