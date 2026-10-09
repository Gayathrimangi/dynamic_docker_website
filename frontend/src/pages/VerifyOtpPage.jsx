import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';
import { Notification } from '../components/Notification';

export const VerifyOtpPage = ({ onNavigate, routeParams }) => {
  const { pendingEmail, login } = useAuth();
  const [email, setEmail] = useState(routeParams?.email || pendingEmail || '');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(60);
  const [notification, setNotification] = useState({
    type: 'info',
    message: 'A 6-digit verification code has been sent to your email. It expires in 5 minutes.',
  });

  const inputRefs = useRef([]);

  // Focus first digit box on mount
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const interval = setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldownSeconds]);

  const handleDigitChange = (index, value) => {
    // Only accept numeric characters
    const char = value.replace(/\D/g, '').slice(-1);

    const newDigits = [...otpDigits];
    newDigits[index] = char;
    setOtpDigits(newDigits);

    // If digit entered, jump to next box
    if (char && index < 5 && inputRefs.current[index + 1]) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!otpDigits[index] && index > 0 && inputRefs.current[index - 1]) {
        inputRefs.current[index - 1].focus();
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1].focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    const cleanNumbers = pastedData.replace(/\D/g, '').slice(0, 6);
    if (!cleanNumbers) return;

    const newDigits = [...otpDigits];
    for (let i = 0; i < cleanNumbers.length; i++) {
      newDigits[i] = cleanNumbers[i];
    }
    setOtpDigits(newDigits);

    const focusIdx = Math.min(cleanNumbers.length, 5);
    if (inputRefs.current[focusIdx]) {
      inputRefs.current[focusIdx].focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otpDigits.join('');

    if (!email.trim()) {
      setNotification({ type: 'error', message: 'Email address is required.' });
      return;
    }

    if (otpCode.length !== 6) {
      setNotification({ type: 'error', message: 'Please enter all 6 digits of the OTP.' });
      return;
    }

    setLoading(true);
    setNotification(null);

    try {
      const res = await api.verifyOtp(email.trim().toLowerCase(), otpCode);
      if (res.success) {
        login(res.user, res.token);
        setNotification({
          type: 'success',
          message: 'OTP verified successfully! Welcome to your secure dashboard.',
        });
        setTimeout(() => {
          onNavigate('dashboard');
        }, 1000);
      } else {
        setNotification({ type: 'error', message: res.message || 'Verification failed.' });
      }
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Invalid or expired OTP. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldownSeconds > 0 || resending) return;

    if (!email.trim()) {
      setNotification({ type: 'error', message: 'Please specify your email to resend OTP.' });
      return;
    }

    setResending(true);
    setNotification(null);

    try {
      const res = await api.resendOtp(email.trim().toLowerCase());
      if (res.success) {
        setCooldownSeconds(res.cooldown_seconds || 60);
        setNotification({
          type: 'success',
          message: res.message || 'A new verification code has been dispatched to your email.',
        });
        setOtpDigits(['', '', '', '', '', '']);
        if (inputRefs.current[0]) inputRefs.current[0].focus();
      } else {
        setNotification({ type: 'error', message: res.message });
      }
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to resend OTP. Please try again later.',
      });
      if (err.data?.cooldown_seconds) {
        setCooldownSeconds(err.data.cooldown_seconds);
      }
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="page-container">
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'inline-flex', padding: 12, borderRadius: '50%', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', marginBottom: 12 }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="16" height="12" x="4" y="8" rx="2" />
              <path d="M4 10l8 6 8-6" />
            </svg>
          </div>
          <h1 className="card-title">Verify OTP Code</h1>
          <p className="card-subtitle">
            Enter the 6-digit code sent to: <br />
            <strong style={{ color: '#f8fafc' }}>{email || 'your email'}</strong>
          </p>
        </div>

        <Notification
          type={notification?.type}
          message={notification?.message}
          onClose={() => setNotification(null)}
        />

        <form onSubmit={handleSubmit} noValidate>
          {/* Option to adjust email if needed */}
          {!pendingEmail && (
            <div className="form-group">
              <label className="form-label" htmlFor="otp-email">Email Address</label>
              <input
                id="otp-email"
                type="email"
                className="form-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" style={{ textAlign: 'center' }}>Six-Digit Security Code</label>
            <div className="otp-container" onPaste={handlePaste}>
              {otpDigits.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => (inputRefs.current[idx] = el)}
                  type="text"
                  inputMode="numeric"
                  pattern="\d*"
                  maxLength={1}
                  className={`otp-digit-box ${digit ? 'filled' : ''}`}
                  value={digit}
                  onChange={(e) => handleDigitChange(idx, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(idx, e)}
                  disabled={loading}
                  autoComplete="one-time-code"
                />
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || otpDigits.join('').length !== 6}
          >
            {loading ? (
              <>
                <span className="spinner" />
                <span>Verifying with Redis...</span>
              </>
            ) : (
              'Verify & Complete Registration'
            )}
          </button>
        </form>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleResend}
            disabled={cooldownSeconds > 0 || resending}
          >
            {resending ? (
              <>
                <span className="spinner" />
                <span>Requesting Code...</span>
              </>
            ) : cooldownSeconds > 0 ? (
              `Resend Code in ${cooldownSeconds}s`
            ) : (
              'Resend Code'
            )}
          </button>
        </div>

        <div className="footer-nav">
          Entered the wrong email?{' '}
          <button className="link-btn" onClick={() => onNavigate('register')}>
            Restart Registration
          </button>
        </div>
      </div>
    </div>
  );
};
