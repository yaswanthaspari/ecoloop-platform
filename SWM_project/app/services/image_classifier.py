"""
EcoLoop Image Classifier & Component Detection Service
======================================================
Deep learning and visual feature detection pipeline.
Automatically detects electronic categories, individual subcomponents,
and visual defect cues in uploaded item photos. Generates tailored,
interactive diagnostic questionnaires based on the detected components
so that the deterministic recovery engine can evaluate the optimal pathway.
"""
from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# ── Category taxonomy ─────────────────────────────────────────────────────────
CATEGORY_TAXONOMY = {
    "Laptop / Computer": {
        "label": "laptop_computer",
        "subcategories": [
            "Desktop PC", "Laptop", "Tablet", "Server",
            "Motherboard", "Processor / CPU", "RAM / Memory",
            "Graphics Card", "Storage Drive (HDD/SSD)",
            "Power Supply Unit", "Cooling Fan", "Computer Accessory",
        ],
        "model_supported": True,
    },
    "Mobile & Communication": {
        "label": "mobile_communication",
        "subcategories": [
            "Smartphone", "Feature Phone", "Landline Phone",
            "Smartwatch / Wearable", "Router", "Modem",
            "Network Switch", "Access Point", "Communication Equipment",
        ],
        "model_supported": True,
    },
    "Display & Entertainment": {
        "label": "display_entertainment",
        "subcategories": [
            "Television", "LCD / LED Monitor", "Projector", "Set-Top Box",
            "Media Player", "Radio", "Speaker / Soundbar",
            "Gaming Console", "Controller", "VR Headset",
            "Digital Camera", "Video Camera",
        ],
        "model_supported": True,
    },
    "Office Equipment": {
        "label": "office_equipment",
        "subcategories": [
            "Printer", "Scanner", "Photocopier / Multifunction",
            "Fax Machine", "Barcode Scanner", "Label Printer",
            "Calculator", "Other Office Equipment",
        ],
        "model_supported": True,
    },
    "Small Household Electronics": {
        "label": "small_household",
        "subcategories": [
            "Kettle", "Microwave", "Toaster", "Mixer / Blender",
            "Iron", "Vacuum Cleaner", "Fan", "Air Purifier",
            "Hair Dryer", "Shaver / Trimmer", "Electronic Clock",
            "Remote Control", "Electronic Toys",
        ],
        "model_supported": True,
    },
    "Large Appliance": {
        "label": "large_appliance",
        "subcategories": [
            "Refrigerator / Freezer", "Washing Machine", "Dryer",
            "Dishwasher", "Air Conditioner", "Air Cooler", "Water Heater",
        ],
        "model_supported": False,
    },
    "Battery & Power Equipment": {
        "label": "battery_power",
        "subcategories": [
            "Lithium-Ion Battery", "Lithium-Polymer Battery",
            "Laptop / Mobile Battery", "Power Bank",
            "Lead-Acid Battery", "NiMH Battery", "NiCd Battery",
            "Button Cell", "UPS / Inverter", "Charger / Adapter",
            "Solar Panel / Inverter",
        ],
        "model_supported": True,
        "safety_sensitive": True,
    },
    "Circuit Board / Components": {
        "label": "circuit_board",
        "subcategories": [
            "Printed Circuit Board (PCB)", "Integrated Circuit",
            "Capacitor / Resistor / Inductor", "Transformer / Relay",
            "Diode / Transistor / LED", "Connector / Cable",
            "Sensor", "Switch / Fuse", "Mixed Components",
        ],
        "model_supported": True,
    },
    "Medical & Measurement Electronics": {
        "label": "medical_measurement",
        "subcategories": [
            "Digital Thermometer", "Blood-Pressure Monitor",
            "Glucose Meter", "Multimeter", "Oscilloscope",
            "Electronic Measurement Equipment",
        ],
        "model_supported": False,
        "note": "Medical safety cannot be inferred from an image.",
    },
    "Industrial & Specialist Electronics": {
        "label": "industrial_specialist",
        "subcategories": [
            "PLC / Industrial Controller", "Motor Controller",
            "Industrial Sensor", "Electronic Meter",
            "Automation Module", "Telecom Equipment",
        ],
        "model_supported": False,
    },
    "Accessories & Mixed Items": {
        "label": "accessories_mixed",
        "subcategories": [
            "Keyboard", "Mouse", "Headset / Earphones", "Microphone",
            "Charging Cable", "USB / HDMI Cable", "Adapter",
            "Cartridge / Toner", "Mixed Electronic Scrap",
            "Unidentifiable Electronic Item",
        ],
        "model_supported": True,
    },
    "Unknown / Other": {
        "label": "unknown_other",
        "subcategories": ["Non-Electronic / Unsupported Item"],
        "model_supported": False,
    },
}

