import React from 'react';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, onNavigate }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
          <p style={{ marginTop: 16, color: '#94a3b8' }}>Validating session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    onNavigate('login');
    return null;
  }

  return children;
};
