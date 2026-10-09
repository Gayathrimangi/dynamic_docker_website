# Secure Full-Stack Web Application with Email OTP Verification

A production-ready, fully Dockerized full-stack web application featuring user registration, cryptographic email OTP verification, authentication with HTTP-only cookies, and an authenticated dashboard.

Built with **React (Vite)**, **Python (Flask REST API)**, **PostgreSQL**, **Redis**, and **Docker Compose**.

---

## Architecture Overview

```
                      +-----------------------------+
                      |       Web Browser           |
                      |   (http://localhost:3000)   |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               | (Port 3000 -> 80)                         |
               v                                           v
    +----------------------+                    +--------------------+
    |   Nginx Frontend     | -- (Proxy /api/) ->|    Flask API       |
    | (React 18 + Vite)    |                    |    (Port 5000)     |
    +----------------------+                    +----+----------+----+
                                                     |          |
                                                     |          |
                             +-----------------------+          +-----------------------+
                             v                                                          v
                +-------------------------+                                +-------------------------+
                |       PostgreSQL        |                                |          Redis          |
                |       (Port 5432)       |                                |       (Port 6379)       |
                |-------------------------|                                |-------------------------|
                | • Verified users ONLY   |                                | • Pending registrations |
                | • Bcrypt password hash  |                                | • SHA-256 OTP hashes    |
                | • Persistent volume     |                                | • 5-minute TTL          |
                +-------------------------+                                | • Cooldown & rate limit |
                                                                           +-------------------------+
```

### Key Security & Architecture Guarantees
1. **Zero Unverified Database Polluters**: Unverified registration data is stored strictly in **Redis** with a 5-minute TTL. The **PostgreSQL** `users` table is never written to until the OTP is successfully validated.
2. **Cryptographically Secure OTP**: Generated using Python `secrets.randbelow` and stored in Redis as a **SHA-256 hash**, evaluated with constant-time equality checks (`hmac.compare_digest`).
3. **Brute Force & Rate Limit Protection**:
   - Verification attempts are strictly capped (default 5 attempts). Exceeding the limit immediately invalidates and deletes the registration session.
   - Resend OTP has an automatic 60-second cooldown timer and maximum resend limit (3 resends).
4. **SMTP Error Consistency**: If email delivery fails, pending registration data in Redis is atomically wiped out, preventing inconsistent state.
5. **Secure Authentication**: Authentication issues a signed JWT delivered in a secure **HTTP-Only cookie** with `SameSite=Lax` protection, mitigating XSS token theft.

---

## Directory Structure

```
dynamic_redis_website/
├── .env.example                # Sample environment variables
├── .gitignore                  # Git ignore rules
├── docker-compose.yml          # Multi-container orchestration
├── README.md                   # Documentation
├── backend/
│   ├── Dockerfile              # Python 3.12-slim production container
│   ├── .dockerignore
│   ├── requirements.txt        # Backend dependencies
│   ├── app.py                  # Flask application factory
│   ├── config.py               # Environment configuration
│   ├── extensions.py           # DB, Bcrypt, and Redis instances
│   ├── models/
│   │   └── user.py             # PostgreSQL User model
│   ├── services/
│   │   ├── auth_service.py     # Registration, login, validation logic
│   │   ├── email_service.py    # SMTP email delivery (HTML & text)
│   │   └── redis_service.py    # Redis pending state, OTP hash, TTL
│   ├── routes/
│   │   ├── auth_routes.py      # /api/register, /api/verify-otp, etc.
│   │   └── health_routes.py    # /api/health
│   └── tests/                  # Automated pytest test suite (21 tests)
│       ├── conftest.py
│       ├── test_registration.py
│       ├── test_otp_verification.py
│       ├── test_otp_resend.py
│       ├── test_auth_login.py
│       └── test_protected_routes.py
└── frontend/
    ├── Dockerfile              # Multi-stage Node build + Nginx serve
    ├── .dockerignore
    ├── nginx.conf              # Nginx reverse proxy for /api/
    ├── package.json
    ├── vite.config.js          # Vite config with dev proxy
    ├── index.html
    └── src/
        ├── App.jsx             # SPA routing
        ├── main.jsx            # React root
        ├── index.css           # Modern dark UI theme
        ├── api.js              # Fetch client
        ├── context/
        │   └── AuthContext.jsx # Authentication state
        ├── components/
        │   ├── Navbar.jsx
        │   ├── Notification.jsx
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── RegisterPage.jsx
            ├── VerifyOtpPage.jsx
            ├── LoginPage.jsx
            └── DashboardPage.jsx
```

