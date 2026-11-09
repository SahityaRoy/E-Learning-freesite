document.querySelectorAll("form[data-confirm-delete]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirmDelete)) {
      event.preventDefault();
    }
  });
});
