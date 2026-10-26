/**
 * EcoLoop — Multi-Step Listing Creation Wizard
 */

let currentStep = 1;
let selectedFile = null;
let classifiedImageFile = null;
let currentRoute = "manual_review";
let currentSafetyFlag = false;
let detectedComponents = [];
let diagnosticQuestions = [];
let diagnosticAnswers = {};
let detectedAnomalies = [];

document.addEventListener("DOMContentLoaded", function () {
  initStep1Upload();
  initStep2Category();
  initStep3Details();
  initStep4Recovery();
});

// ── Step Navigation ──────────────────────────────────────────────────────────
function goToStep(step) {
  if (step < 1 || step > 6) return;
  currentStep = step;

  // Update progress bar
  const progressBar = document.getElementById("progressBar");
  if (progressBar) {
    progressBar.style.width = (step / 6) * 100 + "%";
  }

  // Update labels
  for (let i = 1; i <= 6; i++) {
    const lbl = document.getElementById("stepLabel" + i);
    if (!lbl) continue;
    lbl.classList.remove("active", "completed");
    if (i === step) {
      lbl.classList.add("active");
    } else if (i < step) {
      lbl.classList.add("completed");
    }
  }

  // Toggle step sections
  document.querySelectorAll(".eco-form-step").forEach((el) => {
    el.classList.add("d-none");
  });
  const currentStepEl = document.getElementById("step" + step);
  if (currentStepEl) {
    currentStepEl.classList.remove("d-none");
  }

  window.scrollTo({ top: 0, behavior: "smooth" });

  // Hook step triggers
  if (step === 4) {
    runRecoveryAssessment();
  } else if (step === 5) {
    loadEcoImpact();
  } else if (step === 6) {
    populateReview();
  }
}

// ── Step 1: Upload Image ─────────────────────────────────────────────────────
function initStep1Upload() {
  const fileInput = document.getElementById("imageFileInput");
  const uploadZone = document.getElementById("uploadZone");
  const uploadPrompt = document.getElementById("uploadPrompt");
  const uploadPreview = document.getElementById("uploadPreview");
  const previewImg = document.getElementById("previewImg");
  const previewName = document.getElementById("previewName");
  const previewSize = document.getElementById("previewSize");
  const removeBtn = document.getElementById("removeImageBtn");
  const step1Next = document.getElementById("step1Next");
  const uploadError = document.getElementById("uploadError");

  if (!fileInput || !uploadZone) return;

  function handleFile(file) {
    uploadError.classList.add("d-none");
    if (!file) return;

    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type) && !/\.(jpe?g|png|webp|gif)$/i.test(file.name)) {
      uploadError.textContent = "Please upload a valid image file (JPG, PNG, WEBP, GIF).";
      uploadError.classList.remove("d-none");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      uploadError.textContent = "Image file must be under 10 MB.";
      uploadError.classList.remove("d-none");
      return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = function (e) {
      previewImg.src = e.target.result;
      previewName.textContent = file.name;
      previewSize.textContent = "(" + (file.size / 1024).toFixed(1) + " KB)";
      uploadPrompt.classList.add("d-none");
      uploadPreview.classList.remove("d-none");
      step1Next.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  fileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
      handleFile(this.files[0]);
    }
  });

  // Drag and drop
  ["dragenter", "dragover"].forEach((eventName) => {
    uploadZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    uploadZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadZone.classList.remove("dragover");
    });
  });

  uploadZone.addEventListener("drop", (e) => {
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      fileInput.files = e.dataTransfer.files;
      handleFile(e.dataTransfer.files[0]);
    }
  });

  if (removeBtn) {
    removeBtn.addEventListener("click", function () {
      selectedFile = null;
      classifiedImageFile = null;
      detectedComponents = [];
      diagnosticQuestions = [];
      diagnosticAnswers = {};
      detectedAnomalies = [];
      fileInput.value = "";
      previewImg.src = "";
      uploadPreview.classList.add("d-none");
      uploadPrompt.classList.remove("d-none");
      step1Next.disabled = true;
      document.getElementById("hidImagePath").value = "";
      const hidDetected = document.getElementById("hidDetectedComponents");
      if (hidDetected) hidDetected.value = "[]";
      const hidAnswers = document.getElementById("hidDiagnosticAnswers");
      if (hidAnswers) hidAnswers.value = "{}";
      renderDetectedComponents([], []);
      renderDiagnosticQuestions([]);
    });
  }

  if (step1Next) {
    step1Next.addEventListener("click", function () {
      if (!selectedFile) return;

      // If classifier is enabled and we haven't classified this file yet, run it
      if (typeof CLASSIFIER_AVAILABLE !== "undefined" && CLASSIFIER_AVAILABLE && classifiedImageFile !== selectedFile) {
        runImageClassification(selectedFile);
      }
      goToStep(2);
    });
  }
}

