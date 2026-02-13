from datetime import datetime
import secrets

from flask_login import UserMixin
from pymongo import ReturnDocument

from app import get_db, login_manager


def _next_sequence(counter_name):
    db = get_db()
    result = db.counters.find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result["seq"]


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(int(user_id))
    except (TypeError, ValueError):
        return None


class User(UserMixin):
    def __init__(self, doc):
        self.doc = doc
        self.id = doc["id"]
        self.username = doc["username"]
        self.email = doc["email"]
        self.phone = doc["phone"]
        self.password_hash = doc["password_hash"]
        self.role = doc.get("role", "user")
        self.created_at = doc.get("created_at")

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
        }

    @staticmethod
    def _collection():
        return get_db().users

    @classmethod
    def _from_doc(cls, doc):
        return cls(doc) if doc else None

    @classmethod
    def create(cls, username, email, phone, password_hash, role="user"):
        now = datetime.utcnow()
        doc = {
            "id": _next_sequence("users"),
            "username": username,
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": role,
            "created_at": now,
        }
        cls._collection().insert_one(doc)
        return cls(doc)

    @classmethod
    def get(cls, user_id):
        return cls._from_doc(cls._collection().find_one({"id": user_id}))

    @classmethod
    def find_by_username(cls, username):
        return cls._from_doc(cls._collection().find_one({"username": username}))

    @classmethod
    def find_by_username_or_email(cls, username, email):
        return cls._from_doc(
            cls._collection().find_one(
                {"$or": [{"username": username}, {"email": email}]}
            )
        )

    @classmethod
    def all(cls):
        return [cls(doc) for doc in cls._collection().find().sort("created_at", -1)]


class Ticket:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc["id"]
        self.created_by_id = doc["created_by_id"]
        self.assigned_to_id = doc["assigned_to_id"]
        self.status = doc.get("status", "pending_approval")
        self.items = doc.get("items", [
            {
                "cable_type": doc.get("cable_type", ""),
                "cable_length": doc.get("cable_length", ""),
                "quantity": doc.get("cable_gauge", doc.get("quantity", "")),
            }
        ])
        self.location = doc.get("location")
        self.notes = doc.get("notes")
        self.priority = doc.get("priority", "medium")
        self.approval_token = doc["approval_token"]
        self.rejection_reason = doc.get("rejection_reason")
        self.created_at = doc.get("created_at")
        self.updated_at = doc.get("updated_at")

    @property
    def creator(self):
        return User.get(self.created_by_id)

    @property
    def assignee(self):
        return User.get(self.assigned_to_id)

    def to_dict(self):
        creator = self.creator
        assignee = self.assignee
        return {
            "id": self.id,
            "created_by": creator.to_dict() if creator else None,
            "assigned_to": assignee.to_dict() if assignee else None,
            "status": self.status,
            "items": self.items,
            "location": self.location,
            "notes": self.notes,
            "priority": self.priority,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def _collection():
        return get_db().tickets

    @classmethod
    def _from_doc(cls, doc):
        return cls(doc) if doc else None

    @classmethod
    def create(
        cls,
        created_by_id,
        assigned_to_id,
        items,
        location=None,
        notes=None,
        priority="medium",
    ):
        now = datetime.utcnow()
        doc = {
            "id": _next_sequence("tickets"),
            "created_by_id": created_by_id,
            "assigned_to_id": assigned_to_id,
            "status": "pending_approval",
            "items": items,
            "location": location,
            "notes": notes,
            "priority": priority,
            "approval_token": secrets.token_urlsafe(32),
            "rejection_reason": None,
            "created_at": now,
            "updated_at": now,
        }
        cls._collection().insert_one(doc)
        return cls(doc)

    @classmethod
    def get(cls, ticket_id):
        return cls._from_doc(cls._collection().find_one({"id": ticket_id}))

    @classmethod
    def all(cls):
        return [cls(doc) for doc in cls._collection().find().sort("created_at", -1)]

    @classmethod
    def update_fields(cls, ticket_id, updates):
        updates["updated_at"] = datetime.utcnow()
        cls._collection().update_one({"id": ticket_id}, {"$set": updates})
        return cls.get(ticket_id)

    @classmethod
    def delete(cls, ticket_id):
        cls._collection().delete_one({"id": ticket_id})

    @classmethod
    def count_all(cls):
        return cls._collection().count_documents({})

    @classmethod
    def count_by_status(cls, status):
        return cls._collection().count_documents({"status": status})


class Notification:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc["id"]
        self.ticket_id = doc["ticket_id"]
        self.recipient_user_id = doc["recipient_user_id"]
        self.notification_type = doc["notification_type"]
        self.status = doc.get("status", "pending")
        self.error_message = doc.get("error_message")
        self.sent_at = doc.get("sent_at")
        self.created_at = doc.get("created_at")

    @property
    def recipient(self):
        return User.get(self.recipient_user_id)

    def to_dict(self):
        recipient = self.recipient
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "recipient": recipient.to_dict() if recipient else None,
            "type": self.notification_type,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def _collection():
        return get_db().notifications

    @classmethod
    def create(
        cls,
        ticket_id,
        recipient_user_id,
        notification_type,
        status="pending",
        error_message=None,
        sent_at=None,
    ):
        doc = {
            "id": _next_sequence("notifications"),
            "ticket_id": ticket_id,
            "recipient_user_id": recipient_user_id,
            "notification_type": notification_type,
            "status": status,
            "error_message": error_message,
            "sent_at": sent_at,
            "created_at": datetime.utcnow(),
        }
        cls._collection().insert_one(doc)
        return cls(doc)

    @classmethod
    def delete_by_ticket_id(cls, ticket_id):
        cls._collection().delete_many({"ticket_id": ticket_id})
