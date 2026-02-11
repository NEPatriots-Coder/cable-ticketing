import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

function ApprovalPage({ action }) {
  const { ticketId, token } = useParams();
  const [status, setStatus] = useState('loading');
  const [ticket, setTicket] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showReasonInput, setShowReasonInput] = useState(false);

  useEffect(() => {
    if (action === 'approve') {
      handleApprove();
    } else {
      setShowReasonInput(true);
      setStatus('awaiting_reason');
    }
  }, []);

  const handleApprove = async () => {
    try {
      const response = await axios.get(`/api/tickets/${ticketId}/approve/${token}`);
      setTicket(response.data.ticket);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      console.error(err);
    }
  };

  const handleReject = async () => {
    try {
      const response = await axios.post(
        `/api/tickets/${ticketId}/reject/${token}`,
        { reason: rejectionReason }
      );
      setTicket(response.data.ticket);
      setStatus('success');
    } catch (err) {
      setStatus('error');
      console.error(err);
    }
  };

  if (status === 'loading') {
    return (
      <div className="approval-container">
        <div className="approval-card">
          <div className="loader">Processing...</div>
        </div>
      </div>
    );
  }

  if (status === 'awaiting_reason') {
    return (
      <div className="approval-container">
        <div className="approval-card">
          <h2>❌ Reject Cable Request</h2>
          <p>Please provide a reason for rejection:</p>

          <div className="form-group">
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Enter rejection reason..."
              rows="4"
              style={{ width: '100%', padding: '10px' }}
            />
          </div>

          <button
            onClick={handleReject}
            className="btn-danger"
            disabled={!rejectionReason.trim()}
          >
            Confirm Rejection
          </button>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="approval-container">
        <div className="approval-card error">
          <h2>❌ Error</h2>
          <p>Failed to process your request. The link may be invalid or expired.</p>
          <Link to="/" className="btn-primary">Go to Dashboard</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="approval-container">
      <div className="approval-card success">
        {action === 'approve' ? (
          <>
            <div className="approval-icon">✅</div>
            <h2>Request Approved!</h2>
            <p>You have approved the cable request.</p>
          </>
        ) : (
          <>
            <div className="approval-icon">❌</div>
            <h2>Request Rejected</h2>
            <p>You have rejected the cable request.</p>
          </>
        )}

        {ticket && (
          <div className="ticket-details">
            <h3>Ticket Details</h3>
            <div className="detail-row">
              <strong>Ticket ID:</strong> #{ticket.id}
            </div>
            <div className="detail-row">
              <strong>Cable Type:</strong> {ticket.cable_type}
            </div>
            <div className="detail-row">
              <strong>Length:</strong> {ticket.cable_length}
            </div>
            <div className="detail-row">
              <strong>Gauge:</strong> {ticket.cable_gauge}
            </div>
            <div className="detail-row">
              <strong>Status:</strong> {ticket.status}
            </div>
          </div>
        )}

        <Link to="/" className="btn-primary">Go to Dashboard</Link>
      </div>
    </div>
  );
}

export default ApprovalPage;
