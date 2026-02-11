from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Ticket, Notification
from app.notifications import notify_ticket_created, notify_status_change
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

api = Blueprint('api', __name__)

# ============= AUTH ROUTES =============

@api.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        phone=data['phone'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'user')
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created', 'user': user.to_dict()}), 201

@api.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200

# ============= USER ROUTES =============

@api.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

# ============= TICKET ROUTES =============

@api.route('/tickets', methods=['GET'])
def get_tickets():
    """Get all tickets"""
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

@api.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get specific ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    return jsonify(ticket.to_dict()), 200

@api.route('/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    data = request.json

    ticket = Ticket(
        created_by_id=data['created_by_id'],
        assigned_to_id=data['assigned_to_id'],
        cable_type=data['cable_type'],
        cable_length=data['cable_length'],
        cable_gauge=data['cable_gauge'],
        location=data.get('location'),
        notes=data.get('notes'),
        priority=data.get('priority', 'medium')
    )

    db.session.add(ticket)
    db.session.commit()

    # Send notifications
    notify_ticket_created(ticket)

    return jsonify({'message': 'Ticket created', 'ticket': ticket.to_dict()}), 201

@api.route('/tickets/<int:ticket_id>', methods=['PATCH'])
def update_ticket(ticket_id):
    """Update ticket status"""
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.json

    old_status = ticket.status

    if 'status' in data:
        ticket.status = data['status']
    if 'rejection_reason' in data:
        ticket.rejection_reason = data['rejection_reason']

    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    # Notify if status changed significantly
    if old_status != ticket.status and ticket.status in ['approved', 'rejected', 'fulfilled']:
        notify_status_change(ticket, ticket.status)

    return jsonify({'message': 'Ticket updated', 'ticket': ticket.to_dict()}), 200

# ============= APPROVAL ROUTES (Token-based) =============

@api.route('/tickets/<int:ticket_id>/approve/<token>', methods=['GET', 'POST'])
def approve_ticket(ticket_id, token):
    """Approve a ticket via token link"""
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.approval_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if ticket.status != 'pending_approval':
        return jsonify({'message': 'Ticket already processed', 'status': ticket.status}), 200

    ticket.status = 'approved'
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    # Notify creator
    notify_status_change(ticket, 'approved')

    return jsonify({
        'message': 'Ticket approved successfully!',
        'ticket': ticket.to_dict()
    }), 200

@api.route('/tickets/<int:ticket_id>/reject/<token>', methods=['GET', 'POST'])
def reject_ticket(ticket_id, token):
    """Reject a ticket via token link"""
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.approval_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if ticket.status != 'pending_approval':
        return jsonify({'message': 'Ticket already processed', 'status': ticket.status}), 200

    # Get rejection reason from query params or body
    reason = request.args.get('reason') or request.json.get('reason') if request.json else None

    ticket.status = 'rejected'
    ticket.rejection_reason = reason or 'No reason provided'
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    # Notify creator
    notify_status_change(ticket, 'rejected')

    return jsonify({
        'message': 'Ticket rejected',
        'ticket': ticket.to_dict()
    }), 200

# ============= DASHBOARD ROUTES =============

@api.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    total_tickets = Ticket.query.count()
    pending = Ticket.query.filter_by(status='pending_approval').count()
    approved = Ticket.query.filter_by(status='approved').count()
    rejected = Ticket.query.filter_by(status='rejected').count()
    fulfilled = Ticket.query.filter_by(status='fulfilled').count()

    return jsonify({
        'total_tickets': total_tickets,
        'pending_approval': pending,
        'approved': approved,
        'rejected': rejected,
        'fulfilled': fulfilled
    }), 200

# ============= HEALTH CHECK =============

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200
