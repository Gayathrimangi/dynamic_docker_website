import React, { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';
import { Notification } from '../components/Notification';

export const RegisterPage = ({ onNavigate }) => {
  const { setPendingEmail } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirm_password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Password strength calculation
  const getPasswordStrength = (pwd) => {
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd)) score += 1;
    if (/[a-z]/.test(pwd)) score += 1;
    if (/\d/.test(pwd)) score += 1;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) score += 1;
    return score;
  };

  const strengthScore = getPasswordStrength(formData.password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setNotification(null);

    // Frontend validations
    if (!formData.name.trim()) {
      setNotification({ type: 'error', message: 'Full name is required.' });
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email.trim())) {
      setNotification({ type: 'error', message: 'Please enter a valid email address.' });
      return;
    }

    if (formData.password.length < 8) {
      setNotification({ type: 'error', message: 'Password must be at least 8 characters long.' });
      return;
    }

    if (strengthScore < 3) {
      setNotification({
        type: 'warning',
        message: 'Please choose a stronger password (include uppercase, numbers, and special characters).',
      });
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setNotification({ type: 'error', message: 'Passwords do not match.' });
      return;
    }

    setLoading(true);
    try {
      const res = await api.register(
        formData.name.trim(),
        formData.email.trim().toLowerCase(),
        formData.password,
        formData.confirm_password
      );

      if (res.success) {
        setPendingEmail(formData.email.trim().toLowerCase());
        setNotification({
          type: 'success',
          message: res.message || 'Verification code sent to your email! Redirecting...',
        });
        setTimeout(() => {
          onNavigate('verify', { email: formData.email.trim().toLowerCase() });
        }, 1200);
      } else {
        setNotification({ type: 'error', message: res.message || 'Registration failed.' });
      }
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to submit registration. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="card">
        <div className="card-header">
          <h1 className="card-title">Create Account</h1>
          <p className="card-subtitle">Register with email verification via Redis OTP</p>
        </div>

        <Notification
          type={notification?.type}
          message={notification?.message}
          onClose={() => setNotification(null)}
        />

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="name">Full Name</label>
            <input
              id="name"
              name="name"
              type="text"
              className="form-input"
              placeholder="e.g. John Doe"
              value={formData.name}
              onChange={handleChange}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              name="email"
              type="email"
              className="form-input"
              placeholder="name@example.com"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <div className="input-wrapper">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
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

            {formData.password && (
              <>
                <div className="strength-meter">
                  <div className={`strength-bar ${strengthScore >= 1 ? (strengthScore <= 2 ? 'weak' : strengthScore <= 4 ? 'medium' : 'strong') : ''}`} />
                  <div className={`strength-bar ${strengthScore >= 3 ? (strengthScore <= 4 ? 'medium' : 'strong') : ''}`} />
                  <div className={`strength-bar ${strengthScore >= 5 ? 'strong' : ''}`} />
                </div>
                <div className="strength-labels">
                  <span>Strength</span>
                  <span>{strengthScore <= 2 ? 'Weak' : strengthScore <= 4 ? 'Moderate' : 'Strong'}</span>
                </div>
              </>
            )}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirm_password">Confirm Password</label>
            <div className="input-wrapper">
              <input
                id="confirm_password"
                name="confirm_password"
                type={showConfirmPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                value={formData.confirm_password}
                onChange={handleChange}
                disabled={loading}
                required
              />
              <button
                type="button"
                className="input-icon-btn"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label="Toggle confirm password visibility"
              >
                {showConfirmPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" />
                <span>Sending OTP...</span>
              </>
            ) : (
              'Continue with Verification'
            )}
          </button>
        </form>

        <div className="footer-nav">
          Already have an account?{' '}
          <button className="link-btn" onClick={() => onNavigate('login')}>
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};