// ── Run AI Classification ────────────────────────────────────────────────────
function runImageClassification(file) {
  const loading = document.getElementById("classifierLoading");
  const resultBox = document.getElementById("classifierResult");
  const categorySelect = document.getElementById("categorySelect");

  if (loading) loading.classList.remove("d-none");
  if (resultBox) resultBox.classList.add("d-none");

  const formData = new FormData();
  formData.append("image", file);

  fetch(CLASSIFY_URL, {
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (loading) loading.classList.add("d-none");
      classifiedImageFile = file;

      if (data.temp_path) {
        document.getElementById("hidImagePath").value = data.temp_path;
      }
      document.getElementById("hidInferenceStatus").value = data.inference_status || "fallback";

      // Store detected components & anomalies
      detectedComponents = data.detected_components || [];
      diagnosticQuestions = data.diagnostic_questions || [];
      detectedAnomalies = data.visual_anomalies || [];
      diagnosticAnswers = {};

      const hidDetected = document.getElementById("hidDetectedComponents");
      if (hidDetected) hidDetected.value = JSON.stringify(detectedComponents);
      const hidAnswers = document.getElementById("hidDiagnosticAnswers");
      if (hidAnswers) hidAnswers.value = JSON.stringify(diagnosticAnswers);

      renderDetectedComponents(detectedComponents, detectedAnomalies);
      renderDiagnosticQuestions(diagnosticQuestions);

      if (data.inference_status === "success" && data.predicted_category) {
        document.getElementById("hidPredictedCategory").value = data.predicted_category;
        document.getElementById("hidPredictedConfidence").value = data.confidence || "";
        document.getElementById("hidModelVersion").value = data.model_version || "";

        document.getElementById("resultCategory").textContent = data.predicted_category;
        document.getElementById("resultConfidence").textContent =
          Math.round((data.confidence || 0) * 100) + "%";
        document.getElementById("resultModel").textContent = data.model_version || "1.0.0";
        document.getElementById("resultMessage").textContent = data.message || "";

        if (resultBox) resultBox.classList.remove("d-none");

        // Automatically select the category in the dropdown if available
        if (categorySelect && data.predicted_category) {
          for (let opt of categorySelect.options) {
            if (opt.value === data.predicted_category) {
              categorySelect.value = data.predicted_category;
              document.getElementById("hidCategoryConfirmed").value = data.predicted_category;
              document.getElementById("hidCategorySource").value = "model";
              checkSafetyCategory(data.predicted_category);
              break;
            }
          }
        }

        if (data.safety_sensitive) {
          const safetyAlert = document.getElementById("safetyAlert");
          if (safetyAlert) safetyAlert.classList.remove("d-none");
        }
      } else {
        // Fallback message
        const resultMsg = document.getElementById("resultMessage");
        if (resultMsg) {
          resultMsg.textContent = data.message || "Please select the category manually.";
        }
        if (resultBox) resultBox.classList.remove("d-none");
      }
    })
    .catch((err) => {
      console.warn("Classification request error:", err);
      if (loading) loading.classList.add("d-none");
    });
}

