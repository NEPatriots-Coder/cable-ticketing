# MongoDB Setup and Usage for This Project

This backend now uses MongoDB via `pymongo` (not SQLAlchemy).

## 1. Backend Install

```bash
cd /Users/lwells/Desktop/ticketing_app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Start MongoDB (Docker, persistent)

```bash
docker run -d \
  --name ticketing-mongo \
  -p 27017:27017 \
  -v ticketing-mongo-data:/data/db \
  mongo:7
```

The named volume `ticketing-mongo-data` makes data persistent across container restarts/recreates.

## 3. Configure Environment

In `backend/.env`, confirm:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=ticketing
```

## 4. Run Backend

```bash
cd /Users/lwells/Desktop/ticketing_app/backend
source .venv/bin/activate
python run.py
```

Backend runs at:
- `http://localhost:5001`

## 5. Health Check

```bash
curl http://localhost:5001/api/health
```

## 6. Query MongoDB

If `mongosh` is not installed locally, use it inside the running Mongo container:

```bash
docker exec -it ticketing-mongo mongosh
```

Then run:

```javascript
use ticketing
show collections
db.users.find().pretty()
db.tickets.find().pretty()
db.notifications.find().pretty()
db.counters.find().pretty()
db.tickets.find({ status: "pending_approval" }).pretty()
```

## 7. Persistence Behavior

Your Mongo data persists when:
- Backend is stopped/restarted
- Mongo container is stopped/restarted
- Mongo container is removed and recreated using the same volume name (`ticketing-mongo-data`)

Data is deleted only if you explicitly remove the volume, such as:
- `docker volume rm ticketing-mongo-data`
- `docker compose down -v` (if that volume is part of the compose project)

Check volume exists:

```bash
docker volume ls | grep ticketing-mongo-data
```

## 8. Important Project Note

Current `docker-compose.yml` still reflects older SQL-style environment values and does not define a MongoDB service yet.

So for now:
- run Mongo with `docker run ...` above, or
- update compose to include a `mongo` service and pass `MONGO_URI` to backend.
