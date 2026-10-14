async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "Không thể kết nối máy chủ.");
    return payload;
}

function showMessage(element, text, success = false) {
    element.textContent = text;
    element.classList.toggle("is-success", success);
}

async function initAuthPage() {
    const loginForm = document.getElementById("login-form");
    if (!loginForm) return;

    const registerForm = document.getElementById("register-form");
    const googleButton = document.getElementById("google-login-button");
    const googleMessage = document.getElementById("google-login-message");
    const isRegister = new URLSearchParams(location.search).get("view") === "register";
    document.getElementById("form-title").textContent = isRegister ? "Tạo tài khoản học viên" : "Chào mừng trở lại";
    document.getElementById("form-intro").textContent = isRegister
        ? "Đăng ký miễn phí để bắt đầu hành trình học tập."
        : "Đăng nhập để vào không gian học tập của bạn.";
    loginForm.hidden = isRegister;
    registerForm.hidden = !isRegister;
    document.getElementById("login-footer").hidden = isRegister;
    document.getElementById("register-footer").hidden = !isRegister;

    try {
        const { client_id: googleClientId } = await apiRequest("/api/auth/google-config");
        if (!googleClientId) {
            googleButton.disabled = true;
            showMessage(googleMessage, "Chưa cấu hình Client ID của Google.");
        } else {
            const waitForGoogleIdentity = async () => {
                for (let attempt = 0; attempt < 50; attempt += 1) {
                    if (window.google?.accounts?.id) return;
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
                throw new Error("Không thể tải Google Identity Services.");
            };

            await waitForGoogleIdentity();
            window.google.accounts.id.initialize({
                client_id: googleClientId,
                callback: async ({ credential }) => {
                    googleButton.disabled = true;
                    googleButton.textContent = "Đang đăng nhập...";
                    try {
                        const account = await apiRequest("/api/auth/google", {
                            method: "POST",
                            body: JSON.stringify({ credential }),
                        });
                        location.href = account.role === "admin" ? "admin.html" : "index.html";
                    } catch (error) {
                        showMessage(googleMessage, error.message);
                    } finally {
                        googleButton.disabled = false;
                        googleButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#EA4335" d="M12 10.2v3.9h5.5a4.7 4.7 0 0 1-2 3.1l3.2 2.5A10.6 10.6 0 0 0 22 12c0-.8-.1-1.6-.3-2.3H12Z"/><path fill="#34A853" d="M12 22a9.5 9.5 0 0 0 6.6-2.4l-3.2-2.5a6 0 0 1-8.8-3.1l-3.2 2.5A10 10 0 0 0 12 22Z"/><path fill="#4A90E2" d="M5.6 14a6 6 0 0 1 0-4l-3.2-2.5a10 10 0 0 0 0 9L5.6 14Z"/><path fill="#FBBC05" d="M12 6.1a5.4 5.4 0 0 1 3.8 1.5l2.9-2.9A9.7 9.7 0 0 0 12 2a10 10 0 0 0-8.6 4.5L6.8 9a6 6 0 0 1 5.2-2.9Z"/></svg>Đăng nhập bằng Google';
                    }
                },
            });
            window.google.accounts.id.renderButton(googleButton, { theme: "outline", size: "large", width: 300 });
        }
    } catch (error) {
        googleButton.disabled = true;
        showMessage(googleMessage, error.message);
    }

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = document.getElementById("login-message");
        const submitButton = loginForm.querySelector("button[type='submit']");
        submitButton.disabled = true;
        try {
            const account = await apiRequest("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: loginForm.elements.email.value.trim(),
                    password: loginForm.elements.password.value,
                }),
            });
            location.href = account.role === "admin" ? "admin.html" : "index.html";
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            submitButton.disabled = false;
        }
    });

    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = document.getElementById("register-message");
        const submitButton = registerForm.querySelector("button[type='submit']");
        submitButton.disabled = true;
        try {
            await apiRequest("/api/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    name: registerForm.elements.name.value.trim(),
                    email: registerForm.elements.email.value.trim(),
                    password: registerForm.elements.password.value,
                }),
            });
            location.replace("index.html");
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            submitButton.disabled = false;
        }
    });
}

