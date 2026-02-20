from datetime import datetime, timezone
import secrets

from flask_login import UserMixin
from sqlalchemy import func

from app import db, login_manager


def _utcnow():
    return datetime.now(timezone.utc)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(int(user_id))
    except (TypeError, ValueError):
        return None


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
        }

    @classmethod
    def create(cls, username, email, phone, password_hash, role='user'):
        user = cls(
            username=username,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_username_or_email(cls, username, email):
        return cls.query.filter((cls.username == username) | (cls.email == email)).first()

    @classmethod
    def all(cls):
        return cls.query.order_by(cls.created_at.desc()).all()


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, default='pending_approval', index=True)
    items = db.Column(db.JSON, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(50), nullable=False, default='medium')
    approval_token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    deleted_by_id = db.Column(db.Integer, nullable=True)
    deleted_previous_status = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)

    creator_rel = db.relationship('User', foreign_keys=[created_by_id], lazy='joined')
    assignee_rel = db.relationship('User', foreign_keys=[assigned_to_id], lazy='joined')

    @property
    def creator(self):
        return self.creator_rel

    @property
    def assignee(self):
        return self.assignee_rel

    def to_dict(self):
        creator = self.creator
        assignee = self.assignee
        return {
            'id': self.id,
            'created_by': creator.to_dict() if creator else None,
            'assigned_to': assignee.to_dict() if assignee else None,
            'status': self.status,
            'items': self.items or [],
            'location': self.location,
            'notes': self.notes,
            'priority': self.priority,
            'rejection_reason': self.rejection_reason,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by_id': self.deleted_by_id,
            'deleted_previous_status': self.deleted_previous_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create(cls, created_by_id, assigned_to_id, items, location=None, notes=None, priority='medium'):
        now = _utcnow()
        ticket = cls(
            created_by_id=created_by_id,
            assigned_to_id=assigned_to_id,
            status='pending_approval',
            items=items,
            location=location,
            notes=notes,
            priority=priority,
            approval_token=secrets.token_urlsafe(32),
            rejection_reason=None,
            deleted_at=None,
            deleted_by_id=None,
            deleted_previous_status=None,
            created_at=now,
            updated_at=now,
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket

    @classmethod
    def get(cls, ticket_id):
        return db.session.get(cls, ticket_id)

    @classmethod
    def all(cls, include_deleted=False):
        query = cls.query
        if not include_deleted:
            query = query.filter(cls.status != 'deleted')
        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def update_fields(cls, ticket_id, updates):
        ticket = cls.get(ticket_id)
        if not ticket:
            return None
        updates = dict(updates or {})
        updates['updated_at'] = _utcnow()
        for key, value in updates.items():
            setattr(ticket, key, value)
        db.session.commit()
        return ticket

    @classmethod
    def soft_delete(cls, ticket_id, deleted_by_id=None, previous_status=None):
        ticket = cls.get(ticket_id)
        if not ticket or ticket.status == 'deleted':
            class Result:
                matched_count = 0
            return Result()

        ticket.status = 'deleted'
        ticket.deleted_at = _utcnow()
        ticket.updated_at = _utcnow()
        ticket.deleted_previous_status = previous_status
        if deleted_by_id is not None:
            ticket.deleted_by_id = deleted_by_id
        db.session.commit()

        class Result:
            matched_count = 1
        return Result()

    @classmethod
    def restore(cls, ticket_id):
        ticket = cls.get(ticket_id)
        if not ticket:
            return None
        if ticket.status != 'deleted':
            return ticket
        ticket.status = ticket.deleted_previous_status or 'pending_approval'
        ticket.updated_at = _utcnow()
        ticket.deleted_at = None
        ticket.deleted_by_id = None
        ticket.deleted_previous_status = None
        db.session.commit()
        return ticket

    @classmethod
    def hard_delete(cls, ticket_id):
        ticket = cls.get(ticket_id)
        if not ticket:
            class Result:
                deleted_count = 0
            return Result()
        db.session.delete(ticket)
        db.session.commit()

        class Result:
            deleted_count = 1
        return Result()

    @classmethod
    def count_all(cls, include_deleted=False):
        query = cls.query
        if not include_deleted:
            query = query.filter(cls.status != 'deleted')
        return query.count()

    @classmethod
    def count_by_status(cls, status):
        return cls.query.filter_by(status=status).count()


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False, index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)

    recipient_rel = db.relationship('User', foreign_keys=[recipient_user_id], lazy='joined')

    @property
    def recipient(self):
        return self.recipient_rel

    def to_dict(self):
        recipient = self.recipient
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'recipient': recipient.to_dict() if recipient else None,
            'type': self.notification_type,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create(cls, ticket_id, recipient_user_id, notification_type, status='pending', error_message=None, sent_at=None):
        item = cls(
            ticket_id=ticket_id,
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            status=status,
            error_message=error_message,
            sent_at=sent_at,
            created_at=_utcnow(),
        )
        db.session.add(item)
        db.session.commit()
        return item

    @classmethod
    def delete_by_ticket_id(cls, ticket_id):
        cls.query.filter_by(ticket_id=ticket_id).delete(synchronize_session=False)
        db.session.commit()


class CableReceipt(db.Model):
    __tablename__ = 'cable_receiving'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vendor = db.Column(db.String(255), nullable=True)
    po_number = db.Column(db.String(255), nullable=True)
    storage_location = db.Column(db.String(255), nullable=True)
    items = db.Column(db.JSON, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    received_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)

    receiver_rel = db.relationship('User', foreign_keys=[received_by_id], lazy='joined')

    @property
    def receiver(self):
        return self.receiver_rel

    def to_dict(self):
        receiver = self.receiver
        return {
            'id': self.id,
            'vendor': self.vendor,
            'po_number': self.po_number,
            'storage_location': self.storage_location,
            'items': self.items or [],
            'notes': self.notes,
            'received_by': receiver.to_dict() if receiver else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create(cls, received_by_id, items, vendor=None, po_number=None, storage_location=None, notes=None):
        now = _utcnow()
        item = cls(
            vendor=vendor,
            po_number=po_number,
            storage_location=storage_location,
            items=items,
            notes=notes,
            received_by_id=received_by_id,
            received_at=now,
            created_at=now,
        )
        db.session.add(item)
        db.session.commit()
        return item

    @classmethod
    def all(cls):
        return cls.query.order_by(cls.received_at.desc()).all()

    @classmethod
    def get(cls, receipt_id):
        return db.session.get(cls, receipt_id)

    @classmethod
    def delete_by_id(cls, receipt_id):
        item = cls.get(receipt_id)
        if item:
            db.session.delete(item)
            db.session.commit()


class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movement_type = db.Column(db.String(50), nullable=False, index=True)
    source_type = db.Column(db.String(100), nullable=True, index=True)
    source_id = db.Column(db.Integer, nullable=True, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cable_type = db.Column(db.String(120), nullable=False, index=True)
    cable_length = db.Column(db.String(120), nullable=False, index=True)
    quantity_delta = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'movement_type': self.movement_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'actor_user_id': self.actor_user_id,
            'cable_type': self.cable_type,
            'cable_length': self.cable_length,
            'quantity_delta': self.quantity_delta,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create_many(cls, movement_docs):
        if not movement_docs:
            return []

        now = _utcnow()
        rows = []
        for raw in movement_docs:
            rows.append(
                cls(
                    movement_type=raw['movement_type'],
                    source_type=raw.get('source_type'),
                    source_id=raw.get('source_id'),
                    actor_user_id=raw.get('actor_user_id'),
                    cable_type=raw['cable_type'],
                    cable_length=raw['cable_length'],
                    quantity_delta=int(raw['quantity_delta']),
                    notes=raw.get('notes'),
                    created_at=now,
                )
            )
        db.session.add_all(rows)
        db.session.commit()
        return rows

    @classmethod
    def exists_for_source(cls, source_type, source_id):
        return cls.query.filter_by(source_type=source_type, source_id=source_id).first() is not None

    @classmethod
    def list(cls, movement_type=None, source_type=None, source_id=None, limit=200):
        query = cls.query
        if movement_type:
            query = query.filter_by(movement_type=movement_type)
        if source_type:
            query = query.filter_by(source_type=source_type)
        if source_id is not None:
            query = query.filter_by(source_id=source_id)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def summary_on_hand(cls):
        rows = (
            db.session.query(
                cls.cable_type,
                cls.cable_length,
                func.sum(cls.quantity_delta).label('on_hand'),
            )
            .group_by(cls.cable_type, cls.cable_length)
            .order_by(cls.cable_type.asc(), cls.cable_length.asc())
            .all()
        )
        return [
            {
                'cable_type': row.cable_type,
                'cable_length': row.cable_length,
                'on_hand': int(row.on_hand or 0),
            }
            for row in rows
        ]
