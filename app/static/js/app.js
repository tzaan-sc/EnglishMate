document.addEventListener("DOMContentLoaded", () => {
  const cards = [...document.querySelectorAll("[data-card]")];
  let current = 0;
  const progress = document.getElementById("deck-progress");
  const indexLabel = document.getElementById("card-index");
  const deck = document.querySelector(".card-deck");
  const done = document.getElementById("deck-done");

  cards.forEach((wrap) => {
    const card = wrap.querySelector(".flashcard");
    card?.addEventListener("click", () => card.classList.toggle("flipped"));
    wrap.querySelectorAll("[data-review-form]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = form.querySelector("button");
        button.disabled = true;
        try {
          const response = await fetch(form.action, {method: "POST", body: new FormData(form)});
          if (!response.ok) throw new Error("request failed");
          wrap.classList.add("d-none");
          current += 1;
          if (current < cards.length) {
            cards[current].classList.remove("d-none");
            indexLabel.textContent = current + 1;
            progress.style.width = `${((current + 1) / cards.length) * 100}%`;
          } else {
            deck.classList.add("d-none");
            document.querySelector(".deck-status")?.classList.add("d-none");
            done.classList.remove("d-none");
          }
        } catch (_error) {
          button.disabled = false;
          alert("Không thể lưu kết quả. Vui lòng thử lại.");
        }
      });
    });
  });

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
});
