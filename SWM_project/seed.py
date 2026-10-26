
"""
EcoLoop Database Seed Script
============================
Initializes the database schema and seeds initial data:
- Admin user and demo accounts (seller, recovery partners)
- Environmental knowledge records (EcoImpact)
- Sample listings across different categories and recovery routes
"""

import os
import json
from datetime import date

from app import create_app, db
from app.models.user import User
from app.models.environmental_impact import EnvironmentalImpact
from app.models.listing import Listing
from app.models.image_assessment import ImageAssessment
from app.models.recommendation import Recommendation
from app.models.listing_status_history import ListingStatusHistory


app = create_app()


def seed_database():
    with app.app_context():
        print("Creating all database tables (if not already existing)...")
        db.create_all()

        # ============================================================
        # 1. SEED / UPDATE USERS
        # ============================================================

        admin_email = os.environ.get(
            "ADMIN_EMAIL", "admin@ecoloop.local"
        )
        admin_pass = os.environ.get(
            "ADMIN_PASSWORD", "AdminPass123!"
        )
        admin_name = os.environ.get(
            "ADMIN_NAME", "EcoLoop Administrator"
        )

        # Admin account
        admin = User.query.filter_by(email=admin_email).first()

        if not admin:
            admin = User(
                name=admin_name,
                email=admin_email,
                role="admin",
                is_active_account=True,
            )
            admin.set_password(admin_pass)
            db.session.add(admin)
            print(f"Created admin: {admin_email}")
        else:
            admin.role = "admin"
            admin.is_active_account = True
            admin.set_password(admin_pass)
            print(f"Updated admin account: {admin_email}")

        # Seller account
        seller = User.query.filter_by(
            email="seller@ecoloop.local"
        ).first()

        if not seller:
            seller = User(
                name="Alice Green",
                email="seller@ecoloop.local",
                role="seller",
                contact="+1-555-0101",
                is_active_account=True,
            )
            seller.set_password("SellerPass123!")
            db.session.add(seller)
            print("Created demo seller: seller@ecoloop.local")
        else:
            seller.role = "seller"
            seller.is_active_account = True
            seller.set_password("SellerPass123!")
            print("Updated demo seller account")

        # Repairer account
        repairer = User.query.filter_by(
            email="repairer@ecoloop.local"
        ).first()

        if not repairer:
            repairer = User(
                name="Bob Fixer (TechSolutions)",
                email="repairer@ecoloop.local",
                role="recovery_partner",
                contact="+1-555-0202",
                is_active_account=True,
            )
            repairer.set_password("RepairerPass123!")
            db.session.add(repairer)
            print("Created demo repairer partner")
        else:
            repairer.role = "recovery_partner"
            repairer.is_active_account = True
            repairer.set_password("RepairerPass123!")
            print("Updated demo repairer account")

        # Recycler account
        recycler = User.query.filter_by(
            email="recycler@ecoloop.local"
        ).first()

        if not recycler:
            recycler = User(
                name="Charlie Certified Recycling",
                email="recycler@ecoloop.local",
                role="recovery_partner",
                contact="+1-555-0303",
                is_active_account=True,
            )
            recycler.set_password("RecyclerPass123!")
            db.session.add(recycler)
            print("Created demo recycler partner")
        else:
            recycler.role = "recovery_partner"
            recycler.is_active_account = True
            recycler.set_password("RecyclerPass123!")
            print("Updated demo recycler account")

        # Save accounts so their IDs are available below.
        db.session.commit()

        # ============================================================
        # 2. SEED ECOIMPACT KNOWLEDGE RECORDS
        # ============================================================

        knowledge_entries = [
            {
                "category": "Mobile & Communication",
                "hazard_type": "Lithium-Ion Battery",
                "improper_disposal_effect": (
                    "Damaged or compressed lithium batteries in regular "
                    "landfills may short-circuit and ignite intense "
                    "thermal runaway fires."
                ),
                "environmental_consequence": (
                    "Burning batteries release hydrogen fluoride and "
                    "airborne toxins; uncontained cells can leach cobalt "
                    "and nickel into groundwater."
                ),
                "recommended_action": (
                    "Never discard in household trash. Take to a dedicated "
                    "battery drop-off box or tape battery terminals "
                    "before drop-off."
                ),
                "source_title": "EPA Used Lithium-Ion Batteries Guidance",
                "source_organization": (
                    "U.S. Environmental Protection Agency"
                ),
                "source_url": (
                    "https://www.epa.gov/recycle/used-lithium-ion-batteries"
                ),
                "reviewed_at": date(2026, 1, 15),
                "review_status": "reviewed",
            },
            {
                "category": "Laptop / Computer",
                "hazard_type": "Lead & Brominated Flame Retardants",
                "improper_disposal_effect": (
                    "Circuit boards and solder contain lead; casing "
                    "plastics often contain brominated flame retardants "
                    "(BFRs) that resist natural decay."
                ),
                "environmental_consequence": (
                    "Leached lead contaminates soil and aquatic ecosystems, "
                    "while incineration of BFRs produces toxic dioxins "
                    "and furans."
                ),
                "recommended_action": (
                    "Deliver to a certified e-Stewards or R2 recycler "
                    "who can safely desolder chips and separate materials."
                ),
                "source_title": (
                    "Electronics Donation and Recycling Guidelines"
                ),
                "source_organization": "U.S. EPA",
                "source_url": (
                    "https://www.epa.gov/recycle/"
                    "electronics-donation-and-recycling"
                ),
                "reviewed_at": date(2026, 1, 20),
                "review_status": "reviewed",
            },
            {
                "category": "Display & Entertainment",
                "hazard_type": "Mercury & Phosphor Powders",
                "improper_disposal_effect": (
                    "Older CCFL-backlit LCDs and CRTs contain elemental "
                    "mercury vapor and toxic phosphors inside sealed "
                    "display tubes."
                ),
                "environmental_consequence": (
                    "Crushing monitors disperses mercury vapor into local "
                    "air, settling into waterways and bioaccumulating "
                    "in wildlife."
                ),
                "recommended_action": (
                    "Handle intact without breaking the display panel; "
                    "transport carefully to a municipal hazardous "
                    "e-waste collection center."
                ),
                "source_title": (
                    "Management of Spent Mercury-Containing Lamps "
                    "and Monitors"
                ),
                "source_organization": "Basel Action Network",
                "source_url": "https://www.ban.org",
                "reviewed_at": date(2026, 2, 1),
                "review_status": "reviewed",
            },
            {
                "category": "Office Equipment",
                "hazard_type": "Toner Particulates & Ozone Emissions",
                "improper_disposal_effect": (
                    "Residue toner dust contains carbon black and "
                    "microscopic plastic polymers that pose inhalation "
                    "hazards if ruptured."
                ),
                "environmental_consequence": (
                    "Fine toner dust contaminates urban runoff and "
                    "stormwater systems."
                ),
                "recommended_action": (
                    "Remove toner and ink cartridges for separate "
                    "cartridge recycling before recycling printer chassis."
                ),
                "source_title": "Printer Cartridge Recycling Best Practices",
                "source_organization": "CalRecycle",
                "source_url": "https://calrecycle.ca.gov",
                "reviewed_at": date(2026, 2, 15),
                "review_status": "reviewed",
            },
            {
                "category": "Battery & Power Equipment",
                "hazard_type": "Corrosive Electrolytes & Heavy Metals",
                "improper_disposal_effect": (
                    "Pouch and cylindrical battery cells can leak "
                    "corrosive electrolytes when punctured, causing "
                    "chemical burns and soil contamination."
                ),
                "environmental_consequence": (
                    "Heavy metals persist in topsoil, potentially "
                    "hindering plant growth and entering the food chain."
                ),
                "recommended_action": (
                    "Avoid puncturing or handling damaged cells. Deliver "
                    "them to an appropriate municipal household hazardous "
                    "waste collection site."
                ),
                "source_title": "Management of Spent Batteries",
                "source_organization": (
                    "United Nations Environment Programme"
                ),
                "source_url": "https://www.unep.org",
                "reviewed_at": date(2026, 2, 10),
                "review_status": "reviewed",
            },
        ]

        added_knowledge_count = 0

        for data in knowledge_entries:
            existing = EnvironmentalImpact.query.filter_by(
                category=data["category"],
                hazard_type=data["hazard_type"],
            ).first()

            if not existing:
                record = EnvironmentalImpact(**data)
                db.session.add(record)
                added_knowledge_count += 1

        if added_knowledge_count > 0:
            db.session.commit()
            print(
                f"Added {added_knowledge_count} EcoImpact records."
            )
        else:
            print("EcoImpact records already exist; skipping duplicates.")

        # ============================================================
        # 3. SEED SAMPLE LISTINGS
        # ============================================================

        if Listing.query.count() == 0:
            print("Seeding realistic sample listings...")

            items = [
                {
                    "title": "Apple iPhone 12 128GB - Fully Working",
                    "category_confirmed": "Mobile & Communication",
                    "brand_model": "Apple iPhone 12",
                    "age_years": 3.0,
                    "working_status": "working",
                    "physical_condition": "good",
                    "defects": (
                        "None. Minor hairline scratches on bezel only."
                    ),
                    "repair_history": (
                        "Battery replaced 1 year ago at authorized center."
                    ),
                    "estimated_repair_cost": None,
                    "estimated_resale_value": 300.00,
                    "asking_price": 280.00,
                    "additional_notes": (
                        "Upgraded to a newer phone. Ready for immediate reuse."
                    ),
                    "status": "available",
                    "pred_cat": "Mobile & Communication",
                    "confidence": 0.94,
                    "route": "reuse_resale",
                    "suitability_score": 95,
                    "reason_codes": ["WORKING_NO_DEFECT"],
                    "safety_flag": False,
                    "manual_review_flag": False,
                    "explanation": (
                        "Device is fully functional with good cosmetic "
                        "condition and strong residual market value."
                    ),
                },
                {
                    "title": "Dell XPS 13 9300 - Cracked Screen Glass",
                    "category_confirmed": "Laptop / Computer",
                    "brand_model": "Dell XPS 13 9300",
                    "age_years": 4.0,
                    "working_status": "partially_working",
                    "physical_condition": "fair",
                    "defects": (
                        "Internal display cracked from a drop; external "
                        "display output works fine."
                    ),
                    "repair_history": "None.",
                    "estimated_repair_cost": 80.00,
                    "estimated_resale_value": 250.00,
                    "asking_price": 150.00,
                    "additional_notes": (
                        "Powers on and boots to BIOS. Motherboard and SSD "
                        "operational."
                    ),
                    "status": "available",
                    "pred_cat": "Laptop / Computer",
                    "confidence": 0.91,
                    "route": "repair",
                    "suitability_score": 85,
                    "reason_codes": [
                        "PARTIALLY_WORKING",
                        "REPAIRABLE_DEFECT",
                        "REPAIR_ECONOMIC",
                    ],
                    "safety_flag": False,
                    "manual_review_flag": False,
                    "explanation": (
                        "Core logic board and storage are operational; "
                        "economical screen panel replacement makes this "
                        "device viable for repair."
                    ),
                },
                {
                    "title": "HP LaserJet Pro MFP M227fdw",
                    "category_confirmed": "Office Equipment",
                    "brand_model": "HP LaserJet Pro MFP M227fdw",
                    "age_years": 5.0,
                    "working_status": "partially_working",
                    "physical_condition": "good",
                    "defects": (
                        "Paper pickup roller needs cleaning or replacement."
                    ),
                    "repair_history": (
                        "Regular toner cartridge replacements."
                    ),
                    "estimated_repair_cost": 25.00,
                    "estimated_resale_value": 100.00,
                    "asking_price": 60.00,
                    "additional_notes": (
                        "Scanner and networking fully work. Minor servicing "
                        "restores full operation."
                    ),
                    "status": "available",
                    "pred_cat": "Office Equipment",
                    "confidence": 0.88,
                    "route": "refurbishment",
                    "suitability_score": 80,
                    "reason_codes": [
                        "PARTIALLY_WORKING",
                        "REPAIRABLE_DEFECT",
                    ],
                    "safety_flag": False,
                    "manual_review_flag": False,
                    "explanation": (
                        "Standard maintenance wear; roller replacement "
                        "and cleaning will restore full working condition."
                    ),
                },
                {
                    "title": "Water Damaged iPad Mini 4 - For Parts",
                    "category_confirmed": "Laptop / Computer",
                    "brand_model": "Apple iPad Mini 4",
                    "age_years": 7.0,
                    "working_status": "not_working",
                    "physical_condition": "poor",
                    "defects": (
                        "Liquid intrusion. Device does not turn on."
                    ),
                    "repair_history": "None.",
                    "estimated_repair_cost": None,
                    "estimated_resale_value": 30.00,
                    "asking_price": 25.00,
                    "additional_notes": (
                        "Aluminum casing, cameras, buttons, and internal "
                        "brackets are intact for spares."
                    ),
                    "status": "available",
                    "pred_cat": "Laptop / Computer",
                    "confidence": 0.89,
                    "route": "parts_recovery",
                    "suitability_score": 75,
                    "reason_codes": [
                        "NOT_WORKING",
                        "CONDITION_POOR",
                        "PARTS_REUSABLE",
                    ],
                    "safety_flag": False,
                    "manual_review_flag": False,
                    "explanation": (
                        "Liquid damage prevents reliable board-level "
                        "repair, but physical chassis and modular "
                        "components may be salvaged."
                    ),
                },
                {
                    "title": "Anker 20,000mAh Power Bank - Battery Swelling",
                    "category_confirmed": "Battery & Power Equipment",
                    "brand_model": "Anker PowerCore 20K",
                    "age_years": 3.0,
                    "working_status": "not_working",
                    "physical_condition": "poor",
                    "defects": (
                        "Visible case bulge from swollen pouch cell. "
                        "Potential fire risk."
                    ),
                    "repair_history": "None.",
                    "estimated_repair_cost": None,
                    "estimated_resale_value": 0.00,
                    "asking_price": 0.00,
                    "additional_notes": (
                        "Case has visible bulge from swollen pouch cell. "
                        "Submitted for hazardous disposal review."
                    ),
                    "status": "pending_review",
                    "pred_cat": "Battery & Power Equipment",
                    "confidence": 0.75,
                    "route": "manual_review",
                    "suitability_score": 20,
                    "reason_codes": [
                        "SAFETY_CRITICAL",
                        "SAFETY_OVERRIDE",
                    ],
                    "safety_flag": True,
                    "manual_review_flag": True,
                    "explanation": (
                        "Swollen battery presents a potential fire hazard. "
                        "Withheld from the public marketplace pending "
                        "specialist e-waste handling."
                    ),
                },
            ]

            for item_data in items:
                listing = Listing(
                    seller_id=seller.id,
                    title=item_data["title"],
                    category_confirmed=item_data["category_confirmed"],
                    category_source="user",
                    brand_model=item_data["brand_model"],
                    age_years=item_data["age_years"],
                    working_status=item_data["working_status"],
                    physical_condition=item_data["physical_condition"],
                    defects=item_data.get("defects"),
                    repair_history=item_data.get("repair_history"),
                    estimated_repair_cost=item_data.get(
                        "estimated_repair_cost"
                    ),
                    estimated_resale_value=item_data.get(
                        "estimated_resale_value"
                    ),
                    asking_price=item_data.get("asking_price"),
                    additional_notes=item_data.get("additional_notes"),
                    status=item_data["status"],
                )

                db.session.add(listing)
                db.session.flush()

                # Image assessment
                assessment = ImageAssessment(
                    listing_id=listing.id,
                    predicted_category=item_data["pred_cat"],
                    confidence=item_data["confidence"],
                    model_version="1.0.0",
                    inference_status="success",
                )
                db.session.add(assessment)

                # Recovery recommendation
                recommendation = Recommendation(
                    listing_id=listing.id,
                    route=item_data["route"],
                    suitability_score=item_data.get(
                        "suitability_score", 90
                    ),
                    reason_codes=json.dumps(
                        item_data.get("reason_codes", [])
                    ),
                    explanation=item_data["explanation"],
                    safety_flag=item_data.get("safety_flag", False),
                    manual_review_flag=item_data.get(
                        "manual_review_flag", False
                    ),
                    missing_info=json.dumps([]),
                )
                db.session.add(recommendation)

                # Initial status history
                history = ListingStatusHistory(
                    listing_id=listing.id,
                    changed_by=seller.id,
                    old_status=None,
                    new_status=listing.status,
                    note="Initial seed listing submission",
                )
                db.session.add(history)

            db.session.commit()
            print(f"Seeded {len(items)} sample listings.")

        else:
            print(
                f"Listings already exist ({Listing.query.count()} listings "
                "in DB). Skipping listing creation."
            )

        # ============================================================
        # 4. COMPLETION MESSAGE
        # ============================================================

        print("\nDatabase seeding completed successfully!")
        print("-" * 65)
        print(f"Admin Account:            {admin_email} / {admin_pass}")
        print("Seller Account:           seller@ecoloop.local / SellerPass123!")
        print(
            "Repairer Partner Account: "
            "repairer@ecoloop.local / RepairerPass123!"
        )
        print(
            "Recycler Partner Account: "
            "recycler@ecoloop.local / RecyclerPass123!"
        )
        print("-" * 65)


if __name__ == "__main__":
    seed_database()
