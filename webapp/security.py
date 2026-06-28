"""
BBAP-Sec — Security Configuration (Phase A)
=============================================
Centralizes security hardening: JWT secret enforcement, CORS,
rate limiting, request size limits, and audit logging setup.

Integrate in webapp/app.py:
    from webapp.security import configure_security, audit_log
    configure_security(app)
"""

import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger("security")

# ── Audit logger (separate file) ──
audit_logger = logging.getLogger("audit")
_audit_handler = logging.FileHandler("logs/audit.log")
_audit_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
audit_logger.addHandler(_audit_handler)
audit_logger.setLevel(logging.INFO)


def audit_log(event, user=None, detail="", ip=None):
    """Log a security-relevant event to logs/audit.log."""
    user_str = user or "anonymous"
    ip_str = ip or "-"
    audit_logger.info(f"{event} | user={user_str} | ip={ip_str} | {detail}")


def _require_secret():
    """Enforce JWT_SECRET in production; warn in dev."""
    secret = os.environ.get("JWT_SECRET", "")
    env = os.environ.get("BBAP_ENV", "development")

    if env == "production":
        if not secret or secret == "bbap-sec-change-this-in-production":
            logger.critical("JWT_SECRET not set in production. Refusing to start.")
            print("\n" + "=" * 60)
            print("  FATAL: JWT_SECRET environment variable is required")
            print("  in production. Set it before starting:")
            print("    export JWT_SECRET=$(python -c \"import secrets; print(secrets.token_hex(32))\")")
            print("=" * 60 + "\n")
            sys.exit(1)
    else:
        if not secret:
            logger.warning("JWT_SECRET not set — using insecure dev default. "
                           "Set JWT_SECRET before deploying to production.")


def configure_security(app):
    """Apply all Phase A security hardening to the Flask app."""

    # 1. Enforce JWT secret
    _require_secret()

    # 2. Restrict CORS to known frontend origins
    allowed_origins = os.environ.get(
        "BBAP_ALLOWED_ORIGINS",
        "http://localhost:5000,http://127.0.0.1:5000"
    ).split(",")

    try:
        from flask_cors import CORS
        CORS(app,
             origins=allowed_origins,
             supports_credentials=True,
             allow_headers=["Content-Type", "Authorization"],
             methods=["GET", "POST", "PUT", "DELETE"])
        logger.info(f"CORS restricted to: {allowed_origins}")
    except ImportError:
        logger.warning("flask-cors not installed. Run: pip install flask-cors")

    # 3. Request size limit (default 500MB for model uploads, configurable)
    max_upload = int(os.environ.get("BBAP_MAX_UPLOAD_MB", "500"))
    app.config["MAX_CONTENT_LENGTH"] = max_upload * 1024 * 1024
    logger.info(f"Max request size: {max_upload}MB")

    # 4. Security headers on every response
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if os.environ.get("BBAP_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    logger.info("Security headers enabled")

    return app


def setup_rate_limiting(app):
    """Configure flask-limiter for abuse protection.

    Returns the limiter instance so routes can apply specific limits.
    """
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            get_remote_address,
            app=app,
            default_limits=["200 per hour"],
            storage_uri="memory://",
        )
        logger.info("Rate limiting enabled (200/hour default)")
        return limiter
    except ImportError:
        logger.warning("flask-limiter not installed. Run: pip install flask-limiter")
        return None
