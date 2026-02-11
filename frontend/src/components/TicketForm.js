import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TicketForm({ currentUser, onTicketCreated }) {
  const [users, setUsers] = useState([]);
  const [formData, setFormData] = useState({
    assigned_to_id: '',
    cable_type: '',
    cable_length: '',
    cable_gauge: '',
    location: '',
    notes: '',
    priority: 'medium'
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/api/users');
      // Show all users (including current user for testing)
      setUsers(response.data);
    } catch (err) {
      console.error('Error fetching users:', err);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/tickets', {
        ...formData,
        created_by_id: currentUser.id
      });

      setSuccess('Ticket created! Notification sent to assignee.');
      setFormData({
        assigned_to_id: '',
        cable_type: '',
        cable_length: '',
        cable_gauge: '',
        location: '',
        notes: '',
        priority: 'medium'
      });

      if (onTicketCreated) {
        onTicketCreated(response.data.ticket);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create ticket');
    }
  };

  return (
    <div className="ticket-form-container">
      <h3>Create New Cable Request</h3>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit} className="ticket-form">
        <div className="form-row">
          <div className="form-group">
            <label>Assign To *</label>
            <select
              name="assigned_to_id"
              value={formData.assigned_to_id}
              onChange={handleChange}
              required
            >
              <option value="">Select user...</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>
                  {user.username} ({user.email})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Priority</label>
            <select
              name="priority"
              value={formData.priority}
              onChange={handleChange}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Cable Type *</label>
            <input
              type="text"
              name="cable_type"
              value={formData.cable_type}
              onChange={handleChange}
              placeholder="e.g., Cat6, Cat6a, Fiber"
              required
            />
          </div>

          <div className="form-group">
            <label>Length *</label>
            <input
              type="text"
              name="cable_length"
              value={formData.cable_length}
              onChange={handleChange}
              placeholder="e.g., 100ft, 50m"
              required
            />
          </div>

          <div className="form-group">
            <label>Gauge *</label>
            <input
              type="text"
              name="cable_gauge"
              value={formData.cable_gauge}
              onChange={handleChange}
              placeholder="e.g., 23AWG, 24AWG"
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label>Location</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g., Building A, Floor 3, Room 301"
          />
        </div>

        <div className="form-group">
          <label>Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            placeholder="Additional information..."
            rows="3"
          />
        </div>

        <button type="submit" className="btn-primary">Create Ticket</button>
      </form>
    </div>
  );
}

export default TicketForm;
