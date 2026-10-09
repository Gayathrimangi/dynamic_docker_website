import json
import hashlib
import hmac
from datetime import datetime, timezone
from backend.extensions import get_redis

def _hash_otp(otp: str) -> str:
    """Hash OTP using SHA-256 for secure storage."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()

class RedisService:
    @staticmethod
    def _user_key(email: str) -> str:
        return f"pending_user:{email.lower().strip()}"

    @staticmethod
    def _otp_key(email: str) -> str:
        return f"otp:{email.lower().strip()}"

    @staticmethod
    def _cooldown_key(email: str) -> str:
        return f"otp_cooldown:{email.lower().strip()}"

    @classmethod
    def save_pending_registration(
        cls,
        email: str,
        name: str,
        password_hash: str,
        otp: str,
        ttl: int = 300,
        max_attempts: int = 5,
        cooldown_seconds: int = 60
    ) -> bool:
        r = get_redis()
        if not r:
            raise RuntimeError("Redis client is not initialized")

        email_clean = email.lower().strip()
        user_key = cls._user_key(email_clean)
        otp_key = cls._otp_key(email_clean)
        cooldown_key = cls._cooldown_key(email_clean)

        user_data = {
            "name": name,
            "email": email_clean,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        otp_data = {
            "otp_hash": _hash_otp(otp),
            "attempts_left": max_attempts,
            "resend_count": 0,
        }

        pipe = r.pipeline()
        pipe.set(user_key, json.dumps(user_data), ex=ttl)
        pipe.set(otp_key, json.dumps(otp_data), ex=ttl)
        pipe.set(cooldown_key, "1", ex=cooldown_seconds)
        pipe.execute()
        return True

    @classmethod
    def get_pending_user(cls, email: str) -> dict | None:
        r = get_redis()
        if not r:
            return None
        data = r.get(cls._user_key(email))
        if data:
            return json.loads(data)
        return None

    @classmethod
    def get_otp_ttl(cls, email: str) -> int:
        r = get_redis()
        if not r:
            return 0
        ttl = r.ttl(cls._otp_key(email))
        return max(0, ttl)

    @classmethod
    def get_cooldown_ttl(cls, email: str) -> int:
        r = get_redis()
        if not r:
            return 0
        ttl = r.ttl(cls._cooldown_key(email))
        return max(0, ttl)

    @classmethod
    def verify_otp(cls, email: str, provided_otp: str) -> tuple[bool, str, int]:
        """
        Validates OTP against Redis.
        Returns (success: bool, message: str, attempts_left: int).
        """
        r = get_redis()
        if not r:
            raise RuntimeError("Redis client is not initialized")

        email_clean = email.lower().strip()
        user_key = cls._user_key(email_clean)
        otp_key = cls._otp_key(email_clean)

        user_raw = r.get(user_key)
        otp_raw = r.get(otp_key)

        if not user_raw or not otp_raw:
            return False, "OTP has expired or no pending registration found. Please register again.", 0

        otp_data = json.loads(otp_raw)
        attempts_left = int(otp_data.get("attempts_left", 0))

        if attempts_left <= 0:
            cls.delete_pending_registration(email_clean)
            return False, "Maximum verification attempts exceeded. Pending registration invalidated.", 0

        stored_hash = otp_data.get("otp_hash", "")
        candidate_hash = _hash_otp(provided_otp)

        if hmac.compare_digest(stored_hash, candidate_hash):
            return True, "OTP verified successfully.", attempts_left

        # OTP is incorrect, decrement attempts left
        attempts_left -= 1
        if attempts_left <= 0:
            cls.delete_pending_registration(email_clean)
            return False, "Invalid OTP. Maximum attempts exceeded. Verification session invalidated.", 0

        # Update remaining attempts preserving the remaining TTL
        current_ttl = r.ttl(otp_key)
        if current_ttl > 0:
            otp_data["attempts_left"] = attempts_left
            r.set(otp_key, json.dumps(otp_data), ex=current_ttl)
        else:
            cls.delete_pending_registration(email_clean)
            return False, "OTP has expired. Please register again.", 0

        return False, f"Invalid OTP code. {attempts_left} attempt(s) remaining.", attempts_left

    @classmethod
    def check_resend_allowed(
        cls,
        email: str,
        max_resends: int = 3
    ) -> tuple[bool, str, int]:
        """
        Checks if resend is permitted.
        Returns (allowed: bool, error_message: str, cooldown_remaining: int).
        """
        r = get_redis()
        if not r:
            return False, "Redis client not available", 0

        email_clean = email.lower().strip()
        user_raw = r.get(cls._user_key(email_clean))
        if not user_raw:
            return False, "No pending registration found for this email. Please register first.", 0

        cooldown_ttl = cls.get_cooldown_ttl(email_clean)
        if cooldown_ttl > 0:
            return False, f"Please wait {cooldown_ttl} seconds before requesting a new OTP.", cooldown_ttl

        otp_raw = r.get(cls._otp_key(email_clean))
        if otp_raw:
            otp_data = json.loads(otp_raw)
            resend_count = int(otp_data.get("resend_count", 0))
            if resend_count >= max_resends:
                return False, f"Maximum OTP resend limit ({max_resends}) reached. Please restart registration.", 0

        return True, "", 0

    @classmethod
    def update_resend_otp(
        cls,
        email: str,
        new_otp: str,
        ttl: int = 300,
        max_attempts: int = 5,
        cooldown_seconds: int = 60
    ) -> bool:
        r = get_redis()
        if not r:
            raise RuntimeError("Redis client is not initialized")

        email_clean = email.lower().strip()
        user_key = cls._user_key(email_clean)
        otp_key = cls._otp_key(email_clean)
        cooldown_key = cls._cooldown_key(email_clean)

        user_raw = r.get(user_key)
        if not user_raw:
            return False

        otp_raw = r.get(otp_key)
        resend_count = 1
        if otp_raw:
            old_otp_data = json.loads(otp_raw)
            resend_count = int(old_otp_data.get("resend_count", 0)) + 1

        otp_data = {
            "otp_hash": _hash_otp(new_otp),
            "attempts_left": max_attempts,
            "resend_count": resend_count,
        }

        pipe = r.pipeline()
        pipe.set(user_key, user_raw, ex=ttl)  # refresh pending user TTL
        pipe.set(otp_key, json.dumps(otp_data), ex=ttl)
        pipe.set(cooldown_key, "1", ex=cooldown_seconds)
        pipe.execute()
        return True

    @classmethod
    def delete_pending_registration(cls, email: str) -> None:
        r = get_redis()
        if not r:
            return
        email_clean = email.lower().strip()
        r.delete(
            cls._user_key(email_clean),
            cls._otp_key(email_clean),
            cls._cooldown_key(email_clean),
        )

    @classmethod
    def is_registration_pending(cls, email: str) -> bool:
        r = get_redis()
        if not r:
            return False
        return bool(r.exists(cls._user_key(email.lower().strip())))
