import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';
import { Notification } from '../components/Notification';

export const DashboardPage = ({ onNavigate }) => {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchHealth = async () => {
    setHealthLoading(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({ status: 'unreachable', services: { database: 'unknown', redis: 'unknown' } });
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      onNavigate('login');
    } catch {
      setNotification({ type: 'error', message: 'Logout failed. Please try again.' });
    }
  };

  if (!user) {
    return (
      <div className="page-container">
        <div className="card">
          <p>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  const formattedDate = user.created_at
    ? new Date(user.created_at).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Recently';

  return (
    <div className="page-container">
      <div className="card large">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <h1 className="card-title" style={{ margin: 0 }}>User Dashboard</h1>
              <span className="badge success">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Email Verified
              </span>
            </div>
            <p className="card-subtitle">Authenticated session active via HTTP-Only cookie</p>
          </div>

          <button className="btn btn-secondary" style={{ width: 'auto', padding: '8px 16px' }} onClick={handleLogout}>
            Sign Out
          </button>
        </div>

        <Notification
          type={notification?.type}
          message={notification?.message}
          onClose={() => setNotification(null)}
        />

        <div className="dashboard-grid">
          {/* User Profile Card */}
          <div className="dash-card">
            <div className="dash-card-title">User Profile</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '1.25rem',
                  color: '#fff',
                }}
              >
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#fff' }}>{user.name}</div>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{user.email}</div>
              </div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Member since: <strong style={{ color: '#cbd5e1' }}>{formattedDate}</strong>
            </div>
          </div>

          {/* Database & Verification Status */}
          <div className="dash-card">
            <div className="dash-card-title">Security & Storage State</div>
            <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.88rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#10b981' }}>✔</span>
                <span>PostgreSQL: <strong>Permanent Verified Record</strong></span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#10b981' }}>✔</span>
                <span>Redis: <strong>Temporary OTP State Purged</strong></span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#10b981' }}>✔</span>
                <span>Password: <strong>Bcrypt Hashed</strong></span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#10b981' }}>✔</span>
                <span>Session: <strong>HTTP-Only Cookie Protected</strong></span>
              </li>
            </ul>
          </div>

          {/* System Health Status */}
          <div className="dash-card" style={{ gridColumn: '1 / -1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div className="dash-card-title" style={{ margin: 0 }}>Cluster Health Status</div>
              <button
                className="link-btn"
                style={{ fontSize: '0.8rem' }}
                onClick={fetchHealth}
                disabled={healthLoading}
              >
                {healthLoading ? 'Checking...' : 'Refresh Status'}
              </button>
            </div>

            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 160, padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>PostgreSQL Database</div>
                <div style={{ fontWeight: 700, color: health?.services?.database === 'healthy' ? '#34d399' : '#f87171' }}>
                  {health?.services?.database || 'Loading...'}
                </div>
              </div>

              <div style={{ flex: 1, minWidth: 160, padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Redis Cache</div>
                <div style={{ fontWeight: 700, color: health?.services?.redis === 'healthy' ? '#34d399' : '#f87171' }}>
                  {health?.services?.redis || 'Loading...'}
                </div>
              </div>

              <div style={{ flex: 1, minWidth: 160, padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>API Gateway</div>
                <div style={{ fontWeight: 700, color: health?.status === 'healthy' ? '#34d399' : '#fbbf24' }}>
                  {health?.status ? `${health.status.toUpperCase()}` : 'Loading...'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