async function initHomeAccount() {
    const accountLink = document.getElementById("home-account-link");
    if (!accountLink) return;

    try {
        const account = await apiRequest("/api/auth/me");
        const accountName = account.name.trim();
        const accountLabel = document.getElementById("home-account-label");
        const avatar = document.getElementById("home-account-avatar");
        accountLink.href = account.role === "admin" ? "admin.html" : "user.html";
        accountLink.classList.add("home-account-link");
        accountLabel.textContent = accountName;
        accountLabel.classList.add("home-account-name");
        accountLabel.removeAttribute("data-i18n");
        avatar.textContent = accountName.charAt(0).toLocaleUpperCase("vi");
        avatar.hidden = false;
    } catch {
        accountLink.href = "auth.html";
    }
}

async function requireRole(requiredRole) {
    try {
        const account = await apiRequest("/api/auth/me");
        if (account.role !== requiredRole) {
            location.replace("auth.html");
            return;
        }
        document.querySelectorAll("[data-account-name]").forEach((element) => {
            element.textContent = account.name;
        });
        document.querySelectorAll("[data-account-email]").forEach((element) => {
            element.textContent = account.email;
        });
        document.querySelectorAll("[data-account-avatar]").forEach((element) => {
            element.textContent = account.name.trim().charAt(0).toLocaleUpperCase("vi");
        });

        document.getElementById("logout-button")?.addEventListener("click", async () => {
            await apiRequest("/api/auth/logout", { method: "POST" });
            location.replace("auth.html");
        });

        if (requiredRole === "admin") {
            await Promise.all([renderUsersTable(), initAdminForms(), renderCourseTable()]);
        }
    } catch {
        location.replace("auth.html");
    }
}

async function renderUsersTable() {
    const tableBody = document.getElementById("users-table-body");
    const userCount = document.getElementById("user-count");
    const adminCount = document.getElementById("admin-count");
    if (!tableBody && !userCount && !adminCount) return;
    try {
        const users = await apiRequest("/api/admin/users");
        if (userCount) userCount.textContent = String(users.filter((user) => user.role === "user").length);
        if (adminCount) adminCount.textContent = String(users.filter((user) => user.role === "admin").length);
        if (!tableBody) return;
        tableBody.replaceChildren();
        users.forEach((user, index) => {
            const row = document.createElement("tr");
            [String(index + 1), user.name, user.email, user.role === "admin" ? "Quản trị viên" : "Học viên"].forEach((value) => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.append(cell);
            });
            tableBody.append(row);
        });
    } catch (error) {
        if (tableBody) {
            tableBody.replaceChildren();
            addEmptyRow(tableBody, 4, error.message);
        }
    }
}

