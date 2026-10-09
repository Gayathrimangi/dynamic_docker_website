import os
import time
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.extensions import db, bcrypt, init_redis
from backend.routes import auth_bp, health_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("auth_app")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(
        app,
        supports_credentials=True,
        origins=app.config.get("CORS_ORIGINS", ["http://localhost:3000", "http://localhost:5173"])
    )

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    init_redis(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)

    # Global JSON error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error("Internal Server Error: %s", str(e))
        return jsonify({"success": False, "message": "Internal server error"}), 500

    # Auto-initialize database tables when not testing
    if not app.config.get("TESTING", False):
        with app.app_context():
            retries = 5
            while retries > 0:
                try:
                    db.create_all()
                    logger.info("PostgreSQL database tables verified/created successfully.")
                    break
                except Exception as ex:
                    retries -= 1
                    logger.warning("Database connection attempt failed (%s). Retrying in 2s...", ex)
                    time.sleep(2)

    return app

if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
