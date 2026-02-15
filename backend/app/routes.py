from flask import Blueprint, current_app, request, jsonify
from app.models import User, Ticket, Notification, CableReceipt, InventoryMovement
from app.notifications import notify_ticket_created, notify_status_change
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime, timezone

api = Blueprint('api', __name__)

ALLOWED_STATUSES = {
    'pending_approval',
    'approved',
    'rejected',
    'in_progress',
    'fulfilled',
    'closed',
}
STATUS_TRANSITIONS = {
    'pending_approval': {'approved', 'rejected'},
    'approved': {'in_progress', 'closed'},
    'rejected': {'closed'},
    'in_progress': {'fulfilled', 'closed'},
    'fulfilled': {'closed'},
    'closed': set(),
}


def _token_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='auth-token-v1')


def _issue_access_token(user):
    return _token_serializer().dumps({'user_id': user.id})


def _require_actor():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, jsonify({'error': 'Authorization bearer token is required'}), 401

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        return None, jsonify({'error': 'Authorization bearer token is required'}), 401

    max_age = int(current_app.config.get('AUTH_TOKEN_TTL_SECONDS', 86400))
    try:
        payload = _token_serializer().loads(token, max_age=max_age)
    except SignatureExpired:
        return None, jsonify({'error': 'Token expired'}), 401
    except BadSignature:
        return None, jsonify({'error': 'Invalid token'}), 401

    user_id = payload.get('user_id')
    user = User.get(user_id)
    if not user:
        return None, jsonify({'error': 'User not found'}), 404
    return user, None, None


