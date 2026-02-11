import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TicketList({ currentUser, refreshTrigger }) {
  const [tickets, setTickets] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTickets();
  }, [refreshTrigger]);

  const fetchTickets = async () => {
    try {
      const response = await axios.get('/tickets');
      setTickets(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching tickets:', err);
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (ticketId, newStatus) => {
    try {
      await axios.patch(`/api/tickets/${ticketId}`, { status: newStatus });
      fetchTickets(); // Refresh list
    } catch (err) {
      console.error('Error updating ticket:', err);
      alert('Failed to update ticket status');
    }
  };

  const getFilteredTickets = () => {
    if (filter === 'created') {
      return tickets.filter(t => t.created_by.id === currentUser.id);
    } else if (filter === 'assigned') {
      return tickets.filter(t => t.assigned_to.id === currentUser.id);
    }
    return tickets;
  };

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

  const filteredTickets = getFilteredTickets();

  return (
    <div className="ticket-list-container">
      <div className="ticket-list-header">
        <h3>Tickets</h3>
        <div className="filter-buttons">
          <button
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All ({tickets.length})
          </button>
          <button
            className={filter === 'created' ? 'active' : ''}
            onClick={() => setFilter('created')}
          >
            Created by Me ({tickets.filter(t => t.created_by.id === currentUser.id).length})
          </button>
          <button
            className={filter === 'assigned' ? 'active' : ''}
            onClick={() => setFilter('assigned')}
          >
            Assigned to Me ({tickets.filter(t => t.assigned_to.id === currentUser.id).length})
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
                <div className="ticket-spec">
                  <strong>Type:</strong> {ticket.cable_type}
                </div>
                <div className="ticket-spec">
                  <strong>Length:</strong> {ticket.cable_length}
                </div>
                <div className="ticket-spec">
                  <strong>Gauge:</strong> {ticket.cable_gauge}
                </div>
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
