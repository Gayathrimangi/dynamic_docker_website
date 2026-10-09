import re
import secrets
import jwt
from datetime import datetime, timezone, timedelta
from flask import current_app, request
from sqlalchemy.exc import IntegrityError
from backend.extensions import db, bcrypt
from backend.models.user import User
from backend.services.redis_service import RedisService
from backend.services.email_service import EmailService, EmailDeliveryError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class AuthService:
    @staticmethod
    def validate_registration_input(
        name: str | None,
        email: str | None,
        password: str | None,
        confirm_password: str | None
    ) -> list[str]:
        errors = []
        if not name or len(name.strip()) < 2 or len(name.strip()) > 100:
            errors.append("Full name must be between 2 and 100 characters.")

        if not email or not EMAIL_REGEX.match(email.strip()):
            errors.append("A valid email address is required.")

        if not password:
            errors.append("Password is required.")
        else:
            if len(password) < 8:
                errors.append("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", password):
                errors.append("Password must contain at least one uppercase letter.")
            if not re.search(r"[a-z]", password):
                errors.append("Password must contain at least one lowercase letter.")
            if not re.search(r"\d", password):
                errors.append("Password must contain at least one digit.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                errors.append("Password must contain at least one special character.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        return errors

    @staticmethod
    def generate_otp() -> str:
        """Generate a cryptographically secure 6-digit numeric OTP."""
        return str(secrets.randbelow(900000) + 100000)

    @classmethod
    def initiate_registration(cls, name: str, email: str, password: str) -> tuple[bool, str, int]:
        """
        Initiates registration by storing pending user in Redis and emailing OTP.
        Guarantees that SMTP errors do not leave orphaned pending records in Redis.
        Returns (success: bool, message: str, status_code: int).
        """
        email_clean = email.lower().strip()
        name_clean = name.strip()

        # Check if email is already in PostgreSQL
        existing_user = User.query.filter_by(email=email_clean).first()
        if existing_user:
            return False, "An account with this email already exists. Please log in.", 409

        # Hash password using bcrypt
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        otp = cls.generate_otp()

        ttl = current_app.config.get("REGISTRATION_TTL", 300)
        max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
        cooldown = current_app.config.get("OTP_COOLDOWN_SECONDS", 60)

        # Store in Redis
        RedisService.save_pending_registration(
            email=email_clean,
            name=name_clean,
            password_hash=password_hash,
            otp=otp,
            ttl=ttl,
            max_attempts=max_attempts,
            cooldown_seconds=cooldown
        )

        # Send OTP via SMTP
        try:
            EmailService.send_otp_email(
                to_email=email_clean,
                name=name_clean,
                otp=otp,
                expiry_minutes=ttl // 60
            )
        except EmailDeliveryError as e:
            # Ensure Redis is cleaned up on SMTP failure
            RedisService.delete_pending_registration(email_clean)
            return False, f"Failed to send verification email: {str(e)}", 503
        except Exception:
            RedisService.delete_pending_registration(email_clean)
            return False, "Failed to send verification email. Please check server SMTP configuration.", 503

        return True, "Verification code sent to your email. Please verify within 5 minutes.", 201

    @classmethod
    def verify_and_create_user(cls, email: str, otp: str) -> tuple[bool, str, User | None, str | None, int]:
        """
        Verifies OTP and creates permanent PostgreSQL user record.
        Returns (success: bool, message: str, user: User | None, token: str | None, status_code: int).
        """
        email_clean = email.lower().strip()

        # Check existing database record
        if User.query.filter_by(email=email_clean).first():
            RedisService.delete_pending_registration(email_clean)
            return False, "User is already registered and verified. Please log in.", None, None, 400

        # Retrieve pending data first before verification check
        pending_user = RedisService.get_pending_user(email_clean)
        if not pending_user:
            return False, "Registration session expired or not found. Please register again.", None, None, 404

        # Validate OTP
        is_valid, msg, attempts_left = RedisService.verify_otp(email_clean, otp)
        if not is_valid:
            status = 410 if "expired" in msg.lower() or "terminated" in msg.lower() else 400
            return False, msg, None, None, status

        # OTP is valid! Create user in PostgreSQL
        try:
            user = User(
                name=pending_user["name"],
                email=email_clean,
                password_hash=pending_user["password_hash"],
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            RedisService.delete_pending_registration(email_clean)
            return False, "An account with this email was just registered.", None, None, 409
        except Exception as e:
            db.session.rollback()
            return False, f"Database error during registration: {str(e)}", None, None, 500

        # Delete pending registration and OTP state from Redis
        RedisService.delete_pending_registration(email_clean)

        # Generate JWT session token
        token = cls.create_access_token(user)
        return True, "Email successfully verified! Welcome aboard.", user, token, 200

    @classmethod
    def resend_otp(cls, email: str) -> tuple[bool, str, int, int]:
        """
        Resends a fresh OTP if permitted by cooldown and attempt limits.
        Returns (success: bool, message: str, cooldown_remaining: int, status_code: int).
        """
        email_clean = email.lower().strip()

        if User.query.filter_by(email=email_clean).first():
            return False, "Account is already verified. Please log in.", 0, 400

        max_resends = current_app.config.get("OTP_MAX_RESENDS", 3)
        allowed, err_msg, cooldown_left = RedisService.check_resend_allowed(email_clean, max_resends)
        if not allowed:
            status = 429 if cooldown_left > 0 else 400
            return False, err_msg, cooldown_left, status

        pending_user = RedisService.get_pending_user(email_clean)
        if not pending_user:
            return False, "Registration session has expired. Please register again.", 0, 404

        new_otp = cls.generate_otp()
        ttl = current_app.config.get("REGISTRATION_TTL", 300)
        max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
        cooldown = current_app.config.get("OTP_COOLDOWN_SECONDS", 60)

        # Send email
        try:
            EmailService.send_otp_email(
                to_email=email_clean,
                name=pending_user.get("name", "User"),
                otp=new_otp,
                expiry_minutes=ttl // 60
            )
        except Exception as e:
            return False, f"Failed to send email: {str(e)}", 0, 503

        # Update Redis with new OTP and reset attempts
        RedisService.update_resend_otp(
            email=email_clean,
            new_otp=new_otp,
            ttl=ttl,
            max_attempts=max_attempts,
            cooldown_seconds=cooldown
        )

        return True, "A new OTP has been dispatched to your email.", cooldown, 200

    @classmethod
    def authenticate(cls, email: str, password: str) -> tuple[bool, str, User | None, str | None, int]:
        """
        Authenticates user credentials against PostgreSQL.
        Returns (success: bool, message: str, user: User | None, token: str | None, status_code: int).
        """
        email_clean = email.lower().strip()

        user = User.query.filter_by(email=email_clean).first()
        if not user:
            # Check if pending in Redis to provide helpful guidance
            if RedisService.is_registration_pending(email_clean):
                return False, "Your account is pending OTP verification. Please verify your email first.", None, None, 403
            return False, "Invalid email or password.", None, None, 401

        if not user.check_password(password):
            return False, "Invalid email or password.", None, None, 401

        if not user.is_verified:
            return False, "Account is unverified. Please verify your email.", None, None, 403

        token = cls.create_access_token(user)
        return True, "Login successful.", user, token, 200

    @staticmethod
    def create_access_token(user: User) -> str:
        secret = current_app.config.get("JWT_SECRET_KEY")
        expires_in = current_app.config.get("JWT_EXPIRES_IN", timedelta(hours=24))
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "iat": now,
            "exp": now + expires_in,
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    @classmethod
    def get_user_from_request(cls) -> User | None:
        """
        Extracts and verifies JWT token from HTTP-only cookie or Authorization header.
        """
        token = request.cookies.get(current_app.config.get("JWT_COOKIE_NAME", "access_token"))

        # Fallback to Authorization: Bearer <token>
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return None

        try:
            secret = current_app.config.get("JWT_SECRET_KEY")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            if not user_id:
                return None
            return db.session.get(User, int(user_id))
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            return None
