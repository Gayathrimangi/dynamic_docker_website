from datetime import datetime, timezone
from flask import Blueprint, jsonify
from sqlalchemy import text
from backend.extensions import db, get_redis

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def health_check():
    db_status = "unknown"
    redis_status = "unknown"

    # Test Database connectivity
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy ({type(e).__name__})"

    # Test Redis connectivity
    try:
        r = get_redis()
        if r and r.ping():
            redis_status = "healthy"
        else:
            redis_status = "unhealthy (ping failed)"
    except Exception as e:
        redis_status = f"unhealthy ({type(e).__name__})"

    overall_healthy = db_status == "healthy" and redis_status == "healthy"
    status_code = 200 if overall_healthy else 503

    return jsonify({
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
        }
    }), status_code
