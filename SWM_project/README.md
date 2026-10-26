# EcoLoop — AI-Assisted E-Waste Reuse, Recovery & Environmental Awareness

EcoLoop is an end-to-end web platform engineered to combat electronic waste (e-waste). It guides users through evaluating unwanted electronics, predicting device categories via machine learning, determining responsible recovery pathways (Reuse, Repair, Refurbish, Parts Recovery, or Certified Recycling), and presenting verified environmental hazard information.

---

## 🌟 Key Capabilities

1. **AI-Assisted Category Prediction**:
   - Deep learning vision pipeline powered by **MobileNetV2** (ImageNet transfer learning) with category confidence scoring and fallback heuristics.
   - 10 distinct electronics categories supported (smartphones, laptops, monitors, desktops, tablets, printers, audio, gaming consoles, small appliances, battery chargers).

2. **Deterministic Recovery Decision Engine**:
   - Multi-tier rule-based engine evaluating:
     - Physical functionality & power state
     - Economic feasibility of repair vs. residual market value
     - Cosmetic condition & device age
   - Immediate **Safety Flag Interception**:
     - Automatically intercepts hazardous conditions (swollen batteries, liquid intrusion, smoke/sparking).
     - Locks items into administrative review and prevents general resale.

3. **EcoImpact Public Awareness Hub**:
   - Verified, educational repository detailing hazardous substances (Lithium, Lead, Mercury, BFRs), improper disposal pathways, and recommended handling actions with authoritative citations (EPA, UNEP, Basel Action Network).
   - Category-specific contextual advice on listing and detail pages.

4. **Multi-Role Marketplace & Workflow**:
   - **Residents / Sellers**: Multi-step wizard to upload photos, confirm categories, inspect AI recommendations, and publish listings.
   - **Repairers / Refurbishers & Recyclers**: Filter marketplace by recovery route (e.g., browse repair candidates or parts recovery units) and express partner interest.
   - **Administrators**: Comprehensive moderation queue, user management, status transition audit trail, and visual analytics via Chart.js.

---

## 🏗️ Architecture

```text
c:\SWM_project\
├── app\
│   ├── __init__.py               # Application factory & extension setup
│   ├── models\                   # SQLAlchemy relational data models
│   │   ├── user.py               # User authentication & role management
│   │   ├── listing.py            # Item listing records & lifecycle
│   │   ├── image_assessment.py   # AI vision predictions & confidence
│   │   ├── recommendation.py     # Deterministic recovery decisions & flags
│   │   ├── environmental_impact.py# Verified EcoImpact knowledge base
│   │   ├── listing_status_history.py# Status audit trail & notes
│   │   └── partner_interest.py   # Inquiries from repairers & recyclers
│   ├── routes\                   # Modular Flask Blueprints
│   │   ├── main.py               # Landing page & navigation
│   │   ├── auth.py               # Register, login, session management
│   │   ├── listings.py           # Multi-step creation wizard & item detail
│   │   ├── marketplace.py        # Browse, search, filter by route & price
│   │   ├── profile.py            # User profile & password management
│   │   ├── admin.py              # Moderation dashboard & knowledge CRUD
│   │   ├── ecoimpact.py          # Public environmental awareness hub
│   │   ├── api.py                # REST JSON API endpoints
│   │   └── errors.py             # Custom HTTP error handlers (404, 403, 500, 413)
│   ├── services\                 # Core Business Logic
│   │   ├── image_classifier.py   # MobileNetV2 image classifier & preprocessor
│   │   ├── recovery_engine.py    # Deterministic recovery decision engine
│   │   ├── ecoimpact_service.py  # Environmental knowledge retrieval
│   │   └── listing_service.py    # Status transitions & history recording
│   ├── static\                   # Assets (CSS, JS)
│   │   ├── css\main.css          # EcoLoop custom design system
│   │   └── js\main.js           # Client interactions & Chart.js integration
│   └── templates\                # Jinja2 HTML5 Templates
│       ├── base.html             # Base layout with navbar, alerts & footer
│       ├── main\                 # Landing page
│       ├── auth\                 # Login & Registration
│       ├── listings\             # Create wizard, detail, my listings, edit
│       ├── marketplace\          # Public marketplace grid & filters
│       ├── profile\              # Profile overview & password change
│       ├── admin\                # Dashboard, moderation queue, user & knowledge CRUD
│       ├── ecoimpact\            # Environmental knowledge catalog
│       └── errors\               # Error states (404, 403, 500, 413)
├── config.py                     # Environment & database configuration
├── requirements.txt              # Production and development dependencies
├── run.py                        # WSGI entry point
├── seed.py                       # Database table generator & demo seeder
└── .env.example                  # Environment template
```

---

## 🚀 Quickstart Guide

### 1. Requirements & Virtual Environment
- Python 3.10+ installed
- MySQL Server (e.g., via XAMPP) or SQLite

```bash
# Navigate to project folder
cd c:\SWM_project

# Create and activate a Python virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy the environment template:
```bash
copy .env.example .env
```
- If using **XAMPP / MySQL**, ensure MySQL is running on port 3306 and create database `ecoloop`.
- If using **SQLite** (quickest setup without MySQL), simply set in your `.env`:
  ```ini
  DATABASE_URL=sqlite:///ecoloop.db
  ```

### 3. Initialize & Seed Database
Run the seed script to create all database tables and populate demo accounts, sample listings, and environmental knowledge:
```bash
python seed.py
```

### 4. Run the Application
Launch the Flask development server:
```bash
python run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 👥 Default Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@ecoloop.local` | `AdminPass123!` |
| **Seller / Resident** | `seller@ecoloop.local` | `SellerPass123!` |
| **Repairer / Refurbisher** | `repairer@ecoloop.local` | `RepairerPass123!` |
| **Certified Recycler** | `recycler@ecoloop.local` | `RecyclerPass123!` |

---

## 🔒 Safety & Environmental Compliance
- **Safety Interlock**: Items with swollen batteries or smoke/sparking are automatically assigned to `manual_review` with safety flags raised. The admin moderation queue forbids setting these items to `available` without specialized clearance.
- **EcoImpact Guidance**: Direct environmental impact statements cite established authorities and provide actionable disposal instructions.
