import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axiosinstance';

const emptyItem = () => ({ cable_type: '', cable_length: '', quantity: '' });

const ReceivingPage = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const [vendor, setVendor] = useState('');
  const [poNumber, setPoNumber] = useState('');
  const [storageLocation, setStorageLocation] = useState('');
  const [items, setItems] = useState([emptyItem()]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [receipts, setReceipts] = useState([]);
  const [receiptsLoading, setReceiptsLoading] = useState(true);

  const fetchReceipts = useCallback(async () => {
    try {
      const response = await axios.get('/cable-receiving');
      setReceipts(response.data);
    } catch (err) {
      console.error('Error fetching receipts:', err);
    } finally {
      setReceiptsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReceipts();
  }, [fetchReceipts]);

  const handleItemChange = (index, field, value) => {
    setItems(prev =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item))
    );
  };

  const handleAddItem = () => {
    setItems(prev => [...prev, emptyItem()]);
  };

  const handleRemoveItem = (index) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = {
        vendor: vendor.trim() || undefined,
        po_number: poNumber.trim() || undefined,
        storage_location: storageLocation.trim() || undefined,
        items: items.map(item => ({
          cable_type: item.cable_type.trim(),
          cable_length: item.cable_length.trim(),
          quantity: parseInt(item.quantity, 10),
        })),
        notes: notes.trim() || undefined,
      };

      await axios.post('/cable-receiving', payload);
      setSuccess('Receiving record saved successfully!');
      setVendor('');
      setPoNumber('');
      setStorageLocation('');
      setItems([emptyItem()]);
      setNotes('');
      fetchReceipts();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save receiving record');
    } finally {
      setLoading(false);
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
          <span>Welcome, <strong>{user.username}</strong></span>
          <button onClick={onLogout} className="btn-logout">Logout</button>
        </div>
      </nav>

      <div className="main-content">
        <div className="ticket-form-container">
          <h3>📦 Record Cable Receiving</h3>

          {error && <div className="error-message" role="alert">{error}</div>}
          {success && <div className="success-message" role="status">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="vendor">Vendor</label>
                <input
                  id="vendor"
                  type="text"
                  value={vendor}
                  onChange={e => setVendor(e.target.value)}
                  placeholder="e.g. CableCo Inc."
                />
              </div>
              <div className="form-group">
                <label htmlFor="po-number">Purchase Order</label>
                <input
                  id="po-number"
                  type="text"
                  value={poNumber}
                  onChange={e => setPoNumber(e.target.value)}
                  placeholder="e.g. PO-2024-001"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="storage-location">Storage Location</label>
              <input
                id="storage-location"
                type="text"
                value={storageLocation}
                onChange={e => setStorageLocation(e.target.value)}
                placeholder="e.g. Warehouse A, Shelf 3"
              />
            </div>

            <div className="form-group">
              <label>Items Received</label>
              {items.map((item, index) => (
                <div
                  key={index}
                  className="form-row receiving-item-row"
                >
                  <div className="form-group">
                    <label htmlFor={`cable-type-${index}`} className="sub-label">Cable Type</label>
                    <input
                      id={`cable-type-${index}`}
                      type="text"
                      value={item.cable_type}
                      onChange={e => handleItemChange(index, 'cable_type', e.target.value)}
                      placeholder="e.g. Cat6"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`cable-length-${index}`} className="sub-label">Cable Length</label>
                    <input
                      id={`cable-length-${index}`}
                      type="text"
                      value={item.cable_length}
                      onChange={e => handleItemChange(index, 'cable_length', e.target.value)}
                      placeholder="e.g. 100m"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor={`quantity-${index}`} className="sub-label">Item Quantity</label>
                    <input
                      id={`quantity-${index}`}
                      type="number"
                      value={item.quantity}
                      onChange={e => handleItemChange(index, 'quantity', e.target.value)}
                      placeholder="e.g. 5"
                      min="1"
                      required
                    />
                  </div>
                  {items.length > 1 && (
                    <div className="form-group receiving-remove-col">
                      <label className="sub-label">&nbsp;</label>
                      <button
                        type="button"
                        className="btn-small btn-danger receiving-remove-btn"
                        onClick={() => handleRemoveItem(index)}
                        aria-label={`Remove item ${index + 1}`}
                      >
                        ✕
                      </button>
                    </div>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={handleAddItem}
                className="btn-small btn-progress"
                style={{ marginTop: '8px' }}
              >
                + Add Item
              </button>
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Any additional notes..."
                rows="3"
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Record Receiving'}
            </button>
          </form>
        </div>

        <div className="ticket-list-container">
          <div className="ticket-list-header">
            <h3>Receiving History</h3>
          </div>

          {receiptsLoading ? (
            <div className="loading"><span className="loader">Loading...</span></div>
          ) : receipts.length === 0 ? (
            <div className="no-tickets">No receiving records yet.</div>
          ) : (
            <div className="tickets-grid">
              {receipts.map(receipt => (
                <div key={receipt.id} className="ticket-card">
                  <div className="ticket-header">
                    <span className="ticket-id">Receipt #{receipt.id}</span>
                    {receipt.po_number && (
                      <span className="status-badge status-approved">
                        {receipt.po_number}
                      </span>
                    )}
                  </div>
                  <div className="ticket-body">
                    {receipt.vendor && (
                      <div className="ticket-spec">
                        <strong>Vendor:</strong> {receipt.vendor}
                      </div>
                    )}
                    {receipt.storage_location && (
                      <div className="ticket-spec">
                        <strong>Storage Location:</strong> {receipt.storage_location}
                      </div>
                    )}
                    <div className="ticket-spec">
                      <strong>Items:</strong>
                      <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                        {receipt.items.map((item, i) => (
                          <li key={i} style={{ fontSize: '13px', color: '#555' }}>
                            {item.cable_type} / {item.cable_length} — qty {item.quantity}
                          </li>
                        ))}
                      </ul>
                    </div>
                    {receipt.notes && (
                      <div className="ticket-notes">{receipt.notes}</div>
                    )}
                  </div>
                  <div className="ticket-footer">
                    <div className="ticket-users">
                      <div>
                        <small>Received by</small>
                        <div>{receipt.received_by?.username || '—'}</div>
                      </div>
                      <div>
                        <small>Received at</small>
                        <div style={{ fontSize: '12px' }}>{formatDate(receipt.received_at)}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReceivingPage;
