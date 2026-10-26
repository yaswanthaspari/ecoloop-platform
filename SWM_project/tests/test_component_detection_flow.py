"""
Tests for automatic component detection, diagnostic questions generation,
and component-driven recovery decision routing.
"""
import io
import json
import pytest
from PIL import Image
from app.services.image_classifier import ImageClassifierService, get_classifier
from app.services.recovery_engine import (
    evaluate,
    ROUTE_REPAIR,
    ROUTE_PARTS_RECOVERY,
    ROUTE_REFURBISHMENT,
    ROUTE_SAFETY_REVIEW,
    ROUTE_REUSE_RESALE,
)


def create_dummy_image(color=(50, 150, 50), size=(300, 300)):
    """Generate in-memory test image bytes."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_image_classifier_detects_components_and_generates_questions(tmp_path):
    """Test that ImageClassifier analyzes an image and generates detected components & questions."""
    classifier = get_classifier()
    img_path = tmp_path / "test_phone.jpg"
    img = Image.new("RGB", (300, 600), color=(30, 30, 30))  # phone-like aspect ratio
    img.save(img_path)

    res = classifier.classify(str(img_path))
    assert res.inference_status == "success"
    assert len(res.detected_components) > 0
    assert any(c["id"] == "display" for c in res.detected_components)
    assert len(res.diagnostic_questions) > 0
    assert any(q.get("component_id") == "display" or q.get("id") == "display_health" for q in res.diagnostic_questions)


def test_recovery_engine_with_swollen_battery():
    """Swollen battery diagnostic answer must trigger safety review immediately."""
    res = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="working",
        physical_condition="good",
        diagnostic_answers={"battery": "swollen"},
        detected_components=[{"id": "battery", "name": "Internal Lithium Battery"}]
    )
    assert res.route == ROUTE_SAFETY_REVIEW
    assert res.safety_flag is True
    assert "critical" in res.explanation.lower() or "safety" in res.explanation.lower()


def test_recovery_engine_with_cracked_glass_repair():
    """Cracked screen + working motherboard should route to repair with targeted display replacement."""
    res = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="partially_working",
        physical_condition="fair",
        diagnostic_answers={"display": "cracked_glass", "motherboard": "boots"},
        detected_components=[
            {"id": "display", "name": "Display Screen"},
            {"id": "motherboard", "name": "Motherboard & Logic Board"}
        ]
    )
    assert res.route == ROUTE_REPAIR
    assert any("Display" in target for target in res.repair_target_components)
    assert res.suitability_score >= 70


def test_recovery_engine_with_dead_motherboard_parts_recovery():
    """Dead motherboard with healthy screen & casing should route to parts recovery."""
    res = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="not_working",
        physical_condition="fair",
        diagnostic_answers={"motherboard": "dead", "display": "working", "casing": "good"},
        detected_components=[
            {"id": "motherboard", "name": "Motherboard & Logic Board"},
            {"id": "display", "name": "Display Screen"},
            {"id": "casing", "name": "Chassis & Enclosure"}
        ]
    )
    assert res.route == ROUTE_PARTS_RECOVERY
    assert any("Display" in s for s in res.salvageable_components)


def test_recovery_engine_with_degraded_battery_refurbishment():
    """Degraded battery with working system should route to refurbishment."""
    res = evaluate(
        category="Laptops & Portable Computers",
        working_status="working",
        physical_condition="good",
        diagnostic_answers={"battery": "degraded", "motherboard": "boots"},
        detected_components=[
            {"id": "battery", "name": "Internal Lithium Battery"},
            {"id": "motherboard", "name": "Motherboard & Logic Board"}
        ]
    )
    assert res.route == ROUTE_REFURBISHMENT
    assert any("Battery" in target for target in res.repair_target_components)


def test_recovery_engine_all_healthy_resale():
    """All components verified healthy should route to reuse / resale."""
    res = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="working",
        physical_condition="good",
        diagnostic_answers={"display": "working", "battery": "normal", "motherboard": "boots", "casing": "good"},
        detected_components=[
            {"id": "display", "name": "Display Screen"},
            {"id": "battery", "name": "Internal Lithium Battery"},
            {"id": "motherboard", "name": "Motherboard & Logic Board"}
        ]
    )
    assert res.route == ROUTE_REUSE_RESALE
    assert res.suitability_score >= 85


def test_api_classify_and_evaluate_endpoints(client, app):
    """Test /listings/classify and /listings/evaluate HTTP endpoints."""
    # Log in first
    login_res = client.post("/auth/login", data={"email": "user@test.local", "password": "User123!"})
    assert login_res.status_code == 302

    # Classify image
    img_buf = create_dummy_image()
    res = client.post(
        "/listings/classify",
        data={"image": (img_buf, "test.jpg")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "detected_components" in data
    assert "diagnostic_questions" in data
    assert len(data["detected_components"]) > 0

    # Evaluate with diagnostic answers
    eval_res = client.post(
        "/listings/evaluate",
        data={
            "category": "Smartphones & Mobile Devices",
            "working_status": "partially_working",
            "physical_condition": "fair",
            "diagnostic_answers": json.dumps({"display": "cracked_glass", "motherboard": "boots"}),
            "detected_components": json.dumps(data["detected_components"]),
        }
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.get_json()
    assert eval_data["route"] == "repair"
    assert any("Display" in target for target in eval_data["repair_target_components"])
