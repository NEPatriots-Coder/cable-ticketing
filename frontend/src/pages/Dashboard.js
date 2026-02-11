import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TicketForm from '../components/TicketForm';
import TicketList from '../components/TicketList';

function Dashboard({ user, onLogout }) {
  const [stats, setStats] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchStats();
  }, [refreshTrigger]);

  const fetchStats = async () => {
    try {
      const response = await axios.get('dashboard/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const handleTicketCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>🔌 Cable Ticketing System</h1>
        </div>
        <div className="nav-user">
          <span>Welcome, <strong>{user.username}</strong></span>
          <button onClick={onLogout} className="btn-logout">Logout</button>
        </div>
      </nav>

      {stats && (
        <div className="stats-container">
          <div className="stat-card">
            <div className="stat-value">{stats.total_tickets}</div>
            <div className="stat-label">Total Tickets</div>
          </div>
          <div className="stat-card pending">
            <div className="stat-value">{stats.pending_approval}</div>
            <div className="stat-label">Pending Approval</div>
          </div>
          <div className="stat-card approved">
            <div className="stat-value">{stats.approved}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-card rejected">
            <div className="stat-value">{stats.rejected}</div>
            <div className="stat-label">Rejected</div>
          </div>
          <div className="stat-card fulfilled">
            <div className="stat-value">{stats.fulfilled}</div>
            <div className="stat-label">Fulfilled</div>
          </div>
        </div>
      )}

      <div className="main-content">
        <TicketForm currentUser={user} onTicketCreated={handleTicketCreated} />
        <TicketList currentUser={user} refreshTrigger={refreshTrigger} />
      </div>
    </div>
  );
}

export default Dashboard;
