document.querySelectorAll("[data-nav-toggle]").forEach((toggle) => {
  toggle.addEventListener("click", (event) => {
    event.preventDefault();
    const navigation = document.getElementById(toggle.getAttribute("aria-controls"));
    if (!navigation) {
      return;
    }

    const isExpanded = navigation.style.display !== "block";
    navigation.style.display = isExpanded ? "block" : "none";
    toggle.setAttribute("aria-expanded", String(isExpanded));
  });
});