async function initAdminForms() {
    const form = document.getElementById("admin-create-form");
    if (form) form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = document.getElementById("admin-create-message");
        const button = form.querySelector("button[type='submit']");
        button.disabled = true;
        try {
            await apiRequest("/api/admin/users", {
                method: "POST",
                body: JSON.stringify({
                    name: form.elements.name.value.trim(),
                    email: form.elements.email.value.trim(),
                    password: form.elements.password.value,
                }),
            });
            form.reset();
            showMessage(message, "Đã tạo tài khoản quản trị viên.", true);
            await renderUsersTable();
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            button.disabled = false;
        }
    });

    const deleteForm = document.getElementById("course-delete-form");
    if (deleteForm) await initCourseDeleteForm(deleteForm);

    const courseForm = document.getElementById("course-form");
    if (!courseForm) return;
    const courseId = new URLSearchParams(location.search).get("id");
    if (courseId) {
        try {
            const course = (await apiRequest("/api/courses")).find((item) => String(item.id) === courseId);
            if (!course) throw new Error("Không tìm thấy khóa học.");
            courseForm.elements.id.value = course.id;
            courseForm.elements.title.value = course.title;
            courseForm.elements.description.value = course.description;
            courseForm.elements.image_url.value = course.image_url;
            courseForm.elements.course_url.value = course.course_url;
            document.getElementById("course-form-title").textContent = "Sửa khóa học";
            document.getElementById("course-submit-label").textContent = "Lưu thay đổi";
            showMessage(document.getElementById("course-image-status"), course.image_url ? "Ảnh hiện tại. Chọn file mới để thay." : "PNG, JPG, GIF hoặc WebP, tối đa 5 MB.");
            updateImagePreview(course.image_url);
        } catch (error) {
            showMessage(document.getElementById("course-message"), error.message);
            courseForm.querySelector("button[type='submit']").disabled = true;
        }
    } else {
        resetCourseForm();
    }

    const imageInput = document.getElementById("course-image-file");
    imageInput.addEventListener("change", async () => {
        const file = imageInput.files[0];
        if (!file) return;
        const status = document.getElementById("course-image-status");
        const submitButton = courseForm.querySelector("button[type='submit']");
        if (file.size > 5 * 1024 * 1024) {
            imageInput.value = "";
            showMessage(status, "Ảnh không được vượt quá 5 MB.");
            return;
        }

        const formData = new FormData();
        formData.set("image", file);
        submitButton.disabled = true;
        showMessage(status, "Đang tải ảnh lên...");
        try {
            const response = await fetch("/api/admin/uploads", {
                method: "POST",
                credentials: "same-origin",
                body: formData,
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.error || "Không thể tải ảnh lên.");
            courseForm.elements.image_url.value = result.image_url;
            updateImagePreview(result.image_url);
            showMessage(status, "Đã tải ảnh lên.", true);
        } catch (error) {
            imageInput.value = "";
            showMessage(status, error.message);
        } finally {
            submitButton.disabled = false;
        }
    });

    courseForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!courseForm.reportValidity()) return;
        const message = document.getElementById("course-message");
        const button = courseForm.querySelector("button[type='submit']");
        const editingId = courseForm.elements.id.value;
        const data = {
            title: courseForm.elements.title.value.trim(),
            description: courseForm.elements.description.value.trim(),
            image_url: courseForm.elements.image_url.value.trim(),
            course_url: courseForm.elements.course_url.value.trim(),
        };
        button.disabled = true;
        try {
            await apiRequest(editingId ? `/api/courses/${editingId}` : "/api/courses", {
                method: editingId ? "PUT" : "POST",
                body: JSON.stringify(data),
            });
            location.href = `admin-courses.html?saved=${editingId ? "updated" : "created"}`;
        } catch (error) {
            showMessage(message, error.message);
        } finally {
            button.disabled = false;
        }
    });

    document.getElementById("course-form-reset").addEventListener("click", () => {
        if (courseForm.elements.id.value) location.reload();
        else resetCourseForm();
    });
    document.getElementById("course-image-clear").addEventListener("click", () => {
        courseForm.elements.image_url.value = "";
        imageInput.value = "";
        updateImagePreview("");
        showMessage(document.getElementById("course-image-status"), "Đã bỏ ảnh.", true);
    });
}

async function initCourseDeleteForm(form) {
    const message = document.getElementById("course-delete-message");
    const button = form.querySelector("button[type='submit']");
    const courseId = new URLSearchParams(location.search).get("id");
    if (!/^\d+$/.test(courseId || "")) {
        showMessage(message, "Liên kết khóa học không hợp lệ.");
        button.disabled = true;
        return;
    }

    try {
        const course = (await apiRequest("/api/courses")).find((item) => String(item.id) === courseId);
        if (!course) throw new Error("Không tìm thấy khóa học.");
        document.getElementById("delete-course-title").textContent = course.title;
        document.getElementById("delete-course-description").textContent = course.description || "Không có mô tả.";
    } catch (error) {
        showMessage(message, error.message);
        button.disabled = true;
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.reportValidity()) return;
        button.disabled = true;
        try {
            await apiRequest(`/api/courses/${courseId}`, { method: "DELETE" });
            location.href = "admin-courses.html?saved=deleted";
        } catch (error) {
            showMessage(message, error.message);
            button.disabled = false;
        }
    });
}

    function initAdminNavigation() {
        const sidebar = document.getElementById("admin-sidebar");
        const toggle = document.getElementById("sidebar-toggle");
        const close = document.getElementById("sidebar-close");
        const backdrop = document.getElementById("sidebar-backdrop");
        const setSidebarOpen = (open) => {
            sidebar?.classList.toggle("is-open", open);
            backdrop?.classList.toggle("hidden", !open);
            toggle?.setAttribute("aria-expanded", String(open));
        };

        toggle?.addEventListener("click", () => setSidebarOpen(true));
        close?.addEventListener("click", () => setSidebarOpen(false));
        backdrop?.addEventListener("click", () => setSidebarOpen(false));
        sidebar?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setSidebarOpen(false)));
        window.addEventListener("resize", () => {
            if (window.matchMedia("(min-width: 1024px)").matches) setSidebarOpen(false);
        });

        const dateLabel = document.querySelector("[data-current-date]");
        if (dateLabel) {
            dateLabel.textContent = new Intl.DateTimeFormat("vi-VN", {
                weekday: "long",
                day: "2-digit",
                month: "long",
            }).format(new Date()).toLocaleUpperCase("vi");
        }

        document.getElementById("course-search")?.addEventListener("input", (event) => {
            const query = event.currentTarget.value.trim().toLocaleLowerCase("vi");
            document.querySelectorAll("#courses-table-body tr:not(.empty-row)").forEach((row) => {
                row.hidden = !row.textContent.toLocaleLowerCase("vi").includes(query);
            });
        });
    }

