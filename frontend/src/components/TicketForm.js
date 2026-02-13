import React, { useState, useEffect } from 'react';
import axios from '../api/axiosinstance';

const newItem = () => ({ cable_type: '', cable_length: '', quantity: '' });

const getInitialFormData = () => ({
  assigned_to_id: '',
  items: [newItem()],
  location: '',
  notes: '',
  priority: 'medium'
});

function TicketForm({ currentUser, onTicketCreated }) {
  const [users, setUsers] = useState([]);
  const [formData, setFormData] = useState(getInitialFormData);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('/users');
        setUsers(response.data);
      } catch (err) {
        console.error('Error fetching users:', err);
      }
    };
    fetchUsers();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleItemChange = (index, e) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const items = [...prev.items];
      items[index] = { ...items[index], [name]: value };
      return { ...prev, items };
    });
  };

  const addItem = () => {
    setFormData((prev) => ({ ...prev, items: [...prev.items, newItem()] }));
  };

  const removeItem = (index) => {
    setFormData((prev) => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/tickets', {
        ...formData,
        created_by_id: currentUser.id
      });

      setSuccess('Ticket created! Notification sent to assignee.');
      setFormData(getInitialFormData());

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

        <div className="form-group">
          <label>Items *</label>
          {formData.items.map((item, index) => (
            <div key={index} className="form-row item-row">
              <div className="form-group">
                <input
                  type="text"
                  name="cable_type"
                  value={item.cable_type}
                  onChange={(e) => handleItemChange(index, e)}
                  placeholder="Cable Type (e.g., Cat6)"
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="text"
                  name="cable_length"
                  value={item.cable_length}
                  onChange={(e) => handleItemChange(index, e)}
                  placeholder="Length (e.g., 100ft)"
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="text"
                  name="quantity"
                  value={item.quantity}
                  onChange={(e) => handleItemChange(index, e)}
                  placeholder="Quantity"
                  required
                />
              </div>
              {formData.items.length > 1 && (
                <button
                  type="button"
                  className="btn-small btn-danger"
                  onClick={() => removeItem(index)}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" className="btn-secondary" onClick={addItem}>
            + Add Item
          </button>
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
