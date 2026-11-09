async function loadCourseCatalog() {
    const sections = Array.from(document.querySelectorAll(".course-section"));
    const catalogSection = sections.find((section) => section.id === "course");
    if (!catalogSection) return;

    sections.filter((section) => section !== catalogSection).forEach((section) => section.remove());
    const catalog = catalogSection.querySelector(".card-deck");
    const showMoreButton = catalogSection.querySelector("#courses-show-more");
    if (!catalog) return;
    catalog.className = "course-catalog";
    catalog.id = "course-catalog";
    catalog.replaceChildren(makeCourseStatus("Đang tải khóa học..."));

    try {
        const response = await fetch("/api/courses", { credentials: "same-origin" });
        if (!response.ok) throw new Error("Không thể tải danh sách khóa học.");
        const courses = await response.json();
        catalog.replaceChildren();
        if (courses.length === 0) {
            catalog.append(makeCourseStatus("Hiện chưa có khóa học."));
            return;
        }
        courses.forEach((course) => catalog.append(createCourseCard(course)));
        updateCourseVisibility(catalog, showMoreButton, false);
    } catch {
        catalog.replaceChildren(makeCourseStatus("Không kết nối được máy chủ khóa học. Hãy chạy backend Python."));
    }
}

function updateCourseVisibility(catalog, button, expanded) {
    const cards = Array.from(catalog.querySelectorAll(":scope > .card"));
    cards.forEach((card, index) => {
        card.hidden = !expanded && index >= 4;
    });
    if (!button) return;

    button.hidden = cards.length <= 4;
    button.setAttribute("aria-expanded", String(expanded));
    const remaining = Math.max(0, cards.length - 4);
    button.textContent = document.documentElement.lang === "en"
        ? (expanded ? "Show fewer courses" : `Show ${remaining} more courses`)
        : (expanded ? "Thu gọn" : `Xem thêm ${remaining} khóa học`);
}

function createCourseCard(course) {
    const card = document.createElement("article");
    card.className = "card";

    const art = document.createElement("div");
    art.className = "course-card-art";
    if (course.image_url) {
        const image = document.createElement("img");
        image.className = "course-card-art__image";
        image.src = course.image_url;
        image.alt = course.title;
        image.loading = "lazy";
        art.append(image);
    }
    const eyebrow = document.createElement("span");
    eyebrow.className = "course-card-art__eyebrow";
    eyebrow.textContent = "EDUHUB  /  KHÓA HỌC";
    const artTitle = document.createElement("strong");
    artTitle.className = "course-card-art__title";
    artTitle.textContent = course.title;
    art.append(eyebrow, artTitle);
    card.append(art);

    const body = document.createElement("div");
    body.className = "card-body";
    const description = document.createElement("p");
    description.className = "card-text";
    description.textContent = course.description;
    const link = document.createElement("a");
    link.className = "nav-link nav-btn";
    link.href = `/courses/${encodeURIComponent(course.id)}`;
    link.textContent = "Chi tiết khóa học";
    body.append(description, link);
    card.append(body);
    return card;
}

function makeCourseStatus(message) {
    const status = document.createElement("p");
    status.className = "course-status";
    status.setAttribute("role", "status");
    status.textContent = message;
    return status;
}

document.addEventListener("DOMContentLoaded", () => {
    loadCourseCatalog();
    const showMoreButton = document.getElementById("courses-show-more");
    let expanded = false;
    showMoreButton?.addEventListener("click", () => {
        const catalog = document.getElementById("course-catalog");
        if (!catalog) return;
        expanded = !expanded;
        updateCourseVisibility(catalog, showMoreButton, expanded);
        if (!expanded) {
            document.querySelector("#course .title-text")?.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});