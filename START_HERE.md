# 🚀 Fixed - Start Here!

## ✅ **What I Fixed**

Changed backend port from **5000 → 5001** to avoid port conflict with AirPlay Receiver (common on Mac).

---

## 📝 **Run These Commands**

```bash
# 1. Stop any running containers
docker compose down

# 2. Start fresh
docker compose up -d

# 3. Check status
docker compose ps
```

---

## 🌐 **Access the Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001/api/health

---

## ✅ **Quick Test**

```bash
# Test backend is running
curl http://localhost:5001/api/health

# Should return: {"status":"healthy","timestamp":"..."}
```

---

## 📋 **Demo Steps**

1. **Open browser**: http://localhost:3000
2. **Register user 1** (Technician):
   - Username: `alice_tech`
   - Email: `alice@company.com`
   - Phone: `+12025551234`
   - Password: `demo123`

3. **Register user 2** (Inventory):
   - Logout, then register
   - Username: `bob_inventory`
   - Email: `bob@company.com`
   - Phone: `+12025555678`
   - Password: `demo123`

4. **Create a ticket as Alice**:
   - Assign to: bob_inventory
   - Cable Type: Cat6
   - Length: 100ft
   - Gauge: 23AWG
   - Location: Building A

5. **Get approval URL**:
   ```bash
   docker compose exec backend python -c "
   from app import create_app, db
   from app.models import Ticket
   app = create_app()
   with app.app_context():
       ticket = Ticket.query.first()
       if ticket:
           print(f'http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
   "
   ```

6. **Approve the ticket**: Paste URL in browser

7. **View as Bob**: See approved ticket, mark as "In Progress" → "Fulfilled"

---

## 🚨 **Troubleshooting**

### If port 3000 is also in use:
Edit `docker-compose.yml` and change:
```yaml
ports:
  - "3001:80"  # Changed from 3000:80
```

### If containers won't start:
```bash
# View logs
docker compose logs

# Restart
docker compose restart
```

### If you need to reset everything:
```bash
docker compose down -v
docker compose up -d
```

---

## 📧 **Warnings You Can Ignore**

The warnings about Twilio/SendGrid are **normal**:
```
WARN[0000] The "TWILIO_ACCOUNT_SID" variable is not set
```

These are optional for the demo. The app works without them - you just won't get SMS/Email notifications.

---

## 🎉 **You're Ready!**

Run the commands above and your app will be live at:
- **http://localhost:3000** (Frontend)
- **http://localhost:5001** (Backend)

Then follow the demo steps or use `DEMO_GUIDE.md` for the full walkthrough! 🚀
