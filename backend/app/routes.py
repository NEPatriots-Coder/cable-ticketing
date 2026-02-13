from flask import Blueprint, request, jsonify
from app.models import User, Ticket, Notification
from app.notifications import notify_ticket_created, notify_status_change
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

api = Blueprint('api', __name__)

# ============= AUTH ROUTES =============

@api.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json or {}

    # Make registration idempotent for demo/testing flows:
    # if user already exists by username or email, return that user
    # instead of failing with 400.
    existing_user = User.find_by_username_or_email(data.get('username'), data.get('email'))
    if existing_user:
        return jsonify({
            'message': 'User already exists',
            'user': existing_user.to_dict()
        }), 200

    if not all([data.get('username'), data.get('email'), data.get('phone'), data.get('password')]):
        return jsonify({'error': 'username, email, phone, and password are required'}), 400

    user = User.create(
        username=data['username'],
        email=data['email'],
        phone=data['phone'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'user'),
    )

    return jsonify({'message': 'User created', 'user': user.to_dict()}), 201

@api.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json or {}
    user = User.find_by_username(data.get('username'))

    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200

# ============= USER ROUTES =============

@api.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.all()
    return jsonify([user.to_dict() for user in users]), 200

@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user"""
    user = User.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

# ============= TICKET ROUTES =============

@api.route('/tickets', methods=['GET'])
def get_tickets():
    """Get all tickets"""
    tickets = Ticket.all()
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

@api.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get specific ticket"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    return jsonify(ticket.to_dict()), 200

@api.route('/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    data = request.json or {}

    required = ['created_by_id', 'assigned_to_id', 'items']
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    items = data['items']
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'error': 'items must be a non-empty list'}), 400
    for item in items:
        if not all(item.get(f) for f in ['cable_type', 'cable_length', 'quantity']):
            return jsonify({'error': 'Each item requires cable_type, cable_length, and quantity'}), 400

    try:
        created_by_id = int(data['created_by_id'])
        assigned_to_id = int(data['assigned_to_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'created_by_id and assigned_to_id must be integers'}), 400

    creator = User.get(created_by_id)
    assignee = User.get(assigned_to_id)
    if not creator or not assignee:
        return jsonify({'error': 'created_by_id and assigned_to_id must reference valid users'}), 400

    ticket = Ticket.create(
        created_by_id=created_by_id,
        assigned_to_id=assigned_to_id,
        items=items,
        location=data.get('location'),
        notes=data.get('notes'),
        priority=data.get('priority', 'medium'),
    )

    # Send notifications
    notify_ticket_created(ticket)

    return jsonify({'message': 'Ticket created', 'ticket': ticket.to_dict()}), 201

@api.route('/tickets/<int:ticket_id>', methods=['PATCH'])
def update_ticket(ticket_id):
    """Update ticket status"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    data = request.json or {}

    old_status = ticket.status
    updates = {}
    if 'status' in data:
        updates['status'] = data['status']
    if 'rejection_reason' in data:
        updates['rejection_reason'] = data['rejection_reason']

    ticket = Ticket.update_fields(ticket_id, updates) if updates else ticket

    # Notify if status changed significantly
    if old_status != ticket.status and ticket.status in ['approved', 'rejected', 'fulfilled']:
        notify_status_change(ticket, ticket.status)

    return jsonify({'message': 'Ticket updated', 'ticket': ticket.to_dict()}), 200

@api.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    # Only the creator can delete
    data = request.json or {}
    user_id = data.get('user_id')
    if user_id and ticket.created_by_id != user_id:
        return jsonify({'error': 'Only the ticket creator can delete this ticket'}), 403

    Notification.delete_by_ticket_id(ticket.id)
    Ticket.delete(ticket.id)

    return jsonify({'message': 'Ticket deleted'}), 200

# ============= APPROVAL ROUTES (Token-based) =============

@api.route('/tickets/<int:ticket_id>/approve/<token>', methods=['GET', 'POST'])
def approve_ticket(ticket_id, token):
    """Approve a ticket via token link"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.approval_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if ticket.status != 'pending_approval':
        return jsonify({'message': 'Ticket already processed', 'status': ticket.status}), 200

    ticket = Ticket.update_fields(ticket.id, {'status': 'approved'})

    # Notify creator
    notify_status_change(ticket, 'approved')

    return jsonify({
        'message': 'Ticket approved successfully!',
        'ticket': ticket.to_dict()
    }), 200

@api.route('/tickets/<int:ticket_id>/reject/<token>', methods=['GET', 'POST'])
def reject_ticket(ticket_id, token):
    """Reject a ticket via token link"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.approval_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if ticket.status != 'pending_approval':
        return jsonify({'message': 'Ticket already processed', 'status': ticket.status}), 200

    # Get rejection reason from query params or body
    reason = request.args.get('reason') or request.json.get('reason') if request.json else None

    ticket = Ticket.update_fields(
        ticket.id,
        {
            'status': 'rejected',
            'rejection_reason': reason or 'No reason provided',
        }
    )

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
    total_tickets = Ticket.count_all()
    pending = Ticket.count_by_status('pending_approval')
    approved = Ticket.count_by_status('approved')
    rejected = Ticket.count_by_status('rejected')
    fulfilled = Ticket.count_by_status('fulfilled')

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