---

## Prerequisites

- **Docker Desktop** (version 24.0+ recommended) with Docker Compose v2.
- (Optional for local development outside Docker): **Python 3.11+**, **Node.js 18+**, **PostgreSQL**, and **Redis**.

---

## Configuration & Gmail Setup

### 1. Create your `.env` file
In the project root, copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

### 2. Configure Gmail SMTP (App Password)
To enable real email OTP delivery through Gmail:
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is turned ON.
3. Open [App Passwords](https://myaccount.google.com/apppasswords).
4. Enter an application name (e.g. `AuthWebApp`) and click **Create**.
5. Copy the generated 16-character password (e.g., `abcd efgh ijkl mnop`).
6. Update the following fields in `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_character_app_password
   SMTP_FROM_EMAIL=your_email@gmail.com
   SMTP_USE_TLS=true
   SMTP_DEV_MODE=false
   ```

> **Tip:** If you do not wish to set up SMTP right now, set `SMTP_DEV_MODE=true` in `.env`. The backend will simulate email dispatch so you can test all registration and login flows seamlessly!

---

## Running with Docker Compose (Windows PowerShell)

Open **Windows PowerShell** inside `d:\internship\dynamic_redis_website` and run:

### 1. Build and Start All Containers
```powershell
docker compose up --build -d
```

### 2. Check Service Status & Health
```powershell
docker compose ps
```
All four containers (`auth_frontend`, `auth_backend`, `auth_postgres`, `auth_redis`) will initialize and transition to `healthy`.

### 3. View Logs
```powershell
# View all logs
docker compose logs -f

# View backend logs specifically
docker compose logs -f backend
```

### 4. Stop All Services
```powershell
docker compose down
```
To stop and remove database volumes as well:
```powershell
docker compose down -v
```

---

## Application URLs

| Service | URL | Description |
|---|---|---|
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Responsive React UI |
| **Backend API Health** | [http://localhost:3000/api/health](http://localhost:3000/api/health) | Live DB & Redis Health Status |
| **API Endpoints** | `http://localhost:3000/api/*` | Nginx proxied API routes |

---

## API Endpoints & Testing Examples

You can test the endpoints directly using PowerShell (`Invoke-RestMethod`) or `curl`:

### 1. Register User (Initiates OTP in Redis)
```powershell
$body = @{
    name = "John Doe"
    email = "john@example.com"
    password = "SecurePassword123!"
    confirm_password = "SecurePassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/register" -Method Post -Body $body -ContentType "application/json"
```

**Response:**
```json
{
  "email": "john@example.com",
  "message": "Verification code sent to your email. Please verify within 5 minutes.",
  "success": true
}
```

### 2. Verify OTP (Creates user in PostgreSQL)
```powershell
$body = @{
    email = "john@example.com"
    otp = "123456"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/verify-otp" -Method Post -Body $body -ContentType "application/json"
```

### 3. Resend OTP
```powershell
$body = @{
    email = "john@example.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/resend-otp" -Method Post -Body $body -ContentType "application/json"
```

### 4. Login
```powershell
$body = @{
    email = "john@example.com"
    password = "SecurePassword123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/login" -Method Post -Body $body -ContentType "application/json" -SessionVariable session
```

### 5. Access Protected Dashboard (/api/me)
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/me" -Method Get -WebSession $session
```

### 6. Logout
```powershell
Invoke-RestMethod -Uri "http://localhost:3000/api/logout" -Method Post -WebSession $session
```

---

## Running the Automated Test Suite

The test suite covers:
- Registration validation, duplicate checks, and SMTP failure rollback
- OTP verification, PostgreSQL user creation, and attempt decrement
- Rate limiting, cooldown timers, and max attempt lockout
- Authentication, unverified user blocking, and cookie handling

To run tests:
```powershell
python -m pytest backend/tests -v
```

---

## Troubleshooting

1. **Docker Desktop is not starting on Windows:**
   - Open Docker Desktop from the Start Menu.
   - If WSL errors appear, run `wsl --update` in an Administrator PowerShell prompt, then restart Docker Desktop.
2. **SMTP Authentication Fails:**
   - Double check that you are using a 16-character **Google App Password**, NOT your normal account password.
   - Ensure `SMTP_USE_TLS=true` and port is `587`.
   - Alternatively, toggle `SMTP_DEV_MODE=true` to test locally.
3. **Port Conflicts:**
   - If port `3000` is already in use by another application, modify `docker-compose.yml` to map to another port, e.g., `"8080:80"`.
