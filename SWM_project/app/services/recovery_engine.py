"""
EcoLoop Recovery Decision Engine
==================================
Implements the rule-based logic defined in the Rule-Based Logic
Specification (sections 3–9).

This module is intentionally kept separate from Flask routes so it can
be unit-tested independently of the web application.

Input
-----
A dict (or ItemDetails dataclass) containing:
  - category           : str  — confirmed category (display name)
  - working_status     : str  — "working" | "not_working" | "partially_working"
  - physical_condition : str  — "excellent" | "good" | "fair" | "poor"
  - defects            : str  — free-text description of known defects (may be empty)
  - repair_history     : str  — free text
  - estimated_repair_cost : float | None
  - estimated_resale_value : float | None
  - asking_price       : float | None
  - age_years          : float | None
  - safety_flags       : list[str]   — e.g. ["swollen_battery", "overheating"]

Output
------
A RecoveryResult dataclass with:
  - route              : str
  - suitability_score  : int | None   (0-100, rule-based indicator only)
  - reason_codes       : list[str]
  - explanation        : str
  - safety_flag        : bool
  - manual_review_flag : bool
  - missing_info       : list[str]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Route constants ───────────────────────────────────────────────────────────
ROUTE_REUSE_RESALE       = "reuse_resale"
ROUTE_REPAIR             = "repair"
ROUTE_REFURBISHMENT      = "refurbishment"
ROUTE_PARTS_RECOVERY     = "parts_recovery"
ROUTE_RECYCLING          = "recycling"
ROUTE_MANUAL_REVIEW      = "manual_review"
ROUTE_SAFETY_REVIEW      = "safety_review"

# ── Safety trigger keywords ───────────────────────────────────────────────────
SAFETY_FLAGS_CRITICAL = {
    "swollen_battery",
    "leaking_battery",
    "overheating",
    "smoke",
    "burning_smell",
    "fire_damage",
}

SAFETY_FLAGS_MODERATE = {
    "unknown_hazardous_component",
    "damaged_battery",
    "capacitor_damage",
}

# ── Categories considered safety-sensitive by default ────────────────────────
SAFETY_SENSITIVE_CATEGORIES = {
    "Battery & Power Equipment",
    "Circuit Board / Components",
    "Medical & Measurement Electronics",
}

# ── Reason code definitions ───────────────────────────────────────────────────
RC = {
    "WORKING_NO_DEFECT":    "Item is reported as working with no serious defect.",
    "NOT_WORKING":          "Item is reported as not working.",
    "PARTIALLY_WORKING":    "Item is reported as partially working.",
    "REPAIRABLE_DEFECT":    "Reported defect appears potentially repairable.",
    "REPAIR_ECONOMIC":      "Estimated repair cost is within economic threshold.",
    "REPAIR_UNECONOMIC":    "Estimated repair cost exceeds the economic threshold.",
    "MISSING_REPAIR_COST":  "Estimated repair cost was not provided.",
    "MISSING_RESALE_VALUE": "Estimated resale value was not provided.",
    "PARTS_REUSABLE":       "Components may be recoverable for reuse.",
    "SAFETY_OVERRIDE":      "A safety-sensitive condition requires specialist handling.",
    "SAFETY_CRITICAL":      "Critical safety flag detected — urgent specialist handling required.",
    "SAFETY_CATEGORY":      "This item category may contain safety-sensitive components.",
    "CATEGORY_UNKNOWN":     "Item category is unknown or uncertain.",
    "CRITICAL_INFO_MISSING":"One or more required fields were not provided.",
    "CONFLICTING_DATA":     "Submitted details appear to conflict.",
    "MANUAL_REVIEW_NEEDED": "Manual review is required due to uncertainty or missing data.",
    "CONDITION_POOR":       "Physical condition is reported as poor.",
    "AGE_HIGH":             "Item is old; repairability may be limited.",
}


@dataclass
class RecoveryResult:
    route:              str
    reason_codes:       list = field(default_factory=list)
    explanation:        str  = ""
    safety_flag:        bool = False
    manual_review_flag: bool = False
    suitability_score:  Optional[int] = None
    missing_info:       list = field(default_factory=list)
    salvageable_components: list = field(default_factory=list)
    repair_target_components: list = field(default_factory=list)
    diagnostic_summary: str = ""


# ── Configurable thresholds (match Config.REPAIR_COST_RATIO_THRESHOLD) ────────
DEFAULT_REPAIR_RATIO_THRESHOLD = 0.60
DEFAULT_OLD_AGE_YEARS = 10


# ═══════════════════════════════════════════════════════════════════════════════
# Main engine function
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate(
    category: str,
    working_status: str,
    physical_condition: str,
    defects: Optional[str] = None,
    repair_history: Optional[str] = None,
    estimated_repair_cost: Optional[float] = None,
    estimated_resale_value: Optional[float] = None,
    asking_price: Optional[float] = None,
    age_years: Optional[float] = None,
    safety_flags: Optional[list] = None,
    repair_ratio_threshold: float = DEFAULT_REPAIR_RATIO_THRESHOLD,
    diagnostic_answers: Optional[dict] = None,
    detected_components: Optional[list] = None,
) -> RecoveryResult:
    """
    Evaluate an item and return a RecoveryResult.

    Decision priority (as per specification):
      1. Validate input
      2. Safety overrides & component diagnostic hazard checks
      3. Component health diagnostic evaluation (if provided)
      4. Confirm category / missing critical data
      5. Condition and repair economics
      6. Return result
    """
    safety_flags = list(safety_flags or [])
    reason_codes: list[str] = []
    missing_info: list[str] = []
    diagnostic_answers = diagnostic_answers or {}
    detected_components = detected_components or []

    # ── Step 1: Validate input ───────────────────────────────────────────────
    validation_error = _validate_inputs(
        category, working_status, physical_condition,
        estimated_repair_cost, estimated_resale_value,
        asking_price, age_years,
    )
    if validation_error:
        missing_info.extend(validation_error)

    # ── Step 1b: Component Diagnostic Hazards ────────────────────────────────
    # Check if user answered that a component is swollen, sparking, or burnt
    batt_ans = diagnostic_answers.get("battery") or diagnostic_answers.get("battery_health")
    mb_ans = diagnostic_answers.get("motherboard") or diagnostic_answers.get("motherboard_health")
    pcb_ans = diagnostic_answers.get("pcb") or diagnostic_answers.get("pcb_components") or diagnostic_answers.get("pcb_health")
    psu_ans = diagnostic_answers.get("power_supply") or diagnostic_answers.get("power_supply_health")
    disp_ans = diagnostic_answers.get("display") or diagnostic_answers.get("display_health")
    casing_ans = diagnostic_answers.get("casing") or diagnostic_answers.get("casing_health")

    if batt_ans in ("swollen", "leaking", "bulging"):
        safety_flags.append("swollen_battery")
    if mb_ans in ("smoke_spark", "smoke", "sparks", "burning_smell"):
        safety_flags.append("smoke")
        safety_flags.append("burning_smell")
    if pcb_ans in ("burnt_board", "burnt_pcb", "charred"):
        safety_flags.append("fire_damage")
    if psu_ans in ("sparking", "overheating"):
        safety_flags.append("overheating")

    # ── Step 2: Safety overrides (SAFE-01 .. SAFE-04) ────────────────────────
    critical_flags = [f for f in safety_flags if f in SAFETY_FLAGS_CRITICAL]
    moderate_flags = [f for f in safety_flags if f in SAFETY_FLAGS_MODERATE]
    category_safety = category in SAFETY_SENSITIVE_CATEGORIES

    if critical_flags:
        reason_codes.append("SAFETY_CRITICAL")
        reason_codes.append("SAFETY_OVERRIDE")
        if diagnostic_answers:
            reason_codes.append("SAFETY_DIAGNOSTIC_CONFIRMED")
        explanation = (
            "⚠️ A critical safety condition has been detected "
            f"({', '.join(set(critical_flags)).replace('_', ' ')}). "
            "This item must not be resold, placed in general household waste, "
            "or dismantled at home. Please contact a qualified e-waste collection "
            "service or your local authority's hazardous waste facility immediately."
        )
        return RecoveryResult(
            route=ROUTE_SAFETY_REVIEW,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=True,
            manual_review_flag=True,
            suitability_score=0,
            diagnostic_summary="Safety lock triggered due to confirmed component hazards.",
        )

    if moderate_flags:
        reason_codes.append("SAFETY_OVERRIDE")
        explanation = (
            "⚠️ A potentially hazardous condition has been reported "
            f"({', '.join(set(moderate_flags)).replace('_', ' ')}). "
            "This item requires assessment by a qualified specialist. "
            "Do not attempt to dismantle or repair the item yourself."
        )
        return RecoveryResult(
            route=ROUTE_SAFETY_REVIEW,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=True,
            manual_review_flag=True,
            suitability_score=5,
        )

    # ── Step 3: Component Diagnostic-Driven Route Decision ───────────────────
    # If diagnostic answers were provided by the user, evaluate them deterministically
    if diagnostic_answers and category and category.lower() not in ("unknown / other", "unknown", ""):
        # 3a. Display Screen Repair: Core logic board boots, but screen glass is cracked
        if disp_ans in ("cracked_glass", "cracked") and (mb_ans in ("boots", "boots_normal", "working", "intact") or mb_ans is None):
            reason_codes.extend(["REPAIRABLE_DEFECT", "SCREEN_GLASS_REPAIRABLE", "CORE_FUNCTIONAL"])
            if category_safety:
                reason_codes.append("SAFETY_CATEGORY")
            return RecoveryResult(
                route=ROUTE_REPAIR,
                reason_codes=reason_codes,
                explanation=(
                    "Component diagnostics confirm that the core motherboard powers on and boots normally, "
                    "with defect isolated to the outer display glass. Economic display replacement/repair is recommended."
                ),
                suitability_score=78,
                safety_flag=bool(category_safety),
                repair_target_components=["LCD Display Screen (Outer Glass Replacement)", "Display Screen"],
                salvageable_components=["Motherboard & Logic Board", "Chassis & Hinges"],
                diagnostic_summary="Display glass defect with functional motherboard — routed to Repair.",
            )

        # 3b. Battery Degraded: Core logic boots & screen works, but battery degraded
        if batt_ans in ("degraded", "missing_dead", "dead", "poor") and (mb_ans in ("boots", "boots_normal", "working", "intact") or mb_ans is None) and (disp_ans in ("working", "intact", "normal") or disp_ans is None):
            reason_codes.extend(["REPAIRABLE_DEFECT", "BATTERY_DEGRADED", "REFURBISHMENT_VIABLE"])
            return RecoveryResult(
                route=ROUTE_REFURBISHMENT,
                reason_codes=reason_codes,
                explanation=(
                    "Core electronics and display are functional, but battery capacity has degraded. "
                    "Battery cell replacement and standard refurbishment is suggested to extend useful life."
                ),
                suitability_score=80,
                safety_flag=bool(category_safety),
                repair_target_components=["Internal Lithium Battery"],
                salvageable_components=["Display Screen", "Motherboard & Logic Board", "Chassis"],
                diagnostic_summary="Battery replacement needed — routed to Refurbishment.",
            )

        # 3c. PCB Component Repair: Bulging capacitors on board
        if pcb_ans in ("bulging_cap", "bulging"):
            reason_codes.extend(["REPAIRABLE_DEFECT", "CAPACITOR_REPLACEMENT_VIABLE"])
            return RecoveryResult(
                route=ROUTE_REPAIR,
                reason_codes=reason_codes,
                explanation=(
                    "Diagnostics identified domed or leaking electrolytic capacitors on the circuit board. "
                    "Board-level component desoldering and capacitor replacement is recommended."
                ),
                suitability_score=72,
                safety_flag=bool(category_safety),
                repair_target_components=["Electrolytic Capacitors"],
                diagnostic_summary="Bulging capacitors identified — routed to Board-Level Repair.",
            )

        # 3d. Parts Harvesting: Dead Motherboard / No Power, BUT display or casing intact
        if mb_ans in ("no_power", "power_error", "dead", "unresponsive") and (disp_ans in ("working", "intact", "normal", "cracked_glass") or casing_ans in ("good", "intact", "normal")):
            salvage = []
            if disp_ans in ("working", "intact", "normal"):
                salvage.append("Display Screen & Backlight")
                salvage.append("Display Screen")
            if casing_ans in ("good", "intact", "normal"):
                salvage.append("Chassis Enclosure & Hinges")
                salvage.append("Chassis & Enclosure")
            if diagnostic_answers.get("keyboard_health") in ("working", "intact") or diagnostic_answers.get("keyboard") in ("working", "intact"):
                salvage.append("Keyboard & Trackpad")

            reason_codes.extend(["CORE_DEAD_PARTS_SALVAGEABLE", "PARTS_REUSABLE"])
            return RecoveryResult(
                route=ROUTE_PARTS_RECOVERY,
                reason_codes=reason_codes,
                explanation=(
                    "The main logic board is unresponsive or non-functional, but key detected components "
                    f"({', '.join(salvage) or 'Display and casing'}) are in good condition. "
                    "Parts harvesting is recommended so these components can be reused to repair other units."
                ),
                suitability_score=68,
                safety_flag=bool(category_safety),
                salvageable_components=salvage,
                diagnostic_summary="Dead motherboard with healthy peripherals — routed to Parts Recovery.",
            )

        # 3e. Certified Material Recycling: Multiple major components damaged
        if (mb_ans in ("no_power", "dead") and disp_ans in ("broken_panel", "broken", "shattered")) or casing_ans in ("crushed", "broken") or pcb_ans in ("corrosion", "water_damage"):
            reason_codes.extend(["MULTIPLE_COMPONENTS_FAILED", "RECYCLING_RECOMMENDED"])
            return RecoveryResult(
                route=ROUTE_RECYCLING,
                reason_codes=reason_codes,
                explanation=(
                    "Multiple core components (Motherboard, Display Screen, or Chassis) have failed or sustained "
                    "severe physical damage beyond economic repair. The item is routed to certified material recycling "
                    "to recover precious metals and hazardous materials safely."
                ),
                suitability_score=45,
                safety_flag=bool(category_safety),
                diagnostic_summary="Multiple core systems damaged — routed to Material Recycling.",
            )

        # 3f. Direct Reuse / Resale: All answered components healthy
        all_healthy = (
            disp_ans in ("working", "intact", "normal", None) and
            batt_ans in ("normal", "healthy", "intact", None) and
            mb_ans in ("boots", "boots_normal", "working", "intact", None) and
            casing_ans in ("good", "intact", "normal", None) and
            pcb_ans in ("intact", "clean", None) and
            working_status != "not_working"
        )
        if all_healthy:
            reason_codes.append("ALL_COMPONENTS_FUNCTIONAL")
            reason_codes.append("WORKING_NO_DEFECT")
            if category_safety:
                reason_codes.append("SAFETY_CATEGORY")
            return RecoveryResult(
                route=ROUTE_REUSE_RESALE,
                reason_codes=reason_codes,
                explanation=(
                    "All detected components (Screen, Motherboard, Battery, and Casing) were verified fully functional "
                    "through diagnostics. Direct reuse or secondary resale provides the highest circular economic value."
                ),
                suitability_score=92,
                safety_flag=False,
                salvageable_components=[c.get("name", "Component") for c in detected_components],
                diagnostic_summary="All components verified functional — routed to Direct Reuse.",
            )

    # ── Step 4: Category / critical-data check (REC-01) ─────────────────────
    validation_error = _validate_inputs(
        category, working_status, physical_condition,
        estimated_repair_cost, estimated_resale_value,
        asking_price, age_years,
    )
    if validation_error:
        missing_info.extend(validation_error)

    # ── Step 2: Safety overrides (SAFE-01 .. SAFE-04) ────────────────────────
    critical_flags = [f for f in safety_flags if f in SAFETY_FLAGS_CRITICAL]
    moderate_flags = [f for f in safety_flags if f in SAFETY_FLAGS_MODERATE]
    category_safety = category in SAFETY_SENSITIVE_CATEGORIES

    if critical_flags:
        reason_codes.append("SAFETY_CRITICAL")
        reason_codes.append("SAFETY_OVERRIDE")
        explanation = (
            "⚠️ A critical safety condition has been detected "
            f"({', '.join(critical_flags).replace('_', ' ')}). "
            "This item must not be resold, placed in general household waste, "
            "or dismantled at home. Please contact a qualified e-waste collection "
            "service or your local authority's hazardous waste facility immediately."
        )
        return RecoveryResult(
            route=ROUTE_SAFETY_REVIEW,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=True,
            manual_review_flag=True,
            suitability_score=0,
        )

    if moderate_flags:
        reason_codes.append("SAFETY_OVERRIDE")
        explanation = (
            "⚠️ A potentially hazardous condition has been reported "
            f"({', '.join(moderate_flags).replace('_', ' ')}). "
            "This item requires assessment by a qualified specialist. "
            "Do not attempt to dismantle or repair the item yourself."
        )
        return RecoveryResult(
            route=ROUTE_SAFETY_REVIEW,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=True,
            manual_review_flag=True,
            suitability_score=5,
        )

    # ── Step 3: Category / critical-data check (REC-01) ─────────────────────
    if not category or category.lower() in ("unknown / other", "unknown", ""):
        reason_codes.append("CATEGORY_UNKNOWN")
        return RecoveryResult(
            route=ROUTE_MANUAL_REVIEW,
            reason_codes=reason_codes,
            explanation=(
                "The item category could not be confirmed. "
                "A manual review is needed before a recovery route can be suggested."
            ),
            manual_review_flag=True,
            suitability_score=None,
        )

    if missing_info:
        reason_codes.append("CRITICAL_INFO_MISSING")
        reason_codes.append("MANUAL_REVIEW_NEEDED")
        return RecoveryResult(
            route=ROUTE_MANUAL_REVIEW,
            reason_codes=reason_codes,
            explanation=(
                "Some required information is missing: "
                + ", ".join(missing_info) + ". "
                "Please complete the listing details so a recommendation can be made."
            ),
            manual_review_flag=True,
            missing_info=missing_info,
            suitability_score=None,
        )

    # ── Step 4: Recovery route decision ─────────────────────────────────────
    defects_lower = (defects or "").lower()
    has_serious_defect = _has_serious_defect(defects_lower)
    is_repairable = _appears_repairable(defects_lower)

    # Add category safety flag as a note (doesn't block but informs)
    if category_safety:
        reason_codes.append("SAFETY_CATEGORY")

    # REC-02: Reuse / Resale
    if working_status == "working" and not has_serious_defect:
        reason_codes.append("WORKING_NO_DEFECT")
        score = _compute_score(
            base=85,
            physical_condition=physical_condition,
            age_years=age_years,
        )
        explanation = (
            "The item is reported as working with no serious defect. "
            "Reuse or resale is suggested as the primary route. "
            "Note: this recommendation is based on seller-provided information. "
            "A buyer or partner may inspect the item before purchase."
        )
        if category_safety:
            explanation += (
                " This category may contain safety-sensitive components; "
                "the receiving party should verify the item's condition."
            )
        return RecoveryResult(
            route=ROUTE_REUSE_RESALE,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=False,
            suitability_score=score,
        )

    # REC-03: Repair
    if working_status in ("not_working", "partially_working") and is_repairable:
        reason_codes.append("NOT_WORKING" if working_status == "not_working" else "PARTIALLY_WORKING")
        reason_codes.append("REPAIRABLE_DEFECT")

        repair_economic, econ_reason = _assess_repair_economics(
            estimated_repair_cost, estimated_resale_value, repair_ratio_threshold
        )
        reason_codes.append(econ_reason)

        if econ_reason == "MISSING_REPAIR_COST":
            missing_info.append("estimated repair cost")
        if econ_reason == "MISSING_RESALE_VALUE":
            missing_info.append("estimated resale value")

        if repair_economic is True:
            score = _compute_score(
                base=65,
                physical_condition=physical_condition,
                age_years=age_years,
            )
            explanation = (
                "The item is not fully working but the reported defect appears potentially repairable "
                "and estimated repair cost is within an acceptable range relative to estimated resale value. "
                "A repair assessment by a qualified technician is suggested."
            )
            # Distinguish repair vs refurbishment by condition
            if physical_condition in ("fair", "poor") or (age_years or 0) > 5:
                reason_codes.append("CONDITION_POOR")
                explanation = (
                    "The item has reported defects and its condition or age suggests "
                    "more than basic repair may be needed. "
                    "A refurbishment assessment (repair, cleaning and part replacement) is suggested."
                )
                return RecoveryResult(
                    route=ROUTE_REFURBISHMENT,
                    reason_codes=reason_codes,
                    explanation=explanation,
                    safety_flag=bool(category_safety),
                    suitability_score=score,
                )
            return RecoveryResult(
                route=ROUTE_REPAIR,
                reason_codes=reason_codes,
                explanation=explanation,
                safety_flag=bool(category_safety),
                suitability_score=score,
            )

        if repair_economic is False:
            reason_codes.append("REPAIR_UNECONOMIC")
            # Fall through to parts recovery / recycling

        if repair_economic is None:
            # Economics unavailable → use condition fallback (REC-07)
            explanation = (
                "The item is not working and may be repairable, but repair cost or "
                "estimated resale value information is missing. "
                "Without a cost comparison, an independent inspection is recommended "
                "before committing to repair or recycling."
            )
            return RecoveryResult(
                route=ROUTE_MANUAL_REVIEW,
                reason_codes=reason_codes,
                explanation=explanation,
                manual_review_flag=True,
                missing_info=missing_info,
                suitability_score=None,
            )

    # REC-05: Parts Recovery
    if _components_may_be_recoverable(category):
        reason_codes.append("PARTS_REUSABLE")
        reason_codes.append("NOT_WORKING")
        score = _compute_score(
            base=40,
            physical_condition=physical_condition,
            age_years=age_years,
        )
        explanation = (
            "The item does not appear economically repairable, but some components "
            "may still be recoverable for reuse. "
            "An assessment by an appropriate repair or recovery partner is suggested."
        )
        return RecoveryResult(
            route=ROUTE_PARTS_RECOVERY,
            reason_codes=reason_codes,
            explanation=explanation,
            safety_flag=bool(category_safety),
            suitability_score=score,
        )

    # REC-06: Recycling
    reason_codes.append("NOT_WORKING")
    explanation = (
        "The item does not appear suitable for reuse or economical repair. "
        "Disposal through an approved e-waste recycling route is suggested. "
        "Do not place electronic equipment in general household waste."
    )
    return RecoveryResult(
        route=ROUTE_RECYCLING,
        reason_codes=reason_codes,
        explanation=explanation,
        safety_flag=bool(category_safety),
        suitability_score=_compute_score(
            base=20, physical_condition=physical_condition, age_years=age_years
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_inputs(
    category, working_status, physical_condition,
    repair_cost, resale_value, asking_price, age_years,
) -> list:
    errors = []
    if not working_status:
        errors.append("working status")
    if not physical_condition:
        errors.append("physical condition")
    if repair_cost is not None and repair_cost < 0:
        errors.append("estimated repair cost (must be non-negative)")
    if resale_value is not None and resale_value < 0:
        errors.append("estimated resale value (must be non-negative)")
    if asking_price is not None and asking_price < 0:
        errors.append("asking price (must be non-negative)")
    if age_years is not None and age_years < 0:
        errors.append("age in years (must be non-negative)")
    return errors


def _has_serious_defect(defects_lower: str) -> bool:
    serious_keywords = [
        "cracked screen", "broken screen", "motherboard", "dead", "water damage",
        "burnt", "melted", "irreparable", "no power", "missing parts",
    ]
    return any(kw in defects_lower for kw in serious_keywords)


def _appears_repairable(defects_lower: str) -> bool:
    """
    Conservative heuristic: consider a defect potentially repairable if it
    includes common repairable indicators.  Returns False if no defect text
    or if serious/irrepairable keywords dominate.
    """
    if not defects_lower.strip():
        return False   # No defect info → cannot assess
    irreparable = ["dead", "burnt", "melted", "irreparable", "total loss"]
    if any(kw in defects_lower for kw in irreparable):
        return False
    repairable = [
        "battery", "screen", "keyboard", "fan", "charger port", "speaker",
        "hinge", "button", "cable", "power button", "charging", "slow",
        "software", "freezes", "corrupted", "cracked case",
    ]
    return any(kw in defects_lower for kw in repairable)


def _assess_repair_economics(
    repair_cost: Optional[float],
    resale_value: Optional[float],
    threshold: float,
) -> tuple:
    """
    Returns (decision, reason_code).
    decision: True = economic, False = uneconomic, None = cannot assess.
    """
    if repair_cost is None:
        return None, "MISSING_REPAIR_COST"
    if resale_value is None or resale_value == 0:
        return None, "MISSING_RESALE_VALUE"
    ratio = repair_cost / resale_value
    if ratio <= threshold:
        return True, "REPAIR_ECONOMIC"
    return False, "REPAIR_UNECONOMIC"


def _components_may_be_recoverable(category: str) -> bool:
    component_rich = {
        "Laptop / Computer",
        "Mobile & Communication",
        "Display & Entertainment",
        "Circuit Board / Components",
        "Office Equipment",
        "Battery & Power Equipment",
    }
    return category in component_rich


def _compute_score(base: int, physical_condition: str, age_years: Optional[float]) -> int:
    """
    Rule-based suitability score (0–100).
    This is NOT a probability of sale, repair success or environmental benefit.
    It is labelled 'rule-based suitability score' wherever displayed.
    """
    score = base
    condition_adjustment = {
        "excellent":  +10,
        "good":       +5,
        "fair":       0,
        "poor":       -15,
    }
    score += condition_adjustment.get(physical_condition, 0)

    if age_years is not None:
        if age_years > DEFAULT_OLD_AGE_YEARS:
            score -= 10
        elif age_years > 5:
            score -= 5

    return max(0, min(100, score))


# ── Human-readable route labels ───────────────────────────────────────────────
ROUTE_DISPLAY = {
    ROUTE_REUSE_RESALE:   "Reuse / Resale",
    ROUTE_REPAIR:         "Repair Assessment",
    ROUTE_REFURBISHMENT:  "Refurbishment Assessment",
    ROUTE_PARTS_RECOVERY: "Parts Recovery",
    ROUTE_RECYCLING:      "Approved E-Waste Recycling",
    ROUTE_MANUAL_REVIEW:  "Manual Review Required",
    ROUTE_SAFETY_REVIEW:  "Specialist Safety Handling",
}

ROUTE_ICON = {
    ROUTE_REUSE_RESALE:   "bi-arrow-repeat",
    ROUTE_REPAIR:         "bi-tools",
    ROUTE_REFURBISHMENT:  "bi-wrench-adjustable",
    ROUTE_PARTS_RECOVERY: "bi-puzzle",
    ROUTE_RECYCLING:      "bi-recycle",
    ROUTE_MANUAL_REVIEW:  "bi-clipboard-check",
    ROUTE_SAFETY_REVIEW:  "bi-exclamation-triangle-fill",
}
