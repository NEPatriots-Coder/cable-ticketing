# Demo & Presentation Guide

Everything you need to demo the Cable Ticketing System to stakeholders.

---

## Quick Setup (5 minutes)

### 1. Start the Application
```bash
cd ticketing_app
docker-compose up --build
# OR: ./quick-start.sh
```
Wait for services to be running.

### 2. Open Browser
Navigate to: **http://localhost:3000**

### 3. Create Demo Users

**User 1 - Alice (Technician):**
- Username: `alice_tech`
- Email: `alice@company.com`
- Phone: `+12025551234`
- Password: `demo123`

**User 2 - Bob (Inventory):**
- Logout, then Register
- Username: `bob_inventory`
- Email: `bob@company.com`
- Phone: `+12025555678`
- Password: `demo123`

Or seed users automatically:
```bash
docker compose exec backend python seed_users.py
```

---

## Demo Script (10 minutes)

### Act 1: Alice Needs Cable (2 min)

**Login as Alice** (`alice_tech` / `demo123`)

1. Show the dashboard: "This is our cable ticketing system -- here's the dashboard with ticket statistics"
2. Scroll to "Create New Cable Request" and fill out:
   - **Assign To:** Bob (bob_inventory)
   - **Priority:** High
   - **Cable Type:** Cat6
   - **Length:** 100ft
   - **Gauge:** 23AWG
   - **Location:** Building A, Floor 3, Server Room
   - **Notes:** "Urgent - New office setup needs network connectivity by EOD"
3. Click **Create Ticket**

**Point out:**
- Success message appears
- Ticket shows in "Created by Me" with status "pending approval"
- Dashboard stats updated
- "In production, Bob receives SMS + Email right now with approve/reject links"

### Act 2: Bob Approves (2 min)

**Logout and login as Bob** (`bob_inventory` / `demo123`)

1. Click **"Assigned to Me"** filter
2. Show the cable request from Alice

**Get approval link** (if not using live notifications):
```bash
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Ticket
app = create_app()
with app.app_context():
    ticket = Ticket.query.order_by(Ticket.id.desc()).first()
    if ticket:
        print(f'http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
"
```

3. Paste approval URL in browser -- show "Request Approved!"
4. Status changes from "pending approval" to "approved"

### Act 3: Bob Fulfills (2 min)

**As Bob (still logged in):**
1. Click **"Start Work"** -- status changes to "in_progress"
2. Click **"Mark Fulfilled"** -- status changes to "fulfilled"
3. Show dashboard: 1 fulfilled ticket, full audit trail visible

### Act 4: Alice Sees Completion (1 min)

**Logout and login as Alice:**
1. Click **"Created by Me"** filter
2. Ticket status = "Fulfilled" -- Alice knows her cable is ready

---

## Key Talking Points

### Problem It Solves
- **Before:** Phone calls, emails, sticky notes, no tracking
- **After:** Digital workflow, instant notifications, full audit trail

### Features
1. Simple ticket creation (30 seconds)
2. Instant SMS + Email notifications
3. One-click approve/reject (no login needed from notification)
4. Real-time dashboard with stats
5. Complete tracking from creation to fulfillment

### Technical Highlights
- Fully containerized (Docker)
- Kubernetes-ready (Helm chart included)
- Deploys to CoreWeave or DigitalOcean
- Mobile responsive
- Secure token-based approvals

### Cost
- **Development:** $0 (built in-house)
- **Production:** $15-40/month
  - CoreWeave: $10-30 (compute + storage)
  - Twilio: $1 + ~$0.0075 per SMS
  - SendGrid/Resend: Free tier available

### Elevator Pitch (30 seconds)
"This is our cable ticketing system -- think Jira for cable management. Technicians submit requests in 30 seconds. Inventory staff get instant SMS and email with one-click approve or reject. Everything is tracked and works on any device. It's containerized and deploys to Kubernetes. Cost is under $40/month."

---

## Pre-Demo Checklist

### 24 Hours Before
- [ ] Start app and verify services run
- [ ] Register test users (or run seed script)
- [ ] Walk through full workflow: create ticket -> approve -> fulfill
- [ ] Check dashboard stats and filters work
- [ ] Test on mobile browser (responsive design)

### 2 Hours Before
- [ ] Restart services: `docker-compose restart`
- [ ] Have terminal open with `docker-compose logs -f backend`
- [ ] Have approval URL command copied and ready
- [ ] Presentation file ready: `Cable_Ticketing_Stakeholder_Presentation.pptx`
- [ ] Browser tabs ready: localhost:3000 (logged out) + empty tab for approval URL

### Right Before (15 min)
- [ ] `docker-compose ps` -- services running
- [ ] `curl http://localhost:5000/api/health` -- backend healthy
- [ ] Open http://localhost:3000 -- frontend loads
- [ ] Mental rehearsal of the 4-act demo script

### Emergency Backup
```bash
# Port conflict
lsof -i :3000
lsof -i :5000
kill -9 [PID]

# Fresh start
docker-compose down -v
docker-compose up -d
```

If the live demo fails: pivot to slide-based walkthrough with screenshots.

---

## Stakeholder Email Template

### Full Version

**Subject:** Cable Ticketing System - Demo & Implementation Proposal

Hi [Team/Stakeholder Name],

I'm excited to share a new **Cable Ticketing System** I've built to streamline our cable request workflow.

**Problem:** Cable requests happen via phone/email with no tracking, leading to lost requests, manual follow-ups, and zero visibility.

**Solution:** A web-based ticketing system where:
1. Technicians submit cable requests (30 seconds)
2. Inventory staff receive SMS + Email with one-click approve/reject
3. System tracks everything from creation to fulfillment

**Key Features:**
- Instant notifications (SMS + Email)
- Real-time dashboard
- Mobile-friendly
- Complete audit trail
- Production-ready (Docker + Kubernetes)

**Cost:** $15-40/month in production

I'd love to show you a **live demo** (10 min) and discuss implementation. Can we schedule 30 minutes this week?

Best regards,
**Lamar Wells**

### Short Version

**Subject:** New Cable Ticketing System - Ready for Demo

Hi Team,

I built a **cable ticketing system** to replace our current phone/email process.

**What it does:** Technicians submit requests via web form -> Inventory gets SMS/Email with approve/reject links -> System tracks everything.

**Cost:** $15-40/month | **Status:** Production-ready

**Next step:** 30-min demo + discussion?

Thanks,
Lamar

---

## Common Stakeholder Questions

**Q: How much does it cost?**
A: $15-40/month (CoreWeave $10-30, Twilio $1 + usage, Resend/SendGrid free tier)

**Q: How long to deploy?**
A: 4 weeks (staging -> testing -> production -> training)

**Q: Can it scale?**
A: Yes -- Kubernetes autoscaling, handles 100+ users easily.

**Q: Is it secure?**
A: Password hashing, token-based approvals, Kubernetes secrets, no hardcoded credentials.

**Q: What if someone loses the notification?**
A: They can log into the web dashboard anytime. Notifications are supplementary.

**Q: Can we add more features?**
A: Modular architecture -- easy to add attachments, comments, integrations.

**Q: Why not use Jira/ServiceNow?**
A: Simpler, cheaper ($40 vs $100s/month), focused on one workflow, fully customizable.

---

## Post-Demo Actions

- [ ] Send thank-you email with presentation attached
- [ ] Share project access if requested
- [ ] Schedule follow-up meeting
- [ ] Document feedback and feature requests
- [ ] Begin deployment if approved
