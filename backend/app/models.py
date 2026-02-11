from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import secrets

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_tickets = db.relationship('Ticket', foreign_keys='Ticket.created_by_id', backref='creator', lazy=True)
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id', backref='assignee', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'role': self.role
        }

class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)

    # User relationships
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Status
    status = db.Column(db.String(20), default='pending_approval')
    # Status options: pending_approval, approved, rejected, in_progress, fulfilled, closed

    # Cable specifications
    cable_type = db.Column(db.String(50), nullable=False)
    cable_length = db.Column(db.String(20), nullable=False)
    cable_gauge = db.Column(db.String(20), nullable=False)

    # Additional info
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high

    # Approval
    approval_token = db.Column(db.String(64), unique=True)
    rejection_reason = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super(Ticket, self).__init__(**kwargs)
        if not self.approval_token:
            self.approval_token = secrets.token_urlsafe(32)

    def to_dict(self):
        return {
            'id': self.id,
            'created_by': self.creator.to_dict(),
            'assigned_to': self.assignee.to_dict(),
            'status': self.status,
            'cable_type': self.cable_type,
            'cable_length': self.cable_length,
            'cable_gauge': self.cable_gauge,
            'location': self.location,
            'notes': self.notes,
            'priority': self.priority,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # sms, email
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    ticket = db.relationship('Ticket', backref='notifications')
    recipient = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'recipient': self.recipient.to_dict(),
            'type': self.notification_type,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat()
        }