// ── Render Detected Components & Visual Anomalies ───────────────────────────
function renderDetectedComponents(components, anomalies) {
  const panel = document.getElementById("detectedComponentsPanel");
  const list = document.getElementById("detectedComponentsList");
  const badge = document.getElementById("componentCountBadge");
  const anomaliesWrap = document.getElementById("visualAnomaliesWrap");
  const anomaliesText = document.getElementById("visualAnomaliesText");

  if (!panel || !list) return;

  if (components && components.length > 0) {
    list.innerHTML = "";
    if (badge) badge.textContent = components.length + " detected";

    components.forEach((c) => {
      const chip = document.createElement("div");
      chip.className = "d-inline-flex align-items-center gap-2 px-3 py-2 bg-white rounded-3 border shadow-sm me-2 mb-2";
      const iconClass = c.icon ? "bi-" + c.icon : "bi-cpu";
      const confPct = Math.round((c.confidence || 0.85) * 100);
      chip.innerHTML = `
        <div class="rounded-circle bg-light p-2 text-primary d-flex align-items-center justify-content-center" style="width:36px;height:36px;">
          <i class="bi ${iconClass} fs-5"></i>
        </div>
        <div>
          <div class="fw-600 small text-dark">${c.name}</div>
          <div class="x-small text-muted"><span class="badge bg-success-subtle text-success border-0 px-1">Detected</span> • ${confPct}% conf</div>
        </div>
      `;
      list.appendChild(chip);
    });

    if (anomalies && anomalies.length > 0) {
      if (anomaliesText) anomaliesText.textContent = anomalies.join(" | ");
      if (anomaliesWrap) anomaliesWrap.classList.remove("d-none");
    } else {
      if (anomaliesWrap) anomaliesWrap.classList.add("d-none");
    }

    panel.classList.remove("d-none");
  } else {
    panel.classList.add("d-none");
    if (anomaliesWrap) anomaliesWrap.classList.add("d-none");
  }
}

// ── Render Interactive Component Diagnostic Questions ───────────────────────
function renderDiagnosticQuestions(questions) {
  const panel = document.getElementById("diagnosticQuestionsPanel");
  const list = document.getElementById("diagnosticQuestionsList");
  const progressBadge = document.getElementById("questionsProgressBadge");

  if (!panel || !list) return;

  if (questions && questions.length > 0) {
    list.innerHTML = "";
    if (progressBadge) {
      progressBadge.textContent = "0 of " + questions.length + " answered";
    }

    questions.forEach((q, idx) => {
      const card = document.createElement("div");
      card.className = "card border shadow-none p-3";
      card.id = "qCard_" + q.component_id;

      let optionsHtml = "";
      q.options.forEach((opt) => {
        const isHazard = !!opt.hazard;
        const hazardBadge = isHazard
          ? '<span class="badge bg-danger text-white ms-2 x-small"><i class="bi bi-shield-exclamation me-1"></i>Hazard</span>'
          : "";
        optionsHtml += `
          <button type="button" class="btn btn-outline-secondary text-start option-btn mb-2 d-flex align-items-center justify-content-between py-2 px-3"
                  data-comp="${q.component_id}" data-val="${opt.value}"
                  data-working="${opt.working_status || ''}" data-hazard="${isHazard ? 'true' : 'false'}"
                  data-label="${opt.label.replace(/"/g, '&quot;')}">
            <span class="small">${opt.label}</span>
            ${hazardBadge}
          </button>
        `;
      });

      card.innerHTML = `
        <div class="d-flex align-items-center justify-content-between mb-2">
          <div class="d-flex align-items-center gap-2">
            <span class="badge bg-secondary-subtle text-dark fw-bold">${idx + 1}</span>
            <strong class="text-dark small">${q.question}</strong>
          </div>
          <span class="badge bg-light text-muted border answer-status-badge" id="qBadge_${q.component_id}">Pending</span>
        </div>
        <div class="d-flex flex-column gap-1 mt-1 options-container">
          ${optionsHtml}
        </div>
      `;

      list.appendChild(card);
    });

    // Add click listeners to option buttons
    list.querySelectorAll(".option-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const compId = this.getAttribute("data-comp");
        const val = this.getAttribute("data-val");
        const isHazard = this.getAttribute("data-hazard") === "true";
        const workingStatus = this.getAttribute("data-working");
        const optLabel = this.getAttribute("data-label");

        // Record answer
        diagnosticAnswers[compId] = val;
        const hidAnswers = document.getElementById("hidDiagnosticAnswers");
        if (hidAnswers) hidAnswers.value = JSON.stringify(diagnosticAnswers);

        // Update UI state for this question card
        const card = document.getElementById("qCard_" + compId);
        if (card) {
          card.querySelectorAll(".option-btn").forEach((b) => {
            b.classList.remove("btn-primary", "btn-danger", "text-white", "active");
            b.classList.add("btn-outline-secondary");
          });
          this.classList.remove("btn-outline-secondary");
          if (isHazard) {
            this.classList.add("btn-danger", "text-white", "active");
            card.classList.add("border-danger");
          } else {
            this.classList.add("btn-primary", "text-white", "active");
            card.classList.remove("border-danger");
          }
        }

        // Update badge
        const badge = document.getElementById("qBadge_" + compId);
        if (badge) {
          badge.className = isHazard
            ? "badge bg-danger text-white border-0"
            : "badge bg-success text-white border-0";
          badge.textContent = isHazard ? "Hazard Flagged" : "Verified";
        }

        // Update progress badge
        const answeredCount = Object.keys(diagnosticAnswers).length;
        if (progressBadge) {
          progressBadge.textContent = answeredCount + " of " + questions.length + " answered";
        }

        // Auto-handle hazards
        if (isHazard) {
          if (val === "swollen" || val === "leaking") {
            const chk = document.getElementById("sf_" + val + "_battery");
            if (chk && !chk.checked) {
              chk.checked = true;
              chk.dispatchEvent(new Event("change"));
            }
          }
          if (val === "burnt_pcb" || val === "sparking") {
            const chk = document.getElementById("sf_smoke") || document.getElementById("sf_burning_smell");
            if (chk && !chk.checked) {
              chk.checked = true;
              chk.dispatchEvent(new Event("change"));
            }
          }
          const safetyAlert = document.getElementById("safetyAlert");
          if (safetyAlert) safetyAlert.classList.remove("d-none");
        }

        // Auto-sync working_status in Step 3
        const workingSelect = document.getElementById("working_status");
        if (workingSelect) {
          if (workingStatus === "not_working") {
            workingSelect.value = "not_working";
            workingSelect.dispatchEvent(new Event("change"));
          } else if (workingStatus === "partially_working" && workingSelect.value !== "not_working") {
            workingSelect.value = "partially_working";
            workingSelect.dispatchEvent(new Event("change"));
          }
        }

        // Auto-sync defects in Step 3 if defect option selected
        const defectsField = document.getElementById("defects");
        if (defectsField && (workingStatus === "partially_working" || workingStatus === "not_working" || isHazard)) {
          if (!defectsField.value.includes(optLabel)) {
            defectsField.value = defectsField.value ? defectsField.value + "; " + optLabel : optLabel;
          }
        }
      });
    });

    panel.classList.remove("d-none");
  } else {
    panel.classList.add("d-none");
  }
}

