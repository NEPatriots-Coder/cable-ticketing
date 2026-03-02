import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axiosinstance';

const OTHER_OPTION = 'Other';

const OpticsReturnPage = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const [partOptions, setPartOptions] = useState([]);
  const [selectedPart, setSelectedPart] = useState('');
  const [otherPart, setOtherPart] = useState('');
  const [quantity, setQuantity] = useState('');
  const [requesterName, setRequesterName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [returns, setReturns] = useState([]);
  const [returnsLoading, setReturnsLoading] = useState(true);

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

  const fetchReturns = useCallback(async () => {
    try {
      const response = await axios.get('/optics-returns');
      setReturns(response.data || []);
    } catch (err) {
      console.error('Error fetching optics returns:', err);
    } finally {
      setReturnsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPartOptions();
    fetchReturns();
  }, [fetchPartOptions, fetchReturns]);

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

      await axios.post('/optics-returns', payload);
      setSuccess('Optics return submitted successfully.');
      setSelectedPart('');
      setOtherPart('');
      setQuantity('');
      setRequesterName('');
      fetchReturns();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit optics return');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminAction = async (returnId, action) => {
    try {
      await axios.patch(`/optics-returns/${returnId}/status`, { action });
      fetchReturns();
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${action} return`);
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
          <button
            onClick={() => navigate('/optics')}
            className="btn-nav-link"
            aria-label="Go to Optics"
          >
            Optics
          </button>
          <span>Welcome, <strong>{user.username}</strong></span>
          <button onClick={onLogout} className="btn-logout">Logout</button>
        </div>
      </nav>

      <div className="main-content">
        <div className="ticket-form-container">
          <h3>🔦 Submit Optics Return</h3>

          {error && <div className="error-message" role="alert">{error}</div>}
          {success && <div className="success-message" role="status">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="optics-return-part">Part Number</label>
              <select
                id="optics-return-part"
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
                <label htmlFor="other-return-part">Model (if not listed)</label>
                <input
                  id="other-return-part"
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
              <label htmlFor="optics-return-quantity">Quantity</label>
              <input
                id="optics-return-quantity"
                type="number"
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                min="1"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="returner-name">Requester Name</label>
              <input
                id="returner-name"
                type="text"
                value={requesterName}
                onChange={e => setRequesterName(e.target.value)}
                placeholder="First name + last initial (e.g. John D)"
                maxLength={50}
                required
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Submitting...' : 'Submit Return'}
            </button>
          </form>
        </div>

        <div className="ticket-list-container">
          <div className="ticket-list-header">
            <h3>{isAdmin ? 'All Optics Returns' : 'My Optics Returns'}</h3>
          </div>

          {returnsLoading ? (
            <div className="loading"><span className="loader">Loading...</span></div>
          ) : returns.length === 0 ? (
            <div className="no-tickets">No optics returns yet.</div>
          ) : (
            <div className="tickets-grid">
              {returns.map(ret => (
                <div key={ret.id} className="ticket-card">
                  <div className="ticket-header">
                    <span className="ticket-id">Return #{ret.id}</span>
                    <span className="status-badge">{ret.status}</span>
                  </div>
                  <div className="ticket-body">
                    <div className="ticket-spec">
                      <strong>Part:</strong> {ret.part_number}
                    </div>
                    <div className="ticket-spec">
                      <strong>Quantity:</strong> {ret.quantity}
                    </div>
                    <div className="ticket-spec">
                      <strong>Name:</strong> {ret.requester_name}
                    </div>
                    {ret.admin_note && (
                      <div className="ticket-notes">{ret.admin_note}</div>
                    )}
                  </div>
                  <div className="ticket-footer">
                    <div className="ticket-users">
                      <div>
                        <small>Submitted by</small>
                        <div>{ret.requested_by?.username || '—'}</div>
                      </div>
                      <div>
                        <small>Submitted at</small>
                        <div style={{ fontSize: '12px' }}>{formatDate(ret.created_at)}</div>
                      </div>
                    </div>
                  </div>
                  {isAdmin && (
                    <div className="optics-actions">
                      <button
                        type="button"
                        className="btn-small btn-progress"
                        onClick={() => handleAdminAction(ret.id, 'approve')}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="btn-small btn-danger"
                        onClick={() => handleAdminAction(ret.id, 'deny')}
                      >
                        Deny
                      </button>
                      <button
                        type="button"
                        className="btn-small"
                        onClick={() => handleAdminAction(ret.id, 'archive')}
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

export default OpticsReturnPage;