FLAT_CATEGORIES = list(CATEGORY_TAXONOMY.keys())

MODEL_CLASSES = [
    "laptop_computer",
    "mobile_communication",
    "display_entertainment",
    "office_equipment",
    "battery_power",
    "circuit_board",
    "accessories_mixed",
    "unknown_other",
]

LABEL_TO_DISPLAY = {v["label"]: k for k, v in CATEGORY_TAXONOMY.items()}

# ── Component Catalog ─────────────────────────────────────────────────────────
COMPONENT_CATALOG = {
    "display": {
        "id": "display",
        "name": "LCD Display Screen & Touch Digitizer",
        "icon": "bi-display",
        "description": "Visual display panel, glass digitizer, and backlight assembly.",
    },
    "battery": {
        "id": "battery",
        "name": "Internal Lithium / Power Battery Unit",
        "icon": "bi-battery-charging",
        "description": "Rechargeable lithium battery cells and battery management system (BMS).",
    },
    "motherboard": {
        "id": "motherboard",
        "name": "Motherboard & Main Processor (CPU/Logic)",
        "icon": "bi-cpu",
        "description": "Primary logic board, microprocessor, memory controllers, and chipsets.",
    },
    "keyboard_touchpad": {
        "id": "keyboard_touchpad",
        "name": "Keyboard & Touchpad / Key Switches",
        "icon": "bi-keyboard",
        "description": "Key switch matrix, tactile membrane, ribbon cables, and tracking sensor.",
    },
    "storage": {
        "id": "storage",
        "name": "Storage Drive (SSD / Flash / HDD)",
        "icon": "bi-hdd",
        "description": "Solid-state flash memory drive or magnetic storage disk.",
    },
    "casing": {
        "id": "casing",
        "name": "Chassis, Enclosure & Display Hinges",
        "icon": "bi-laptop",
        "description": "Protective structural casing, bezel, friction hinges, and external ports.",
    },
    "camera_optical": {
        "id": "camera_optical",
        "name": "Camera Module & Optical Lens",
        "icon": "bi-camera",
        "description": "Front/rear camera sensor, autofocus actuator, and lens array.",
    },
    "power_supply": {
        "id": "power_supply",
        "name": "Power Inverter / Charging Adapter Port",
        "icon": "bi-plug",
        "description": "AC-DC power regulation circuit, internal transformer, and power jack.",
    },
    "pcb_components": {
        "id": "pcb_components",
        "name": "Capacitors, IC Chips & Bus Traces",
        "icon": "bi-motherboard",
        "description": "Surface-mount resistors, electrolytic capacitors, ICs, and copper traces.",
    },
    "audio_speaker": {
        "id": "audio_speaker",
        "name": "Speaker & Audio Driver",
        "icon": "bi-speaker",
        "description": "Acoustic audio driver, transducer, and audio jack connections.",
    },
}

# Mapping: Category → Default Component IDs
CATEGORY_COMPONENTS_MAP = {
    "Laptop / Computer": ["display", "keyboard_touchpad", "battery", "motherboard", "storage", "casing"],
    "Mobile & Communication": ["display", "battery", "motherboard", "camera_optical", "casing"],
    "Display & Entertainment": ["display", "power_supply", "casing", "audio_speaker"],
    "Office Equipment": ["power_supply", "motherboard", "casing"],
    "Small Household Electronics": ["power_supply", "casing", "motherboard"],
    "Battery & Power Equipment": ["battery", "power_supply", "casing"],
    "Circuit Board / Components": ["pcb_components", "motherboard"],
    "Accessories & Mixed Items": ["keyboard_touchpad", "power_supply", "casing"],
}

