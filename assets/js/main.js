const backToTop = document.querySelector('.back-to-top');

document.querySelectorAll('[data-course-id][href="#"]').forEach(function (courseLink) {
  courseLink.setAttribute('aria-disabled', 'true');
  courseLink.title = 'Registration temporarily unavailable';
});

document.addEventListener('click', function (event) {
  const courseLink = event.target.closest('[data-course-id][href="#"]');
  if (courseLink) {
    event.preventDefault();
  }
});

document.addEventListener('scroll', function () {
  if (window.scrollY > 500) {
    backToTop.style.display = 'inline-block';
  } else {
    backToTop.style.display = 'none';
  }
});

backToTop.addEventListener('click', () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  });
});

const bookGrid = document.querySelector('#book-grid');
const bookSearch = document.querySelector('#book-search');
const bookFilters = document.querySelectorAll('[data-book-filter]');
const bookResults = document.querySelector('#book-results');
const bookEmpty = document.querySelector('#book-empty');
const booksShowMore = document.querySelector('#books-show-more');
const langToggle = document.querySelector('#langToggle');

const translations = {
  vi: {
    'nav.categories': 'Danh mục',
    'nav.login': 'Đăng nhập',
    'search.submit': 'Tìm kiếm',
    'search.label': 'Tìm khóa học, sách và quiz',
    'search.placeholder': 'Tìm khóa học, sách, bài tập...',
    'menu.heading': 'Chọn cách học phù hợp',
    'menu.allCourses': 'Xem tất cả <span aria-hidden="true">↗</span>',
    'menu.recorded': 'Khóa học quay sẵn',
    'menu.recordedText': 'Học theo nhịp độ của riêng bạn.',
    'menu.zoom': 'Khóa học qua Zoom',
    'menu.zoomText': 'Bắt đầu với lộ trình học có hướng dẫn.',
    'menu.booksText': 'Tài liệu được tuyển chọn cho lập trình viên.',
    'menu.quizText': 'Thử sức với các bộ câu hỏi lập trình.',
    'nav.books': 'Sách',
    'nav.articles': 'Bài viết',
    'nav.write': 'Viết bài',
    'nav.courses': 'Khóa học',
    'nav.start': 'Bắt đầu học',
    'nav.quiz': 'Quiz',
    'nav.signup': 'Đăng ký',
    'nav.support': 'Ủng hộ',
    'hero.ready': 'BẠN ĐÃ SẴN SÀNG HỌC CHƯA?',
    'hero.heading': 'Học thật vui <br> theo <span>lịch của bạn</span>',
    'hero.text': 'Lập trình đang là một trong những lĩnh vực phát triển mạnh mẽ. Hãy học lập trình để nắm bắt cơ hội nghề nghiệp trong ngành công nghệ đang có nhu cầu nhân lực cao.',
    'hero.quiz': 'BÀI KIỂM TRA',
    'hero.support': 'ỦNG HỘ',
    'carousel.label': 'Khóa học nổi bật',
    'carousel.cppEyebrow': 'LẬP TRÌNH C++',
    'carousel.cppTitle': 'Bắt đầu hành trình lập trình của bạn',
    'carousel.cppText': 'Nắm vững nền tảng C++ qua những bài học dễ hiểu và thực hành từng bước.',
    'carousel.javaEyebrow': 'LẬP TRÌNH JAVA',
    'carousel.javaTitle': 'Chinh phục Java từ những bước đầu tiên',
    'carousel.javaText': 'Học tư duy hướng đối tượng và xây dựng nền tảng vững chắc cho ứng dụng thực tế.',
    'carousel.pythonEyebrow': 'LẬP TRÌNH PYTHON',
    'carousel.pythonTitle': 'Khám phá Python qua những dự án thực tế',
    'carousel.pythonText': 'Học Python với các bài thực hành trực quan, từ nền tảng đến ứng dụng thực tế.',
    'carousel.cta': 'Khám phá ngay',
    'carousel.previous': 'Trang trước',
    'carousel.next': 'Trang tiếp theo',
    'carousel.indicators': 'Chọn khóa học',
    'carousel.goToCpp': 'Đến khóa học C++',
    'carousel.goToJava': 'Đến khóa học Java',
    'carousel.goToPython': 'Đến khóa học Python',
    'books.eyebrow': 'GÓC SÁCH LẬP TRÌNH',
    'books.title': 'Sách hay cho hành trình lập trình',
    'books.subtitle': 'Tìm cuốn sách phù hợp và bắt đầu học theo cách của bạn.',
    'books.searchLabel': 'Tìm sách theo tên hoặc tác giả',
    'books.filterAll': 'Tất cả',
    'books.filterPython': 'Python',
    'books.filterJava': 'Java',
    'books.filterWeb': 'Web',
    'books.filterCs': 'Khoa học máy tính',
    'courses.title': 'Các khóa học trực tuyến',
    'course.cppTitle': 'C++ từ cơ bản đến nâng cao',
    'course.cppText': 'Bắt đầu học lập trình C++'
  },
  en: {
    'nav.categories': 'Categories',
    'nav.login': 'Log in',
    'search.submit': 'Search',
    'search.label': 'Search courses, books, and quizzes',
    'search.placeholder': 'Search courses, books, exercises...',
    'menu.heading': 'Choose how you want to learn',
    'menu.allCourses': 'Browse all <span aria-hidden="true">↗</span>',
    'menu.recorded': 'Recorded courses',
    'menu.recordedText': 'Learn at your own pace.',
    'menu.zoom': 'Live courses on Zoom',
    'menu.zoomText': 'Follow a guided learning path.',
    'menu.booksText': 'Curated resources for developers.',
    'menu.quizText': 'Practice with programming quizzes.',
    'nav.books': 'Books',
    'nav.articles': 'Articles',
    'nav.write': 'Write',
    'nav.courses': 'Courses',
    'nav.start': 'Start learning',
    'nav.quiz': 'Quiz',
    'nav.signup': 'Sign up',
    'nav.support': 'Support',
    'hero.ready': 'READY TO START LEARNING?',
    'hero.heading': 'Learn with joy <br> on <span>your schedule</span>',
    'hero.text': 'Programming is one of the fastest-growing career fields. Learn to code and seize the opportunities in a technology industry with strong demand for skilled developers.',
    'hero.quiz': 'TAKE QUIZ',
    'hero.support': 'SUPPORT',
    'carousel.label': 'Featured courses',
    'carousel.cppEyebrow': 'C++ PROGRAMMING',
    'carousel.cppTitle': 'Start your programming journey',
    'carousel.cppText': 'Build a strong C++ foundation with clear lessons and hands-on practice.',
    'carousel.javaEyebrow': 'JAVA PROGRAMMING',
    'carousel.javaTitle': 'Master Java from the very beginning',
    'carousel.javaText': 'Learn object-oriented thinking and build a solid foundation for real-world applications.',
    'carousel.pythonEyebrow': 'PYTHON PROGRAMMING',
    'carousel.pythonTitle': 'Explore Python through real-world projects',
    'carousel.pythonText': 'Learn Python with hands-on lessons, from the fundamentals to practical applications.',
    'carousel.cta': 'Explore now',
    'carousel.previous': 'Previous slide',
    'carousel.next': 'Next slide',
    'carousel.indicators': 'Choose a course',
    'carousel.goToCpp': 'Go to C++ course',
    'carousel.goToJava': 'Go to Java course',
    'carousel.goToPython': 'Go to Python course',
    'books.eyebrow': 'PROGRAMMING BOOKS',
    'books.title': 'Great books for your coding journey',
    'books.subtitle': 'Find the right book and start learning your own way.',
    'books.searchLabel': 'Search by title or author',
    'books.filterAll': 'All',
    'books.filterPython': 'Python',
    'books.filterJava': 'Java',
    'books.filterWeb': 'Web',
    'books.filterCs': 'Computer Science',
    'courses.title': 'Online courses',
    'course.cppTitle': 'C++ from beginner to advanced',
    'course.cppText': 'Start learning C++ programming'
  }
};

