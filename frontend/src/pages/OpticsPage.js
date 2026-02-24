import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axiosinstance';

const OTHER_OPTION = 'Other';

const OpticsPage = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const [partOptions, setPartOptions] = useState([]);
  const [selectedPart, setSelectedPart] = useState('');
  const [otherPart, setOtherPart] = useState('');
  const [quantity, setQuantity] = useState('');
  const [requesterName, setRequesterName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [requests, setRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(true);

  const isAdmin = user?.role === 'admin';

  const fetchPartOptions = useCallback(async () => {
    try {
      const response = await axios.get('/optics-parts');
      setPartOptions(response.data || []);
    } catch (err) {
      console.error('Error fetching optics parts:', err);
      setError('Failed to load optics parts list');
    }
  }, []);

  const fetchRequests = useCallback(async () => {
    try {
      const response = await axios.get('/optics-requests');
      setRequests(response.data || []);
    } catch (err) {
      console.error('Error fetching optics requests:', err);
    } finally {
      setRequestsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPartOptions();
    fetchRequests();
  }, [fetchPartOptions, fetchRequests]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = {
        selected_part: selectedPart,
        quantity: parseInt(quantity, 10),
        requester_name: requesterName.trim(),
      };
      if (selectedPart === OTHER_OPTION) {
        payload.other_part = otherPart.trim();
      }

      await axios.post('/optics-requests', payload);
      setSuccess('Optics request submitted successfully.');
      setSelectedPart('');
      setOtherPart('');
      setQuantity('');
      setRequesterName('');
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit optics request');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminAction = async (requestId, action) => {
    try {
      await axios.patch(`/optics-requests/${requestId}/status`, { action });
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${action} request`);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>🔌 Cable Ticketing System</h1>
        </div>
        <div className="nav-user">
          <button
            onClick={() => navigate('/')}
            className="btn-nav-link"
            aria-label="Go to Dashboard"
          >
            Dashboard
          </button>
          <button
            onClick={() => navigate('/receiving')}
            className="btn-nav-link"
            aria-label="Go to Receiving"
          >
            Receiving
          </button>
          <span>Welcome, <strong>{user.username}</strong></span>
          <button onClick={onLogout} className="btn-logout">Logout</button>
        </div>
      </nav>

      <div className="main-content">
        <div className="ticket-form-container">
          <h3>🔦 Submit Optics Request</h3>

          {error && <div className="error-message" role="alert">{error}</div>}
          {success && <div className="success-message" role="status">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="optics-part">Part Number</label>
              <select
                id="optics-part"
                value={selectedPart}
                onChange={e => setSelectedPart(e.target.value)}
                required
              >
                <option value="">Select a part</option>
                {partOptions.map(part => (
                  <option key={part} value={part}>{part}</option>
                ))}
              </select>
            </div>

            {selectedPart === OTHER_OPTION && (
              <div className="form-group">
                <label htmlFor="other-part">Model (if not listed)</label>
                <input
                  id="other-part"
                  type="text"
                  value={otherPart}
                  onChange={e => setOtherPart(e.target.value)}
                  placeholder="Type model number"
                  maxLength={255}
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="optics-quantity">Quantity</label>
              <input
                id="optics-quantity"
                type="number"
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                min="1"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="requester-name">Requester Name</label>
              <input
                id="requester-name"
                type="text"
                value={requesterName}
                onChange={e => setRequesterName(e.target.value)}
                placeholder="First name + last initial (e.g. John D)"
                maxLength={50}
                required
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Submitting...' : 'Submit Request'}
            </button>
          </form>
        </div>

        <div className="ticket-list-container">
          <div className="ticket-list-header">
            <h3>{isAdmin ? 'All Optics Requests' : 'My Optics Requests'}</h3>
          </div>

          {requestsLoading ? (
            <div className="loading"><span className="loader">Loading...</span></div>
          ) : requests.length === 0 ? (
            <div className="no-tickets">No optics requests yet.</div>
          ) : (
            <div className="tickets-grid">
              {requests.map(req => (
                <div key={req.id} className="ticket-card">
                  <div className="ticket-header">
                    <span className="ticket-id">Request #{req.id}</span>
                    <span className="status-badge">{req.status}</span>
                  </div>
                  <div className="ticket-body">
                    <div className="ticket-spec">
                      <strong>Part:</strong> {req.part_number}
                    </div>
                    <div className="ticket-spec">
                      <strong>Quantity:</strong> {req.quantity}
                    </div>
                    <div className="ticket-spec">
                      <strong>Name:</strong> {req.requester_name}
                    </div>
                    {req.admin_note && (
                      <div className="ticket-notes">{req.admin_note}</div>
                    )}
                  </div>
                  <div className="ticket-footer">
                    <div className="ticket-users">
                      <div>
                        <small>Submitted by</small>
                        <div>{req.requested_by?.username || '—'}</div>
                      </div>
                      <div>
                        <small>Submitted at</small>
                        <div style={{ fontSize: '12px' }}>{formatDate(req.created_at)}</div>
                      </div>
                    </div>
                  </div>
                  {isAdmin && (
                    <div className="optics-actions">
                      <button
                        type="button"
                        className="btn-small btn-progress"
                        onClick={() => handleAdminAction(req.id, 'approve')}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="btn-small btn-danger"
                        onClick={() => handleAdminAction(req.id, 'deny')}
                      >
                        Deny
                      </button>
                      <button
                        type="button"
                        className="btn-small"
                        onClick={() => handleAdminAction(req.id, 'archive')}
                      >
                        Archive
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OpticsPage;
