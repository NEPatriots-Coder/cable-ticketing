import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import ApprovalPage from './pages/ApprovalPage';
import ReceivingPage from './pages/ReceivingPage';
import axios from './api/axiosinstance';
import './App.css';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    axios.get('/auth/me')
      .then((response) => {
        const authedUser = response.data?.user;
        if (!authedUser) {
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
          return;
        }
        setUser(authedUser);
        localStorage.setItem('user', JSON.stringify(authedUser));
      })
      .catch(() => {
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
      });
  }, []);

  useEffect(() => {
    const handleAuthExpired = () => {
      setUser(null);
    };

    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, []);

  const handleLogin = (userData, accessToken) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('access_token', accessToken);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
  };

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={
            user ? <Navigate to="/" /> : <LoginForm onLogin={handleLogin} />
          } />
          <Route path="/register" element={
            user ? <Navigate to="/" /> : <RegisterForm onRegister={handleLogin} />
          } />
          <Route path="/tickets/:ticketId/approve/:token" element={<ApprovalPage action="approve" />} />
          <Route path="/tickets/:ticketId/reject/:token" element={<ApprovalPage action="reject" />} />
          <Route path="/" element={
            user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/login" />
          } />
          <Route path="/receiving" element={
            user ? <ReceivingPage user={user} onLogout={handleLogout} /> : <Navigate to="/login" />
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
