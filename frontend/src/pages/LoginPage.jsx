import React, { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';
import { Notification } from '../components/Notification';

export const LoginPage = ({ onNavigate }) => {
  const { login, setPendingEmail } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [showVerifyLink, setShowVerifyLink] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setNotification(null);
    setShowVerifyLink(false);

    if (!email.trim() || !password) {
      setNotification({ type: 'error', message: 'Email and password are required.' });
      return;
    }

    setLoading(true);
    try {
      const res = await api.login(email.trim().toLowerCase(), password);
      if (res.success) {
        login(res.user, res.token);
        setNotification({ type: 'success', message: 'Login successful! Redirecting...' });
        setTimeout(() => {
          onNavigate('dashboard');
        }, 800);
      } else {
        setNotification({ type: 'error', message: res.message || 'Login failed.' });
      }
    } catch (err) {
      const msg = err.message || 'Invalid email or password.';
      setNotification({ type: 'error', message: msg });
      if (msg.toLowerCase().includes('pending') || msg.toLowerCase().includes('unverified')) {
        setShowVerifyLink(true);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="card">
        <div className="card-header">
          <h1 className="card-title">Welcome Back</h1>
          <p className="card-subtitle">Sign in to your account</p>
        </div>

        <Notification
          type={notification?.type}
          message={notification?.message}
          onClose={() => setNotification(null)}
        />

        {showVerifyLink && (
          <div style={{ marginBottom: 20, textAlign: 'center' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setPendingEmail(email.trim().toLowerCase());
                onNavigate('verify', { email: email.trim().toLowerCase() });
              }}
            >
              Verify Pending OTP for {email}
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <div className="input-wrapper">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
              <button
                type="button"
                className="input-icon-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label="Toggle password visibility"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" />
                <span>Authenticating...</span>
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="footer-nav">
          Don't have an account yet?{' '}
          <button className="link-btn" onClick={() => onNavigate('register')}>
            Register Now
          </button>
        </div>
      </div>
    </div>
  );
};
