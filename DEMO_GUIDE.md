# 🎬 Stakeholder Demo Guide

## Quick Setup (5 minutes)

### 1. Start the Application
```bash
cd /sessions/loving-exciting-heisenberg/mnt/ticketing_app
./quick-start.sh
```

Wait for: `✅ Services are running!`

### 2. Open in Browser
Navigate to: **http://localhost:3000**

---

## 🎭 Demo Script (10 minutes)

### **Setup: Create Two Users**

**User 1 - Technician (Alice)**
1. Click **Register**
2. Fill in:
   - Username: `alice_tech`
   - Email: `alice@company.com`
   - Phone: `+12025551234`
   - Password: `demo123`
3. Click **Register**

**User 2 - Inventory Staff (Bob)**
1. Logout (top right)
2. Click **Register**
3. Fill in:
   - Username: `bob_inventory`
   - Email: `bob@company.com`
   - Phone: `+12025555678`
   - Password: `demo123`
4. Click **Register**

---

## 📋 Demo Scenario: "Building A Cable Request"

### **Act 1: Alice Needs Cable (2 min)**

**Login as Alice** (`alice_tech` / `demo123`)

**Show the Dashboard:**
- "This is our cable ticketing system"
- "Here's the dashboard showing all ticket statistics"
- "Notice: 0 tickets currently"

**Create a Ticket:**
1. Scroll to "Create New Cable Request"
2. Fill out the form:
   - **Assign To:** Bob (bob_inventory)
   - **Priority:** High
   - **Cable Type:** Cat6
   - **Length:** 100ft
   - **Gauge:** 23AWG
   - **Location:** Building A, Floor 3, Server Room
   - **Notes:** "Urgent - New office setup needs network connectivity by EOD"
3. Click **Create Ticket**

**Point out:**
- ✅ Success message appears
- ✅ Ticket appears in "Created by Me" section
- ✅ Status: "pending approval"
- ✅ Dashboard stats updated (1 total, 1 pending)
- 📱 "In production, Bob would receive SMS + Email right now with approve/reject links"

---

### **Act 2: Bob Receives & Approves (2 min)**

**Logout and Login as Bob** (`bob_inventory` / `demo123`)

**Show Bob's View:**
- Click **"Assigned to Me"** filter
- "Bob sees the cable request from Alice"
- Show the ticket card with all details

**Demo the Approval (Manual Method):**

Since we're not using SMS/Email for this demo, get the approval link:

```bash
# Open a terminal
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Ticket
app = create_app()
with app.app_context():
    ticket = Ticket.query.first()
    if ticket:
        print(f'\nApproval URL to copy/paste:')
        print(f'http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
"
```

**Approve the Ticket:**
1. Copy the approval URL from terminal
2. Paste into browser
3. Show the approval page: ✅ "Request Approved!"
4. Click "Go to Dashboard"

**Show Updated Ticket:**
- Status changed from "pending approval" → "approved"
- Dashboard stats updated
- 📱 "Alice would receive notification of approval"

---

### **Act 3: Bob Fulfills the Request (2 min)**

**As Bob (still logged in):**

1. Find the approved ticket
2. Click **"Start Work"** button
   - Status changes to "in_progress"
3. Click **"Mark Fulfilled"** button
   - Status changes to "fulfilled"
   - 📱 "Alice would get notification that cable is ready"

**Show the completed workflow:**
- Dashboard shows: 1 fulfilled ticket
- Full audit trail visible
- Timeline from creation → approval → fulfillment

---

### **Act 4: Alice Sees Completion (1 min)**

**Logout and Login as Alice:**

1. View dashboard
2. Click **"Created by Me"** filter
3. Show the ticket: Status = "Fulfilled"
4. "Alice knows her cable request is complete!"

---

## 🎯 Key Demo Points to Emphasize

