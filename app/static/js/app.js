
function replaceSocialIcons() {
  document.querySelectorAll(".btn-google svg, .btn-facebook svg").forEach((icon) => {
    const replacement = document.createElement("i");
    replacement.className = icon.closest(".btn-google") ? "ph-bold ph-globe icon-social" : "ph-bold ph-chats-circle icon-social";
    icon.replaceWith(replacement);
  });
}

function initializeIcons() {
  replaceSocialIcons();
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    try {
      window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
    } catch (e) {}
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initializeIcons();

  document.querySelectorAll(".alert").forEach((alert) => {
    window.setTimeout(() => {
      if (window.bootstrap) bootstrap.Alert.getOrCreateInstance(alert).close();
    }, 4500);
  });

  // Password Strength Meter
  const passwordInput = document.getElementById("password");
  const strengthWrap = document.getElementById("password-strength-wrap");
  const strengthBar = document.getElementById("password-strength-bar");
  const strengthText = document.getElementById("password-strength-text");
  const strengthHint = document.getElementById("password-strength-hint");

  if (passwordInput && strengthWrap) {
    passwordInput.addEventListener("input", () => {
      const val = passwordInput.value;
      if (!val) {
        strengthWrap.classList.add("d-none");
        return;
      }
      strengthWrap.classList.remove("d-none");

      let score = 0;
      if (val.length >= 6) score += 1;
      if (val.length >= 10) score += 1;
      if (/[A-Z]/.test(val)) score += 1;
      if (/[0-9]/.test(val)) score += 1;
      if (/[^A-Za-z0-9]/.test(val)) score += 1;

      strengthBar.className = "progress-bar";
      if (score <= 2) {
        strengthBar.style.width = "25%";
        strengthBar.classList.add("strength-weak");
        strengthText.textContent = "Độ mạnh: Yếu";
        strengthText.className = "fw-semibold text-danger";
        strengthHint.textContent = "Nên thêm số & chữ hoa";
      } else if (score === 3) {
        strengthBar.style.width = "50%";
        strengthBar.classList.add("strength-medium");
        strengthText.textContent = "Độ mạnh: Trung bình";
        strengthText.className = "fw-semibold text-warning";
        strengthHint.textContent = "Thêm ký tự đặc biệt";
      } else if (score === 4) {
        strengthBar.style.width = "75%";
        strengthBar.classList.add("strength-strong");
        strengthText.textContent = "Độ mạnh: Mạnh";
        strengthText.className = "fw-semibold text-primary";
        strengthHint.textContent = "Mật khẩu an toàn";
      } else {
        strengthBar.style.width = "100%";
        strengthBar.classList.add("strength-very-strong");
        strengthText.textContent = "Độ mạnh: Rất mạnh";
        strengthText.className = "fw-semibold text-success";
        strengthHint.textContent = "Mật khẩu tuyệt vời!";
      }
    });
  }

  // Show/Hide Password Eye Toggle
  document.querySelectorAll(".toggle-password-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const targetInput = targetId ? document.getElementById(targetId) : btn.previousElementSibling;
      if (targetInput) {
        const isPassword = targetInput.type === "password";
        targetInput.type = isPassword ? "text" : "password";
        const icon = btn.querySelector("i");
        if (icon) {
          if (icon.className.includes("bi-")) {
            icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
          } else {
            icon.className = isPassword ? "ph-bold ph-eye-slash fs-5" : "ph-bold ph-eye fs-5";
          }
        }
      }
    });
  });

  // Sidebar Collapse / Expand on Background Click
  const sidebar = document.querySelector(".app-sidebar");
  if (sidebar) {
    // Sync initial state from localStorage
    try {
      if (localStorage.getItem("sidebar_collapsed") === "true") {
        sidebar.classList.add("collapsed");
      }
    } catch (e) {}

    // Toggle when clicking on the sidebar background (not on links, buttons, or forms)
    sidebar.addEventListener("click", (e) => {
      const interactive = e.target.closest("a, button, input, select, textarea, form");
      if (interactive) {
        // Allow normal navigation and actions when clicking on links/buttons
        return;
      }

      // User clicked on the background / empty space of the sidebar
      const isCollapsed = sidebar.classList.toggle("collapsed");
      try {
        localStorage.setItem("sidebar_collapsed", isCollapsed ? "true" : "false");
      } catch (err) {}
    });
  }
});
