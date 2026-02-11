# 🚀 Quick Start for Stakeholder Demo

## ⚡ Super Fast Setup (5 minutes)

### Step 1: Start the App
```bash
cd ticketing_app
./quick-start.sh
```

Wait for: `✅ Services are running!`

### Step 2: Open Browser
Go to: **http://localhost:3000**

### Step 3: Create Demo Users

**User 1 - Alice (Technician):**
- Click Register
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

### Step 4: Demo the Workflow

**As Alice:**
1. Create ticket: Cat6, 100ft, 23AWG, Building A
2. Assign to: Bob
3. Show: Ticket created, status "pending approval"

**Get Approval URL:**
```bash
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Ticket
app = create_app()
with app.app_context():
    ticket = Ticket.query.first()
    print(f'http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
"
```

**As Bob:**
1. Login as bob_inventory
2. View assigned ticket
3. Copy/paste approval URL
4. Approve!
5. Mark as In Progress → Fulfilled

**Done!** ✨

---

## 📧 Email to Stakeholders

**Subject:** Cable Ticketing System - Live Demo Available

Hi [Name],

I've built a **cable ticketing system** to streamline our request workflow.

**What:** Web app for cable requests with SMS/Email notifications
**Cost:** $15-40/month
**Status:** Production-ready, deploys to CoreWeave

**Live demo running at:** http://localhost:3000
- Username: `demo_user` / Password: `demo123` (create your own!)

Or schedule 30-min demo + Q&A?

Attached: 14-slide presentation with full details.

Thanks,
Lamar

---

## 📁 Files Ready for Stakeholders

Your project folder has everything:

- ✅ **Cable_Ticketing_Stakeholder_Presentation.pptx** - 14 slides
- ✅ **DEMO_GUIDE.md** - Step-by-step demo script
- ✅ **README.md** - Complete documentation
- ✅ **DEPLOYMENT.md** - CoreWeave deployment guide
- ✅ **TESTING.md** - Testing instructions
- ✅ **PROJECT_OVERVIEW.md** - Technical deep dive

---

## 🎬 2-Minute Elevator Pitch

"We currently handle cable requests via phone and email - stuff gets lost, there's no tracking, lots of manual follow-ups.

I built a ticketing system: technicians submit requests in a web form, inventory staff get SMS and email with approve/reject links, everything is tracked.

It's production-ready: Docker containers, Kubernetes deployment, runs on CoreWeave. Costs about $30/month.

Want to see it? Takes 10 minutes."

---

## ✅ You're Ready!

Everything is complete:
- ✅ Working application
- ✅ Professional presentation
- ✅ Complete documentation
- ✅ Docker + Kubernetes ready
- ✅ Email templates
- ✅ Demo scripts

**Just run `./quick-start.sh` and you're good to go!** 🚀