// ── Step 2: Category Selection ───────────────────────────────────────────────
const SAFETY_CATEGORIES = [
  "Battery & Power Equipment",
  "Circuit Board / Components",
  "Medical & Measurement Electronics",
];

function checkSafetyCategory(cat) {
  const panel = document.getElementById("safetyFlagsPanel");
  if (!panel) return;
  if (SAFETY_CATEGORIES.includes(cat)) {
    panel.classList.remove("d-none");
  } else {
    // Only hide if no checkboxes are checked
    const checked = document.querySelectorAll(".safety-flag-input:checked");
    if (checked.length === 0) {
      panel.classList.add("d-none");
    }
  }
}

function initStep2Category() {
  const categorySelect = document.getElementById("categorySelect");
  const step2Next = document.getElementById("step2Next");

  if (categorySelect) {
    categorySelect.addEventListener("change", function () {
      const val = this.value;
      document.getElementById("hidCategoryConfirmed").value = val;
      document.getElementById("hidCategorySource").value = "user";
      checkSafetyCategory(val);
    });
  }

  // Safety checkboxes
  document.querySelectorAll(".safety-flag-input").forEach((chk) => {
    chk.addEventListener("change", function () {
      const checkedVals = Array.from(document.querySelectorAll(".safety-flag-input:checked")).map(
        (c) => c.value
      );
      document.getElementById("hidSafetyFlags").value = JSON.stringify(checkedVals);
      currentSafetyFlag = checkedVals.length > 0;
    });
  });

  if (step2Next) {
    step2Next.addEventListener("click", function () {
      const cat = categorySelect ? categorySelect.value : "";
      if (!cat) {
        alert("Please confirm or select an item category.");
        if (categorySelect) categorySelect.focus();
        return;
      }
      document.getElementById("hidCategoryConfirmed").value = cat;
      goToStep(3);
    });
  }
}

