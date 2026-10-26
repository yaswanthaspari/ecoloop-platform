"""
Vercel Serverless Function Entrypoint for EcoLoop.
"""
import os
import sys

# Ensure root directory and SWM_project directory are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
swm_dir = os.path.join(root_dir, "SWM_project")
for path in [root_dir, swm_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Signal Vercel environment
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("VERCEL", "1")

from app import create_app, db

app = create_app()

# Auto-seed SQLite database in /tmp if fresh container instance
with app.app_context():
    try:
        from app.models.user import User
        db.create_all()
        if not User.query.first():
            try:
                from seed import seed_database
                seed_database()
            except Exception as se:
                app.logger.warning("Auto-seed error: %s", se)
    except Exception as e:
        app.logger.warning("DB init error: %s", e)

# Handler for Vercel WSGI
handler = app
