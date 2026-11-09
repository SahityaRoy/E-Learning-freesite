# Vòng đời dữ liệu cá nhân

Đây là chính sách vận hành của phiên bản hiện tại, nhằm chỉ giữ dữ liệu cần cho tài khoản học tập và thống kê quiz. Tài liệu này không thay thế tư vấn pháp lý. Mặc định, dữ liệu lượt quiz chi tiết được giữ 365 ngày; có thể đặt `QUIZ_ATTEMPT_RETENTION_DAYS` thành số ngày nguyên dương khác.

## Kiểm kê dữ liệu

| Dữ liệu / trường | Mục đích | Nơi lưu | Ai truy cập | Bắt buộc? | Thời hạn |
|---|---|---|---|---|---|
| `users.id` | Khóa nội bộ và liên kết dữ liệu | SQLite `users` | Server; quản trị viên không nhận ID qua API báo cáo | Tự sinh | Đến khi tài khoản bị xóa |
| `users.name`, `users.email` | Nhận diện và đăng nhập tài khoản | SQLite `users` | Chủ tài khoản; quản trị viên qua API quản lý tài khoản | Có khi đăng ký | Đến khi người dùng xóa tài khoản |
| `users.password_hash` | Xác minh đăng nhập, không lưu mật khẩu gốc | SQLite `users` | Chỉ server; không trả về API | Có | Đến khi tài khoản bị xóa |
| `users.role`, `users.created_at` | Phân quyền và quản lý tài khoản | SQLite `users` | Server; vai trò/tạo lúc được trả trong dữ liệu tài khoản | Do hệ thống đặt | Đến khi tài khoản bị xóa |
| `quiz_attempts.exam_id`, `exam_title`, `subject` | Phân loại kết quả và tổng hợp theo đề | SQLite `quiz_attempts` | Chủ tài khoản qua API xuất; quản trị viên thấy tên đề/chủ đề trong báo cáo | Có khi nộp bài | Tối đa 365 ngày |
| `quiz_attempts.correct_count`, `total_questions`, `score` | Hiển thị kết quả và thống kê | SQLite `quiz_attempts` | Chủ tài khoản; quản trị viên chỉ nhận số liệu cần cho báo cáo | Có khi nộp bài | Tối đa 365 ngày |
| `quiz_attempts.duration_seconds`, `created_at` | Thời lượng và thời điểm kết quả | SQLite `quiz_attempts` | Chủ tài khoản; báo cáo admin chỉ nhận thời điểm gần đây, không nhận thời lượng | Có khi nộp bài | Tối đa 365 ngày |
| `quiz_attempts.user_id` | Gắn lượt với người đã đăng nhập; `NULL` cho khách | SQLite `quiz_attempts` | Server; báo cáo chỉ phân biệt “Học viên”/“Khách” | Không, tùy đăng nhập | Tối đa 365 ngày; xóa sớm khi xóa tài khoản |
| `quiz_monthly_aggregates` | Giữ số lượt, tổng điểm/câu đúng và điểm cao nhất theo tháng/đề | SQLite | Server và API thống kê admin | Không | Giữ dạng tổng hợp; rà soát định kỳ |
| Lịch sử tối đa 20 lượt quiz trên trình duyệt | Tiện ích xem lại kết quả cá nhân | `localStorage` của trình duyệt | Người dùng trình duyệt đó | Không | Đến khi người dùng xóa dữ liệu trình duyệt |

Khách có thể nộp quiz; lượt khách không được gắn với tài khoản. Không lưu đáp án được chọn hoặc email trong bản ghi lượt quiz. Dữ liệu gửi lên từ quiz chỉ bao gồm mã/tên đề, chủ đề, số câu đúng/tổng câu và thời lượng.

## Báo cáo và giảm thiểu dữ liệu

`GET /api/admin/quiz/statistics` chỉ dành cho quản trị viên. Báo cáo tổng hợp giữ số lượt, điểm trung bình, số câu đúng/tổng câu và thống kê theo đề. Danh sách gần đây chỉ trả nhãn “Khách” hoặc “Học viên”, tên đề/chủ đề, điểm, số câu đúng/tổng câu và thời điểm; tên, email, ID tài khoản và thời lượng không được trả. Số tài khoản trong báo cáo chỉ tính lượt chi tiết còn liên kết tài khoản, không bao gồm các lượt đã lưu dạng tổng hợp tháng.

Khi hết thời hạn lưu, lệnh `archive-expired-quiz-attempts` gộp dữ liệu theo tháng và đề, lưu tổng số lượt/tổng điểm/tổng câu đúng/điểm cao nhất, rồi xóa các bản ghi lượt cá nhân. Bảng tổng hợp không lưu user ID, tên, email, thời lượng, điểm riêng từng lượt hoặc thời điểm chính xác. Vì vậy, báo cáo vẫn giữ tổng lượt, điểm trung bình và chỉ số theo đề; thống kê người học chỉ tính trên dữ liệu chi tiết còn thời hạn.

## Truy cập và xóa dữ liệu

- Người dùng đã đăng nhập gọi `GET /api/auth/me/data` để tải thông tin tài khoản và các lượt quiz chi tiết còn liên kết với tài khoản. Mật khẩu/hash không nằm trong phản hồi.
- Người dùng gọi `DELETE /api/auth/me` để xóa tài khoản. Hệ thống gộp các lượt quiz của tài khoản vào bảng tổng hợp tháng, xóa bản ghi lượt cá nhân và xóa tài khoản; phiên đăng nhập bị kết thúc. Việc này không thể hoàn tác.
- Lượt quiz đã được gộp thành tổng hợp không còn liên kết với người cụ thể và không thể xuất theo tài khoản.
- Không thể tự xóa tài khoản quản trị bootstrap đang được cấu hình hoặc quản trị viên cuối cùng. Trước tiên cần chuyển cấu hình `BOOTSTRAP_ADMIN_EMAIL` sang tài khoản quản trị khác và bảo đảm còn một quản trị viên hoạt động.
- Người chưa đăng nhập không có định danh trong hệ thống để tra cứu/xóa lượt khách; có thể xóa lịch sử cục bộ bằng cách xóa dữ liệu trang web trong trình duyệt.

## Vận hành, tác vụ định kỳ và sao lưu

Lên lịch chạy lệnh sau ít nhất mỗi ngày trên môi trường chạy Flask; lệnh chỉ xóa các lượt cũ hơn thời hạn cấu hình và có thể chạy lặp lại an toàn:

```powershell
python -m flask --app app archive-expired-quiz-attempts
```

Có thể kiểm tra hoặc chạy với thời hạn khác bằng `--retention-days N`. Lệnh in số lượt đã gộp. Sao lưu database SQLite không được ứng dụng tự động quản lý: đơn vị triển khai phải giới hạn người truy cập, mã hóa bản sao lưu, đặt thời hạn lưu bản sao lưu (khuyến nghị tối đa 30 ngày), và bảo đảm yêu cầu xóa được áp dụng lại nếu khôi phục bản sao lưu cũ. Không đưa database, secret hoặc bản sao lưu lên repository.