def _validate_inventory_items(items):
    if not isinstance(items, list) or len(items) == 0:
        return None, 'items must be a non-empty list'

    normalized = []
    for item in items:
        cable_type = (item.get('cable_type') or '').strip()
        cable_length = (item.get('cable_length') or '').strip()
        quantity_raw = item.get('quantity')

        if not cable_type or not cable_length:
            return None, 'Each item requires cable_type and cable_length'
        try:
            quantity = int(quantity_raw)
        except (TypeError, ValueError):
            return None, 'Each item quantity must be an integer'
        if quantity <= 0:
            return None, 'Each item quantity must be greater than zero'

        normalized.append(
            {
                'cable_type': cable_type,
                'cable_length': cable_length,
                'quantity': quantity,
            }
        )

    return normalized, None

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
        token = _issue_access_token(existing_user)
        return jsonify({
            'message': 'User already exists',
            'user': existing_user.to_dict(),
            'access_token': token,
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

    token = _issue_access_token(user)
    return jsonify({'message': 'User created', 'user': user.to_dict(), 'access_token': token}), 201

@api.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json or {}
    user = User.find_by_username(data.get('username'))

    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = _issue_access_token(user)
    return jsonify({'message': 'Login successful', 'user': user.to_dict(), 'access_token': token}), 200

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
    include_deleted = request.args.get('include_deleted') == 'true'
    tickets = Ticket.all(include_deleted=include_deleted)
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

@api.route('/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get specific ticket"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    include_deleted = request.args.get('include_deleted') == 'true'
    if ticket.status == 'deleted' and not include_deleted:
        return jsonify({'error': 'Ticket was deleted'}), 410
    return jsonify(ticket.to_dict()), 200

@api.route('/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code

    data = request.json or {}

    required = ['assigned_to_id', 'items']
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
        assigned_to_id = int(data['assigned_to_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'assigned_to_id must be an integer'}), 400

    creator = actor
    assignee = User.get(assigned_to_id)
    if not assignee:
        return jsonify({'error': 'assigned_to_id must reference a valid user'}), 400

    ticket = Ticket.create(
        created_by_id=creator.id,
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
    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code

    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    if ticket.status == 'deleted':
        return jsonify({'error': 'Ticket was deleted'}), 410
    data = request.json or {}

    old_status = ticket.status
    updates = {}
    if 'status' in data:
        new_status = data['status']
        if new_status not in ALLOWED_STATUSES:
            return jsonify({'error': f'Invalid status: {new_status}'}), 400
        if new_status != old_status and new_status not in STATUS_TRANSITIONS.get(old_status, set()):
            return jsonify({'error': f'Invalid status transition: {old_status} -> {new_status}'}), 409
        if actor.role != 'admin':
            if new_status in ['approved', 'rejected'] and ticket.assigned_to_id != actor.id:
                return jsonify({'error': 'Only assignee or admin can set approval states'}), 403
            if new_status in ['in_progress', 'fulfilled', 'closed'] and ticket.assigned_to_id != actor.id:
                return jsonify({'error': 'Only assignee or admin can set work states'}), 403
        updates['status'] = new_status
    if 'rejection_reason' in data:
        if actor.role != 'admin' and ticket.assigned_to_id != actor.id:
            return jsonify({'error': 'Only assignee or admin can update rejection reason'}), 403
        updates['rejection_reason'] = data['rejection_reason']

    ticket = Ticket.update_fields(ticket_id, updates) if updates else ticket

    if old_status != ticket.status and ticket.status == 'fulfilled':
        if not InventoryMovement.exists_for_source('ticket_fulfillment', ticket.id):
            movement_docs = []
            for item in ticket.items:
                cable_type = (item.get('cable_type') or '').strip()
                cable_length = (item.get('cable_length') or '').strip()
                try:
                    quantity = int(item.get('quantity', 0))
                except (TypeError, ValueError):
                    continue
                if not cable_type or not cable_length or quantity <= 0:
                    continue
                movement_docs.append(
                    {
                        'movement_type': 'consumption',
                        'source_type': 'ticket_fulfillment',
                        'source_id': ticket.id,
                        'actor_user_id': ticket.assigned_to_id,
                        'cable_type': cable_type,
                        'cable_length': cable_length,
                        'quantity_delta': -quantity,
                        'notes': f'Ticket #{ticket.id} fulfilled',
                    }
                )
            try:
                InventoryMovement.create_many(movement_docs)
            except Exception:
                # Roll back status to avoid fulfilled-without-ledger inconsistency.
                Ticket.update_fields(ticket_id, {'status': old_status})
                return jsonify({'error': 'Inventory ledger update failed; ticket status rolled back'}), 500

    # Notify if status changed significantly
    if old_status != ticket.status and ticket.status in ['approved', 'rejected', 'fulfilled']:
        notify_status_change(ticket, ticket.status)

    return jsonify({'message': 'Ticket updated', 'ticket': ticket.to_dict()}), 200

@api.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Soft-delete a ticket"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code
    if ticket.created_by_id != actor.id and actor.role != 'admin':
        return jsonify({'error': 'Only the ticket creator or admin can delete this ticket'}), 403

    res = Ticket.soft_delete(
        ticket.id,
        deleted_by_id=actor.id,
        previous_status=ticket.status,
    )
    if res.matched_count == 0:
        return jsonify({'error': 'Ticket was already deleted'}), 410

    current_app.logger.info('ticket_archived ticket_id=%s actor_id=%s', ticket.id, actor.id)
    return jsonify({'message': 'Ticket archived', 'status': 'deleted'}), 200


@api.route('/tickets/<int:ticket_id>/restore', methods=['POST'])
def restore_ticket(ticket_id):
    """Restore a soft-deleted ticket"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code
    if ticket.created_by_id != actor.id and actor.role != 'admin':
        return jsonify({'error': 'Only the ticket creator or admin can restore this ticket'}), 403
    if ticket.status != 'deleted':
        return jsonify({'error': 'Ticket is not deleted'}), 409

    restored = Ticket.restore(ticket.id)
    current_app.logger.info('ticket_restored ticket_id=%s actor_id=%s', ticket.id, actor.id)
    return jsonify({'message': 'Ticket restored', 'ticket': restored.to_dict()}), 200


@api.route('/tickets/<int:ticket_id>/purge', methods=['DELETE'])
def purge_ticket(ticket_id):
    """Permanently delete a soft-deleted ticket (admin only)"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code
    if actor.role != 'admin':
        return jsonify({'error': 'Only admins can permanently delete tickets'}), 403
    if ticket.status != 'deleted':
        return jsonify({'error': 'Ticket must be archived before purge'}), 409

    Notification.delete_by_ticket_id(ticket.id)
    Ticket.hard_delete(ticket.id)
    current_app.logger.info('ticket_purged ticket_id=%s actor_id=%s', ticket.id, actor.id)
    return jsonify({'message': 'Ticket permanently deleted'}), 200


# ============= INVENTORY ROUTES =============

@api.route('/cable-receiving', methods=['POST'])
def create_cable_receiving():
    """Record received cable inventory and create positive stock movements"""
    actor, error_response, status_code = _require_actor()
    if error_response:
        return error_response, status_code
    if actor.role != 'admin':
        return jsonify({'error': 'Only admins can record cable receiving'}), 403

    data = request.json or {}
    items, validation_error = _validate_inventory_items(data.get('items'))
    if validation_error:
        return jsonify({'error': validation_error}), 400

    receipt = CableReceipt.create(
        received_by_id=actor.id,
        items=items,
        vendor=data.get('vendor'),
        po_number=data.get('po_number'),
        notes=data.get('notes'),
    )

    movement_docs = [
        {
            'movement_type': 'receipt',
            'source_type': 'cable_receiving',
            'source_id': receipt.id,
            'actor_user_id': actor.id,
            'cable_type': item['cable_type'],
            'cable_length': item['cable_length'],
            'quantity_delta': int(item['quantity']),
            'notes': f'Cable receipt #{receipt.id}',
        }
        for item in receipt.items
    ]
    try:
        InventoryMovement.create_many(movement_docs)
    except Exception:
        CableReceipt._collection().delete_one({'id': receipt.id})
        return jsonify({'error': 'Failed to write inventory ledger; receipt rolled back'}), 500
    current_app.logger.info('cable_receiving_created receipt_id=%s actor_id=%s', receipt.id, actor.id)

    return jsonify({'message': 'Cable receiving recorded', 'receipt': receipt.to_dict()}), 201


@api.route('/cable-receiving', methods=['GET'])
def list_cable_receiving():
    """List cable receiving records"""
    receipts = CableReceipt.all()
    return jsonify([receipt.to_dict() for receipt in receipts]), 200


@api.route('/inventory/movements', methods=['GET'])
def list_inventory_movements():
    """List inventory movement ledger entries"""
    source_type = request.args.get('source_type')
    movement_type = request.args.get('movement_type')
    source_id_raw = request.args.get('source_id')
    limit_raw = request.args.get('limit') or '200'

    source_id = None
    if source_id_raw is not None:
        try:
            source_id = int(source_id_raw)
        except ValueError:
            return jsonify({'error': 'source_id must be an integer'}), 400
    try:
        limit = int(limit_raw)
    except ValueError:
        return jsonify({'error': 'limit must be an integer'}), 400

    limit = max(1, min(limit, 1000))
    movements = InventoryMovement.list(
        movement_type=movement_type,
        source_type=source_type,
        source_id=source_id,
        limit=limit,
    )
    return jsonify([movement.to_dict() for movement in movements]), 200


@api.route('/inventory/on-hand', methods=['GET'])
def inventory_on_hand():
    """Get on-hand inventory grouped by cable type and length"""
    include_zero = request.args.get('include_zero') == 'true'
    summary = InventoryMovement.summary_on_hand()
    if not include_zero:
        summary = [row for row in summary if row.get('on_hand', 0) != 0]
    return jsonify(summary), 200

# ============= APPROVAL ROUTES (Token-based) =============

@api.route('/tickets/<int:ticket_id>/approve/<token>', methods=['GET', 'POST'])
def approve_ticket(ticket_id, token):
    """Approve a ticket via token link"""
    ticket = Ticket.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.approval_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if ticket.status == 'deleted':
        return jsonify({'error': 'Ticket was deleted'}), 410

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

    if ticket.status == 'deleted':
        return jsonify({'error': 'Ticket was deleted'}), 410

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
    archived = Ticket.count_by_status('deleted')

    return jsonify({
        'total_tickets': total_tickets,
        'pending_approval': pending,
        'approved': approved,
        'rejected': rejected,
        'fulfilled': fulfilled,
        'archived': archived,
    }), 200

# ============= HEALTH CHECK =============

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()}), 200
