"""
EcoLoop Presentation Generator (PPTX & PDF)
Replicates the exact visual design, typography, layout, and colors of
EcoCycle-Waste-to-Recycling-Marketplace-no-watermark.pptx / .pdf
customized specifically for the EcoLoop E-Waste Management & Recovery Platform.
Preserves OpenXML run properties (solidFill srgbClr, typeface, size, kerning).
"""

import os
import sys
import subprocess
import win32com.client
from pptx import Presentation
from PIL import Image

WORKSPACE_DIR = r"c:\Users\yaswa\OneDrive\Desktop\e waste management system\SWM_project"
WEB_DEV_DIR = r"C:\web development"
ORIGINAL_PPTX = os.path.join(WEB_DEV_DIR, "EcoCycle-Waste-to-Recycling-Marketplace-no-watermark.pptx")
OUTPUT_PPTX_NAME = "EcoLoop-AI-Assisted-E-Waste-Marketplace.pptx"
OUTPUT_PDF_NAME = "EcoLoop-AI-Assisted-E-Waste-Marketplace.pdf"

TEMP_ASSETS_DIR = os.path.join(WORKSPACE_DIR, "presentation_assets")
os.makedirs(TEMP_ASSETS_DIR, exist_ok=True)

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# High-fidelity HTML templates for the 8 screenshot slots
MOCKUP_TEMPLATES = {
    "slide3_img0_auth.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; display: flex; align-items: center; justify-content: center; height: 100vh; padding: 24px; }
  .login-card { background: #161e1a; border: 1.5px solid #28372f; border-radius: 18px; width: 680px; padding: 48px; box-shadow: 0 25px 50px rgba(0,0,0,0.6); }
  .brand { display: flex; align-items: center; gap: 14px; margin-bottom: 28px; }
  .logo-icon { width: 50px; height: 50px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; color: white; }
  .brand-text h2 { font-size: 28px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
  .brand-text p { font-size: 14px; color: #9ca3af; margin-top: 2px; }
  .role-tabs { display: flex; background: #0f1512; padding: 5px; border-radius: 12px; margin-bottom: 26px; border: 1px solid #233029; }
  .role-tab { flex: 1; text-align: center; padding: 12px 0; font-size: 14px; font-weight: 700; color: #9ca3af; border-radius: 8px; cursor: pointer; }
  .role-tab.active { background: #10b981; color: #ffffff; box-shadow: 0 4px 12px rgba(16,185,129,0.3); }
  .form-group { margin-bottom: 20px; }
  .form-group label { display: block; font-size: 14px; font-weight: 600; color: #e5e7eb; margin-bottom: 8px; }
  .form-input { width: 100%; padding: 14px 16px; background: #0f1512; border: 1.5px solid #2b3a32; border-radius: 10px; color: #fff; font-size: 15px; }
  .btn-submit { width: 100%; padding: 16px; background: #10b981; border: none; border-radius: 10px; font-size: 16px; font-weight: 700; color: #fff; cursor: pointer; margin-top: 10px; text-align: center; }
  .demo-pills { display: flex; gap: 12px; margin-top: 28px; padding-top: 24px; border-top: 1px solid #233029; }
  .demo-pill { flex: 1; background: #1f2a24; border: 1px solid #2f4036; padding: 10px; border-radius: 8px; font-size: 12px; color: #a7f3d0; text-align: center; }
</style>
</head>
<body>
<div class="login-card">
  <div class="brand">
    <div class="logo-icon">&#9851;</div>
    <div class="brand-text">
      <h2>EcoLoop Authentication</h2>
      <p>Intelligent E-Waste Diagnostics & Circular Recovery Portal</p>
    </div>
  </div>
  <div class="role-tabs">
    <div class="role-tab active">Resident / Seller</div>
    <div class="role-tab">Repairer</div>
    <div class="role-tab">Recycler</div>
    <div class="role-tab">Admin</div>
  </div>
  <div class="form-group">
    <label>Email Address</label>
    <div class="form-input">seller@ecoloop.local</div>
  </div>
  <div class="form-group">
    <label>Password</label>
    <div class="form-input">&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;</div>
  </div>
  <div class="btn-submit">Sign In to Dashboard &rarr;</div>
  <div class="demo-pills">
    <div class="demo-pill"><strong>Demo Seller:</strong> seller@ecoloop</div>
    <div class="demo-pill"><strong>Demo Repairer:</strong> repairer@ecoloop</div>
    <div class="demo-pill"><strong>Demo Recycler:</strong> recycler@ecoloop</div>
  </div>
</div>
</body>
</html>""",

    "slide3_img1_dashboard.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 30px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 18px; border-bottom: 1.5px solid #233029; }
  .welcome h2 { font-size: 26px; font-weight: 800; color: #fff; }
  .welcome p { font-size: 14px; color: #9ca3af; margin-top: 4px; }
  .btn-new { background: #10b981; color: white; padding: 12px 22px; border-radius: 10px; font-size: 14px; font-weight: 700; }
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 26px; }
  .kpi-card { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 18px; }
  .kpi-label { font-size: 13px; color: #9ca3af; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; }
  .kpi-value { font-size: 28px; font-weight: 800; color: #fff; }
  .kpi-sub { font-size: 12px; color: #10b981; margin-top: 6px; font-weight: 600; }
  .section-title { font-size: 17px; font-weight: 700; color: #e5e7eb; margin-bottom: 14px; }
  .table-card { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; overflow: hidden; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { background: #0f1512; text-align: left; padding: 14px 18px; color: #9ca3af; font-weight: 700; border-bottom: 1.5px solid #28372f; }
  td { padding: 14px 18px; border-bottom: 1px solid #202b25; color: #e5e7eb; }
  .badge { display: inline-block; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; }
  .badge-repair { background: #1e3a2f; color: #34d399; }
  .badge-parts { background: #3b2d18; color: #fbbf24; }
  .badge-recycle { background: #1e293b; color: #93c5fd; }
  .val-rupee { font-weight: 800; color: #34d399; font-size: 15px; }
</style>
</head>
<body>
<div class="header">
  <div class="welcome">
    <h2>Resident E-Waste Dashboard</h2>
    <p>Logged in as: V Sushan Reddy (Seller) &bull; Managing Active Diagnostics & Resale</p>
  </div>
  <div class="btn-new">+ Start AI Diagnostic</div>
</div>
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Active Listings</div>
    <div class="kpi-value">4 Items</div>
    <div class="kpi-sub">&uarr; 2 evaluated this week</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Est. Resale / Salvage</div>
    <div class="kpi-value val-rupee">&#8377;18,500</div>
    <div class="kpi-sub">Across verified partners</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">E-Waste Diverted</div>
    <div class="kpi-value">14.8 kg</div>
    <div class="kpi-sub">Diverted from landfill</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">CO&#8322;e Avoided</div>
    <div class="kpi-value">42.5 kg</div>
    <div class="kpi-sub">Circular recovery score</div>
  </div>
</div>
<div class="section-title">Recent Electronics in Recovery Pipeline</div>
<div class="table-card">
  <table>
    <thead>
      <tr>
        <th>Device & Model</th>
        <th>AI Classification</th>
        <th>Recommended Pathway</th>
        <th>Asking Price</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Dell XPS 13 9370</strong></td>
        <td>Laptop / Computer</td>
        <td><span class="badge badge-parts">Parts Recovery</span></td>
        <td class="val-rupee">&#8377;8,500</td>
        <td>Available in Market</td>
      </tr>
      <tr>
        <td><strong>Samsung Galaxy S21</strong></td>
        <td>Smartphone</td>
        <td><span class="badge badge-repair">Repair & Resale</span></td>
        <td class="val-rupee">&#8377;6,200</td>
        <td>2 Partner Offers</td>
      </tr>
      <tr>
        <td><strong>HP LaserJet MFP 135a</strong></td>
        <td>Printer / Scanner</td>
        <td><span class="badge badge-repair">Refurbishment</span></td>
        <td class="val-rupee">&#8377;2,800</td>
        <td>Under Diagnostic</td>
      </tr>
      <tr>
        <td><strong>Old CRT 17" Monitor</strong></td>
        <td>Display / Monitor</td>
        <td><span class="badge badge-recycle">Certified Recycling</span></td>
        <td class="val-rupee">&#8377;1,000</td>
        <td>Hazmat Intake Scheduled</td>
      </tr>
    </tbody>
  </table>
</div>
</body>
</html>""",

    "slide4_img0_ai_detection.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
  .title h2 { font-size: 24px; font-weight: 800; color: #fff; }
  .model-tag { background: #13271f; color: #34d399; border: 1.5px solid #1f4736; padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 700; }
  .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: calc(100vh - 110px); }
  .image-panel { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 18px; position: relative; display: flex; flex-direction: column; }
  .mock-photo { flex: 1; background: #090d0b url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23121915"/><rect x="40" y="40" width="320" height="220" rx="8" fill="%231b2620" stroke="%232d3d34" stroke-width="2"/><circle cx="200" cy="150" r="40" fill="%2310b981" opacity="0.2"/><path d="M160 120h80v60h-80z" fill="%2324332b"/><rect x="60" y="60" width="100" height="80" fill="%232b3d32" stroke="%2334d399" stroke-width="2" stroke-dasharray="4,2"/></svg>') center/cover no-repeat; border-radius: 10px; position: relative; border: 1.5px solid #2b3a32; }
  .bbox { position: absolute; border: 2.5px solid #10b981; background: rgba(16,185,129,0.18); border-radius: 6px; }
  .bbox-label { position: absolute; top: -22px; left: 0; background: #10b981; color: #000; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 4px; }
  .bbox1 { top: 40px; left: 40px; width: 170px; height: 120px; border-color: #34d399; }
  .bbox2 { bottom: 40px; right: 40px; width: 150px; height: 85px; border-color: #fbbf24; }
  .bbox2 .bbox-label { background: #fbbf24; }
  .bbox3 { top: 60px; right: 40px; width: 120px; height: 80px; border-color: #60a5fa; }
  .bbox3 .bbox-label { background: #60a5fa; color: #fff; }
  .qa-panel { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; }
  .qa-heading { font-size: 17px; font-weight: 800; color: #34d399; margin-bottom: 16px; }
  .qa-item { background: #0f1512; border: 1.5px solid #233029; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
  .qa-q { font-size: 13px; color: #d1d5db; font-weight: 700; margin-bottom: 6px; }
  .qa-a { font-size: 13px; color: #34d399; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .confidence-bar { background: #0f1512; padding: 14px; border-radius: 10px; border: 1.5px solid #233029; }
  .bar-bg { height: 10px; background: #28372f; border-radius: 5px; overflow: hidden; margin-top: 8px; }
  .bar-fill { height: 100%; width: 96.8%; background: linear-gradient(90deg, #10b981, #34d399); }
</style>
</head>
<body>
<div class="header">
  <div class="title">
    <h2>AI Vision Component Detection & Diagnostic Q&A</h2>
  </div>
  <div class="model-tag">MobileNetV2 Engine &bull; Inference: 64ms</div>
</div>
<div class="main-grid">
  <div class="image-panel">
    <div class="mock-photo">
      <div class="bbox bbox1"><div class="bbox-label">Motherboard: 98.4%</div></div>
      <div class="bbox bbox2"><div class="bbox-label">Li-ion Battery: 96.1%</div></div>
      <div class="bbox bbox3"><div class="bbox-label">16GB RAM: 94.7%</div></div>
    </div>
  </div>
  <div class="qa-panel">
    <div>
      <div class="qa-heading">Dynamic Diagnostic Questionnaire</div>
      <div class="qa-item">
        <div class="qa-q">1. Does the device power on when plugged into AC power?</div>
        <div class="qa-a">&#10004; Powers On / Fans spin, but no display output</div>
      </div>
      <div class="qa-item">
        <div class="qa-q">2. Is there any evidence of liquid ingress or internal corrosion?</div>
        <div class="qa-a">&#10004; No moisture indicators triggered; clean PCB contacts</div>
      </div>
      <div class="qa-item">
        <div class="qa-q">3. Is the internal battery pack visibly swollen, bulging or hot?</div>
        <div class="qa-a">&#10004; Normal flat condition (No thermal hazard detected)</div>
      </div>
    </div>
    <div class="confidence-bar">
      <div style="display:flex; justify-content:space-between; font-size:13px;">
        <span style="color:#9ca3af;">Overall Classification Confidence</span>
        <span style="color:#34d399; font-weight:800;">96.8% (High Certainty)</span>
      </div>
      <div class="bar-bg"><div class="bar-fill"></div></div>
    </div>
  </div>
</div>
</body>
</html>""",

    "slide4_img1_wizard.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .stepper { display: flex; justify-content: space-between; margin-bottom: 24px; background: #161e1a; padding: 14px 24px; border-radius: 14px; border: 1.5px solid #28372f; }
  .step { font-size: 13px; font-weight: 700; color: #9ca3af; display: flex; align-items: center; gap: 8px; }
  .step.done { color: #34d399; }
  .step.active { color: #fff; background: #233029; padding: 8px 14px; border-radius: 8px; }
  .form-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; }
  .form-col { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 24px; }
  .section-title { font-size: 17px; font-weight: 800; color: #fff; margin-bottom: 16px; border-bottom: 1.5px solid #28372f; padding-bottom: 10px; }
  .field { margin-bottom: 14px; }
  .label { font-size: 13px; color: #9ca3af; margin-bottom: 6px; font-weight: 600; }
  .input-box { background: #0f1512; border: 1.5px solid #2b3a32; border-radius: 8px; padding: 12px; font-size: 14px; color: #fff; }
  .part-item { display: flex; justify-content: space-between; align-items: center; background: #0f1512; border: 1.5px solid #28372f; padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; font-size: 13px; }
  .val-rupee { font-weight: 800; color: #34d399; font-size: 15px; }
  .econ-summary { background: #13271f; border: 1.5px solid #1f4736; border-radius: 10px; padding: 16px; margin-top: 16px; }
  .econ-row { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 8px; }
  .btn-publish { width: 100%; background: #10b981; color: #fff; border: none; padding: 16px; border-radius: 10px; font-weight: 800; font-size: 15px; margin-top: 16px; cursor: pointer; text-align: center; }
</style>
</head>
<body>
<div class="stepper">
  <div class="step done">&#10004; 1. Image Upload</div>
  <div class="step done">&#10004; 2. AI Diagnostics</div>
  <div class="step active">&#9679; 3. Economics & Parts Evaluation</div>
  <div class="step">4. Review & Publish</div>
</div>
<div class="form-grid">
  <div class="form-col">
    <div class="section-title">Device Specifications & Defects</div>
    <div class="field">
      <div class="label">Item Title</div>
      <div class="input-box">Dell XPS 13 9370 (Core i7 / 16GB RAM)</div>
    </div>
    <div class="field">
      <div class="label">Confirmed Category</div>
      <div class="input-box">Laptop / Computer (Confirmed by user)</div>
    </div>
    <div class="label" style="margin-top:14px;">Component Harvest Inventory</div>
    <div class="part-item">
      <span>&#9745; 13.3" 4K InfinityEdge Display</span>
      <span class="val-rupee">&#8377;3,200</span>
    </div>
    <div class="part-item">
      <span>&#9745; 16GB Integrated Logic Board</span>
      <span class="val-rupee">&#8377;4,500</span>
    </div>
    <div class="part-item">
      <span>&#9745; 52Wh Li-ion Battery (Healthy)</span>
      <span class="val-rupee">&#8377;1,100</span>
    </div>
  </div>
  <div class="form-col">
    <div class="section-title">Valuation & Economic Model</div>
    <div class="econ-summary">
      <div class="econ-row">
        <span style="color:#9ca3af;">Est. Resale (Working):</span>
        <span class="val-rupee">&#8377;14,000</span>
      </div>
      <div class="econ-row">
        <span style="color:#9ca3af;">Est. Repair Cost:</span>
        <span style="color:#fbbf24; font-weight:800;">&#8377;4,500</span>
      </div>
      <div class="econ-row" style="border-top:1.5px solid #1f4736; padding-top:8px; margin-top:8px;">
        <span style="color:#fff; font-weight:800;">Recommended Asking Price:</span>
        <span class="val-rupee" style="font-size:18px;">&#8377;8,500</span>
      </div>
    </div>
    <div class="btn-publish">Confirm Valuation & Proceed to Review &rarr;</div>
  </div>
</div>
</body>
</html>""",

    "slide5_img0_decision.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
  .header h2 { font-size: 24px; font-weight: 800; color: #fff; }
  .hero-recommendation { background: linear-gradient(135deg, #13271f, #161e1a); border: 2px solid #10b981; border-radius: 14px; padding: 26px; margin-bottom: 24px; }
  .route-badge { display: inline-block; background: #10b981; color: #000; font-size: 14px; font-weight: 800; padding: 7px 16px; border-radius: 20px; text-transform: uppercase; margin-bottom: 12px; }
  .hero-title { font-size: 28px; font-weight: 800; color: #fff; margin-bottom: 10px; }
  .hero-desc { font-size: 15px; color: #d1d5db; line-height: 1.5; }
  .grid-two { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; }
  .card-box { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 20px; }
  .box-title { font-size: 16px; font-weight: 800; color: #34d399; margin-bottom: 14px; }
  .rule-step { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; font-size: 13px; color: #e5e7eb; }
  .check-icon { color: #10b981; font-weight: bold; font-size: 15px; }
  .safety-box { background: #261f12; border: 1.5px solid #573e16; border-radius: 10px; padding: 14px; margin-top: 12px; }
  .safety-title { font-size: 13px; font-weight: 800; color: #fbbf24; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
  .safety-desc { font-size: 12px; color: #fef3c7; }
</style>
</head>
<body>
<div class="header">
  <h2>Deterministic Recovery Decision Engine</h2>
  <div style="font-size:13px; color:#9ca3af;">Rule Engine: DecisionTree_v2 &bull; Deterministic & Explainable</div>
</div>
<div class="hero-recommendation">
  <div class="route-badge">Recommended Route: Parts Recovery &amp; Refurbishment</div>
  <div class="hero-title">Route Recommended: High Value Parts Salvage</div>
  <div class="hero-desc">Device exhibits logic board power failure but contains a working 4K display panel and battery. Repair cost is 53% of residual value, making direct component harvesting the optimal economic &amp; ecological choice.</div>
</div>
<div class="grid-two">
  <div class="card-box">
    <div class="box-title">Rule-Based Evaluation Factors</div>
    <div class="rule-step">
      <span class="check-icon">&#10004;</span>
      <span><strong>Economic Feasibility:</strong> Estimated Repair (&#8377;4,500) vs Resale (&#8377;14,000) = 32% ratio &rarr; Feasible.</span>
    </div>
    <div class="rule-step">
      <span class="check-icon">&#10004;</span>
      <span><strong>Component Viability:</strong> Display assembly, keyboard, and battery validated for reuse.</span>
    </div>
    <div class="rule-step">
      <span class="check-icon">&#10004;</span>
      <span><strong>Suitability Score:</strong> 88 / 100 (Deterministic rule indicator).</span>
    </div>
  </div>
  <div class="card-box">
    <div class="box-title">Active Safety Interlock Status</div>
    <div class="safety-box">
      <div class="safety-title">&#9888; Safety Verification: CLEARED</div>
      <div class="safety-desc">No swollen battery or smoke reported. If battery swelling is flagged, the item is instantly locked from general marketplace resale and rerouted exclusively to licensed recyclers.</div>
    </div>
  </div>
</div>
</body>
</html>""",

    "slide5_img1_ecoimpact.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
  .header h2 { font-size: 24px; font-weight: 800; color: #fff; }
  .source-badges { display: flex; gap: 10px; }
  .source-badge { background: #13271f; border: 1.5px solid #1f4736; color: #34d399; font-size: 12px; font-weight: 800; padding: 6px 12px; border-radius: 8px; }
  .hazard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-bottom: 24px; }
  .hazard-card { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 20px; }
  .substance-name { font-size: 17px; font-weight: 800; color: #fff; margin-bottom: 6px; }
  .chemical-tag { font-size: 12px; color: #fbbf24; font-weight: 700; margin-bottom: 10px; }
  .hazard-body { font-size: 13px; color: #d1d5db; line-height: 1.45; margin-bottom: 14px; }
  .directive-box { background: #0f1512; border-left: 4px solid #10b981; padding: 10px 12px; font-size: 12px; color: #a7f3d0; border-radius: 0 8px 8px 0; }
  .citation-bar { background: #161e1a; border: 1.5px solid #28372f; border-radius: 10px; padding: 14px 18px; font-size: 12px; color: #9ca3af; display: flex; justify-content: space-between; align-items: center; }
</style>
</head>
<body>
<div class="header">
  <h2>EcoImpact — Verified Environmental Awareness</h2>
  <div class="source-badges">
    <div class="source-badge">EPA Guidelines</div>
    <div class="source-badge">UNEP Basel Convention</div>
  </div>
</div>
<div class="hazard-grid">
  <div class="hazard-card">
    <div class="substance-name">Lithium-Ion Batteries</div>
    <div class="chemical-tag">Hazard: Thermal Runaway &amp; Heavy Metals</div>
    <div class="hazard-body">Punctured or degraded cells can cause explosive fires in compactors and release toxic cobalt and nickel compounds into ground soil.</div>
    <div class="directive-box">Directive: Never discard in general waste. Store in insulated containers.</div>
  </div>
  <div class="hazard-card">
    <div class="substance-name">Lead &amp; Solder Flux</div>
    <div class="chemical-tag">Hazard: Severe Neurotoxic Bioaccumulation</div>
    <div class="hazard-body">Older circuit boards and CRTs contain bioaccumulative lead that leaches into aquifers when subjected to landfill acid rainwater.</div>
    <div class="directive-box">Directive: Must undergo closed-loop hydrometallurgical recovery.</div>
  </div>
  <div class="hazard-card">
    <div class="substance-name">Mercury Backlights</div>
    <div class="chemical-tag">Hazard: Vapor Inhalation &amp; Aquatic Toxicity</div>
    <div class="hazard-body">CCFL lamps in legacy monitors contain mercury vapor which causes neurotoxicity upon lamp fracture during crushing.</div>
    <div class="directive-box">Directive: Specialized vacuum-sealed recovery mandated.</div>
  </div>
</div>
<div class="citation-bar">
  <span><strong>Authoritative Knowledge Base:</strong> Citations referenced directly from EPA Title 40 CFR and UNEP Technical Guidelines.</span>
  <span style="color:#34d399; font-weight:700;">Reviewed by EcoLoop Environmental Safety Board</span>
</div>
</body>
</html>""",

    "slide6_img0_marketplace.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
  .header h2 { font-size: 24px; font-weight: 800; color: #fff; }
  .filter-bar { display: flex; gap: 12px; margin-bottom: 22px; background: #161e1a; padding: 12px 18px; border-radius: 12px; border: 1.5px solid #28372f; }
  .filter-pill { background: #0f1512; border: 1.5px solid #2b3a32; padding: 8px 16px; border-radius: 20px; font-size: 13px; color: #9ca3af; }
  .filter-pill.active { background: #10b981; color: #fff; border-color: #10b981; font-weight: 700; }
  .grid-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
  .item-card { background: #161e1a; border: 1.5px solid #28372f; border-radius: 14px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; }
  .card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
  .item-name { font-size: 17px; font-weight: 800; color: #fff; margin-bottom: 6px; }
  .item-route { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; }
  .badge-repair { background: #1e3a2f; color: #34d399; }
  .badge-parts { background: #3b2d18; color: #fbbf24; }
  .badge-recycle { background: #1e293b; color: #93c5fd; }
  .item-price { font-size: 22px; font-weight: 800; color: #34d399; margin: 12px 0; }
  .item-meta { font-size: 13px; color: #9ca3af; margin-bottom: 14px; }
  .btn-interest { background: #10b981; color: #000; border: none; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 800; text-align: center; cursor: pointer; }
</style>
</head>
<body>
<div class="header">
  <h2>EcoLoop Multi-Role Circular Marketplace</h2>
  <div style="font-size:13px; color:#34d399; font-weight:700;">Showing 3 Verified Listings Matching Partner Filters</div>
</div>
<div class="filter-bar">
  <div class="filter-pill active">All Verified Items</div>
  <div class="filter-pill">Repair Candidates</div>
  <div class="filter-pill">Parts Harvesting</div>
  <div class="filter-pill">Certified Recycling</div>
</div>
<div class="grid-cards">
  <div class="item-card">
    <div>
      <div class="card-top">
        <span class="item-route badge-parts">PARTS HARVESTING</span>
        <span style="font-size:12px; color:#9ca3af;">Hyderabad</span>
      </div>
      <div class="item-name">Dell XPS 13 9370</div>
      <div class="item-meta">Salvageable 4K Display, Keyboard &amp; Chassis</div>
      <div class="item-price">&#8377;8,500</div>
    </div>
    <div class="btn-interest">Express Partner Interest &rarr;</div>
  </div>
  <div class="item-card">
    <div>
      <div class="card-top">
        <span class="item-route badge-repair">REPAIR CANDIDATE</span>
        <span style="font-size:12px; color:#9ca3af;">Bangalore</span>
      </div>
      <div class="item-name">Samsung Galaxy S21</div>
      <div class="item-meta">Cracked outer glass; AMOLED &amp; camera intact</div>
      <div class="item-price">&#8377;6,200</div>
    </div>
    <div class="btn-interest">Express Partner Interest &rarr;</div>
  </div>
  <div class="item-card">
    <div>
      <div class="card-top">
        <span class="item-route badge-recycle">HAZMAT RECYCLING</span>
        <span style="font-size:12px; color:#9ca3af;">Secunderabad</span>
      </div>
      <div class="item-name">Lithium Battery Pack (x8)</div>
      <div class="item-meta">Certified E-Waste Recycler intake required</div>
      <div class="item-price">&#8377;1,200</div>
    </div>
    <div class="btn-interest">Request Recycler Intake &rarr;</div>
  </div>
</div>
</body>
</html>""",

    "slide6_img1_admin.html": """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0c100e; color: #f3f4f6; padding: 28px; height: 100vh; overflow: hidden; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
  .header h2 { font-size: 24px; font-weight: 800; color: #fff; }
  .alert-pill { background: #3b1d1d; border: 1.5px solid #7f1d1d; color: #f87171; font-size: 13px; font-weight: 800; padding: 6px 14px; border-radius: 20px; }
  .kpi-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 22px; }
  .stat-box { background: #161e1a; border: 1.5px solid #28372f; border-radius: 12px; padding: 16px; }
  .stat-title { font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: 700; }
  .stat-num { font-size: 26px; font-weight: 800; color: #fff; margin-top: 6px; }
  .table-box { background: #161e1a; border: 1.5px solid #28372f; border-radius: 12px; overflow: hidden; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #0f1512; text-align: left; padding: 12px 16px; color: #9ca3af; font-weight: 700; border-bottom: 1.5px solid #28372f; }
  td { padding: 12px 16px; border-bottom: 1px solid #202b25; color: #e5e7eb; }
  .btn-action { background: #10b981; color: #000; border: none; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: 800; cursor: pointer; }
  .btn-danger { background: #ef4444; color: #fff; }
</style>
</head>
<body>
<div class="header">
  <h2>Admin Moderation Queue &amp; Safety Audit Log</h2>
  <div class="alert-pill">&#9888; 2 Items Requiring Safety Review</div>
</div>
<div class="kpi-strip">
  <div class="stat-box">
    <div class="stat-title">Total Active Listings</div>
    <div class="stat-num">184</div>
  </div>
  <div class="stat-box">
    <div class="stat-title">Flagged Safety Risks</div>
    <div class="stat-num" style="color:#f87171;">2 Pending</div>
  </div>
  <div class="stat-box">
    <div class="stat-title">Verified Partners</div>
    <div class="stat-num" style="color:#34d399;">28 Active</div>
  </div>
</div>
<div class="table-box">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Listing Title</th>
        <th>Seller</th>
        <th>Flag Raised</th>
        <th>Moderation Action</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>#107</td>
        <td><strong>iPhone 11 (Swollen Battery)</strong></td>
        <td>R. Sharma</td>
        <td><span style="color:#f87171; font-weight:800;">SWOLLEN_BATTERY</span></td>
        <td><button class="btn-action btn-danger">Lock for Hazmat</button></td>
      </tr>
      <tr>
        <td>#109</td>
        <td><strong>Sony Trinitron CRT 21"</strong></td>
        <td>K. Reddy</td>
        <td><span style="color:#fbbf24; font-weight:800;">HEAVY_METAL_LEAD</span></td>
        <td><button class="btn-action">Route to Recycler</button></td>
      </tr>
      <tr>
        <td>#104</td>
        <td><strong>Dell XPS 13 9370</strong></td>
        <td>S. Reddy</td>
        <td><span style="color:#34d399; font-weight:800;">CLEARED</span></td>
        <td><button class="btn-action">Approved</button></td>
      </tr>
    </tbody>
  </table>
</div>
</body>
</html>"""
}

def update_para(p, new_text):
    """Updates paragraph text while preserving existing run formatting and solidFill color."""
    if not p.runs:
        p.text = new_text
        return
    p.runs[0].text = new_text
    for r in p.runs[1:]:
        r.text = ""

def render_html_to_jpg():
    print("[1/5] Rendering UI mockups using Edge headless...")
    rendered_images = {}
    for html_name, html_content in MOCKUP_TEMPLATES.items():
        html_path = os.path.join(TEMP_ASSETS_DIR, html_name)
        png_name = html_name.replace(".html", ".png")
        jpg_name = html_name.replace(".html", ".jpg")
        png_path = os.path.join(TEMP_ASSETS_DIR, png_name)
        jpg_path = os.path.join(TEMP_ASSETS_DIR, jpg_name)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        cmd = [
            EDGE_EXE,
            "--headless=new",
            "--disable-gpu",
            f"--screenshot={os.path.abspath(png_path)}",
            "--window-size=1584,1000",
            os.path.abspath(html_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Convert PNG to high-quality RGB JPEG
        with Image.open(png_path) as im:
            rgb_im = im.convert("RGB")
            rgb_im.save(jpg_path, "JPEG", quality=95)
            
        rendered_images[jpg_name] = jpg_path
        print(f"  Generated: {jpg_name} ({os.path.getsize(jpg_path)} bytes)")
    return rendered_images

def update_presentation(rendered_images):
    print("[2/5] Updating PowerPoint presentation slides preserving exact styles...")
    prs = Presentation(ORIGINAL_PPTX)

    # ------------------ SLIDE 1: Title Slide ------------------
    slide1 = prs.slides[0]
    for shape in slide1.shapes:
        if shape.name == "Text 0":
            update_para(shape.text_frame.paragraphs[0], "EcoLoop")
        elif shape.name == "Text 1":
            update_para(shape.text_frame.paragraphs[0], "AI-Assisted E-Waste Reuse & Recovery Marketplace")
        elif shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "AI-powered digital platform for sustainable electronics diagnostics, recovery, and circular recycling.")
        elif shape.name == "Text 6":
            update_para(shape.text_frame.paragraphs[0], "Repair")

    # ------------------ SLIDE 2: Platform Concept ------------------
    slide2 = prs.slides[1]
    for shape in slide2.shapes:
        if shape.name == "Text 1":
            update_para(shape.text_frame.paragraphs[0], "About EcoLoop")
        elif shape.name == "Text 4":
            update_para(shape.text_frame.paragraphs[0], "E-waste is hazardous, complex, and difficult to route responsibly.")
        elif shape.name == "Text 5":
            update_para(shape.text_frame.paragraphs[0], "Electronics contain valuable parts yet pose severe hazards (Lithium, Lead, Mercury). Users lack guidance on repairability, salvage, and safe recycling.")
        elif shape.name == "Text 8":
            update_para(shape.text_frame.paragraphs[0], "One intelligent marketplace coordinates circular recovery.")
        elif shape.name == "Text 9":
            update_para(shape.text_frame.paragraphs[0], "EcoLoop integrates MobileNetV2 vision for component detection, a deterministic decision engine, safety interlocks, and verified EcoImpact guidance.")
        elif shape.name == "Text 11":
            paras = shape.text_frame.paragraphs
            if len(paras) >= 5:
                update_para(paras[0], "User uploads device photo and specifies basic condition.")
                update_para(paras[1], "MobileNetV2 AI detects device category and key internal/external components.")
                update_para(paras[2], "Interactive diagnostic questions evaluate power, screen, and battery safety.")
                update_para(paras[3], "Deterministic engine recommends optimal recovery route (Reuse, Repair, Refurbish, Parts, or Recycle).")
                update_para(paras[4], "Listed on marketplace connecting residents with verified repairers and certified recyclers.")

    # ------------------ SLIDE 3: Module 1 Access & Overview ------------------
    slide3 = prs.slides[2]
    for shape in slide3.shapes:
        if shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "User Authentication / Role-Based Access")
        elif shape.name == "Text 3":
            update_para(shape.text_frame.paragraphs[0], "Secure registration, login, and dedicated role portals for Residents/Sellers, Repairers, Recyclers, and Admins.")
        elif shape.name == "Text 4":
            update_para(shape.text_frame.paragraphs[0], "Member Dashboard / Overview")
        elif shape.name == "Text 5":
            update_para(shape.text_frame.paragraphs[0], "Active listings, residual valuations in \u20b9, recovery status tracking, and positive environmental impact footprint.")
        elif shape.name == "Text 6":
            update_para(shape.text_frame.paragraphs[0], "Entry and overview screens for managing a member's circular e-waste recovery journey. EcoLoop \u2014 E-Waste Marketplace.")

    pic_shapes_s3 = [s for s in slide3.shapes if s.shape_type == 13]
    if len(pic_shapes_s3) >= 2:
        rId0 = pic_shapes_s3[0]._element.blipFill.blip.rEmbed
        slide3.part.related_part(rId0)._blob = open(rendered_images["slide3_img0_auth.jpg"], "rb").read()
        rId1 = pic_shapes_s3[1]._element.blipFill.blip.rEmbed
        slide3.part.related_part(rId1)._blob = open(rendered_images["slide3_img1_dashboard.jpg"], "rb").read()

    # ------------------ SLIDE 4: Module 2 AI Component Detection & Listing Wizard ------------------
    slide4 = prs.slides[3]
    for shape in slide4.shapes:
        if shape.name == "Text 0":
            update_para(shape.text_frame.paragraphs[0], "MODULE 2 \u00b7 AI COMPONENT DETECTION & LISTING WIZARD")
        elif shape.name == "Text 1":
            update_para(shape.text_frame.paragraphs[0], "AI Component Detection & Listing Wizard")
        elif shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "AI Vision & Component Diagnostics")
        elif shape.name == "Text 3":
            update_para(shape.text_frame.paragraphs[0], "MobileNetV2 deep learning classifier, automated component recognition, and interactive diagnostic Q&A.")
        elif shape.name == "Text 4":
            update_para(shape.text_frame.paragraphs[0], "Multi-Step Listing Creation Wizard")
        elif shape.name == "Text 5":
            update_para(shape.text_frame.paragraphs[0], "Physical defect evaluation, parts breakdown, asking price in \u20b9, economic repair estimation, and instant review.")
        elif shape.name == "Text 6":
            update_para(shape.text_frame.paragraphs[0], "Members evaluate electronics with AI and publish verified listings. EcoLoop \u2014 E-Waste Marketplace.")

    pic_shapes_s4 = [s for s in slide4.shapes if s.shape_type == 13]
    if len(pic_shapes_s4) >= 2:
        rId0 = pic_shapes_s4[0]._element.blipFill.blip.rEmbed
        slide4.part.related_part(rId0)._blob = open(rendered_images["slide4_img0_ai_detection.jpg"], "rb").read()
        rId1 = pic_shapes_s4[1]._element.blipFill.blip.rEmbed
        slide4.part.related_part(rId1)._blob = open(rendered_images["slide4_img1_wizard.jpg"], "rb").read()

    # ------------------ SLIDE 5: Module 3 Deterministic Recovery Engine & EcoImpact ------------------
    slide5 = prs.slides[4]
    for shape in slide5.shapes:
        if shape.name == "Text 0":
            update_para(shape.text_frame.paragraphs[0], "MODULE 3 \u00b7 DETERMINISTIC RECOVERY ENGINE & ECOIMPACT")
        elif shape.name == "Text 1":
            update_para(shape.text_frame.paragraphs[0], "Deterministic Recovery Engine & EcoImpact Hub")
        elif shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "Recovery Decision Engine & Safety Interlock")
        elif shape.name == "Text 3":
            update_para(shape.text_frame.paragraphs[0], "Multi-tier economic feasibility rules, residual value evaluation, and immediate lockdown for hazardous batteries.")
        elif shape.name == "Text 4":
            update_para(shape.text_frame.paragraphs[0], "EcoImpact Environmental Knowledge Hub")
        elif shape.name == "Text 5":
            update_para(shape.text_frame.paragraphs[0], "Verified toxic substance hazards (Lithium, Lead, Mercury, BFRs), EPA/UNEP citations, and safe handling directives.")
        elif shape.name == "Text 6":
            update_para(shape.text_frame.paragraphs[0], "Deterministic recovery routing paired with verified environmental awareness. EcoLoop \u2014 E-Waste Marketplace.")

    pic_shapes_s5 = [s for s in slide5.shapes if s.shape_type == 13]
    if len(pic_shapes_s5) >= 2:
        rId0 = pic_shapes_s5[0]._element.blipFill.blip.rEmbed
        slide5.part.related_part(rId0)._blob = open(rendered_images["slide5_img0_decision.jpg"], "rb").read()
        rId1 = pic_shapes_s5[1]._element.blipFill.blip.rEmbed
        slide5.part.related_part(rId1)._blob = open(rendered_images["slide5_img1_ecoimpact.jpg"], "rb").read()

    # ------------------ SLIDE 6: Module 4 Partner Operations & Administration ------------------
    slide6 = prs.slides[5]
    for shape in slide6.shapes:
        if shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "Repairer & Recycler Marketplace")
        elif shape.name == "Text 3":
            update_para(shape.text_frame.paragraphs[0], "Filter listings by route (Repair Candidates, Parts Harvesting, Certified Recycling), inspect component specs, and express partner interest.")
        elif shape.name == "Text 4":
            update_para(shape.text_frame.paragraphs[0], "Admin Dashboard & Moderation Queue")
        elif shape.name == "Text 5":
            update_para(shape.text_frame.paragraphs[0], "Moderation queue for flagged safety risks, status change audit trail, user governance, and visual analytics.")
        elif shape.name == "Text 6":
            update_para(shape.text_frame.paragraphs[0], "Partner workflows and administrator governance for circular operations. EcoLoop \u2014 E-Waste Marketplace.")

    pic_shapes_s6 = [s for s in slide6.shapes if s.shape_type == 13]
    if len(pic_shapes_s6) >= 2:
        rId0 = pic_shapes_s6[0]._element.blipFill.blip.rEmbed
        slide6.part.related_part(rId0)._blob = open(rendered_images["slide6_img0_marketplace.jpg"], "rb").read()
        rId1 = pic_shapes_s6[1]._element.blipFill.blip.rEmbed
        slide6.part.related_part(rId1)._blob = open(rendered_images["slide6_img1_admin.jpg"], "rb").read()

    # ------------------ SLIDE 7: Thank You ------------------
    slide7 = prs.slides[6]
    for shape in slide7.shapes:
        if shape.name == "Text 0":
            update_para(shape.text_frame.paragraphs[0], "ECOLOOP")
        elif shape.name == "Text 2":
            update_para(shape.text_frame.paragraphs[0], "Turning electronic waste into value, one recovery at a time.")

    # Save to both destinations
    out_pptx_webdev = os.path.join(WEB_DEV_DIR, OUTPUT_PPTX_NAME)
    out_pptx_workspace = os.path.join(WORKSPACE_DIR, OUTPUT_PPTX_NAME)
    
    prs.save(out_pptx_webdev)
    prs.save(out_pptx_workspace)
    print(f"[3/5] Saved PPTX to:\n  - {out_pptx_webdev}\n  - {out_pptx_workspace}")
    return out_pptx_webdev, out_pptx_workspace

def convert_pptx_to_pdf(pptx_path):
    print("[4/5] Converting PPTX to PDF using native PowerPoint COM...")
    out_pdf_webdev = os.path.join(WEB_DEV_DIR, OUTPUT_PDF_NAME)
    out_pdf_workspace = os.path.join(WORKSPACE_DIR, OUTPUT_PDF_NAME)

    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    try:
        deck = powerpoint.Presentations.Open(os.path.abspath(pptx_path), WithWindow=False)
        # 32 = ppSaveAsPDF
        deck.SaveAs(os.path.abspath(out_pdf_webdev), 32)
        deck.SaveAs(os.path.abspath(out_pdf_workspace), 32)
        deck.Close()
        print(f"[5/5] Exported PDF successfully to:\n  - {out_pdf_webdev}\n  - {out_pdf_workspace}")
    finally:
        powerpoint.Quit()

if __name__ == "__main__":
    print("=== EcoLoop Presentation Generation Starting ===")
    rendered_images = render_html_to_jpg()
    pptx_webdev, pptx_ws = update_presentation(rendered_images)
    convert_pptx_to_pdf(pptx_webdev)
    print("=== All generation completed successfully! ===")