// ── Step 3: Item Details ─────────────────────────────────────────────────────
function initStep3Details() {
  const workingSelect = document.getElementById("working_status");
  const repairFields = document.getElementById("repairFields");
  const step3Next = document.getElementById("step3Next");

  if (workingSelect && repairFields) {
    workingSelect.addEventListener("change", function () {
      if (this.value === "working" || !this.value) {
        repairFields.style.display = "none";
      } else {
        repairFields.style.display = "block";
      }
    });
  }

  if (step3Next) {
    step3Next.addEventListener("click", function () {
      const title = document.getElementById("title");
      const working = document.getElementById("working_status");

      if (!title || !title.value.trim()) {
        alert("Please enter a title for your item.");
        if (title) title.focus();
        return;
      }
      if (!working || !working.value) {
        alert("Please select the item working status.");
        if (working) working.focus();
        return;
      }

      goToStep(4);
    });
  }
}

// ── Step 4: Recovery Assessment ──────────────────────────────────────────────
function initStep4Recovery() {
  const step4Next = document.getElementById("step4Next");
  if (step4Next) {
    step4Next.addEventListener("click", function () {
      goToStep(5);
    });
  }
}

function runRecoveryAssessment() {
  const loading = document.getElementById("recoveryLoading");
  const resultBox = document.getElementById("recoveryResult");
  const errorBox = document.getElementById("recoveryError");

  if (loading) loading.classList.remove("d-none");
  if (resultBox) resultBox.classList.add("d-none");
  if (errorBox) errorBox.classList.add("d-none");

  const formEl = document.getElementById("listingForm");
  const formData = new FormData(formEl);

  fetch("/listings/evaluate", {
    method: "POST",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    body: formData,
  })
    .then((r) => {
      if (!r.ok) throw new Error("Evaluation error: " + r.status);
      return r.json();
    })
    .then((data) => {
      if (loading) loading.classList.add("d-none");
      if (resultBox) resultBox.classList.remove("d-none");

      currentRoute = data.route || "manual_review";
      currentSafetyFlag = data.safety_flag || false;

      // Title & Icon
      const routeTitle = document.getElementById("routeTitle");
      if (routeTitle) routeTitle.textContent = data.route_title || currentRoute.replace("_", " ");

      const routeIcon = document.getElementById("routeIcon");
      if (routeIcon) {
        routeIcon.innerHTML = `<i class="bi ${data.route_icon || 'bi-arrow-repeat'} fs-2 text-success"></i>`;
      }

      // Score
      const scoreDisplay = document.getElementById("scoreDisplay");
      if (scoreDisplay) {
        scoreDisplay.textContent = data.suitability_score !== null ? data.suitability_score : "—";
      }

      // Safety Banner
      const safetyBanner = document.getElementById("safetyBanner");
      const safetyText = document.getElementById("safetyBannerText");
      if (safetyBanner) {
        if (data.safety_flag) {
          safetyBanner.classList.remove("d-none");
          if (safetyText) {
            safetyText.textContent = "A physical hazard was detected. This item will be flagged for safety review.";
          }
        } else if (data.manual_review_flag) {
          safetyBanner.classList.remove("d-none");
          if (safetyText) {
            safetyText.textContent = "Additional review is recommended to confirm the best recovery route.";
          }
        } else {
          safetyBanner.classList.add("d-none");
        }
      }

      // Explanation
      const explanation = document.getElementById("routeExplanation");
      if (explanation) explanation.textContent = data.explanation || "";

      // Component-Driven Diagnostic Decision Card
      const compDecisionCard = document.getElementById("componentDecisionCard");
      const compDiagSummary = document.getElementById("componentDiagnosticSummary");
      const repairTargetsWrap = document.getElementById("repairTargetsWrap");
      const repairTargetsList = document.getElementById("repairTargetsList");
      const salvageableWrap = document.getElementById("salvageablePartsWrap");
      const salvageableList = document.getElementById("salvageablePartsList");

      if (compDecisionCard) {
        const hasDiag = !!(data.diagnostic_summary || 
          (data.repair_target_components && data.repair_target_components.length > 0) ||
          (data.salvageable_components && data.salvageable_components.length > 0));

        if (hasDiag) {
          compDecisionCard.classList.remove("d-none");
          if (compDiagSummary) {
            compDiagSummary.textContent = data.diagnostic_summary || "Hardware diagnostic complete.";
          }
          if (data.repair_target_components && data.repair_target_components.length > 0) {
            if (repairTargetsList) {
              repairTargetsList.innerHTML = data.repair_target_components
                .map((c) => `<span class="badge bg-warning text-dark me-1">${c}</span>`)
                .join("");
            }
            if (repairTargetsWrap) repairTargetsWrap.classList.remove("d-none");
          } else {
            if (repairTargetsWrap) repairTargetsWrap.classList.add("d-none");
          }

          if (data.salvageable_components && data.salvageable_components.length > 0) {
            if (salvageableList) {
              salvageableList.innerHTML = data.salvageable_components
                .map((c) => `<span class="badge bg-success-subtle text-success border border-success me-1">${c}</span>`)
                .join("");
            }
            if (salvageableWrap) salvageableWrap.classList.remove("d-none");
          } else {
            if (salvageableWrap) salvageableWrap.classList.add("d-none");
          }
        } else {
          compDecisionCard.classList.add("d-none");
        }
      }

      // Reason codes
      const reasonWrap = document.getElementById("reasonCodesWrap");
      const reasonList = document.getElementById("reasonCodesList");
      if (reasonWrap && reasonList) {
        reasonList.innerHTML = "";
        if (data.reason_codes && data.reason_codes.length > 0) {
          data.reason_codes.forEach((rc) => {
            const span = document.createElement("span");
            span.className = "eco-pill eco-pill--muted small";
            span.textContent = rc.replace(/_/g, " ").toLowerCase();
            reasonList.appendChild(span);
          });
          reasonWrap.classList.remove("d-none");
        } else {
          reasonWrap.classList.add("d-none");
        }
      }

      // Missing info
      const missingWrap = document.getElementById("missingInfoWrap");
      const missingList = document.getElementById("missingInfoList");
      if (missingWrap && missingList) {
        if (data.missing_info && data.missing_info.length > 0) {
          missingList.textContent = data.missing_info.join(", ");
          missingWrap.classList.remove("d-none");
        } else {
          missingWrap.classList.add("d-none");
        }
      }
    })
    .catch((err) => {
      console.warn("Recovery evaluation error:", err);
      if (loading) loading.classList.add("d-none");
      if (errorBox) errorBox.classList.remove("d-none");
    });
}

