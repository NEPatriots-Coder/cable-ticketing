import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from '../api/axiosinstance';

function TicketList({ currentUser, refreshTrigger, onTicketDeleted }) {
  const [tickets, setTickets] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchTickets = useCallback(async () => {
    try {
      const response = await axios.get('/tickets');
      setTickets(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching tickets:', err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets, refreshTrigger]);

  const handleStatusUpdate = async (ticketId, newStatus) => {
    try {
      await axios.patch(`/tickets/${ticketId}`, { status: newStatus });
      fetchTickets(); // Refresh list
    } catch (err) {
      console.error('Error updating ticket:', err);
      alert('Failed to update ticket status');
    }
  };

  const handleDeleteTicket = async (ticketId) => {
    if (!window.confirm('Archive this ticket? It will be hidden from the default ticket list.')) return;
    try {
      await axios.delete(`/tickets/${ticketId}`, { data: { user_id: currentUser.id } });
      fetchTickets();
      if (onTicketDeleted) onTicketDeleted();
    } catch (err) {
      console.error('Error deleting ticket:', err);
      alert('Failed to archive ticket');
    }
  };

  const visibleTickets = useMemo(
    () => tickets.filter((t) => t.status !== 'deleted'),
    [tickets]
  );

  const createdTickets = useMemo(
    () => visibleTickets.filter((t) => t.created_by.id === currentUser.id),
    [visibleTickets, currentUser.id]
  );

  const assignedTickets = useMemo(
    () => visibleTickets.filter((t) => t.assigned_to.id === currentUser.id),
    [visibleTickets, currentUser.id]
  );

  const filteredTickets = useMemo(() => {
    if (filter === 'created') {
      return createdTickets;
    }
    if (filter === 'assigned') {
      return assignedTickets;
    }
    return visibleTickets;
  }, [filter, visibleTickets, createdTickets, assignedTickets]);

  const getStatusBadgeClass = (status) => {
    const classes = {
      'pending_approval': 'status-pending',
      'approved': 'status-approved',
      'rejected': 'status-rejected',
      'in_progress': 'status-progress',
      'fulfilled': 'status-fulfilled',
      'closed': 'status-closed'
    };
    return classes[status] || 'status-default';
  };

  const getPriorityBadgeClass = (priority) => {
    const classes = {
      'low': 'priority-low',
      'medium': 'priority-medium',
      'high': 'priority-high'
    };
    return classes[priority] || 'priority-medium';
  };

  if (loading) {
    return <div className="loading">Loading tickets...</div>;
  }

  return (
    <div className="ticket-list-container">
      <div className="ticket-list-header">
        <h3>Tickets</h3>
        <div className="filter-buttons">
          <button
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All ({visibleTickets.length})
          </button>
          <button
            className={filter === 'created' ? 'active' : ''}
            onClick={() => setFilter('created')}
          >
            Created by Me ({createdTickets.length})
          </button>
          <button
            className={filter === 'assigned' ? 'active' : ''}
            onClick={() => setFilter('assigned')}
          >
            Assigned to Me ({assignedTickets.length})
          </button>
        </div>
      </div>

      {filteredTickets.length === 0 ? (
        <p className="no-tickets">No tickets found</p>
      ) : (
        <div className="tickets-grid">
          {filteredTickets.map(ticket => (
            <div key={ticket.id} className="ticket-card">
              <div className="ticket-header">
                <span className="ticket-id">#{ticket.id}</span>
                <div className="ticket-badges">
                  <span className={`status-badge ${getStatusBadgeClass(ticket.status)}`}>
                    {ticket.status.replace('_', ' ')}
                  </span>
                  <span className={`priority-badge ${getPriorityBadgeClass(ticket.priority)}`}>
                    {ticket.priority}
                  </span>
                </div>
              </div>

              <div className="ticket-body">
                {(ticket.items || []).map((item, i) => (
                  <div key={i} className="ticket-spec">
                    <strong>Item {i + 1}:</strong> {item.cable_type} | {item.cable_length} | Qty: {item.quantity}
                  </div>
                ))}
                {ticket.location && (
                  <div className="ticket-spec">
                    <strong>Location:</strong> {ticket.location}
                  </div>
                )}
                {ticket.notes && (
                  <div className="ticket-notes">
                    <strong>Notes:</strong> {ticket.notes}
                  </div>
                )}
              </div>

              <div className="ticket-footer">
                <div className="ticket-users">
                  <div>
                    <small>Created by:</small><br />
                    <strong>{ticket.created_by.username}</strong>
                  </div>
                  <div>
                    <small>Assigned to:</small><br />
                    <strong>{ticket.assigned_to.username}</strong>
                  </div>
                </div>

                {ticket.assigned_to.id === currentUser.id && ticket.status === 'approved' && (
                  <div className="ticket-actions">
                    <button
                      className="btn-small btn-progress"
                      onClick={() => handleStatusUpdate(ticket.id, 'in_progress')}
                    >
                      Start Work
                    </button>
                  </div>
                )}

                {ticket.assigned_to.id === currentUser.id && ticket.status === 'in_progress' && (
                  <div className="ticket-actions">
                    <button
                      className="btn-small btn-success"
                      onClick={() => handleStatusUpdate(ticket.id, 'fulfilled')}
                    >
                      Mark Fulfilled
                    </button>
                  </div>
                )}

                {ticket.rejection_reason && (
                  <div className="rejection-reason">
                    <strong>Rejection Reason:</strong> {ticket.rejection_reason}
                  </div>
                )}

                {ticket.created_by.id === currentUser.id && (
                  <div className="ticket-actions">
                    <button
                      className="btn-small btn-danger"
                      onClick={() => handleDeleteTicket(ticket.id)}
                    >
                      Archive
                    </button>
                  </div>
                )}
              </div>

              <div className="ticket-timestamp">
                Created: {new Date(ticket.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TicketList;
