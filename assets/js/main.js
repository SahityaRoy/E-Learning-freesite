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
const langToggle = document.querySelector('#langToggle');

const translations = {
  vi: {
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

  document.querySelectorAll('[data-i18n]').forEach((element) => {
    const key = element.dataset.i18n;
    const value = translationSet[key];
    if (!value) return;

    element.innerHTML = value;
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

if (bookGrid && bookSearch && bookResults && bookEmpty && bookFilters.length) {
  const bookCards = Array.from(bookGrid.querySelectorAll('.book-card'));
  let activeCategory = 'all';

  function filterBooks() {
    const searchTerm = bookSearch.value.trim().toLocaleLowerCase();
    let visibleCount = 0;

    bookCards.forEach((card) => {
      const matchesCategory =
        activeCategory === 'all' || card.dataset.category === activeCategory;
      const searchableText =
        `${card.dataset.title} ${card.dataset.author}`.toLocaleLowerCase();
      const matchesSearch = searchableText.includes(searchTerm);
      const isVisible = matchesCategory && matchesSearch;

      card.hidden = !isVisible;
      if (isVisible) visibleCount += 1;
    });

    bookResults.textContent = `Hiển thị ${visibleCount} trong ${bookCards.length} cuốn sách`;
    bookEmpty.hidden = visibleCount > 0;
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
  filterBooks();
}
