import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { RegisterPage } from './pages/RegisterPage';
import { VerifyOtpPage } from './pages/VerifyOtpPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProtectedRoute } from './components/ProtectedRoute';

export const App = () => {
  const { user, loading } = useAuth();
  const [route, setRoute] = useState('login');
  const [routeParams, setRouteParams] = useState({});

  // Sync state with URL hash
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '');
      const [path, query] = hash.split('?');

      const params = {};
      if (query) {
        const searchParams = new URLSearchParams(query);
        for (const [key, val] of searchParams.entries()) {
          params[key] = val;
        }
      }
      setRouteParams(params);

      if (['login', 'register', 'verify', 'dashboard'].includes(path)) {
        setRoute(path);
      } else {
        setRoute(user ? 'dashboard' : 'login');
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange();

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [user]);

  // Navigate helper
  const navigate = (newRoute, params = {}) => {
    setRoute(newRoute);
    setRouteParams(params);
    let hash = `#${newRoute}`;
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams(params);
      hash += `?${searchParams.toString()}`;
    }
    window.location.hash = hash;
  };

  // If user logs in while on login or register, redirect to dashboard
  useEffect(() => {
    if (!loading && user && (route === 'login' || route === 'register')) {
      navigate('dashboard');
    }
  }, [user, loading, route]);

  return (
    <>
      <Navbar currentRoute={route} onNavigate={navigate} />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {route === 'register' && <RegisterPage onNavigate={navigate} />}
        {route === 'verify' && <VerifyOtpPage onNavigate={navigate} routeParams={routeParams} />}
        {route === 'login' && <LoginPage onNavigate={navigate} />}
        {route === 'dashboard' && (
          <ProtectedRoute onNavigate={navigate}>
            <DashboardPage onNavigate={navigate} />
          </ProtectedRoute>
        )}
      </main>

      <footer style={{ textAlign: 'center', padding: '20px', fontSize: '0.8rem', color: '#64748b', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        Dockerized Full-Stack Auth &copy; {new Date().getFullYear()} &mdash; Flask &bull; PostgreSQL &bull; Redis &bull; React Vite
      </footer>
    </>
  );
};
