from functools import wraps
from flask import Blueprint, request, jsonify, current_app, make_response
from backend.services.auth_service import AuthService
from backend.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthService.get_user_from_request()
        if not user:
            return jsonify({
                "success": False,
                "message": "Authentication required. Please log in."
            }), 401
        return f(user, *args, **kwargs)
    return decorated_function

def _set_auth_cookie(response, token: str):
    cookie_name = current_app.config.get("JWT_COOKIE_NAME", "access_token")
    secure = current_app.config.get("JWT_COOKIE_SECURE", False)
    samesite = current_app.config.get("JWT_COOKIE_SAMESITE", "Lax")
    max_age = int(current_app.config.get("JWT_EXPIRES_IN").total_seconds())

    response.set_cookie(
        key=cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/"
    )
    return response

def _clear_auth_cookie(response):
    cookie_name = current_app.config.get("JWT_COOKIE_NAME", "access_token")
    secure = current_app.config.get("JWT_COOKIE_SECURE", False)
    samesite = current_app.config.get("JWT_COOKIE_SAMESITE", "Lax")

    response.set_cookie(
        key=cookie_name,
        value="",
        expires=0,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/"
    )
    return response

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    errors = AuthService.validate_registration_input(name, email, password, confirm_password)
    if errors:
        return jsonify({
            "success": False,
            "message": errors[0],
            "errors": errors
        }), 400

    success, message, status_code = AuthService.initiate_registration(name, email, password)
    return jsonify({
        "success": success,
        "message": message,
        "email": email if success else None
    }), status_code

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    otp = str(data.get("otp", "")).strip()

    if not email or not otp:
        return jsonify({
            "success": False,
            "message": "Both email and 6-digit OTP code are required."
        }), 400

    if len(otp) != 6 or not otp.isdigit():
        return jsonify({
            "success": False,
            "message": "OTP must be a valid 6-digit number."
        }), 400

    success, message, user, token, status_code = AuthService.verify_and_create_user(email, otp)
    if not success or not user or not token:
        return jsonify({
            "success": False,
            "message": message
        }), status_code

    response = make_response(jsonify({
        "success": True,
        "message": message,
        "user": user.to_dict(),
        "token": token
    }), status_code)

    return _set_auth_cookie(response, token)

@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required to resend verification code."
        }), 400

    success, message, cooldown, status_code = AuthService.resend_otp(email)
    return jsonify({
        "success": success,
        "message": message,
        "cooldown_seconds": cooldown
    }), status_code

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    success, message, user, token, status_code = AuthService.authenticate(email, password)
    if not success or not user or not token:
        return jsonify({
            "success": False,
            "message": message
        }), status_code

    response = make_response(jsonify({
        "success": True,
        "message": message,
        "user": user.to_dict(),
        "token": token
    }), status_code)

    return _set_auth_cookie(response, token)

@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200)
    return _clear_auth_cookie(response)

@auth_bp.route("/me", methods=["GET"])
@login_required
def me(current_user: User):
    return jsonify({
        "success": True,
        "user": current_user.to_dict()
    }), 200