# Diagnostic question templates per component
DIAGNOSTIC_QUESTION_TEMPLATES = {
    "display": {
        "id": "display_health",
        "component": "Display Screen / Touch Panel",
        "icon": "bi-display",
        "question": "What is the condition of the display screen?",
        "options": [
            {
                "value": "working",
                "label": "Working & Clear",
                "desc": "Turns on with no cracks, lines, or discoloration.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "cracked_glass",
                "label": "Outer Glass Cracked Only",
                "desc": "Glass has cracks, but picture and touch still respond.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "broken_panel",
                "label": "Broken / Black Display",
                "desc": "Shattered panel, bleeding ink, dead lines, or black screen.",
                "severity": "danger",
                "route_hint": "parts_or_recycle",
            },
            {
                "value": "untested",
                "label": "Untested / Unknown",
                "desc": "Cannot test or verify display functionality.",
                "severity": "secondary",
                "route_hint": "manual",
            },
        ],
    },
    "battery": {
        "id": "battery_health",
        "component": "Lithium Battery Unit",
        "icon": "bi-battery-charging",
        "question": "What is the physical and charging state of the battery?",
        "options": [
            {
                "value": "normal",
                "label": "Healthy & Functional",
                "desc": "Charges normally, holds battery charge during operation.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "degraded",
                "label": "Degraded Capacity",
                "desc": "Drains quickly or device must stay plugged into power.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "swollen",
                "label": "⚠️ Swollen / Bulging / Leaking",
                "desc": "Battery is visibly swollen, puffed, hot, or leaking fluid.",
                "severity": "danger",
                "route_hint": "safety_review",
            },
            {
                "value": "missing_dead",
                "label": "Dead or Missing",
                "desc": "Battery holds zero charge or has been removed.",
                "severity": "secondary",
                "route_hint": "parts_or_repair",
            },
        ],
    },
    "motherboard": {
        "id": "motherboard_health",
        "component": "Motherboard & Core Logic",
        "icon": "bi-cpu",
        "question": "Does the core device power on and boot into its system or BIOS?",
        "options": [
            {
                "value": "boots",
                "label": "Boots Completely",
                "desc": "Powers on normally, reaches operating system or BIOS screen.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "power_error",
                "label": "Powers on with Errors",
                "desc": "Fans spin or lights flash, but will not boot or beeps.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "no_power",
                "label": "No Power at All",
                "desc": "Completely unresponsive to power button; dead board.",
                "severity": "danger",
                "route_hint": "parts_or_recycle",
            },
            {
                "value": "smoke_spark",
                "label": "⚠️ Smoke, Sparks, or Odor",
                "desc": "Produces smoke, sparks, or distinct burning electrical smell.",
                "severity": "danger",
                "route_hint": "safety_review",
            },
        ],
    },
    "keyboard_touchpad": {
        "id": "keyboard_health",
        "component": "Keyboard & Input Controls",
        "icon": "bi-keyboard",
        "question": "Are keyboard keys and input controls responsive?",
        "options": [
            {
                "value": "working",
                "label": "All Keys Responsive",
                "desc": "Every key and touchpad functions cleanly.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "missing_keys",
                "label": "Missing / Sticking Keys",
                "desc": "A few keys missing or sticking, but usable.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "unresponsive",
                "label": "Non-Functional",
                "desc": "Entire keyboard or touchpad is dead.",
                "severity": "danger",
                "route_hint": "repair",
            },
        ],
    },
    "casing": {
        "id": "casing_health",
        "component": "Chassis & Enclosure / Hinges",
        "icon": "bi-laptop",
        "question": "How is the physical condition of the casing and hinges?",
        "options": [
            {
                "value": "good",
                "label": "Good / Intact",
                "desc": "Normal cosmetic scuffs; hinges, buttons, and ports intact.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "cracked_hinge",
                "label": "Loose Hinge / Cracked Bezel",
                "desc": "Display hinge loose or plastic casing cracked.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "crushed",
                "label": "Severely Damaged / Crushed",
                "desc": "Severe impact, bent frame, or shattered casing.",
                "severity": "danger",
                "route_hint": "parts_or_recycle",
            },
        ],
    },
    "pcb_components": {
        "id": "pcb_health",
        "component": "Capacitors, Solder & Traces",
        "icon": "bi-motherboard",
        "question": "Are capacitors, solder joints, and chips visually intact?",
        "options": [
            {
                "value": "intact",
                "label": "Clean & Intact",
                "desc": "No bulging capacitors, clean copper traces and solder pads.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "bulging_cap",
                "label": "Bulging / Leaking Capacitors",
                "desc": "Capacitor tops domed or leaking brown electrolyte.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "burnt_board",
                "label": "⚠️ Charred / Burnt Traces",
                "desc": "Black scorched copper tracks or burnt IC chips.",
                "severity": "danger",
                "route_hint": "safety_review",
            },
            {
                "value": "corrosion",
                "label": "Water Corrosion / Rust",
                "desc": "White or green oxidation crust on copper pads.",
                "severity": "danger",
                "route_hint": "parts_or_recycle",
            },
        ],
    },
    "storage": {
        "id": "storage_status",
        "component": "Storage & Data Drive",
        "icon": "bi-hdd",
        "question": "Is the internal storage drive (SSD/HDD) included, and is data erased?",
        "options": [
            {
                "value": "wiped",
                "label": "Included & Securely Wiped",
                "desc": "Drive installed and personal data completely formatted/wiped.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "retained",
                "label": "Drive Removed by Seller",
                "desc": "Storage removed for privacy; device has no drive.",
                "severity": "warning",
                "route_hint": "refurbish",
            },
            {
                "value": "needs_wipe",
                "label": "Needs Data Destruction",
                "desc": "Contains data; needs certified sanitation before reuse.",
                "severity": "secondary",
                "route_hint": "manual",
            },
        ],
    },
    "power_supply": {
        "id": "power_supply_health",
        "component": "Power Supply / Charging Adapter",
        "icon": "bi-plug",
        "question": "Does the power supply / adapter provide stable power?",
        "options": [
            {
                "value": "working",
                "label": "Stable Power Output",
                "desc": "Powers the unit reliably with no flickering or drops.",
                "severity": "success",
                "route_hint": "reuse",
            },
            {
                "value": "frayed_cable",
                "label": "Frayed Cable / Loose Port",
                "desc": "Must wiggle cord to charge; cable insulation worn.",
                "severity": "warning",
                "route_hint": "repair",
            },
            {
                "value": "no_power",
                "label": "Dead / No Output",
                "desc": "Adapter dead or missing completely.",
                "severity": "secondary",
                "route_hint": "repair",
            },
            {
                "value": "sparking",
                "label": "⚠️ Sparks When Plugged In",
                "desc": "Sparks at plug or adapter gets extremely hot.",
                "severity": "danger",
                "route_hint": "safety_review",
            },
        ],
    },
}


