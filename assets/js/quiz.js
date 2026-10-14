const questionBank = [
  { id: 'html-foundations', title: 'Nền tảng HTML & CSS', subject: 'HTML & CSS', difficulty: 'Cơ bản', duration: 12, description: 'Cấu trúc trang, semantic HTML và các nguyên tắc CSS.', questions: [
    { text: 'Thẻ HTML nào biểu thị nội dung độc lập, có thể tái sử dụng như một bài viết?', options: ['<section>', '<article>', '<aside>', '<span>'], answer: 1, explanation: '<article> dùng cho nội dung độc lập, chẳng hạn bài viết hoặc tin tức.' },
    { text: 'Thuộc tính CSS nào điều khiển khoảng trống bên trong đường viền của phần tử?', options: ['margin', 'gap', 'padding', 'spacing'], answer: 2, explanation: 'padding là khoảng đệm giữa nội dung và đường viền; margin nằm bên ngoài đường viền.' },
    { text: 'Selector nào chọn phần tử có id là "menu"?', options: ['.menu', '#menu', 'menu#', '*menu'], answer: 1, explanation: 'Selector id trong CSS bắt đầu bằng ký tự #.' },
    { text: 'Thuộc tính nào giúp ảnh giữ tỷ lệ khi vừa khung chứa?', options: ['object-fit: cover', 'display: inline', 'position: fixed', 'float: left'], answer: 0, explanation: 'object-fit: cover giữ tỷ lệ ảnh và phủ kín khung, có thể cắt phần ảnh dư.' },
    { text: 'Vai trò chính của thuộc tính alt trên ảnh là gì?', options: ['Tạo viền cho ảnh', 'Đặt kích thước ảnh', 'Cung cấp mô tả thay thế', 'Tải ảnh nhanh hơn'], answer: 2, explanation: 'alt cung cấp văn bản thay thế khi ảnh không tải được và hỗ trợ công nghệ đọc màn hình.' },
  ] },
  { id: 'javascript-basics', title: 'JavaScript căn bản', subject: 'JavaScript', difficulty: 'Cơ bản', duration: 15, description: 'Biến, kiểu dữ liệu, hàm và các thao tác với mảng.', questions: [
    { text: 'Từ khóa nào khai báo biến có thể gán lại giá trị và có phạm vi khối?', options: ['var', 'let', 'const', 'static'], answer: 1, explanation: 'let khai báo biến có phạm vi khối và cho phép gán lại giá trị.' },
    { text: 'Kết quả của biểu thức typeof null trong JavaScript là gì?', options: ['"null"', '"undefined"', '"object"', '"boolean"'], answer: 2, explanation: 'Do đặc điểm lịch sử của JavaScript, typeof null trả về "object".' },
    { text: 'Phương thức nào tạo một mảng mới bằng cách biến đổi từng phần tử?', options: ['filter()', 'map()', 'find()', 'reduceRight()'], answer: 1, explanation: 'map() biến đổi từng phần tử và trả về mảng mới.' },
    { text: 'Toán tử === kiểm tra điều gì?', options: ['Chỉ kiểm tra giá trị', 'Chỉ kiểm tra kiểu', 'Giá trị và kiểu không ép kiểu', 'Giá trị sau khi ép kiểu'], answer: 2, explanation: '=== so sánh cả giá trị lẫn kiểu dữ liệu mà không ép kiểu.' },
    { text: 'Sự kiện nào thường được dùng để phản hồi thao tác nhấn nút?', options: ['submit', 'change', 'click', 'load'], answer: 2, explanation: 'Sự kiện click được phát khi người dùng nhấn vào phần tử.' },
    { text: 'Promise.resolve(5) tạo ra trạng thái nào?', options: ['pending', 'fulfilled', 'rejected', 'cancelled'], answer: 1, explanation: 'Promise.resolve(value) tạo Promise đã hoàn thành thành công với value.' },
  ] },
  { id: 'programming-logic', title: 'Tư duy lập trình', subject: 'Lập trình', difficulty: 'Trung bình', duration: 15, description: 'Thuật toán, vòng lặp, độ phức tạp và tư duy giải quyết vấn đề.', questions: [
    { text: 'Cấu trúc nào lặp lại một khối lệnh khi điều kiện còn đúng?', options: ['if/else', 'while', 'switch', 'return'], answer: 1, explanation: 'while tiếp tục lặp khi điều kiện được đánh giá là đúng.' },
    { text: 'Độ phức tạp thời gian của tìm kiếm tuyến tính trên n phần tử là gì?', options: ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'], answer: 2, explanation: 'Trong trường hợp xấu nhất, tìm kiếm tuyến tính kiểm tra n phần tử.' },
    { text: 'Điều kiện cần để tìm kiếm nhị phân hoạt động đúng trên mảng là gì?', options: ['Mảng có số phần tử chẵn', 'Mảng đã được sắp xếp', 'Mảng không có số âm', 'Mảng không trùng giá trị'], answer: 1, explanation: 'Tìm kiếm nhị phân dựa trên thứ tự đã sắp xếp để loại bỏ một nửa phạm vi.' },
    { text: 'Trong thuật toán, biến đếm thường được dùng để làm gì?', options: ['Đếm số lần lặp hoặc số phần tử', 'Sắp xếp dữ liệu tự động', 'Lưu toàn bộ chương trình', 'Dừng mọi hàm'], answer: 0, explanation: 'Biến đếm theo dõi số lần lặp hoặc số lượng phần tử đã xử lý.' },
    { text: 'Bước đầu tiên hợp lý khi giải một bài toán lập trình mới là gì?', options: ['Viết mã ngay', 'Hiểu đầu vào, đầu ra và yêu cầu', 'Chọn ngôn ngữ phức tạp nhất', 'Tối ưu trước khi có lời giải'], answer: 1, explanation: 'Xác định yêu cầu, dữ liệu đầu vào và kết quả mong muốn trước khi thiết kế lời giải.' },
  ] },
];

function loadExamCatalog() {
  let catalog;
  try {
    catalog = JSON.parse(localStorage.getItem('eduhubExamCatalog'));
  } catch {
    catalog = null;
  }
  if (!Array.isArray(catalog)) return questionBank;

  return catalog.map((metadata) => {
    const bankExam = questionBank.find((exam) => exam.id === metadata.id);
    if (!bankExam) return { ...metadata, questions: [], isDraft: true };
    return {
      ...bankExam,
      title: metadata.title,
      subject: metadata.subject,
      duration: Number(metadata.duration),
      questionCount: bankExam.questions.length,
      isDraft: false,
    };
  });
}

const exams = loadExamCatalog();

const historyKey = 'eduhubExamHistory';
const $ = (selector) => document.querySelector(selector);
const homeView = $('#examHome');
const sessionView = $('#examSession');
const resultView = $('#examResult');
let activeExam = null;
let answers = [];
let questionIndex = 0;
let timerId = null;
let secondsLeft = 0;
let startedAt = 0;
let resultData = null;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function readHistory() {
  try {
    const data = JSON.parse(localStorage.getItem(historyKey));
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function renderExams(subject = 'all') {
  const visible = subject === 'all' ? exams : exams.filter((exam) => exam.subject === subject);
  $('#examList').innerHTML = visible.map((exam, index) => `<article class="exam-card" style="animation-delay:${index * 55}ms"><div class="exam-card-top"><span class="subject-tag">${escapeHtml(exam.subject)}</span><span class="difficulty-tag">${exam.isDraft ? 'Chưa có câu hỏi' : escapeHtml(exam.difficulty)}</span></div><h3>${escapeHtml(exam.title)}</h3><p>${escapeHtml(exam.isDraft ? 'Đề thi đang chờ biên soạn câu hỏi.' : exam.description)}</p><div class="exam-card-foot"><span>${Number(exam.questionCount || exam.questions.length)} câu · ${exam.duration} phút</span><button class="text-button start-exam" type="button" data-exam-id="${escapeHtml(exam.id)}" ${exam.isDraft ? 'disabled title="Đề thi chưa có câu hỏi"' : ''}>${exam.isDraft ? 'Sắp mở' : 'Bắt đầu →'}</button></div></article>`).join('');
}

function renderHistory() {
  const history = readHistory();
  $('#historyCount').textContent = `${history.length} lượt thi`;
  $('#historyList').innerHTML = history.length ? history.slice(0, 5).map((item) => `<article class="history-row"><div class="history-name"><span class="history-mark">${escapeHtml(item.subject.slice(0, 1))}</span><span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.subject)} · ${escapeHtml(item.date)}</small></span></div><span class="history-score">${item.score}%</span></article>`).join('') : '<p class="empty-history">Các lượt thi đã hoàn thành sẽ xuất hiện tại đây.</p>';
}

function showView(view) {
  homeView.classList.toggle('is-hidden', view !== 'home');
  sessionView.classList.toggle('is-hidden', view !== 'session');
  resultView.classList.toggle('is-hidden', view !== 'result');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatTime(seconds) {
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}

function renderTimer() {
  $('#timerValue').textContent = formatTime(secondsLeft);
  $('#examTimer').classList.toggle('is-urgent', secondsLeft <= 60);
}

function startTimer() {
  clearInterval(timerId);
  timerId = setInterval(() => {
    secondsLeft -= 1;
    renderTimer();
    if (secondsLeft <= 0) submitExam(true);
  }, 1000);
}

function beginExam(exam) {
  activeExam = exam;
  answers = Array(exam.questions.length).fill(null);
  questionIndex = 0;
  secondsLeft = exam.duration * 60;
  startedAt = Date.now();
  resultData = null;
  $('#sessionSubject').textContent = exam.subject.toUpperCase();
  $('#sessionTitle').textContent = exam.title;
  renderQuestion();
  renderTimer();
  showView('session');
  startTimer();
}

function renderQuestion() {
  const question = activeExam.questions[questionIndex];
  const answered = answers.filter((answer) => answer !== null).length;
  const percent = Math.round(answered / activeExam.questions.length * 100);
  $('#questionNumber').textContent = `CÂU ${String(questionIndex + 1).padStart(2, '0')}`;
  $('#questionProgress').textContent = `Câu ${questionIndex + 1} / ${activeExam.questions.length}`;
  $('#answeredProgress').textContent = `${answered} câu đã trả lời`;
  $('#railAnsweredCount').textContent = `${answered}/${activeExam.questions.length}`;
  $('.progress-track').setAttribute('aria-valuenow', String(percent));
  $('#progressBar').style.width = `${percent}%`;
  $('#questionText').textContent = question.text;
  $('#answerOptions').innerHTML = `<legend class="sr-only">Chọn đáp án của bạn</legend>${question.options.map((option, index) => `<label class="answer-option"><input type="radio" name="answer" value="${index}" ${answers[questionIndex] === index ? 'checked' : ''}><span class="answer-letter">${String.fromCharCode(65 + index)}</span><span class="answer-copy">${escapeHtml(option)}</span></label>`).join('')}`;
  $('#questionNavigator').innerHTML = activeExam.questions.map((_, index) => `<button class="question-jump ${index === questionIndex ? 'is-current' : ''} ${answers[index] !== null ? 'is-answered' : ''}" type="button" data-question-index="${index}" aria-label="Đi đến câu ${index + 1}" aria-current="${index === questionIndex ? 'step' : 'false'}">${index + 1}</button>`).join('');
  $('#previousQuestionBtn').disabled = questionIndex === 0;
  $('#nextQuestionBtn').disabled = questionIndex === activeExam.questions.length - 1;
}

function submitExam(timedOut = false) {
  if (!activeExam || resultData) return;
  const unanswered = answers.filter((answer) => answer === null).length;
  if (!timedOut && unanswered && !confirm(`Bạn còn ${unanswered} câu chưa trả lời. Vẫn nộp bài?`)) return;
  if (!timedOut && !unanswered && !confirm('Nộp bài thi ngay bây giờ?')) return;
  clearInterval(timerId);
  const correct = activeExam.questions.reduce((count, question, index) => count + (answers[index] === question.answer ? 1 : 0), 0);
  const duration = Math.min(activeExam.duration * 60, Math.floor((Date.now() - startedAt) / 1000));
  const result = { examId: activeExam.id, title: activeExam.title, subject: activeExam.subject, correct, total: activeExam.questions.length, score: Math.round(correct / activeExam.questions.length * 100), duration, date: new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium' }).format(new Date()) };
  resultData = result;
  try {
    localStorage.setItem(historyKey, JSON.stringify([result, ...readHistory()].slice(0, 20)));
  } catch {
    alert('Không thể lưu lịch sử trên trình duyệt này. Kết quả hiện tại vẫn được giữ.');
  }
  renderResult(result, timedOut);
  renderHistory();
  showView('result');
}

function renderResult(result, timedOut) {
  $('#scorePercent').textContent = `${result.score}%`;
  $('#resultSubject').textContent = result.subject.toUpperCase();
  $('#resultHeading').textContent = timedOut ? 'Hết giờ làm bài' : 'Bài làm đã hoàn thành';
  $('#resultMessage').textContent = result.score >= 80 ? 'Làm tốt lắm. Bạn đã nắm khá vững các kiến thức trong bộ đề này.' : 'Hãy xem lại phần giải thích dưới đây và thử sức thêm một lần nữa.';
  $('#correctCount').textContent = result.correct;
  $('#incorrectCount').textContent = result.total - result.correct;
  $('#resultDuration').textContent = formatTime(result.duration);
  $('#answerReview').innerHTML = activeExam.questions.map((question, index) => {
    const correct = answers[index] === question.answer;
    const selected = answers[index] === null ? 'Chưa chọn đáp án' : question.options[answers[index]];
    return `<article class="review-item ${correct ? 'is-correct' : 'is-wrong'}"><div class="review-result-line"><span>${correct ? '✓ Trả lời đúng' : '× Cần xem lại'}</span><strong>Câu ${index + 1}</strong></div><h3>${escapeHtml(question.text)}</h3><p class="review-answer">Bạn chọn: <strong>${escapeHtml(selected)}</strong></p><p class="review-answer">Đáp án đúng: <strong>${escapeHtml(question.options[question.answer])}</strong></p><p class="review-explanation">${escapeHtml(question.explanation)}</p></article>`;
  }).join('');
}

$('#examFilters').addEventListener('click', (event) => {
  const button = event.target.closest('[data-filter]');
  if (!button) return;
  $('#examFilters').querySelectorAll('[data-filter]').forEach((tab) => {
    tab.classList.toggle('active', tab === button);
    tab.setAttribute('aria-pressed', String(tab === button));
  });
  renderExams(button.dataset.filter);
});

$('#examList').addEventListener('click', (event) => {
  const button = event.target.closest('.start-exam');
  const exam = exams.find((item) => item.id === button?.dataset.examId);
  if (exam) beginExam(exam);
});

$('#answerOptions').addEventListener('change', (event) => {
  if (event.target.matches('input[name="answer"]')) {
    answers[questionIndex] = Number(event.target.value);
    renderQuestion();
  }
});

$('#questionNavigator').addEventListener('click', (event) => {
  const button = event.target.closest('[data-question-index]');
  if (button) { questionIndex = Number(button.dataset.questionIndex); renderQuestion(); }
});

$('#previousQuestionBtn').addEventListener('click', () => { if (questionIndex > 0) { questionIndex -= 1; renderQuestion(); } });
$('#nextQuestionBtn').addEventListener('click', () => { if (questionIndex < activeExam.questions.length - 1) { questionIndex += 1; renderQuestion(); } });
$('#submitExamBtn').addEventListener('click', () => submitExam());
$('#exitExamBtn').addEventListener('click', () => {
  if (confirm('Thoát bài thi? Các câu trả lời hiện tại sẽ không được lưu.')) { clearInterval(timerId); activeExam = null; showView('home'); }
});
$('#resultHomeBtn').addEventListener('click', () => { activeExam = null; showView('home'); });
$('#retryExamBtn').addEventListener('click', () => {
  const exam = exams.find((item) => item.id === resultData?.examId);
  if (exam) beginExam(exam);
});

renderExams();
renderHistory();