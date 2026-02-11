# 📋 Pre-Demo Checklist

Use this checklist before presenting to stakeholders to ensure everything works smoothly.

## ⏰ 24 Hours Before Demo

### 1. Test the Application
```bash
cd /path/to/ticketing_app
./quick-start.sh
```

- [ ] Services start successfully
- [ ] Can access http://localhost:3000
- [ ] Backend API responds at http://localhost:5000/api/health

### 2. Create Test Users
- [ ] Register "alice_tech" (technician)
- [ ] Register "bob_inventory" (inventory staff)
- [ ] Both users can login/logout

### 3. Test Full Workflow
- [ ] Alice creates a ticket
- [ ] Ticket appears in Alice's "Created by Me"
- [ ] Ticket appears in Bob's "Assigned to Me"
- [ ] Get approval URL from backend logs
- [ ] Approve ticket via URL
- [ ] Status updates correctly
- [ ] Bob can mark as "In Progress" → "Fulfilled"

### 4. Check Dashboard
- [ ] Statistics display correctly
- [ ] Filters work (All, Created by Me, Assigned to Me)
- [ ] Ticket cards show all information

### 5. Test on Different Devices (Optional but Recommended)
- [ ] Desktop browser (Chrome/Firefox)
- [ ] Laptop browser
- [ ] Mobile browser (responsive design)

---

## 🎯 2 Hours Before Demo

### 1. Environment Prep
- [ ] Restart services: `docker-compose restart`
- [ ] Clear old test data (optional): `docker-compose down -v && docker-compose up -d`
- [ ] Services are running: `docker-compose ps`

### 2. Have URLs Ready
```bash
# Frontend
http://localhost:3000

# Backend health check
http://localhost:5000/api/health

# Get approval URL command ready
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

### 3. Backup Materials Ready
- [ ] Presentation file: `Cable_Ticketing_Stakeholder_Presentation.pptx`
- [ ] Demo guide open: `DEMO_GUIDE.md`
- [ ] Email template ready: `STAKEHOLDER_EMAIL.md`

### 4. Terminal/Command Prompt Setup
- [ ] Open 2 terminals:
  - Terminal 1: `cd ticketing_app && docker-compose logs -f backend`
  - Terminal 2: For approval URL command
- [ ] Browser tabs ready:
  - Tab 1: http://localhost:3000 (logged out)
  - Tab 2: Empty (for approval URL testing)

---

## 🎬 Right Before Demo (15 min before)

### 1. Final System Check
```bash
# Check services
docker-compose ps

# Check logs for errors
docker-compose logs --tail=50 | grep -i error

# Test health
curl http://localhost:5000/api/health
```

### 2. Create Fresh Demo Users (If Needed)
Only if you want a completely fresh demo:
```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Wait 10 seconds
sleep 10

# Create users via UI or API
```

### 3. Open & Test Everything
- [ ] Open browser to http://localhost:3000
- [ ] Registration page loads
- [ ] Login page loads
- [ ] Docker logs are visible (terminal open)
- [ ] Approval URL command copied and ready

### 4. Mental Rehearsal (5 min)
Walk through the demo script mentally:
1. Show login page
2. Register alice_tech
3. Create ticket
4. Show notification (explain SMS/Email)
5. Logout, login as bob_inventory
6. Show assigned ticket
7. Get approval URL
8. Approve
9. Show status change
10. Mark as fulfilled

---

## 🚨 Emergency Backup Plans

### If Services Won't Start
```bash
# Check what's using ports
lsof -i :3000
lsof -i :5000

# Kill if needed
kill -9 [PID]

# Try again
docker-compose up -d
```

### If Database is Corrupted
```bash
# Nuclear option - fresh start
docker-compose down -v
rm -rf backend/instance/
docker-compose up -d
```

### If Demo Machine Fails
- Have presentation ready on a different machine
- Have screenshots/video as backup
- Pivot to slide-based walkthrough

---

## 📱 SMS/Email Demo (If Configured)

Only if you set up Twilio + SendGrid:

### Before Demo
- [ ] Twilio credentials in `backend/.env`
- [ ] SendGrid API key in `backend/.env`
- [ ] Phone number verified with Twilio
- [ ] Email address verified with SendGrid
- [ ] Test SMS: Create ticket to your own phone
- [ ] Test Email: Check inbox for email

### During Demo
- [ ] Show SMS on phone (screenshot or real-time)
- [ ] Show email in inbox (open in browser)
- [ ] Click approve link from SMS
- [ ] Click approve button from email

---

## 🎤 Presentation Checklist

### Materials
- [ ] Laptop/computer charged
- [ ] Presentation file downloaded
- [ ] Demo environment running
- [ ] Internet connection stable (if showing remote deployment)

### Slide Deck Ready
- [ ] Open `Cable_Ticketing_Stakeholder_Presentation.pptx`
- [ ] Test slideshow mode
- [ ] Slides display correctly
- [ ] Presentation mode works (full screen)

### Speaking Points Prepared
- [ ] Problem statement clear
- [ ] Solution benefits memorized
- [ ] Cost breakdown ready
- [ ] Timeline prepared
- [ ] Answers to common questions ready

---

## ❓ Common Questions - Have Answers Ready

**Q: How much does it cost?**
A: $15-40/month (CoreWeave $10-30, Twilio $1 + usage, SendGrid free)

**Q: How long to deploy?**
A: 4 weeks (staging → testing → production → training)

**Q: Can it scale?**
A: Yes, built on Kubernetes with autoscaling. Handles 100+ users easily.

**Q: Is it secure?**
A: Yes - password hashing, token-based approvals, Kubernetes secrets, no hardcoded credentials.

**Q: What if SMS/Email fails?**
A: Users can always log into the web dashboard. Notifications are supplementary.

**Q: Can we customize it?**
A: Absolutely. Built with modular architecture. Easy to add features.

**Q: Why not use Jira/ServiceNow?**
A: Simpler, cheaper, focused on one workflow, fully customizable, great DevOps learning.

**Q: What happens after you leave?**
A: Complete documentation, containerized, standard tech stack (React/Flask). Any developer can maintain.

---

## ✅ Final Go/No-Go Decision

**GO if:**
- ✅ Services running successfully
- ✅ Can create users and tickets
- ✅ Approval workflow works
- ✅ Presentation ready
- ✅ Feeling confident

**NO-GO if:**
- ❌ Services won't start
- ❌ Critical errors in logs
- ❌ Can't complete basic workflow

**NO-GO Actions:**
- Reschedule demo
- Send presentation first as "preview"
- Offer async demo (video recording)

---

## 🎯 Success Criteria

**Demo is successful if:**
- Stakeholders understand the problem & solution
- They see the working application
- Cost/timeline are clear
- Questions are answered
- Next steps are defined

**You DON'T need:**
- Perfect, bug-free demo
- All features working
- SMS/Email live (can explain/show screenshots)

**Remember:** Even if something breaks, you have:
- Working presentation
- Clear documentation
- Containerized deployment
- Real, functional code

---

## 🚀 Post-Demo Actions

After successful demo:
- [ ] Send thank-you email with presentation attached
- [ ] Share project folder access (if requested)
- [ ] Schedule follow-up meeting
- [ ] Document feedback and feature requests
- [ ] Update timeline based on discussion
- [ ] Begin Week 1 tasks if approved

---

**You got this! 🎉**

The app is production-ready, fully documented, and shows real DevOps skills. Even if the live demo has hiccups, you have a polished presentation and working code to fall back on.

Good luck!
