"""
EcoLoop Flask application factory.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import get_config

# Extensions (initialised without app instance — attached later)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)

    # ── Load config ──────────────────────────────────────────────────────────
    if config_class is None:
        config_class = get_config()
    elif isinstance(config_class, str):
        from config import config_map
        config_class = config_map.get(config_class, get_config())
    app.config.from_object(config_class)

    # ── Ensure required directories exist (safely handle read-only filesystems)
    for folder in [
        app.config.get("UPLOAD_FOLDER"),
        os.path.dirname(app.config.get("MODEL_PATH", "")),
        app.instance_path
    ]:
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError:
                pass

    # ── Initialise extensions ────────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ── User loader ──────────────────────────────────────────────────────────
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Custom Jinja filters ─────────────────────────────────────────────────
    import json

    def fromjson_filter(value):
        if not value:
            return []
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return [value]

    app.jinja_env.filters["fromjson"] = fromjson_filter

    # ── Static uploads serving route ─────────────────────────────────────────
    from flask import send_from_directory

    @app.route("/static/uploads/<path:filename>")
    @app.route("/uploads/<path:filename>")
    def serve_uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ── Register blueprints ──────────────────────────────────────────────────
    from app.routes.main     import bp as main_bp
    from app.routes.auth     import bp as auth_bp
    from app.routes.listings import bp as listings_bp
    from app.routes.marketplace import bp as marketplace_bp
    from app.routes.ecoimpact   import bp as ecoimpact_bp
    from app.routes.profile     import bp as profile_bp
    from app.routes.admin       import bp as admin_bp
    from app.routes.api         import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,        url_prefix="/auth")
    app.register_blueprint(listings_bp,    url_prefix="/listings")
    app.register_blueprint(marketplace_bp, url_prefix="/marketplace")
    app.register_blueprint(ecoimpact_bp,   url_prefix="/ecoimpact")
    app.register_blueprint(profile_bp,     url_prefix="/profile")
    app.register_blueprint(admin_bp,       url_prefix="/admin")
    app.register_blueprint(api_bp,         url_prefix="/api")

    # ── Error handlers ───────────────────────────────────────────────────────
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    return app
