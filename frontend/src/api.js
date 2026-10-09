// API Client with cookie and Bearer token fallback support

const API_BASE = '/api';

function getAuthHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = getAuthHeaders();

  const config = {
    ...options,
    credentials: 'include', // Ensures HTTP-only cookies are attached & received
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.message || `Request failed with status ${response.status}`;
      const error = new Error(errorMsg);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    throw err;
  }
}

export const api = {
  // Registration
  register: (name, email, password, confirmPassword) => {
    return request('/register', {
      method: 'POST',
      body: JSON.stringify({
        name,
        email,
        password,
        confirm_password: confirmPassword,
      }),
    });
  },

  // Verify OTP
  verifyOtp: (email, otp) => {
    return request('/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, otp }),
    });
  },

  // Resend OTP
  resendOtp: (email) => {
    return request('/resend-otp', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  // Login
  login: (email, password) => {
    return request('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  // Logout
  logout: () => {
    localStorage.removeItem('auth_token');
    return request('/logout', {
      method: 'POST',
    });
  },

  // Current authenticated user
  getMe: () => {
    return request('/me', {
      method: 'GET',
    });
  },

  // Service health check
  getHealth: () => {
    return request('/health', {
      method: 'GET',
    });
  },
};