function updateImagePreview(imageUrl) {
    const preview = document.getElementById("course-image-preview");
    const image = document.getElementById("course-image-preview-img");
    preview.hidden = !imageUrl;
    image.src = imageUrl || "";
}

function resetCourseForm() {
    const form = document.getElementById("course-form");
    form.reset();
    document.getElementById("course-id").value = "";
    document.getElementById("course-form-title").textContent = "Thêm khóa học";
    document.getElementById("course-submit-label").textContent = "Thêm khóa học";
    showMessage(document.getElementById("course-message"), "");
    showMessage(document.getElementById("course-image-status"), "PNG, JPG, GIF hoặc WebP, tối đa 5 MB.");
    updateImagePreview("");
}

async function renderCourseTable() {
    const tableBody = document.getElementById("courses-table-body");
    const courseCount = document.getElementById("course-count");
    const sidebarCourseCount = document.getElementById("sidebar-course-count");
    if (!tableBody && !courseCount && !sidebarCourseCount) return;
    try {
        const courses = await apiRequest("/api/courses");
        if (courseCount) courseCount.textContent = String(courses.length);
        if (sidebarCourseCount) sidebarCourseCount.textContent = String(courses.length);
        const overviewCourseCount = document.getElementById("overview-course-count");
        if (overviewCourseCount) overviewCourseCount.textContent = String(courses.length);
        const listMessage = document.getElementById("course-list-message");
        const savedAction = new URLSearchParams(location.search).get("saved");
        const savedMessages = {
            created: "Đã thêm khóa học.",
            updated: "Đã cập nhật khóa học.",
            deleted: "Đã xóa khóa học.",
        };
        if (listMessage && savedMessages[savedAction]) showMessage(listMessage, savedMessages[savedAction], true);
        if (!tableBody) return;
        tableBody.replaceChildren();
        if (courses.length === 0) addEmptyRow(tableBody, 3, "Chưa có khóa học.");
        courses.forEach((course) => {
            const row = document.createElement("tr");
            const titleCell = document.createElement("td");
            titleCell.textContent = course.title;
            const descriptionCell = document.createElement("td");
            descriptionCell.textContent = course.description;
            const actionsCell = document.createElement("td");
            actionsCell.className = "table-actions";
            const editLink = makeCourseActionLink("Sửa", `admin-course-form.html?id=${encodeURIComponent(course.id)}`);
            const deleteLink = makeCourseActionLink("Xóa", `admin-course-delete.html?id=${encodeURIComponent(course.id)}`);
            actionsCell.append(editLink, deleteLink);
            row.append(titleCell, descriptionCell, actionsCell);
            tableBody.append(row);
        });
    } catch (error) {
        if (tableBody) {
            tableBody.replaceChildren();
            addEmptyRow(tableBody, 3, error.message);
        }
    }
}

function makeCourseActionLink(label, href) {
    const link = document.createElement("a");
    link.className = "text-button table-action-link";
    link.href = href;
    link.textContent = label;
    return link;
}

function addEmptyRow(tableBody, columnCount, text) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = columnCount;
    cell.className = "empty-row";
    cell.textContent = text;
    row.append(cell);
    tableBody.append(row);
}

document.addEventListener("DOMContentLoaded", () => {
    initAuthPage();
    initAdminNavigation();
    initHomeAccount();
    const requiredRole = document.body.dataset.protectedRole;
    if (requiredRole) requireRole(requiredRole);
});