
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

  // Auto-dismiss Flash Toasts & Alerts with Pause-on-Hover
  document.querySelectorAll(".flash-toast, .flash-stack .alert, .alert").forEach((toast) => {
    let timer = null;
    const startDismiss = (delay = 4500) => {
      timer = window.setTimeout(() => {
        if (window.bootstrap) {
          bootstrap.Alert.getOrCreateInstance(toast).close();
        } else {
          toast.remove();
        }
      }, delay);
    };

    startDismiss(4500);

    toast.addEventListener("mouseenter", () => {
      if (timer) clearTimeout(timer);
      const progress = toast.querySelector(".flash-toast-progress");
      if (progress) progress.style.animationPlayState = "paused";
    });

    toast.addEventListener("mouseleave", () => {
      const progress = toast.querySelector(".flash-toast-progress");
      if (progress) progress.style.animationPlayState = "running";
      startDismiss(3000);
    });
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

/**
 * Global Flash Toast Notification Generator (Top-Right Toast)
 * @param {string} message - Message text or HTML
 * @param {'success'|'danger'|'error'|'warning'|'info'} type - Toast type
 * @param {string} [customTitle] - Optional custom title
 */
window.showToastNotification = function(message, type = 'success', customTitle = '') {
  let stack = document.getElementById('flashStack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'flash-stack';
    stack.id = 'flashStack';
    stack.setAttribute('aria-live', 'polite');
    stack.setAttribute('aria-atomic', 'true');
    document.body.appendChild(stack);
  }

  const cat = (type === 'error' || type === 'danger') ? 'danger' : (['success', 'warning', 'info'].includes(type) ? type : 'info');
  const defaultTitles = {
    success: 'Thành công',
    danger: 'Có lỗi xảy ra',
    warning: 'Lưu ý',
    info: 'Thông báo'
  };
  const icons = {
    success: 'ph-fill ph-check-circle',
    danger: 'ph-fill ph-x-circle',
    warning: 'ph-fill ph-warning-circle',
    info: 'ph-fill ph-info'
  };

  const toast = document.createElement('div');
  toast.className = `flash-toast flash-toast-${cat} alert alert-dismissible fade show`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="flash-toast-icon">
      <i class="${icons[cat]}"></i>
    </div>
    <div class="flash-toast-content">
      <div class="flash-toast-title">${customTitle || defaultTitles[cat]}</div>
      <div class="flash-toast-message">${message}</div>
    </div>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Đóng"></button>
    <div class="flash-toast-progress"></div>
  `;

  stack.appendChild(toast);

  let timer = setTimeout(() => {
    if (window.bootstrap) {
      bootstrap.Alert.getOrCreateInstance(toast).close();
    } else {
      toast.remove();
    }
  }, 4500);

  toast.addEventListener('mouseenter', () => {
    clearTimeout(timer);
    const progress = toast.querySelector('.flash-toast-progress');
    if (progress) progress.style.animationPlayState = 'paused';
  });

  toast.addEventListener('mouseleave', () => {
    const progress = toast.querySelector('.flash-toast-progress');
    if (progress) progress.style.animationPlayState = 'running';
    timer = setTimeout(() => {
      if (window.bootstrap) {
        bootstrap.Alert.getOrCreateInstance(toast).close();
      } else {
        toast.remove();
      }
    }, 3000);
  });
};