### **Problem It Solves:**
❌ Before: Phone calls, emails, sticky notes, no tracking
✅ After: Digital workflow, instant notifications, full audit trail

### **Key Features:**
1. **Simple Ticket Creation** - 30 seconds to submit request
2. **Instant Notifications** - SMS + Email (production)
3. **One-Click Approve/Reject** - No login needed from notification
4. **Real-Time Dashboard** - See all tickets and stats
5. **Full Tracking** - Complete history of every request

### **Technical Highlights:**
- 🐳 Fully containerized (Docker)
- ☸️ Kubernetes-ready (Helm chart included)
- 🚀 Deploys to CoreWeave cloud
- 📱 Mobile responsive
- 🔐 Secure token-based approvals
- 💰 Cost-effective (~$15-40/month for production)

---

## 📱 Production Notification Demo

If you set up Twilio/SendGrid, show this:

**SMS Example:**
```
Cable Request from alice_tech:

Type: Cat6
Length: 100ft
Gauge: 23AWG
Location: Building A, Floor 3, Server Room

Approve: [link]
Reject: [link]
```

**Email Example:**
Show professional HTML email with:
- Formatted ticket details
- Big green "Approve" and red "Reject" buttons
- Ticket metadata

---

## 🎤 Elevator Pitch (30 seconds)

"This is our cable ticketing system - think Jira for cable management. Technicians submit requests in 30 seconds. Inventory staff get instant SMS and email notifications with one-click approve or reject. Everything is tracked, audited, and works on any device. It's fully containerized and deploys to our CoreWeave Kubernetes cluster. Cost is under $40/month for our team size."

---

## 💡 Common Stakeholder Questions

**Q: How much does it cost?**
A: ~$15-40/month in production (CoreWeave compute + Twilio SMS + SendGrid email)

**Q: How long did it take to build?**
A: MVP built in one sprint. Production-ready with Docker + Kubernetes deployment.

**Q: Can it scale?**
A: Yes - Kubernetes autoscaling, can handle 100+ users easily. Built for growth.

**Q: Is it secure?**
A: Yes - password hashing, token-based approvals, Kubernetes secrets, environment variable config.

**Q: What if someone loses the notification?**
A: They can log into the web app anytime. Dashboard shows all assigned tickets.

**Q: Can we add more features?**
A: Absolutely. Built with modular architecture. Easy to add attachments, comments, integrations, etc.

**Q: Why not use existing tools like Jira?**
A:
- Simpler - focused on one workflow
- Cheaper - $40/month vs $100s/month
- Customizable - we control everything
- Learning opportunity - great for DevOps practice

---

## 📊 Success Metrics to Track

After deployment, measure:
- ⏱️ Average request-to-fulfillment time
- 📈 Tickets per day/week
- ✅ Approval rate (approved vs rejected)
- 🎯 Response time (creation → approval)
- 💬 User adoption rate

---

## 🎥 Demo Tips

1. **Practice first** - Run through the demo twice before presenting
2. **Have terminal ready** - For showing approval URLs
3. **Clear browser cache** - Fresh start
4. **Screenshot important screens** - Backup if live demo fails
5. **Have production screenshots** - Show SMS/Email examples even without live config
6. **Prepare for questions** - Review the FAQ section above

---

## 🚀 Next Steps After Demo

If stakeholders approve:

1. **Week 1:** Set up Twilio + SendGrid for production notifications
2. **Week 2:** Deploy to CoreWeave staging environment
3. **Week 3:** User testing with 5-10 team members
4. **Week 4:** Production rollout

---

## 📸 Screenshots to Prepare

Take these screenshots for a slide deck:

1. Login page
2. Registration page
3. Dashboard with stats
4. Ticket creation form
5. Ticket list with filters
6. Approval page
7. SMS notification (mock or real)
8. Email notification (mock or real)
9. Kubernetes deployment (kubectl get pods)
10. Architecture diagram

---

**Good luck with your demo! 🎉**
