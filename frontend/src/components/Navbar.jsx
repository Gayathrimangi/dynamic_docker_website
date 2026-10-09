import React from 'react';
import { useAuth } from '../context/AuthContext';

export const Navbar = ({ currentRoute, onNavigate }) => {
  const { user, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="nav-brand" onClick={() => onNavigate(user ? 'dashboard' : 'login')}>
        <div className="brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <span>AuthSecure</span>
      </div>

      <nav className="nav-links">
        {user ? (
          <>
            <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>
              Hi, <strong style={{ color: '#f8fafc' }}>{user.name}</strong>
            </span>
            <button
              className={`nav-btn ${currentRoute === 'dashboard' ? 'primary' : ''}`}
              onClick={() => onNavigate('dashboard')}
            >
              Dashboard
            </button>
            <button
              className="nav-btn logout"
              onClick={async () => {
                await logout();
                onNavigate('login');
              }}
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <button
              className={`nav-btn ${currentRoute === 'login' ? 'primary' : ''}`}
              onClick={() => onNavigate('login')}
            >
              Log In
            </button>
            <button
              className={`nav-btn ${currentRoute === 'register' ? 'primary' : ''}`}
              onClick={() => onNavigate('register')}
            >
              Register
            </button>
          </>
        )}
      </nav>
    </header>
  );
};
