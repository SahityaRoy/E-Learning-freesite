(function () {
  const modal = document.getElementById("registrationModal");
  const form = document.getElementById("accountForm");
  if (!modal || !form) return;

  const translations = {
    en: {
      eyebrow: "EDUHUB ACCOUNT",
      registerTitle: "Create your account",
      loginTitle: "Welcome back",
      intro: "Save your learning progress and keep everything in one place.",
      loginIntro: "Sign in to continue learning.",
      google: "Continue with Google",
      facebook: "Continue with Facebook",
      orEmail: "or continue with email",
      fullName: "Full name",
      email: "Email address",
      password: "Password",
      confirmPassword: "Confirm password",
      namePlaceholder: "Enter your full name",
      emailPlaceholder: "you@example.com",
      passwordPlaceholder: "At least 8 characters",
      confirmPlaceholder: "Enter your password again",
      terms: "I agree to the Terms of Service and Privacy Policy.",
      createAccount: "Create account",
      signInSubmit: "Sign in",
      haveAccount: "Already have an account?",
      needAccount: "New to Eduhub?",
      signIn: "Sign in",
      signUp: "Create an account",
      strengthEmpty: "Use at least 8 characters",
      strengthWeak: "Weak",
      strengthFair: "Fair",
      strengthGood: "Good",
      strengthStrong: "Strong",
      showPassword: "Show password",
      hidePassword: "Hide password",
      loading: "Please wait...",
      errors: {
        name: "Enter your full name (at least 2 characters).",
        emailRequired: "Enter your email address.",
        emailInvalid: "Enter a valid email address.",
        passwordRequired: "Enter your password.",
        passwordShort: "Use at least 8 characters.",
        confirm: "Passwords do not match.",
        terms: "Please accept the Terms and Privacy Policy."
      },
      unavailable: "Account service is not connected yet. No information was sent.",
      providerUnavailable: "This sign-in provider is not connected yet.",
      requestFailed: "We could not complete your request. Please try again.",
      registerSuccess: "Registration successful. You can now sign in.",
      loginSuccess: "Signed in successfully."
    },
    vi: {
      eyebrow: "TÀI KHOẢN EDUHUB",
      registerTitle: "Tạo tài khoản",
      loginTitle: "Chào mừng bạn quay lại",
      intro: "Lưu tiến độ học tập và quản lý việc học tại một nơi.",
      loginIntro: "Đăng nhập để tiếp tục học.",
      google: "Tiếp tục với Google",
      facebook: "Tiếp tục với Facebook",
      orEmail: "hoặc tiếp tục bằng email",
      fullName: "Họ và tên",
      email: "Địa chỉ email",
      password: "Mật khẩu",
      confirmPassword: "Nhập lại mật khẩu",
      namePlaceholder: "Nhập họ và tên",
      emailPlaceholder: "ban@example.com",
      passwordPlaceholder: "Ít nhất 8 ký tự",
      confirmPlaceholder: "Nhập lại mật khẩu",
      terms: "Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật.",
      createAccount: "Tạo tài khoản",
      signInSubmit: "Đăng nhập",
      haveAccount: "Đã có tài khoản?",
      needAccount: "Mới đến Eduhub?",
      signIn: "Đăng nhập ngay",
      signUp: "Tạo tài khoản",
      strengthEmpty: "Mật khẩu cần ít nhất 8 ký tự",
      strengthWeak: "Yếu",
      strengthFair: "Trung bình",
      strengthGood: "Tốt",
      strengthStrong: "Mạnh",
      showPassword: "Hiện mật khẩu",
      hidePassword: "Ẩn mật khẩu",
      loading: "Đang xử lý...",
      errors: {
        name: "Vui lòng nhập họ tên (ít nhất 2 ký tự).",
        emailRequired: "Vui lòng nhập địa chỉ email.",
        emailInvalid: "Vui lòng nhập email hợp lệ.",
        passwordRequired: "Vui lòng nhập mật khẩu.",
        passwordShort: "Mật khẩu cần ít nhất 8 ký tự.",
        confirm: "Mật khẩu không trùng khớp.",
        terms: "Vui lòng đồng ý với Điều khoản và Chính sách bảo mật."
      },
      unavailable: "Dịch vụ tài khoản chưa được kết nối. Chưa có thông tin nào được gửi đi.",
      providerUnavailable: "Phương thức đăng nhập này chưa được kết nối.",
      requestFailed: "Không thể hoàn tất yêu cầu. Vui lòng thử lại.",
      registerSuccess: "Đăng ký thành công. Bạn có thể đăng nhập.",
      loginSuccess: "Đăng nhập thành công."
    }
  };

  const fields = {
    name: document.getElementById("accountName"),
    email: document.getElementById("accountEmail"),
    password: document.getElementById("accountPassword"),
    confirmPassword: document.getElementById("accountConfirmPassword"),
    terms: document.getElementById("accountTerms")
  };
  const errors = {
    name: document.getElementById("accountNameError"),
    email: document.getElementById("accountEmailError"),
    password: document.getElementById("accountPasswordError"),
    confirmPassword: document.getElementById("accountConfirmPasswordError"),
    terms: document.getElementById("accountTermsError")
  };
  const submitButton = form.querySelector(".registration-submit");
  const status = document.getElementById("accountStatus");
  const config = window.EDUHUB_AUTH_CONFIG || {};
  let mode = "register";
  let previousFocus = null;

  function locale() {
    return document.documentElement.lang.toLowerCase().startsWith("vi") ? "vi" : "en";
  }

  function message(key) {
    return translations[locale()][key];
  }

  function applyLanguage() {
    const dictionary = translations[locale()];
    modal.querySelectorAll("[data-auth-copy]").forEach(function (element) {
      const key = element.dataset.authCopy;
      if (dictionary[key]) element.textContent = dictionary[key];
    });
    modal.querySelectorAll("[data-auth-placeholder]").forEach(function (element) {
      const key = element.dataset.authPlaceholder;
      if (dictionary[key]) element.placeholder = dictionary[key];
    });
    modal.querySelectorAll("[data-toggle-password]").forEach(function (button) {
      const input = document.getElementById(button.dataset.togglePassword);
      button.setAttribute("aria-label", input.type === "password" ? dictionary.showPassword : dictionary.hidePassword);
    });
    updateMode();
    updateStrength();
    Object.keys(errors).forEach(function (key) {
      if (fields[key].dataset.touched === "true") validateField(key);
    });
  }

  function clearErrors() {
    Object.keys(errors).forEach(function (key) {
      errors[key].textContent = "";
      fields[key].removeAttribute("aria-invalid");
    });
  }

  function setError(key, text) {
    errors[key].textContent = text || "";
    if (text) fields[key].setAttribute("aria-invalid", "true");
    else fields[key].removeAttribute("aria-invalid");
    return !text;
  }

  function validateField(key) {
    const localized = translations[locale()];
    if (key === "name" && mode === "register") {
      const name = fields.name.value.trim();
      return setError("name", name.length >= 2 ? "" : localized.errors.name);
    }
    if (key === "email") {
      const email = fields.email.value.trim();
      if (!email) return setError("email", localized.errors.emailRequired);
      return setError("email", /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? "" : localized.errors.emailInvalid);
    }
    if (key === "password") {
      const password = fields.password.value;
      if (!password) return setError("password", localized.errors.passwordRequired);
      if (mode === "register" && password.length < 8) return setError("password", localized.errors.passwordShort);
      return setError("password", "");
    }
    if (key === "confirmPassword" && mode === "register") {
      const matches = fields.confirmPassword.value === fields.password.value && fields.confirmPassword.value.length > 0;
      return setError("confirmPassword", matches ? "" : localized.errors.confirm);
    }
    if (key === "terms" && mode === "register") {
      return setError("terms", fields.terms.checked ? "" : localized.errors.terms);
    }
    return true;
  }

  function validateAll() {
    const keys = mode === "register"
      ? ["name", "email", "password", "confirmPassword", "terms"]
      : ["email", "password"];
    return keys.map(validateField).every(Boolean);
  }

  function updateStrength() {
    const strength = modal.querySelector(".password-strength");
    const password = fields.password.value;
    let score = 0;
    if (password.length >= 8) score += 1;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
    if (/\d/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    strength.dataset.strength = String(score);
    const localized = translations[locale()];
    const strengthKey = ["strengthEmpty", "strengthWeak", "strengthFair", "strengthGood", "strengthStrong"][score];
    strength.querySelector(".password-strength-label").textContent = localized[strengthKey];
  }

  function updateMode() {
    const isLogin = mode === "login";
    modal.classList.toggle("is-login", isLogin);
    modal.querySelector("#registrationTitle").textContent = message(isLogin ? "loginTitle" : "registerTitle");
    modal.querySelector(".registration-intro").textContent = message(isLogin ? "loginIntro" : "intro");
    modal.querySelectorAll("[data-register-only]").forEach(function (element) {
      element.hidden = isLogin;
    });
    modal.querySelector(".registration-switch [data-auth-copy]").textContent = message(isLogin ? "needAccount" : "haveAccount");
    modal.querySelector("[data-switch-auth-mode]").textContent = message(isLogin ? "signUp" : "signIn");
    submitButton.querySelector("span").textContent = message(isLogin ? "signInSubmit" : "createAccount");
    fields.password.autocomplete = isLogin ? "current-password" : "new-password";
    fields.confirmPassword.autocomplete = "new-password";
    clearErrors();
    status.textContent = "";
    status.className = "registration-status";
  }

  function showStatus(text, type) {
    status.textContent = text;
    status.className = "registration-status" + (type ? " is-" + type : "");
  }

  function openModal() {
    previousFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("registration-open");
    updateMode();
    applyLanguage();
    fields[mode === "register" ? "name" : "email"].focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove("registration-open");
    if (previousFocus) previousFocus.focus();
  }

  async function submitToApi() {
    const endpoint = mode === "register" ? config.registerEndpoint : config.loginEndpoint;
    if (!endpoint) {
      showStatus(message("unavailable"), "error");
      return;
    }

    const originalLabel = message(mode === "register" ? "createAccount" : "signInSubmit");
    submitButton.disabled = true;
    submitButton.querySelector("span").textContent = message("loading");
    showStatus("", "");

    const payload = {
      email: fields.email.value.trim(),
      password: fields.password.value
    };
    if (mode === "register") payload.name = fields.name.value.trim();

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error("request-failed");
      showStatus(message(mode === "register" ? "registerSuccess" : "loginSuccess"), "success");
      form.reset();
      updateStrength();
      clearErrors();
    } catch (error) {
      showStatus(message("requestFailed"), "error");
    } finally {
      submitButton.disabled = false;
      submitButton.querySelector("span").textContent = originalLabel;
    }
  }

  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-open-registration]")) {
      event.preventDefault();
      mode = "register";
      openModal();
    }
    if (event.target.closest("[data-close-registration]")) closeModal();
    if (event.target.closest("[data-switch-auth-mode]")) {
      mode = mode === "register" ? "login" : "register";
      updateMode();
      applyLanguage();
      fields[mode === "register" ? "name" : "email"].focus();
    }
    const visibilityButton = event.target.closest("[data-toggle-password]");
    if (visibilityButton) {
      const input = document.getElementById(visibilityButton.dataset.togglePassword);
      input.type = input.type === "password" ? "text" : "password";
      const icon = visibilityButton.querySelector("i");
      icon.classList.toggle("fa-eye", input.type === "password");
      icon.classList.toggle("fa-eye-slash", input.type === "text");
      visibilityButton.setAttribute("aria-label", message(input.type === "password" ? "showPassword" : "hidePassword"));
    }
    const providerButton = event.target.closest("[data-social-provider]");
    if (providerButton) {
      const providers = config.socialProviders || {};
      const providerUrl = providers[providerButton.dataset.socialProvider];
      if (providerUrl) window.location.assign(providerUrl);
      else showStatus(message("providerUnavailable"), "error");
    }
  });

  form.addEventListener("input", function (event) {
    const field = event.target;
    const key = Object.keys(fields).find(function (fieldKey) { return fields[fieldKey] === field; });
    if (!key) return;
    field.dataset.touched = "true";
    validateField(key);
    if (key === "password") {
      updateStrength();
      if (fields.confirmPassword.dataset.touched === "true") validateField("confirmPassword");
    }
  });

  form.addEventListener("change", function (event) {
    if (event.target === fields.terms) {
      fields.terms.dataset.touched = "true";
      validateField("terms");
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!validateAll()) {
      const firstInvalid = form.querySelector('[aria-invalid="true"]');
      if (firstInvalid) firstInvalid.focus();
      return;
    }
    submitToApi();
  });

  document.addEventListener("keydown", function (event) {
    if (modal.hidden) return;
    if (event.key === "Escape") closeModal();
    if (event.key === "Tab") {
      const focusable = Array.from(modal.querySelectorAll("button:not(:disabled), input:not(:disabled), a[href]"))
        .filter(function (element) { return !element.closest("[hidden]"); });
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });

  document.addEventListener("site-language-change", applyLanguage);
  applyLanguage();
})();