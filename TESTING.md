# Testing Guide

Complete guide for testing the Cable Ticketing System locally.

## Quick Test (Without SMS/Email)

You can test the full application workflow without configuring Twilio/SendGrid. Notifications will fail gracefully and be logged.

### 1. Start the Application

```bash
./quick-start.sh
# OR
docker-compose up --build
```

### 2. Create Test Users

Navigate to http://localhost:3000

**User 1 (Technician):**
- Username: `tech1`
- Email: `tech1@example.com`
- Phone: `+12025551234`
- Password: `password123`

**User 2 (Inventory Staff):**
- Username: `inventory1`
- Email: `inventory1@example.com`
- Phone: `+12025555678`
- Password: `password123`

### 3. Test Workflow

**As tech1:**
1. Login
2. Create a ticket:
   - Assign to: inventory1
   - Cable Type: Cat6
   - Length: 100ft
   - Gauge: 23AWG
   - Location: Building A, Floor 3
   - Notes: Urgent - needed by EOD
   - Priority: High
3. Click "Create Ticket"
4. You'll see success message
5. Check the ticket list - status should be "pending approval"

**As inventory1:**
1. Logout from tech1
2. Login as inventory1
3. View the ticket in "Assigned to Me" tab
4. In production, inventory1 would receive SMS + Email

**Test Approval (Manual):**

Since you don't have SMS/Email configured yet, test approval links manually:

```bash
# Get the approval token from backend logs
docker-compose logs backend | grep "approval_token"

# Or check the database
docker-compose exec backend python -c "
from app import create_app, db
from app.models import Ticket
app = create_app()
with app.app_context():
    ticket = Ticket.query.first()
    if ticket:
        print(f'Ticket ID: {ticket.id}')
        print(f'Approval Token: {ticket.approval_token}')
        print(f'Approve URL: http://localhost:3000/tickets/{ticket.id}/approve/{ticket.approval_token}')
        print(f'Reject URL: http://localhost:3000/tickets/{ticket.id}/reject/{ticket.approval_token}')
"
```

Visit the approve URL in your browser to approve the ticket.

### 4. Test Full Lifecycle

1. **Approve** the ticket (using URL above)
2. **As inventory1**, mark ticket as "In Progress"
3. **Mark as Fulfilled**
4. **As tech1**, view the fulfilled ticket

## Full Test (With SMS/Email)

### 1. Configure Twilio (SMS)

**Get Twilio credentials:**
1. Sign up at https://www.twilio.com/try-twilio
2. Get a phone number ($1/month + usage)
3. Copy your Account SID, Auth Token, and Phone Number

**Update backend/.env:**
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### 2. Configure SendGrid (Email)

**Get SendGrid API key:**
1. Sign up at https://signup.sendgrid.com/
2. Create an API key (Settings > API Keys)
3. Copy the API key

**Update backend/.env:**
```bash
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

**Verify sender email:**
- Go to SendGrid > Settings > Sender Authentication
- Verify your email address

### 3. Restart Services

```bash
docker-compose restart backend
```

### 4. Test End-to-End

1. Create ticket as tech1
2. Inventory1 receives **SMS** with approve/reject links
3. Inventory1 receives **Email** with approve/reject buttons
4. Click approve in SMS or email
5. Tech1 receives notification of approval
6. Complete the workflow!

## API Testing with curl

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Register User
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "phone": "+12025551234",
    "password": "password123"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### Get All Users
```bash
curl http://localhost:5000/api/users
```

### Create Ticket
```bash
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "created_by_id": 1,
    "assigned_to_id": 2,
    "cable_type": "Cat6",
    "cable_length": "100ft",
    "cable_gauge": "23AWG",
    "location": "Building A",
    "notes": "Test ticket",
    "priority": "medium"
  }'
```

### Get All Tickets
```bash
curl http://localhost:5000/api/tickets
```

### Get Dashboard Stats
```bash
curl http://localhost:5000/api/dashboard/stats
```

## Database Testing

### Access SQLite Database

```bash
# Enter backend container
docker-compose exec backend sh

# Open database
sqlite3 instance/ticketing.db

# View tables
.tables

# View users
SELECT * FROM users;

# View tickets
SELECT * FROM tickets;

# View notifications
SELECT * FROM notifications;

# Exit
.quit
exit
```

### Reset Database

```bash
# Stop containers
docker-compose down

# Remove database
docker-compose exec backend rm -f instance/ticketing.db

# Or remove the volume
docker volume rm ticketing_app_backend-data

# Restart
docker-compose up -d
```

## Load Testing

### Install Apache Bench

```bash
# Ubuntu/Debian
sudo apt-get install apache2-utils

# macOS
brew install httpd
```

### Test API Performance

```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:5000/api/health

