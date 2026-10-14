async function loadCourseCatalog() {
    const sections = Array.from(document.querySelectorAll(".course-section"));
    const catalogSection = sections.find((section) => section.id === "course");
    if (!catalogSection) return;

    sections.filter((section) => section !== catalogSection).forEach((section) => section.remove());
    const catalog = catalogSection.querySelector(".card-deck");
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
    } catch {
        catalog.replaceChildren(makeCourseStatus("Không kết nối được máy chủ khóa học. Hãy chạy backend Python."));
    }
}

function createCourseCard(course) {
    const card = document.createElement("article");
    card.className = "card";

    if (course.image_url) {
        const image = document.createElement("img");
        image.className = "card-img-top";
        image.src = course.image_url;
        image.alt = course.title;
        image.loading = "lazy";
        card.append(image);
    } else {
        const placeholder = document.createElement("div");
        placeholder.className = "course-placeholder";
        placeholder.textContent = course.title.slice(0, 1).toUpperCase();
        card.append(placeholder);
    }

    const body = document.createElement("div");
    body.className = "card-body";
    const title = document.createElement("h3");
    title.className = "card-title";
    title.textContent = course.title;
    const description = document.createElement("p");
    description.className = "card-text";
    description.textContent = course.description;
    const link = document.createElement("a");
    link.className = "nav-link nav-btn";
    link.href = course.course_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "Enroll";
    body.append(title, description, link);
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

document.addEventListener("DOMContentLoaded", loadCourseCatalog);