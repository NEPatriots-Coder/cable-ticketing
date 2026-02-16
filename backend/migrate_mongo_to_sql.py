#!/usr/bin/env python3
"""One-time migration from MongoDB ticketing DB to SQL database."""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

from app import create_app, db
from app.models import User, Ticket, Notification, CableReceipt, InventoryMovement


def _parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def main():
    load_dotenv()

    mongo_uri = os.getenv('MIGRATION_MONGO_URI', os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
    mongo_db_name = os.getenv('MIGRATION_MONGO_DB_NAME', os.getenv('MONGO_DB_NAME', 'ticketing'))
    truncate_first = os.getenv('MIGRATION_TRUNCATE_FIRST', 'false').lower() == 'true'

    app = create_app()
    mongo = MongoClient(mongo_uri)[mongo_db_name]

    with app.app_context():
        if truncate_first:
            db.session.query(Notification).delete()
            db.session.query(InventoryMovement).delete()
            db.session.query(CableReceipt).delete()
            db.session.query(Ticket).delete()
            db.session.query(User).delete()
            db.session.commit()

        id_maps = {
            'users': {},
            'tickets': {},
            'receipts': {},
            'movements': {},
            'notifications': {},
        }

        # Users
        for doc in mongo.users.find().sort('id', 1):
            existing = User.find_by_username(doc.get('username'))
            if existing:
                id_maps['users'][doc['id']] = existing.id
                continue
            user = User(
                username=doc['username'],
                email=doc['email'],
                phone=doc.get('phone', ''),
                password_hash=doc.get('password_hash', ''),
                role=doc.get('role', 'user'),
                created_at=_parse_dt(doc.get('created_at')) or datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.flush()
            id_maps['users'][doc['id']] = user.id
        db.session.commit()

        # Tickets
        for doc in mongo.tickets.find().sort('id', 1):
            created_by_id = id_maps['users'].get(doc.get('created_by_id'))
            assigned_to_id = id_maps['users'].get(doc.get('assigned_to_id'))
            if not created_by_id or not assigned_to_id:
                continue
            ticket = Ticket(
                created_by_id=created_by_id,
                assigned_to_id=assigned_to_id,
                status=doc.get('status', 'pending_approval'),
                items=doc.get('items', []),
                location=doc.get('location'),
                notes=doc.get('notes'),
                priority=doc.get('priority', 'medium'),
                approval_token=doc.get('approval_token') or f"migrated-{doc.get('id')}",
                rejection_reason=doc.get('rejection_reason'),
                deleted_at=_parse_dt(doc.get('deleted_at')),
                deleted_by_id=id_maps['users'].get(doc.get('deleted_by_id')),
                deleted_previous_status=doc.get('deleted_previous_status'),
                created_at=_parse_dt(doc.get('created_at')) or datetime.now(timezone.utc),
                updated_at=_parse_dt(doc.get('updated_at')) or datetime.now(timezone.utc),
            )
            db.session.add(ticket)
            db.session.flush()
            id_maps['tickets'][doc['id']] = ticket.id
        db.session.commit()

        # Cable receipts
        for doc in mongo.cable_receiving.find().sort('id', 1):
            receiver_id = id_maps['users'].get(doc.get('received_by_id'))
            if not receiver_id:
                continue
            receipt = CableReceipt(
                vendor=doc.get('vendor'),
                po_number=doc.get('po_number'),
                items=doc.get('items', []),
                notes=doc.get('notes'),
                received_by_id=receiver_id,
                received_at=_parse_dt(doc.get('received_at')) or datetime.now(timezone.utc),
                created_at=_parse_dt(doc.get('created_at')) or datetime.now(timezone.utc),
            )
            db.session.add(receipt)
            db.session.flush()
            id_maps['receipts'][doc['id']] = receipt.id
        db.session.commit()

        # Inventory movements
        for doc in mongo.inventory_movements.find().sort('id', 1):
            source_type = doc.get('source_type')
            source_id = doc.get('source_id')
            if source_type == 'cable_receiving':
                source_id = id_maps['receipts'].get(source_id)
            if source_type == 'ticket_fulfillment':
                source_id = id_maps['tickets'].get(source_id)
            movement = InventoryMovement(
                movement_type=doc.get('movement_type', 'adjustment'),
                source_type=source_type,
                source_id=source_id,
                actor_user_id=id_maps['users'].get(doc.get('actor_user_id')),
                cable_type=doc.get('cable_type', ''),
                cable_length=doc.get('cable_length', ''),
                quantity_delta=int(doc.get('quantity_delta', 0)),
                notes=doc.get('notes'),
                created_at=_parse_dt(doc.get('created_at')) or datetime.now(timezone.utc),
            )
            db.session.add(movement)
            db.session.flush()
            id_maps['movements'][doc['id']] = movement.id
        db.session.commit()

        # Notifications
        for doc in mongo.notifications.find().sort('id', 1):
            ticket_id = id_maps['tickets'].get(doc.get('ticket_id'))
            recipient_id = id_maps['users'].get(doc.get('recipient_user_id'))
            if not ticket_id or not recipient_id:
                continue
            notification = Notification(
                ticket_id=ticket_id,
                recipient_user_id=recipient_id,
                notification_type=doc.get('notification_type', 'email'),
                status=doc.get('status', 'pending'),
                error_message=doc.get('error_message'),
                sent_at=_parse_dt(doc.get('sent_at')),
                created_at=_parse_dt(doc.get('created_at')) or datetime.now(timezone.utc),
            )
            db.session.add(notification)
            db.session.flush()
            id_maps['notifications'][doc['id']] = notification.id
        db.session.commit()

        print('Migration complete')
        print(f"Users: {User.query.count()}")
        print(f"Tickets: {Ticket.query.count()}")
        print(f"Receipts: {CableReceipt.query.count()}")
        print(f"Movements: {InventoryMovement.query.count()}")
        print(f"Notifications: {Notification.query.count()}")


if __name__ == '__main__':
    main()