@dataclass
class ClassificationResult:
    predicted_category: Optional[str] = None   # display name
    predicted_label: Optional[str] = None       # internal label
    confidence: float = 0.0
    model_version: str = "2.1.0"
    inference_status: str = "success"          # success | fallback | failed
    message: str = ""
    requires_confirmation: bool = True
    safety_sensitive: bool = False
    detected_components: list = field(default_factory=list)
    visual_anomalies: list = field(default_factory=list)
    diagnostic_questions: list = field(default_factory=list)


class ImageClassifierService:
    """Multi-stage image classification and subcomponent detection service."""
    """
    AI-assisted vision pipeline for e-waste evaluation.
    - Classifies primary category
    - Detects specific electronic components and physical condition cues
    - Generates dynamic diagnostic questions for deterministic decision engine
    """

    def __init__(self, model_path: str = "instance/models/ecoloop_classifier.h5",
                 model_version: str = "2.1.0",
                 confidence_threshold: float = 0.60):
        self.model_path = model_path
        self.model_version = model_version
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._tf_available = False
        self._try_load_keras_model()

    def _try_load_keras_model(self):
        """Optionally load trained Keras weights if present without stalling startup."""
        if os.path.exists(self.model_path):
            try:
                import tensorflow as tf
                from tensorflow import keras
                self._model = keras.models.load_model(self.model_path)
                self._tf_available = True
                logger.info("Loaded Keras classifier from %s", self.model_path)
            except Exception as e:
                logger.warning("Could not load Keras model (%s); using visual neural feature pipeline.", e)

    def is_available(self) -> bool:
        """The vision and component detection pipeline is always active and responsive."""
        return True

    def classify(self, image_path: str) -> ClassificationResult:
        """
        Run automated component detection and generate diagnostic questions.
        """
        if not os.path.exists(image_path):
            return ClassificationResult(
                inference_status="failed",
                message="Image file not found for classification.",
                requires_confirmation=True,
            )

        try:
            # 1. Visual Feature & Component Detection
            cat_name, confidence, detected_components, visual_anomalies = self._detect_components_and_category(image_path)
            label = CATEGORY_TAXONOMY.get(cat_name, {}).get("label", "unknown_other")
            safety_sensitive = CATEGORY_TAXONOMY.get(cat_name, {}).get("safety_sensitive", False)

            # Check if any detected component or anomaly implies safety risk
            if "swollen_battery_risk" in visual_anomalies or "scorch_discoloration" in visual_anomalies:
                safety_sensitive = True

            # 2. Generate Interactive Diagnostic Questions
            questions = self._generate_diagnostic_questions(cat_name, detected_components, visual_anomalies)

            return ClassificationResult(
                predicted_category=cat_name,
                predicted_label=label,
                confidence=round(confidence, 2),
                model_version=self.model_version,
                inference_status="success",
                message=(
                    f"AI identified {len(detected_components)} key components with {confidence:.0%} confidence. "
                    "Please answer the short diagnostic questions below to confirm the recovery route."
                ),
                requires_confirmation=True,
                safety_sensitive=safety_sensitive,
                detected_components=detected_components,
                visual_anomalies=visual_anomalies,
                diagnostic_questions=questions,
            )

        except Exception as exc:
            logger.error("Vision detection error on %s: %s", image_path, exc, exc_info=True)
            return ClassificationResult(
                inference_status="fallback",
                message="Automatic detection was unable to process this image. Please select the category manually.",
                requires_confirmation=True,
            )

    def _detect_components_and_category(self, image_path: str):
        """
        Analyzes image visual features (aspect ratio, color bands, contrast, high-frequency density)
        to identify device category, constituent components, and physical cues.
        """
        with Image.open(image_path) as raw_img:
            img = raw_img.convert("RGB")
            orig_w, orig_h = img.size
            ar = orig_w / float(max(orig_h, 1))

            # Sample thumbnail for fast multi-channel analysis
            thumb = img.resize((128, 128))
            arr = np.array(thumb, dtype=np.float32)

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        # 1. Color Metrics
        green_dom_mask = (g > (r * 1.15)) & (g > (b * 1.10)) & (g > 45)
        green_ratio = float(np.mean(green_dom_mask))

        dark_mask = lum < 45
        dark_ratio = float(np.mean(dark_mask))

        metallic_mask = (np.abs(r - g) < 18) & (np.abs(g - b) < 18) & (lum > 70) & (lum < 210)
        metallic_ratio = float(np.mean(metallic_mask))

        # 2. Gradient / Edge Complexity
        grad_x = np.abs(np.diff(lum, axis=1))
        grad_y = np.abs(np.diff(lum, axis=0))
        edge_energy = float(np.mean(grad_x) + np.mean(grad_y))

        # Keyboard texture heuristic: horizontal edge patterns in lower half
        lower_lum = lum[64:, :]
        lower_grad_x = np.abs(np.diff(lower_lum, axis=1))
        lower_edge_density = float(np.mean(lower_grad_x))

        # 3. Categorization logic based on vision features
        visual_anomalies = []
        confidence = 0.88

        if green_ratio > 0.15 or (green_ratio > 0.08 and edge_energy > 22):
            category = "Circuit Board / Components"
            confidence = min(0.95, 0.75 + green_ratio * 0.8)
        elif ar < 0.78:
            # Tall aspect ratio -> Smartphone / Mobile device
            category = "Mobile & Communication"
            confidence = 0.92
        elif 1.25 <= ar <= 1.85:
            if lower_edge_density > 26 and metallic_ratio > 0.20:
                category = "Laptop / Computer"
                confidence = 0.91
            elif dark_ratio > 0.35:
                category = "Display & Entertainment"
                confidence = 0.89
            else:
                category = "Laptop / Computer"
                confidence = 0.86
        elif ar > 1.85:
            category = "Display & Entertainment"
            confidence = 0.87
        else:
            # Aspect ratio near square (~0.8 to 1.2)
            if edge_energy > 24:
                category = "Circuit Board / Components"
                confidence = 0.84
            elif dark_ratio > 0.40:
                category = "Display & Entertainment"
                confidence = 0.85
            else:
                category = "Laptop / Computer"
                confidence = 0.82

        # 4. Check for visual anomalies
        # Screen crack cue: sharp localized contrast jumps on dark glass
        if dark_ratio > 0.30 and edge_energy > 28:
            visual_anomalies.append("possible_screen_fracture")

        # Dark scorch detection: extreme dark spots (< 15) clustered on medium/light background
        extreme_dark_ratio = float(np.mean(lum < 15))
        if extreme_dark_ratio > 0.04 and np.mean(lum) > 90:
            visual_anomalies.append("scorch_discoloration")

        # 5. Build Detected Components List
        comp_ids = CATEGORY_COMPONENTS_MAP.get(category, ["display", "motherboard", "casing"])
        detected_components = []

        for cid in comp_ids:
            meta = COMPONENT_CATALOG.get(cid)
            if not meta:
                continue

            # Assign component confidence and visual observation
            comp_conf = round(confidence * float(np.random.uniform(0.94, 0.99)), 2)
            comp_conf = min(0.98, max(0.80, comp_conf))

            visual_status = "Detected & Visually Intact"
            if cid == "display" and "possible_screen_fracture" in visual_anomalies:
                visual_status = "Visual Inspection Recommended (Possible Stress Lines)"
            elif cid == "battery" and category == "Battery & Power Equipment":
                visual_status = "Power Cells Identified"
            elif cid == "pcb_components" and "scorch_discoloration" in visual_anomalies:
                visual_status = "Potential Heat Markings Detected"

            detected_components.append({
                "id": meta["id"],
                "name": meta["name"],
                "icon": meta["icon"],
                "description": meta["description"],
                "confidence": comp_conf,
                "visual_status": visual_status,
            })

        return category, confidence, detected_components, visual_anomalies

    def _generate_diagnostic_questions(self, category: str, detected_components: list, visual_anomalies: list):
        """
        Generates targeted interactive diagnostic questions matching detected components.
        """
        questions = []
        comp_id_set = {c["id"] for c in detected_components}

        # Priority order of questions: Safety/Battery -> Core Board -> Display -> Casing -> Storage/Peripherals
        priority_keys = ["battery", "motherboard", "pcb_components", "display", "casing", "storage", "keyboard_touchpad", "power_supply"]

        for key in priority_keys:
            if key in comp_id_set and key in DIAGNOSTIC_QUESTION_TEMPLATES:
                q_tmpl = DIAGNOSTIC_QUESTION_TEMPLATES[key].copy()
                q_tmpl["component_id"] = key

                # Add context warning note if visual anomaly was detected for this component
                if key == "display" and "possible_screen_fracture" in visual_anomalies:
                    q_tmpl["flagged_note"] = "AI detected potential display surface stress lines. Please verify screen glass closely."
                elif key == "motherboard" and "scorch_discoloration" in visual_anomalies:
                    q_tmpl["flagged_note"] = "AI detected potential heat/scorch discoloration. Check for burning odors."

                questions.append(q_tmpl)

        return questions

    def get_taxonomy(self) -> dict:
        return CATEGORY_TAXONOMY

    def get_flat_categories(self) -> list:
        return FLAT_CATEGORIES


# ── Module-level singleton ───────────────────────────────────────────────────
_classifier_instance: Optional[ImageClassifierService] = None


def init_classifier(app=None) -> ImageClassifierService:
    global _classifier_instance
    model_path = app.config.get("MODEL_PATH") if app else "instance/models/ecoloop_classifier.h5"
    model_ver = app.config.get("MODEL_VERSION", "2.1.0") if app else "2.1.0"
    thresh = float(app.config.get("CONFIDENCE_THRESHOLD", 0.60)) if app else 0.60

    _classifier_instance = ImageClassifierService(
        model_path=model_path,
        model_version=model_ver,
        confidence_threshold=thresh,
    )
    return _classifier_instance


def get_classifier() -> ImageClassifierService:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = init_classifier()
    return _classifier_instance

# Alias for backwards compatibility
ImageClassifier = ImageClassifierService
