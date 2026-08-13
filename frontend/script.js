const modal = document.getElementById("signupModal");
const planSelect = document.getElementById("planSelect");
const form = document.getElementById("signupForm");
const status = document.getElementById("formStatus");

function openModal(plan) {
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  if (plan) {
    const values = {
      "Месяц": "Месяц — 299 ₽/мес",
      "Год": "Год — 2 388 ₽/год",
      "Навсегда": "Навсегда — 4 990 ₽"
    };
    planSelect.value = values[plan] || planSelect.options[0].value;
  }
  setTimeout(() => document.querySelector("#signupForm input")?.focus(), 50);
}

function closeModal() {
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  status.textContent = "";
}

document.querySelectorAll(".js-open-modal").forEach(btn => {
  btn.addEventListener("click", () => openModal(btn.dataset.plan));
});
document.querySelectorAll("[data-close-modal]").forEach(el => el.addEventListener("click", closeModal));
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && modal.classList.contains("is-open")) closeModal();
});

form.addEventListener("submit", e => {
  e.preventDefault();

  // TODO: заменить этим вызовом реальную интеграцию с backend/payment gateway.
  // Например: fetch("/api/create-checkout", { method: "POST", body: new FormData(form) })
  status.textContent = "Демо-режим: здесь будет переход на страницу оплаты.";
});

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach(el => observer.observe(el));
