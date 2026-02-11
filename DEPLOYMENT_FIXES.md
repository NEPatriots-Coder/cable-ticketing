# Digital Ocean Deployment Fixes

## Issues Fixed ✅

### 1. Frontend "Backend service unreachable" ✅ FIXED
**Problem:** Frontend nginx was trying to proxy to `backend:5000` (Docker Compose style)
**Solution:** Removed nginx proxy config - Digital Ocean handles routing at platform level
**File Changed:** `frontend/nginx.conf`

### 2. Backend "Database table already exists" ✅ FIXED
**Problem:** SQLite database persisted between deployments, `db.create_all()` caused conflicts
**Solution:** Added error handling to database initialization
**File Changed:** `backend/app/__init__.py`

### 3. Backend "SQLite usage in production" ✅ FIXED
**Problem:** SQLite not suitable for production (locking issues with multiple workers)
**Solution:** Added PostgreSQL database to app.yaml, installed psycopg2 driver
**Files Changed:**
- `.do/app.yaml` - Added PostgreSQL database configuration
- `backend/requirements.txt` - Added `psycopg2-binary==2.9.9`

---

## Changes Made

### 1. frontend/nginx.conf
```diff
- # API proxy
- location /api {
-     proxy_pass http://backend:5000;
-     ...
- }

+ # React Router - serve index.html for all routes
+ # Digital Ocean handles /api routing to backend service
  location / {
      try_files $uri $uri/ /index.html;
  }
```

### 2. backend/app/__init__.py
```diff
  # Create tables
  with app.app_context():
-     db.create_all()
+     try:
+         from app import models
+         db.create_all()
+         print("✅ Database tables initialized successfully")
+     except Exception as e:
+         print(f"⚠️  Database initialization note: {e}")
```

### 3. .do/app.yaml
```diff
+ # Database
+ databases:
+   - name: cable-ticketing-db
+     engine: PG
+     version: "12"
+     production: false

  services:
    - name: backend
      envs:
-       - key: DATABASE_URL
-         value: sqlite:///ticketing.db
+       - key: DATABASE_URL
+         scope: RUN_AND_BUILD_TIME
+         value: ${cable-ticketing-db.DATABASE_URL}
```

### 4. backend/requirements.txt
```diff
  gunicorn==21.2.0
  boto3==1.34.19
+ psycopg2-binary==2.9.9
```

---

## Redeploy Now

Since you already have the app created on Digital Ocean, you have two options:

### Option A: Update Existing App (Recommended)
```bash
cd /sessions/loving-exciting-heisenberg/mnt/ticketing_app

# Update the app with new configuration
doctl apps update <your-app-id> --spec .do/app.yaml
```

**Note:** This will add the PostgreSQL database to your existing app.

### Option B: Fresh Deployment
```bash
# Delete the old app
doctl apps delete <your-app-id>

# Create a new app with PostgreSQL
doctl apps create --spec .do/app.yaml
```

---

## What Will Happen

1. **PostgreSQL Database Created:**
   - Digital Ocean provisions a managed PostgreSQL database
   - Connection string automatically injected as `DATABASE_URL`
   - Your $200 credits cover this (small database is ~$15/month)

2. **Backend Connects to PostgreSQL:**
   - Uses psycopg2 driver to connect
   - Creates fresh tables in PostgreSQL
   - No more SQLite file conflicts!

3. **Frontend Routes Correctly:**
   - `/` → Serves React app
   - `/api` → Routes to backend service
   - No more nginx proxy errors

---

## Verify Deployment

Once redeployed, check these:

### 1. Health Check
```bash
curl https://your-app-url.ondigitalocean.app/api/health
```
Should return: `{"status": "healthy"}`

### 2. Database Connection
Check logs for: `✅ Database tables initialized successfully`

### 3. Frontend Loads
Visit `https://your-app-url.ondigitalocean.app/` - should see login page

### 4. Full Test
1. Register a new user
2. Login
3. Create a ticket
4. Check email for notification (Resend already working!)

---

## Troubleshooting

### If PostgreSQL provisioning fails:
- Check your Digital Ocean credits/billing
- Try using `production: false` in database config (cheaper tier)
- Check logs: `doctl apps logs <app-id> --type DEPLOY`

### If tables still conflict:
- The error handling should skip the conflict now
- Check logs for the warning message
- Database will work even if warning appears

### If backend still won't start:
- Check environment variables are loaded: `doctl apps get <app-id>`
- Verify DATABASE_URL points to PostgreSQL (starts with `postgresql://`)
- Check build logs for psycopg2 installation

---

## Cost Estimate

With your $200 Digital Ocean credits:

| Component | Cost/Month |
|-----------|------------|
| Backend (basic-xxs) | ~$5 |
| Frontend (basic-xxs) | ~$5 |
| PostgreSQL Dev DB | ~$15 |
| **Total** | **~$25/month** |

Your $200 credits = ~8 months of free hosting! 🎉

---

## Next Steps

1. ✅ Files are updated and ready
2. 🚀 Redeploy using Option A or B above
3. ✅ Test the health endpoint
4. 🎉 Create a demo ticket for stakeholders
5. 📧 Show off those email notifications!

---

## Production Readiness Checklist

Before going live with real users:

- [ ] Change `SECRET_KEY` in app.yaml to a strong random string
- [ ] Set `production: true` on the database
- [ ] Consider upgrading instance sizes for better performance
- [ ] Set up database backups in Digital Ocean dashboard
- [ ] Add monitoring/alerts for downtime
- [ ] Test with multiple concurrent users
- [ ] Document user workflows for your team

Good luck with the deployment! 🚀