function applyTranslations(lang) {
  const translationSet = translations[lang] || translations.vi;
  document.documentElement.lang = lang;

  document.querySelectorAll('[data-i18n], [data-i18n-aria-label]').forEach((element) => {
    const key = element.dataset.i18n;
    const value = translationSet[key];

    if (key && value) {
      element.innerHTML = value;
    }

    const ariaLabelKey = element.dataset.i18nAriaLabel;
    if (ariaLabelKey && translationSet[ariaLabelKey]) {
      element.setAttribute('aria-label', translationSet[ariaLabelKey]);
    }

    const placeholderKey = element.dataset.i18nPlaceholder;
    if (placeholderKey && translationSet[placeholderKey]) {
      element.setAttribute('placeholder', translationSet[placeholderKey]);
    }
  });

  if (langToggle) {
    langToggle.textContent = lang === 'vi' ? 'EN' : 'VI';
    langToggle.setAttribute('aria-label', lang === 'vi' ? 'Switch to English' : 'Chuyển sang tiếng Việt');
  }
}

if (langToggle) {
  let currentLang = 'vi';

  langToggle.addEventListener('click', () => {
    currentLang = currentLang === 'vi' ? 'en' : 'vi';
    applyTranslations(currentLang);
  });

  applyTranslations(currentLang);
}

const courseCarousel = document.querySelector('#course-carousel');