# Test tickets endpoint (GET)
ab -n 500 -c 5 http://localhost:5000/api/tickets
```

## Common Test Scenarios

### Scenario 1: Multiple Approvals

1. Create 5 tickets with different priorities
2. Assign all to same user
3. User receives 5 SMS + 5 emails
4. Approve 3, reject 2
5. Verify status updates

### Scenario 2: Concurrent Requests

```bash
# Create 10 tickets simultaneously
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/tickets \
    -H "Content-Type: application/json" \
    -d '{
      "created_by_id": 1,
      "assigned_to_id": 2,
      "cable_type": "Cat6",
      "cable_length": "'$i'00ft",
      "cable_gauge": "23AWG",
      "priority": "medium"
    }' &
done
wait
```

### Scenario 3: Large Data Set

Create 100 tickets and test:
- Pagination (if implemented)
- Search/filter performance
- Dashboard stats

### Scenario 4: Invalid Data

Test error handling:
```bash
# Missing required field
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "created_by_id": 1,
    "assigned_to_id": 2
  }'

# Invalid user ID
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "created_by_id": 999,
    "assigned_to_id": 2,
    "cable_type": "Cat6",
    "cable_length": "100ft",
    "cable_gauge": "23AWG"
  }'
```

## Frontend Testing

### Manual UI Tests

**Registration:**
- ✅ Can register with valid data
- ✅ Shows error for duplicate username
- ✅ Shows error for duplicate email
- ✅ Validates phone format
- ✅ Validates password

**Login:**
- ✅ Can login with correct credentials
- ✅ Shows error for wrong password
- ✅ Shows error for non-existent user
- ✅ Redirects to dashboard after login

**Ticket Creation:**
- ✅ All fields render correctly
- ✅ Can select assignee from dropdown
- ✅ Can set priority
- ✅ Required fields are validated
- ✅ Success message appears
- ✅ Ticket appears in list

**Ticket List:**
- ✅ Shows all tickets
- ✅ Filters work (All, Created by Me, Assigned to Me)
- ✅ Status badges display correctly
- ✅ Priority badges display correctly
- ✅ Can update ticket status

**Approval Page:**
- ✅ Approve link works
- ✅ Reject link prompts for reason
- ✅ Shows ticket details
- ✅ Displays success message
- ✅ Invalid token shows error

### Responsive Testing

Test on different screen sizes:
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667)

### Browser Testing

Test on:
- Chrome
- Firefox
- Safari
- Edge

## Performance Benchmarks

Expected performance (on standard hardware):

| Metric | Target | Measurement |
|--------|--------|-------------|
| Health endpoint | < 50ms | `ab -n 100 -c 1` |
| Get tickets | < 200ms | `ab -n 100 -c 1` |
| Create ticket | < 500ms | With notifications |
| Frontend load | < 2s | Initial page load |
| API under load | > 50 req/s | `ab -n 1000 -c 10` |

## Debugging

### View Logs

```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Check Container Status

```bash
docker-compose ps
```

### Restart Services

```bash
# Restart backend
docker-compose restart backend

# Restart frontend
docker-compose restart frontend

# Restart all
docker-compose restart
```

### Check Network

```bash
# Enter backend container
docker-compose exec backend sh

# Test if frontend is reachable
curl http://frontend

# Test external APIs
curl https://api.twilio.com
```

## Test Checklist

Before deployment, verify:

- [ ] Users can register and login
- [ ] Tickets can be created
- [ ] Notifications are sent (if configured)
- [ ] Approval links work
- [ ] Rejection requires reason
- [ ] Status updates work
- [ ] Dashboard shows correct stats
- [ ] Filters work
- [ ] Frontend is responsive
- [ ] API handles errors gracefully
- [ ] Database persists data
- [ ] Logs are accessible
- [ ] Performance is acceptable

## Production Testing

After deploying to CoreWeave:

```bash
# Test health
curl https://your-domain.com/api/health

# Test from external phone
# Create ticket and verify SMS received

# Load test
ab -n 1000 -c 10 https://your-domain.com/api/health

# Monitor resources
kubectl top pods -n cable-ticketing
```

## Troubleshooting Tests

### SMS Not Received

1. Check Twilio logs in Twilio console
2. Verify phone number format (+1234567890)
3. Check Twilio account balance
4. View backend logs: `docker-compose logs backend | grep -i twilio`

### Email Not Received

1. Check spam folder
2. Verify sender email in SendGrid
3. Check SendGrid activity feed
4. View backend logs: `docker-compose logs backend | grep -i sendgrid`

### Database Not Persisting

1. Check volume: `docker volume ls`
2. Verify PVC in Kubernetes: `kubectl get pvc`
3. Check database path in logs

### Frontend Can't Reach Backend

1. Check network: `docker network ls`
2. Verify nginx config
3. Check backend is running: `curl http://localhost:5000/api/health`
4. View frontend logs for proxy errors

---

**Happy Testing! 🧪**
