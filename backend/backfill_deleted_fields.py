from datetime import datetime, timezone
import os

from dotenv import load_dotenv
from pymongo import MongoClient


def main():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "ticketing")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    tickets = db.tickets

    now = datetime.now(timezone.utc)
    result = tickets.update_many(
        {
            "$or": [
                {"deleted_at": {"$exists": False}},
                {"deleted_by_id": {"$exists": False}},
                {"deleted_previous_status": {"$exists": False}},
            ]
        },
        {
            "$set": {
                "deleted_at": None,
                "deleted_by_id": None,
                "deleted_previous_status": None,
                "updated_at": now,
            }
        },
    )
    print(f"Backfilled ticket delete metadata on {result.modified_count} documents")

    normalized = tickets.update_many(
        {"deleted_at": {"$ne": None}, "status": {"$ne": "deleted"}},
        {"$set": {"status": "deleted", "updated_at": now}},
    )
    print(f"Normalized deleted status on {normalized.modified_count} documents")


if __name__ == "__main__":
    main()
