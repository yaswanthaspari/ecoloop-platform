"""
EcoLoop EcoImpact Service
===========================
Retrieves reviewed environmental knowledge records from the database
and formats them for display.

Rules implemented (ECO-01 .. ECO-07):
  ECO-01: Use reviewed knowledge records only.
  ECO-02: Show only effects relevant to the confirmed category.
  ECO-03: Include benefits of reuse and responsible recycling.
  ECO-04: Use cautious wording (may / can).
  ECO-05: Cite source with title and URL.
  ECO-06: Return None / empty list when no matching reviewed record exists.
  ECO-07: Match advice wording to the recommended route.

This module does NOT use a generative AI API.
It does NOT invent facts, citations or impact numbers.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EcoImpactResult:
    category: str
    records_found: bool = False
    impacts: list = field(default_factory=list)   # list of dicts
    route_advice: str = ""
    unavailable_message: str = ""


def get_ecoimpact(
    category: str,
    route: str,
    safety_flag: bool = False,
    hazard_types: Optional[list] = None,
) -> EcoImpactResult:
    """
    Retrieve reviewed environmental impact records for a given category.

    Parameters
    ----------
    category    : confirmed item category (display name)
    route       : recommended recovery route from the engine
    safety_flag : True if a safety concern was raised
    hazard_types: optional list of hazard-type keywords to filter records

    Returns
    -------
    EcoImpactResult — contains impacts list and source references.
                      Empty if no reviewed records exist.
    """
    from app.models.environmental_impact import EnvironmentalImpact

    query = EnvironmentalImpact.query.filter_by(
        category=category, review_status="reviewed"
    )
    if hazard_types:
        # Filter to hazard types relevant to the safety flags
        query = query.filter(
            EnvironmentalImpact.hazard_type.in_(hazard_types)
        )

    records = query.all()

    if not records:
        return EcoImpactResult(
            category=category,
            records_found=False,
            unavailable_message=(
                "Verified environmental impact information is not yet available "
                f"for the '{category}' category. "
                "For guidance on responsible e-waste disposal, contact your local "
                "authority or a certified e-waste collection service."
            ),
        )

    impacts = []
    for rec in records:
        impacts.append({
            "hazard_type":               rec.hazard_type,
            "improper_disposal_effect":  rec.improper_disposal_effect,
            "environmental_consequence": rec.environmental_consequence,
            "recommended_action":        rec.recommended_action,
            "source_title":              rec.source_title,
            "source_organization":       rec.source_organization,
            "source_url":                rec.source_url,
            "reviewed_at":               rec.reviewed_at.isoformat() if rec.reviewed_at else None,
        })

    route_advice = _route_advice(route, category, safety_flag)

    return EcoImpactResult(
        category=category,
        records_found=True,
        impacts=impacts,
        route_advice=route_advice,
    )


def _route_advice(route: str, category: str, safety_flag: bool) -> str:
    """Generate route-appropriate advice text (ECO-07)."""
    from app.services.recovery_engine import (
        ROUTE_REUSE_RESALE, ROUTE_REPAIR, ROUTE_REFURBISHMENT,
        ROUTE_PARTS_RECOVERY, ROUTE_RECYCLING, ROUTE_SAFETY_REVIEW,
    )

    if route == ROUTE_REUSE_RESALE:
        return (
            "Reusing or reselling this item can extend its useful life and reduce "
            "the demand for new resources. Choosing reuse is one of the most "
            "effective ways to reduce e-waste generation."
        )
    if route in (ROUTE_REPAIR, ROUTE_REFURBISHMENT):
        return (
            "Repairing or refurbishing electronics can significantly extend product "
            "life and reduce the environmental impact of manufacturing new devices. "
            "Using a qualified technician ensures the item is handled safely."
        )
    if route == ROUTE_PARTS_RECOVERY:
        return (
            "Recovering reusable components can reduce the need for new parts and "
            "keep valuable materials in circulation. "
            "An approved recovery partner can assess which components can be safely reused."
        )
    if route == ROUTE_RECYCLING:
        return (
            "Responsible e-waste recycling can recover valuable materials including "
            "metals, plastics and glass, and may reduce the need for virgin resource extraction. "
            "Always use an approved collection point or certified recycling service — "
            "do not place electronics in general household waste."
        )
    if route == ROUTE_SAFETY_REVIEW or safety_flag:
        return (
            "⚠️ This item may require specialist handling. Do not attempt to dismantle, "
            "puncture or repair hazardous components yourself. "
            "Contact a qualified e-waste collection service or your local authority's "
            "hazardous waste facility for safe disposal guidance."
        )
    return (
        "Please consult a qualified e-waste specialist or approved collection service "
        "for guidance on the most appropriate handling for this item."
    )
