import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Seed test admin
        admin = User(name="Test Admin", email="admin@test.local", role="admin")
        admin.set_password("Admin123!")
        db.session.add(admin)

        # Seed test user
        user = User(name="Test User", email="user@test.local", role="seller")
        user.set_password("User123!")
        db.session.add(user)

        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
