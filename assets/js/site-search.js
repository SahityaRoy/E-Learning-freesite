(() => {
  const form = document.querySelector('#site-search-form');
  const input = document.querySelector('#site-search-input');
  const results = document.querySelector('#site-search-results');
  const categoryToggle = document.querySelector('#category-toggle');
  const categoryMenu = document.querySelector('#category-menu');
  if (!form || !input || !results || !categoryToggle || !categoryMenu) return;

  const normalize = (value) => String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('vi')
    .trim();
  const books = Array.from(document.querySelectorAll('.book-card')).map((card) => ({
    type: 'SÁCH',
    title: card.dataset.title,
    description: `${card.dataset.author} · ${card.querySelector('.book-category')?.textContent || ''}`,
    href: card.querySelector('.book-action')?.href || '#books',
  }));
  const quizItem = {
    type: 'QUIZ',
    title: 'Quiz trắc nghiệm lập trình',
    description: 'Luyện tập với các bộ đề và xem kết quả ngay sau khi nộp.',
    href: '/quiz.html',
    searchTerms: 'quiz trac nghiem bai tap kiem tra',
  };
  let courses = [];
  let activeOption = -1;

  fetch('/api/courses', { credentials: 'same-origin' })
    .then((response) => response.ok ? response.json() : [])
    .then((items) => {
      courses = items.map((course) => ({
        type: 'KHÓA HỌC',
        title: course.title,
        description: course.description || course.category || 'Khóa học lập trình',
        href: `/courses/${encodeURIComponent(course.id)}`,
      }));
      if (input.value.trim()) renderResults(input.value);
    })
    .catch(() => {});

  function closeResults() {
    results.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    activeOption = -1;
  }

  function closeMenu() {
    categoryMenu.hidden = true;
    categoryToggle.setAttribute('aria-expanded', 'false');
  }

  function createResult(item, index) {
    const link = document.createElement('a');
    link.className = 'search-result';
    link.href = item.href;
    link.id = `site-search-option-${index}`;
    link.setAttribute('role', 'option');
    link.setAttribute('aria-selected', 'false');

    const type = document.createElement('span');
    type.className = 'search-result__type';
    type.textContent = item.type.slice(0, 2);
    const copy = document.createElement('span');
    copy.className = 'search-result__copy';
    const title = document.createElement('strong');
    title.textContent = item.title;
    const description = document.createElement('small');
    description.textContent = item.description;
    copy.append(title, description);
    link.append(type, copy);
    link.addEventListener('click', closeMenu);
    return link;
  }

  function renderResults(query) {
    const term = normalize(query);
    if (term.length < 2) {
      closeResults();
      return;
    }

    const quizMatches = normalize(`${quizItem.title} ${quizItem.searchTerms}`).includes(term);
    const matches = [
      ...courses.filter((item) => normalize(`${item.title} ${item.description}`).includes(term)),
      ...books.filter((item) => normalize(`${item.title} ${item.description}`).includes(term)),
      ...(quizMatches ? [quizItem] : []),
    ].slice(0, 8);
    results.replaceChildren();

    if (!matches.length) {
      const empty = document.createElement('p');
      empty.className = 'search-result-empty';
      empty.textContent = document.documentElement.lang === 'en'
        ? 'No matching courses, books, or quizzes.'
        : 'Không tìm thấy khóa học, sách hoặc quiz phù hợp.';
      results.append(empty);
    } else {
      const groups = new Map();
      matches.forEach((item) => {
        if (!groups.has(item.type)) groups.set(item.type, []);
        groups.get(item.type).push(item);
      });
      let index = 0;
      groups.forEach((items, type) => {
        const group = document.createElement('div');
        group.className = 'search-result-group';
        const heading = document.createElement('p');
        heading.className = 'search-result-heading';
        heading.textContent = type;
        group.append(heading);
        items.forEach((item) => group.append(createResult(item, index++)));
        results.append(group);
      });
    }

    activeOption = -1;
    results.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function setActiveOption(index) {
    const options = Array.from(results.querySelectorAll('[role="option"]'));
    if (!options.length) return;
    activeOption = (index + options.length) % options.length;
    options.forEach((option, optionIndex) => {
      const active = optionIndex === activeOption;
      option.setAttribute('aria-selected', String(active));
      if (active) {
        input.setAttribute('aria-activedescendant', option.id);
        option.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  input.addEventListener('input', () => renderResults(input.value));
  input.addEventListener('focus', () => renderResults(input.value));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowDown' && !results.hidden) {
      event.preventDefault();
      setActiveOption(activeOption + 1);
    } else if (event.key === 'ArrowUp' && !results.hidden) {
      event.preventDefault();
      setActiveOption(activeOption < 0 ? 0 : activeOption - 1);
    } else if (event.key === 'Escape') {
      closeResults();
      closeMenu();
    } else if (event.key === 'Enter' && !results.hidden) {
      const options = results.querySelectorAll('[role="option"]');
      if (options.length) {
        event.preventDefault();
        options[activeOption < 0 ? 0 : activeOption].click();
      }
    }
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const firstOption = results.querySelector('[role="option"]');
    if (firstOption) window.location.assign(firstOption.href);
    else renderResults(input.value);
  });

  categoryToggle.addEventListener('click', () => {
    const open = categoryMenu.hidden;
    categoryMenu.hidden = !open;
    categoryToggle.setAttribute('aria-expanded', String(open));
    closeResults();
  });
  categoryMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  document.addEventListener('click', (event) => {
    if (!form.contains(event.target)) closeResults();
    if (!categoryMenu.contains(event.target) && !categoryToggle.contains(event.target)) closeMenu();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeResults();
      closeMenu();
    }
  });
})();