
const emojiIconMap = {
  "🎓": "graduation-cap",
  "🎯": "target",
  "🎁": "gift",
  "🎉": "party-popper",
  "🎲": "dices",
  "🏆": "trophy",
  "🏁": "flag",
  "💡": "lightbulb",
  "💾": "save",
  "🔊": "volume-2",
  "🔄": "refresh-cw",
  "🔍": "search",
  "🔗": "link",
  "🔖": "bookmark",
  "🔔": "bell",
  "📊": "chart-column",
  "📈": "chart-line",
  "📉": "chart-line",
  "📄": "file-text",
  "📥": "download",
  "📤": "upload",
  "📚": "library",
  "📖": "book-open",
  "📜": "scroll-text",
  "📝": "notebook-pen",
  "🛡️": "shield-check",
  "🛡": "shield-check",
  "🖨️": "printer",
  "🖨": "printer",
  "🚀": "rocket",
  "🚩": "flag",
  "👍": "thumbs-up",
  "👁️": "eye",
  "🗑️": "trash-2",
  "🔥": "flame",
  "💪": "dumbbell",
  "🎴": "layers-3",
  "🎖️": "medal",
  "🎖": "medal",
  "👁": "eye",
  "🌅": "sunrise",
  "🌙": "moon",
};


function replaceSocialIcons() {
  document.querySelectorAll(".btn-google svg, .btn-facebook svg").forEach((icon) => {
    const replacement = document.createElement("i");
    replacement.dataset.lucide = icon.closest(".btn-google") ? "globe-2" : "message-circle";
    replacement.className = "icon-social";
    icon.replaceWith(replacement);
  });
}

function replaceEmojiIcons() {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) {
    if (node.parentElement.closest("script, style, textarea")) continue;
    if (node.parentElement.closest("option")) {
      Object.keys(emojiIconMap).forEach((emoji) => {
        node.data = node.data.split(emoji).join("");
      });
      continue;
    }
    if ([...node.data].some((character) => emojiIconMap[character])) textNodes.push(node);
  }

  textNodes.forEach((textNode) => {
    const fragment = document.createDocumentFragment();
    [...textNode.data].forEach((character) => {
      if (!emojiIconMap[character]) {
        fragment.append(character);
        return;
      }
      const icon = document.createElement("i");
      icon.dataset.lucide = emojiIconMap[character];
      icon.className = "icon-emoji";
      icon.setAttribute("aria-hidden", "true");
      fragment.append(icon);
    });
    textNode.replaceWith(fragment);
  });
}

function initializeIcons() {
  replaceSocialIcons();
  replaceEmojiIcons();
  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
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
        const icon = btn.querySelector(".lucide");
        if (icon) {
          const replacement = document.createElement("i");
          replacement.dataset.lucide = isPassword ? "eye-off" : "eye";
          replacement.className = icon.getAttribute("class") || "";
          icon.replaceWith(replacement);
          if (window.lucide) window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
        }
      }
    });
  });
});
