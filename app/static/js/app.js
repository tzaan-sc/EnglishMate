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
});
