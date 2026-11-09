(function () {
  const storageKey = "eduhub-study-timer-v1";
  const timer = document.createElement("aside");
  timer.className = "study-timer";
  timer.setAttribute("aria-label", "Study time tracker");
  timer.innerHTML = '<span class="study-timer-icon" aria-hidden="true">⏱️</span><div class="study-timer-readout"><span class="study-timer-label">Study time:</span><output class="study-timer-value" aria-live="off">00:00:00</output></div><button class="study-timer-toggle" type="button">Pause</button><button class="study-timer-action study-timer-reset" type="button">↻</button><button class="study-timer-action study-timer-hide" type="button">−</button><button class="study-timer-show" type="button" hidden>⏱️</button>';
  document.body.appendChild(timer);

  const output = timer.querySelector(".study-timer-value");
  const toggle = timer.querySelector(".study-timer-toggle");
  const resetButton = timer.querySelector(".study-timer-reset");
  const hideButton = timer.querySelector(".study-timer-hide");
  const showButton = timer.querySelector(".study-timer-show");
  let totalMilliseconds = 0;
  let paused = false;
  let timerHidden = false;
  let activeSince = null;

  function readState() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      if (saved && Number.isFinite(saved.totalMilliseconds) && saved.totalMilliseconds >= 0) {
        totalMilliseconds = saved.totalMilliseconds;
        paused = saved.paused === true;
        timerHidden = saved.hidden === true;
      }
    } catch (error) {
      totalMilliseconds = 0;
      paused = false;
    }
  }

  function elapsedAt(now) {
    return totalMilliseconds + (activeSince === null ? 0 : Math.max(0, now - activeSince));
  }

  function persist(now) {
    totalMilliseconds = elapsedAt(now);
    activeSince = paused || document.hidden ? null : now;
    try {
      localStorage.setItem(storageKey, JSON.stringify({
        totalMilliseconds: totalMilliseconds,
        paused: paused,
        hidden: timerHidden
      }));
    } catch (error) {
      // Keep the timer usable for this visit if browser storage is unavailable.
    }
  }

  function formatTime(milliseconds) {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return [hours, minutes, seconds].map(function (value) {
      return String(value).padStart(2, "0");
    }).join(":");
  }

  function render(now) {
    const isVietnamese = document.documentElement.lang.toLowerCase().startsWith("vi");
    const pauseLabel = paused
      ? (isVietnamese ? "Tiếp tục" : "Resume")
      : (isVietnamese ? "Tạm dừng" : "Pause");
    output.value = formatTime(elapsedAt(now));
    output.textContent = output.value;
    toggle.textContent = pauseLabel;
    toggle.setAttribute("aria-label", isVietnamese ? pauseLabel + " đếm thời gian học" : pauseLabel + " study timer");
    toggle.setAttribute("aria-pressed", String(paused));
    timer.classList.toggle("is-paused", paused);
    timer.classList.toggle("is-hidden", timerHidden);
    timer.setAttribute("aria-label", isVietnamese ? "Bộ đếm thời gian học" : "Study time tracker");
    resetButton.title = isVietnamese ? "Đặt lại thời gian" : "Reset time";
    resetButton.setAttribute("aria-label", resetButton.title);
    hideButton.title = isVietnamese ? "Ẩn đồng hồ" : "Hide timer";
    hideButton.setAttribute("aria-label", hideButton.title);
    showButton.hidden = !timerHidden;
    showButton.title = isVietnamese ? "Hiện đồng hồ" : "Show timer";
    showButton.setAttribute("aria-label", showButton.title);
  }

  readState();
  if (!paused && !document.hidden) activeSince = Date.now();
  render(Date.now());

  toggle.addEventListener("click", function () {
    const now = Date.now();
    if (paused) {
      paused = false;
      activeSince = document.hidden ? null : now;
    } else {
      totalMilliseconds = elapsedAt(now);
      paused = true;
      activeSince = null;
    }
    persist(now);
    render(now);
  });

  resetButton.addEventListener("click", function () {
    const now = Date.now();
    totalMilliseconds = 0;
    activeSince = paused || document.hidden ? null : now;
    persist(now);
    render(now);
  });

  hideButton.addEventListener("click", function () {
    timerHidden = true;
    persist(Date.now());
    render(Date.now());
  });

  showButton.addEventListener("click", function () {
    timerHidden = false;
    persist(Date.now());
    render(Date.now());
  });

  document.addEventListener("visibilitychange", function () {
    const now = Date.now();
    if (document.hidden) {
      persist(now);
    } else if (!paused) {
      activeSince = now;
    }
    render(now);
  });

  window.addEventListener("beforeunload", function () {
    persist(Date.now());
  });

  window.addEventListener("storage", function (event) {
    if (event.key !== storageKey || !event.newValue) return;
    try {
      const saved = JSON.parse(event.newValue);
      if (!Number.isFinite(saved.totalMilliseconds) || saved.totalMilliseconds < 0) return;
      totalMilliseconds = saved.totalMilliseconds;
      paused = saved.paused === true;
      timerHidden = saved.hidden === true;
      activeSince = paused || document.hidden ? null : Date.now();
      render(Date.now());
    } catch (error) {
      // Ignore invalid state written by another tab.
    }
  });

  window.setInterval(function () {
    const now = Date.now();
    persist(now);
    render(now);
  }, 1000);
})();