if (courseCarousel) {
  const slides = Array.from(courseCarousel.querySelectorAll('.course-slide'));
  const indicators = Array.from(courseCarousel.querySelectorAll('[data-slide-to]'));
  const previousButton = courseCarousel.querySelector('.course-carousel__arrow--prev');
  const nextButton = courseCarousel.querySelector('.course-carousel__arrow--next');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let activeSlide = 0;
  let autoplayTimer;
  let isHovered = false;
  let isFocused = false;

  function stopAutoplay() {
    window.clearInterval(autoplayTimer);
    autoplayTimer = undefined;
  }

  function startAutoplay() {
    stopAutoplay();
    if (slides.length < 2 || isHovered || isFocused || document.hidden || reducedMotion.matches) return;

    autoplayTimer = window.setInterval(() => {
      setActiveSlide(activeSlide + 1);
    }, 4500);
  }

  function setActiveSlide(index) {
    activeSlide = (index + slides.length) % slides.length;
    const activeImage = slides[activeSlide].querySelector('.banner-bg');
    if (activeImage && activeImage.loading === 'lazy') {
      activeImage.loading = 'eager';
    }

    slides.forEach((slide, slideIndex) => {
      const isActive = slideIndex === activeSlide;
      slide.classList.toggle('is-active', isActive);
      slide.setAttribute('aria-hidden', String(!isActive));
    });

    indicators.forEach((indicator, indicatorIndex) => {
      const isActive = indicatorIndex === activeSlide;
      indicator.classList.toggle('is-active', isActive);
      indicator.setAttribute('aria-pressed', String(isActive));
    });
  }

  previousButton.addEventListener('click', () => {
    setActiveSlide(activeSlide - 1);
    startAutoplay();
  });

  nextButton.addEventListener('click', () => {
    setActiveSlide(activeSlide + 1);
    startAutoplay();
  });

  indicators.forEach((indicator) => {
    indicator.addEventListener('click', () => {
      setActiveSlide(Number(indicator.dataset.slideTo));
      startAutoplay();
    });
  });

  courseCarousel.addEventListener('mouseenter', () => {
    isHovered = true;
    stopAutoplay();
  });

  courseCarousel.addEventListener('mouseleave', () => {
    isHovered = false;
    startAutoplay();
  });

  courseCarousel.addEventListener('focusin', () => {
    isFocused = true;
    stopAutoplay();
  });

  courseCarousel.addEventListener('focusout', (event) => {
    if (!courseCarousel.contains(event.relatedTarget)) {
      isFocused = false;
      startAutoplay();
    }
  });

  document.addEventListener('visibilitychange', startAutoplay);
  reducedMotion.addEventListener('change', startAutoplay);
  startAutoplay();
}

if (bookGrid && bookSearch && bookResults && bookEmpty && bookFilters.length) {
  const bookCards = Array.from(bookGrid.querySelectorAll('.book-card'));
  let activeCategory = 'all';
  let booksExpanded = false;

  if (bookCards.length === 0) {
    bookResults.hidden = true;
    bookEmpty.hidden = true;
  }

  function filterBooks() {
    const searchTerm = bookSearch.value.trim().toLocaleLowerCase();
    const matchingCards = [];

    bookCards.forEach((card) => {
      const matchesCategory =
        activeCategory === 'all' || card.dataset.category === activeCategory;
      const searchableText =
        `${card.dataset.title} ${card.dataset.author}`.toLocaleLowerCase();
      const matchesSearch = searchableText.includes(searchTerm);
      if (matchesCategory && matchesSearch) matchingCards.push(card);
    });

    matchingCards.forEach((card, index) => {
      card.hidden = !booksExpanded && index >= 4;
    });
    const visibleCount = matchingCards.length;
    bookResults.textContent = `Tìm thấy ${visibleCount} trong ${bookCards.length} cuốn sách`;
    bookResults.hidden = bookCards.length === 0;
    bookEmpty.hidden = bookCards.length === 0 || visibleCount > 0;

    if (booksShowMore) {
      booksShowMore.hidden = visibleCount <= 4;
      booksShowMore.setAttribute('aria-expanded', String(booksExpanded));
      booksShowMore.textContent = document.documentElement.lang === 'en'
        ? (booksExpanded ? 'Show fewer books' : `Show ${visibleCount - 4} more books`)
        : (booksExpanded ? 'Thu gọn' : `Xem thêm ${visibleCount - 4} sách`);
    }
  }

  bookFilters.forEach((filter) => {
    filter.addEventListener('click', () => {
      activeCategory = filter.dataset.bookFilter;
      bookFilters.forEach((button) => {
        const isActive = button === filter;
        button.classList.toggle('is-active', isActive);
        button.setAttribute('aria-pressed', String(isActive));
      });
      filterBooks();
    });
  });

  bookSearch.addEventListener('input', filterBooks);
  booksShowMore?.addEventListener('click', () => {
    booksExpanded = !booksExpanded;
    filterBooks();
    if (!booksExpanded) {
      document.querySelector('#books .books-heading')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
  filterBooks();
}
