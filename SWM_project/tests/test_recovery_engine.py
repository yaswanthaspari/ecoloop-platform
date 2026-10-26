"""Unit tests for the deterministic recovery decision engine."""
import pytest
from app.services.recovery_engine import (
    evaluate,
    ROUTE_REUSE_RESALE,
    ROUTE_REPAIR,
    ROUTE_REFURBISHMENT,
    ROUTE_PARTS_RECOVERY,
    ROUTE_RECYCLING,
    ROUTE_SAFETY_REVIEW,
    ROUTE_MANUAL_REVIEW,
)


def test_working_item_routes_to_reuse():
    """An item reported as working, in excellent condition, should recommend reuse."""
    result = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="working",
        physical_condition="excellent",
        defects=None,
        asking_price=200.0,
        age_years=1.5,
    )
    assert result.route == ROUTE_REUSE_RESALE
    assert not result.safety_flag
    assert not result.manual_review_flag


def test_repairable_item_routes_to_repair():
    """An item needing minor repair with repair cost < threshold should route to repair."""
    result = evaluate(
        category="Laptops & Notebooks",
        working_status="partially_working",
        physical_condition="good",
        defects="Cracked outer screen glass",
        estimated_repair_cost=80.0,
        estimated_resale_value=250.0,
    )
    assert result.route in (ROUTE_REPAIR, ROUTE_REFURBISHMENT)
    assert not result.safety_flag


def test_critical_safety_hazard_triggers_safety_override():
    """Critical safety flags such as swollen battery must immediately trigger safety override."""
    result = evaluate(
        category="Smartphones & Mobile Devices",
        working_status="working",
        physical_condition="good",
        safety_flags=["swollen_battery"],
    )
    assert result.route == ROUTE_SAFETY_REVIEW
    assert result.safety_flag is True
    assert result.manual_review_flag is True


def test_non_functional_severe_damage_routes_to_recycle_or_parts():
    """Severe physical damage or non-working old device without repair viability routes to recycling or parts."""
    result = evaluate(
        category="Monitors & Displays",
        working_status="not_working",
        physical_condition="poor",
        defects="Completely smashed panel, water intrusion",
        age_years=12.0,
    )
    assert result.route in (ROUTE_RECYCLING, ROUTE_PARTS_RECOVERY)


def test_component_diagnostics_cracked_glass_routes_to_repair():
    """Cracked glass with healthy motherboard routes directly to repair."""
    result = evaluate(
        category="Laptop / Computer",
        working_status="partially_working",
        physical_condition="good",
        diagnostic_answers={
            "display_health": "cracked_glass",
            "motherboard_health": "boots",
            "battery_health": "normal",
            "casing_health": "good",
        },
    )
    assert result.route == ROUTE_REPAIR
    assert "Display Screen" in result.repair_target_components[0]
    assert not result.safety_flag


def test_component_diagnostics_swollen_battery_routes_to_safety_review():
    """Swollen battery confirmed in diagnostics triggers safety review."""
    result = evaluate(
        category="Mobile & Communication",
        working_status="working",
        physical_condition="good",
        diagnostic_answers={
            "battery_health": "swollen",
            "display_health": "working",
        },
    )
    assert result.route == ROUTE_SAFETY_REVIEW
    assert result.safety_flag is True
    assert "SAFETY_DIAGNOSTIC_CONFIRMED" in result.reason_codes


def test_component_diagnostics_dead_motherboard_routes_to_parts_recovery():
    """Dead board with working display panel routes to parts harvesting."""
    result = evaluate(
        category="Laptop / Computer",
        working_status="not_working",
        physical_condition="good",
        diagnostic_answers={
            "motherboard_health": "no_power",
            "display_health": "working",
            "casing_health": "good",
        },
    )
    assert result.route == ROUTE_PARTS_RECOVERY
    assert "Display Screen & Backlight" in result.salvageable_components