// ── Step 5: EcoImpact ────────────────────────────────────────────────────────
function loadEcoImpact() {
  const loading = document.getElementById("ecoLoading");
  const content = document.getElementById("ecoContent");
  const unavailable = document.getElementById("ecoUnavailable");
  const adviceText = document.getElementById("ecoRouteAdviceText");
  const impactsWrap = document.getElementById("ecoImpactsWrap");

  if (loading) loading.classList.remove("d-none");
  if (content) content.classList.add("d-none");
  if (unavailable) unavailable.classList.add("d-none");

  const cat = document.getElementById("hidCategoryConfirmed").value || "";
  const url =
    "/listings/ecoimpact-preview?category=" +
    encodeURIComponent(cat) +
    "&route=" +
    encodeURIComponent(currentRoute) +
    "&safety_flag=" +
    (currentSafetyFlag ? "true" : "false");

  fetch(url)
    .then((r) => r.json())
    .then((data) => {
      if (loading) loading.classList.add("d-none");

      if (data.records_found && data.impacts && data.impacts.length > 0) {
        if (adviceText) adviceText.textContent = data.route_advice || "";
        if (impactsWrap) {
          impactsWrap.innerHTML = "";
          data.impacts.forEach((imp) => {
            const card = document.createElement("div");
            card.className = "eco-card p-3 mb-3 border-start border-3 border-warning";
            card.innerHTML = `
              <div class="d-flex align-items-center gap-2 mb-2">
                <span class="badge bg-warning-subtle text-warning border px-2 py-1">${imp.hazard_type || "Hazard Warning"}</span>
                ${imp.source_organization ? `<span class="small text-muted">Source: ${imp.source_organization}</span>` : ""}
              </div>
              <p class="mb-2 fw-semibold text-dark">${imp.improper_disposal_effect || ""}</p>
              ${imp.environmental_consequence ? `<p class="small text-muted mb-2"><strong>Consequence:</strong> ${imp.environmental_consequence}</p>` : ""}
              ${imp.recommended_action ? `<div class="p-2 bg-light rounded small"><strong>Action:</strong> ${imp.recommended_action}</div>` : ""}
              ${imp.source_url ? `<div class="mt-2 text-end"><a href="${imp.source_url}" target="_blank" rel="noopener" class="small text-decoration-none"><i class="bi bi-box-arrow-up-right me-1"></i>Reference</a></div>` : ""}
            `;
            impactsWrap.appendChild(card);
          });
        }
        if (content) content.classList.remove("d-none");
      } else {
        const unavailMsg = document.getElementById("ecoUnavailableMsg");
        if (unavailMsg) {
          unavailMsg.textContent =
            data.unavailable_message ||
            `Verified environmental impact information is not yet catalogued for '${cat}'.`;
        }
        if (unavailable) unavailable.classList.remove("d-none");
      }
    })
    .catch((err) => {
      console.warn("EcoImpact error:", err);
      if (loading) loading.classList.add("d-none");
      if (unavailable) unavailable.classList.remove("d-none");
    });
}

