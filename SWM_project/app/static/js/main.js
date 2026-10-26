/**
 * EcoLoop — Frontend Interactivity & Utilities
 */

document.addEventListener("DOMContentLoaded", function () {
  // ── Navbar Shadow on Scroll ────────────────────────────────────────────
  const mainNav = document.getElementById("mainNav");
  if (mainNav) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 15) {
        mainNav.classList.add("shadow-sm", "scrolled");
      } else {
        mainNav.classList.remove("shadow-sm", "scrolled");
      }
    });
  }

  // ── Initialize Tooltips ────────────────────────────────────────────────
  if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  // ── Auto-dismiss alerts after 5 seconds ────────────────────────────────
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // ── Password Visibility Toggle ─────────────────────────────────────────
  const toggleButtons = document.querySelectorAll(".toggle-password");
  toggleButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === "password") {
          input.type = "text";
          this.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          input.type = "password";
          this.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  // ── Image Preview Helper ───────────────────────────────────────────────
  const imageInputs = document.querySelectorAll('input[type="file"][data-preview-target]');
  imageInputs.forEach(function (input) {
    input.addEventListener("change", function (e) {
      const targetId = this.getAttribute("data-preview-target");
      const previewImg = document.getElementById(targetId);
      if (previewImg && this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          previewImg.src = evt.target.result;
          previewImg.classList.remove("d-none");
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  });

  // ── Admin Dashboard Charts (if elements exist) ─────────────────────────
  initAdminDashboardCharts();
});

/**
 * Initializes Chart.js on the admin dashboard if canvas elements are found.
 */
function initAdminDashboardCharts() {
  const statusCanvas = document.getElementById("adminStatusChart");
  const routeCanvas = document.getElementById("adminRouteChart");

  if (!statusCanvas || !routeCanvas) return;

  fetch("/admin/api/summary")
    .then((res) => {
      if (!res.ok) throw new Error("Network response was not ok");
      return res.json();
    })
    .then((data) => {
      // 1. Status Breakdown (Doughnut)
      const statusLabels = Object.keys(data.status_counts || {});
      const statusValues = Object.values(data.status_counts || {});

      new Chart(statusCanvas, {
        type: "doughnut",
        data: {
          labels: statusLabels.map((s) => s.replace("_", " ").toUpperCase()),
          datasets: [
            {
              data: statusValues,
              backgroundColor: [
                "#10b981", // available
                "#f59e0b", // reserved
                "#64748b", // collected
                "#ef4444", // pending_review
                "#94a3b8", // draft
                "#334155", // withdrawn
              ],
              borderWidth: 2,
              borderColor: "#ffffff",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });

      // 2. Recovery Routes Breakdown (Bar)
      const routeLabels = Object.keys(data.route_counts || {});
      const routeValues = Object.values(data.route_counts || {});

      new Chart(routeCanvas, {
        type: "bar",
        data: {
          labels: routeLabels.map((r) => r.replace("_", " ").toUpperCase()),
          datasets: [
            {
              label: "Items Recommended",
              data: routeValues,
              backgroundColor: [
                "#10b981", // reuse
                "#3b82f6", // repair
                "#8b5cf6", // refurbish
                "#f59e0b", // parts_recovery
                "#06b6d4", // recycle
                "#ef4444", // manual_review
              ],
              borderRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 },
            },
          },
          plugins: {
            legend: { display: false },
          },
        },
      });
    })
    .catch((err) => {
      console.warn("Could not load admin chart analytics:", err);
    });
}
