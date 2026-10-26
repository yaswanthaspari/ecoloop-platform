"""Route integration tests for EcoLoop."""
import pytest


def test_homepage(client):
    """Test that homepage loads successfully (200 OK)."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"EcoLoop" in response.data


def test_marketplace_page(client):
    """Test that marketplace loads successfully."""
    response = client.get("/marketplace/")
    assert response.status_code == 200
    assert b"Marketplace" in response.data


def test_ecoimpact_page(client):
    """Test that public ecoimpact awareness page loads successfully."""
    response = client.get("/ecoimpact/")
    assert response.status_code == 200
    assert b"EcoImpact" in response.data


def test_login_page(client):
    """Test that login page loads successfully."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Log In" in response.data


def test_register_page(client):
    """Test that register page loads successfully."""
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_admin_dashboard_requires_auth(client):
    """Test that admin dashboard redirects unauthorized users to login."""
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_404_handler(client):
    """Test that non-existent routes return 404 with custom error page."""
    response = client.get("/this-route-does-not-exist-at-all")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data


def test_about_page(client):
    """Test that about page loads successfully."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About EcoLoop" in response.data


def test_listing_detail_and_profile_views(client, app):
    """Test listing detail with recommendations and profile views."""
    from app import db
    from app.models.user import User
    from app.models.listing import Listing
    from app.models.recommendation import Recommendation

    with app.app_context():
        seller = User.query.filter_by(email="user@test.local").first()
        listing = Listing(
            seller_id=seller.id,
            title="Dell Inspiron 15 Laptop",
            category_confirmed="Laptop / Computer",
            working_status="working",
            physical_condition="good",
            status="available",
        )
        db.session.add(listing)
        db.session.commit()

        rec = Recommendation(
            listing_id=listing.id,
            route="reuse_resale",
            suitability_score=90,
            reason_codes='["WORKING_NO_DEFECT"]',
            explanation="Laptop is fully working.",
        )
        db.session.add(rec)
        db.session.commit()
        listing_id = listing.id

    # View listing detail page
    response = client.get(f"/listings/{listing_id}")
    assert response.status_code == 200
    assert b"Dell Inspiron 15 Laptop" in response.data
    assert b"Working No Defect" in response.data

    # Log in and view profile
    client.post("/auth/login", data={"email": "user@test.local", "password": "User123!"})
    profile_resp = client.get("/profile/")
    assert profile_resp.status_code == 200
    assert b"Dell Inspiron 15 Laptop" in profile_resp.data


def test_evaluate_and_ecoimpact_preview_endpoints(client, app):
    """Test AJAX evaluate and ecoimpact endpoints."""
    client.post("/auth/login", data={"email": "user@test.local", "password": "User123!"})

    eval_resp = client.post(
        "/listings/evaluate",
        json={
            "category_confirmed": "Mobile & Communication",
            "working_status": "working",
            "physical_condition": "excellent",
        },
    )
    assert eval_resp.status_code == 200
    data = eval_resp.get_json()
    assert data["route"] == "reuse_resale"

    eco_resp = client.get("/listings/ecoimpact-preview?category=Mobile%20%26%20Communication")
    assert eco_resp.status_code == 200
    eco_data = eco_resp.get_json()
    assert "category" in eco_data