// ── Step 6: Review & Publish ─────────────────────────────────────────────────
function populateReview() {
  const getVal = (id, def = "—") => {
    const el = document.getElementById(id);
    return el && el.value.trim() ? el.value.trim() : def;
  };

  const reviewTitle = document.getElementById("reviewTitle");
  if (reviewTitle) reviewTitle.textContent = getVal("title");

  const reviewCategory = document.getElementById("reviewCategory");
  if (reviewCategory) reviewCategory.textContent = getVal("hidCategoryConfirmed");

  const reviewWorking = document.getElementById("reviewWorking");
  if (reviewWorking) {
    const w = getVal("working_status");
    reviewWorking.textContent = w.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const reviewCondition = document.getElementById("reviewCondition");
  if (reviewCondition) {
    const c = getVal("physical_condition");
    reviewCondition.textContent = c.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const reviewComponents = document.getElementById("reviewComponents");
  if (reviewComponents) {
    if (detectedComponents && detectedComponents.length > 0) {
      reviewComponents.innerHTML = detectedComponents
        .map((c) => `<span class="badge bg-light text-dark border me-1">${c.name} (${Math.round((c.confidence || 0.85) * 100)}%)</span>`)
        .join(" ");
    } else {
      reviewComponents.textContent = "None detected automatically";
    }
  }

  const reviewDiagnostics = document.getElementById("reviewDiagnostics");
  if (reviewDiagnostics) {
    const keys = Object.keys(diagnosticAnswers);
    if (keys.length > 0) {
      reviewDiagnostics.innerHTML = keys
        .map((k) => `<span class="badge bg-secondary-subtle text-dark border me-1">${k.replace(/_/g, " ")}: ${diagnosticAnswers[k].replace(/_/g, " ")}</span>`)
        .join(" ");
    } else {
      reviewDiagnostics.textContent = "No diagnostic answers provided";
    }
  }

  const reviewDefects = document.getElementById("reviewDefects");
  if (reviewDefects) reviewDefects.textContent = getVal("defects", "None reported");

  const reviewPrice = document.getElementById("reviewPrice");
  if (reviewPrice) {
    const p = getVal("asking_price", "");
    reviewPrice.textContent = p ? "₹" + p : "Free / To be agreed";
  }

  const reviewRoute = document.getElementById("reviewRoute");
  if (reviewRoute) {
    reviewRoute.textContent = currentRoute.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // Preview image in step 6
  const reviewImg = document.getElementById("reviewImage");
  const reviewPlaceholder = document.getElementById("reviewImagePlaceholder");
  const previewImg = document.getElementById("previewImg");

  if (previewImg && previewImg.src && previewImg.src.startsWith("data:")) {
    if (reviewImg) {
      reviewImg.src = previewImg.src;
      reviewImg.classList.remove("d-none");
    }
    if (reviewPlaceholder) reviewPlaceholder.classList.add("d-none");
  } else {
    if (reviewImg) reviewImg.classList.add("d-none");
    if (reviewPlaceholder) reviewPlaceholder.classList.remove("d-none");
  }
}
