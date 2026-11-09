const catalogStorageKey = 'eduhubExamCatalog';
const defaultExams = [
  { id: 'html-foundations', title: 'Nền tảng HTML & CSS', subject: 'HTML & CSS', questionCount: 5, duration: 12, description: 'Cấu trúc trang, semantic HTML và các nguyên tắc CSS.' },
  { id: 'javascript-basics', title: 'JavaScript căn bản', subject: 'JavaScript', questionCount: 6, duration: 15, description: 'Biến, kiểu dữ liệu, hàm và các thao tác với mảng.' },
  { id: 'programming-logic', title: 'Tư duy lập trình', subject: 'Lập trình', questionCount: 5, duration: 15, description: 'Thuật toán, vòng lặp, độ phức tạp và tư duy giải quyết vấn đề.' },
];
const knownExamIds = new Set(defaultExams.map((exam) => exam.id));
const examTableBody = document.getElementById('examTableBody');
const examForm = document.getElementById('examForm');
const examDialog = document.getElementById('examDialog');
const questionCountInput = document.getElementById('examQuestionCount');
let exams = loadExams();

async function renderQuizAnalytics() {
  const status = document.getElementById('quizAnalyticsStatus');
  const metrics = document.getElementById('quizAnalyticsMetrics');
  const examStats = document.getElementById('quizExamStats');
  const recentAttempts = document.getElementById('quizRecentAttempts');
  if (!status || !metrics || !examStats || !recentAttempts) return;

  status.textContent = 'Đang tải số liệu...';
  try {
    const response = await fetch('/api/admin/quiz/statistics', { credentials: 'same-origin' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Không thể tải thống kê.');
    const summary = data.summary;
    const accuracy = summary.total_questions
      ? Math.round(summary.correct_count / summary.total_questions * 100)
      : 0;
    const metricItems = [
      ['Tổng lượt thi', summary.attempts, 'Đã nộp trên hệ thống'],
      ['Điểm trung bình', `${summary.average_score}%`, 'Trên thang điểm 100'],
      ['Tài khoản có lượt thi', summary.learners, 'Chỉ dữ liệu chi tiết còn lưu'],
      ['Tỷ lệ câu đúng', `${accuracy}%`, 'Tính trên mọi lượt thi'],
    ];
    metrics.innerHTML = metricItems.map(([label, value, caption]) => `
      <article class="analytics-metric"><span>${label}</span><strong>${value}</strong><small>${caption}</small></article>
    `).join('');

    status.textContent = summary.attempts ? `Đã ghi nhận ${summary.attempts} lượt nộp bài.` : 'Chưa có lượt nộp bài nào trên hệ thống.';
    examStats.innerHTML = data.exams.length ? data.exams.map((exam) => `
      <article class="exam-stat-row">
        <div class="exam-stat-copy"><strong>${escapeHtml(exam.exam_title)}</strong><small>${escapeHtml(exam.subject)} · ${exam.attempts} lượt · cao nhất ${exam.best_score}%</small></div>
        <div class="exam-stat-score"><span>${exam.average_score}%</span><div class="exam-stat-track"><i style="width:${Math.max(0, Math.min(100, Number(exam.average_score) || 0))}%"></i></div></div>
      </article>
    `).join('') : '<p class="analytics-empty">Chưa có dữ liệu theo đề thi.</p>';

    recentAttempts.innerHTML = data.recent.length ? data.recent.map((attempt) => `
      <tr><td>${escapeHtml(attempt.learner)}</td><td>${escapeHtml(attempt.exam_title)}<small class="attempt-subject">${escapeHtml(attempt.subject)}</small></td><td><strong>${attempt.score}%</strong><small class="attempt-subject">${attempt.correct_count}/${attempt.total_questions} câu</small></td><td>${escapeHtml(attempt.created_at)}</td></tr>
    `).join('') : '<tr class="empty-row"><td colspan="4">Chưa có lượt nộp bài.</td></tr>';
  } catch (error) {
    status.textContent = error.message;
    metrics.replaceChildren();
    examStats.innerHTML = '';
    recentAttempts.innerHTML = '<tr class="empty-row"><td colspan="4">Không tải được dữ liệu.</td></tr>';
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function loadExams() {
  try {
    const storedExams = JSON.parse(localStorage.getItem(catalogStorageKey));
    if (Array.isArray(storedExams)) return storedExams.filter(isValidExam);
  } catch {
    return [...defaultExams];
  }
  return [...defaultExams];
}

function isValidExam(exam) {
  return exam && typeof exam.id === 'string' && typeof exam.title === 'string' && typeof exam.subject === 'string'
    && Number.isInteger(Number(exam.questionCount)) && Number(exam.questionCount) > 0
    && Number.isInteger(Number(exam.duration)) && Number(exam.duration) > 0;
}

function saveExams() {
  try {
    localStorage.setItem(catalogStorageKey, JSON.stringify(exams));
    return true;
  } catch {
    showFeedback('Không thể lưu dữ liệu trên trình duyệt này.', true);
    return false;
  }
}

function showFeedback(message, isError = false) {
  const feedback = document.getElementById('catalogFeedback');
  feedback.textContent = message;
  feedback.classList.toggle('is-error', isError);
}

function getVisibleExams() {
  const query = document.getElementById('examSearch').value.trim().toLocaleLowerCase('vi');
  const subject = document.getElementById('subjectFilter').value;
  return exams.filter((exam) => {
    const matchesQuery = `${exam.title} ${exam.subject}`.toLocaleLowerCase('vi').includes(query);
    const matchesSubject = subject === 'all' || (subject === 'other'
      ? !['HTML & CSS', 'JavaScript', 'Lập trình'].includes(exam.subject)
      : exam.subject === subject);
    return matchesQuery && matchesSubject;
  });
}

function renderExams() {
  const visibleExams = getVisibleExams();
  document.getElementById('examCount').textContent = `${exams.length} đề thi`;

  if (!visibleExams.length) {
    examTableBody.innerHTML = '<tr class="empty-row"><td colspan="6">Không tìm thấy đề thi phù hợp.</td></tr>';
    return;
  }

  examTableBody.innerHTML = visibleExams.map((exam) => {
    const isQuestionBanked = knownExamIds.has(exam.id);
    return `
      <tr>
        <td class="exam-title-cell"><strong>${escapeHtml(exam.title)}</strong><small>${escapeHtml(exam.description || 'Đề thi mới')}</small></td>
        <td><span class="subject-label">${escapeHtml(exam.subject)}</span></td>
        <td>${Number(exam.questionCount)} câu</td>
        <td>${Number(exam.duration)} phút</td>
        <td><span class="status-label ${isQuestionBanked ? '' : 'draft'}">${isQuestionBanked ? 'Sẵn sàng' : 'Chờ biên soạn câu hỏi'}</span></td>
        <td><div class="row-actions">
          <button class="icon-button edit-exam" type="button" data-id="${escapeHtml(exam.id)}" aria-label="Sửa đề ${escapeHtml(exam.title)}" title="Sửa đề">✎</button>
          <button class="icon-button delete delete-exam" type="button" data-id="${escapeHtml(exam.id)}" aria-label="Xóa đề ${escapeHtml(exam.title)}" title="Xóa đề">×</button>
        </div></td>
      </tr>`;
  }).join('');
}

function openDialog(exam = null) {
  const isEditing = Boolean(exam);
  document.getElementById('dialogTitle').textContent = isEditing ? 'Chỉnh sửa đề thi' : 'Tạo đề thi mới';
  document.getElementById('examTitle').value = exam?.title || '';
  document.getElementById('examSubject').value = exam?.subject || '';
  questionCountInput.value = exam?.questionCount ?? 10;
  questionCountInput.disabled = isEditing && knownExamIds.has(exam.id);
  document.getElementById('questionCountHint').textContent = questionCountInput.disabled
    ? 'Số câu theo ngân hàng câu hỏi hiện có, không thể chỉnh tại đây.'
    : 'Đề mới cần được bổ sung câu hỏi trước khi mở cho sinh viên.';
  document.getElementById('examDuration').value = exam?.duration ?? 15;
  examForm.dataset.editingId = exam?.id || '';
  examDialog.classList.remove('is-hidden');
  examDialog.setAttribute('aria-hidden', 'false');
  document.getElementById('examTitle').focus();
}

function closeDialog() {
  examDialog.classList.add('is-hidden');
  examDialog.setAttribute('aria-hidden', 'true');
  examForm.reset();
  questionCountInput.disabled = false;
  delete examForm.dataset.editingId;
}

function handleSubmit(event) {
  event.preventDefault();
  if (!examForm.reportValidity()) return;

  const editingId = examForm.dataset.editingId;
  const previous = exams.find((exam) => exam.id === editingId);
  const exam = {
    id: editingId || (crypto.randomUUID ? crypto.randomUUID() : `exam-${Date.now()}`),
    title: document.getElementById('examTitle').value.trim(),
    subject: document.getElementById('examSubject').value.trim(),
    questionCount: questionCountInput.disabled ? previous.questionCount : Number(questionCountInput.value),
    duration: Number(document.getElementById('examDuration').value),
    description: previous?.description || '',
  };

  if (!exam.title || !exam.subject || !Number.isInteger(exam.questionCount) || exam.questionCount < 1
      || !Number.isInteger(exam.duration) || exam.duration < 1) return;

  if (editingId) {
    exams = exams.map((item) => item.id === editingId ? exam : item);
  } else {
    exams = [exam, ...exams];
  }

  if (!saveExams()) return;
  renderExams();
  closeDialog();
  showFeedback(editingId ? 'Đã cập nhật đề thi.' : 'Đã tạo đề thi. Đề mới đang chờ biên soạn câu hỏi.');
}

function deleteExam(id) {
  const exam = exams.find((item) => item.id === id);
  if (!exam || !confirm(`Bạn có chắc muốn xóa đề "${exam.title}" không?`)) return;
  exams = exams.filter((item) => item.id !== id);
  if (!saveExams()) return;
  renderExams();
  showFeedback(`Đã xóa đề "${exam.title}".`);
}

document.getElementById('addExamBtn').addEventListener('click', () => openDialog());
document.getElementById('closeDialogBtn').addEventListener('click', closeDialog);
document.getElementById('cancelDialogBtn').addEventListener('click', closeDialog);
examForm.addEventListener('submit', handleSubmit);
examTableBody.addEventListener('click', (event) => {
  const editButton = event.target.closest('.edit-exam');
  const deleteButton = event.target.closest('.delete-exam');
  if (editButton) openDialog(exams.find((exam) => exam.id === editButton.dataset.id));
  if (deleteButton) deleteExam(deleteButton.dataset.id);
});
document.getElementById('examSearch').addEventListener('input', renderExams);
document.getElementById('subjectFilter').addEventListener('change', renderExams);
document.getElementById('refreshQuizAnalytics').addEventListener('click', renderQuizAnalytics);
examDialog.addEventListener('click', (event) => { if (event.target === examDialog) closeDialog(); });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !examDialog.classList.contains('is-hidden')) closeDialog(); });

renderExams();
renderQuizAnalytics();