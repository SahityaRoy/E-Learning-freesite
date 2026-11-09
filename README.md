# Eduhub E-Learning

Eduhub là website học lập trình với thư viện khóa học, sách/tài liệu, bài quiz và khu vực quản trị. Dự án dùng Flask để phục vụ trang HTML, API và dữ liệu SQLite; giao diện được xây dựng bằng HTML, CSS và JavaScript.

## Mục tiêu

- Gom tài nguyên học lập trình vào một website dễ khám phá.
- Cho học viên xem nội dung khóa học, sách và tài liệu trước khi mở liên kết học.
- Cho quản trị viên quản lý khóa học, sách, tài khoản và theo dõi kết quả quiz.
- Làm việc trên màn hình máy tính và điện thoại.

## Chức năng

### Dành cho học viên

- Tìm kiếm khóa học, sách và quiz từ thanh tìm kiếm trên đầu trang; tìm kiếm hỗ trợ từ khóa tiếng Việt có hoặc không có dấu.
- Duyệt khóa học và sách theo dạng lưới. Trang chủ hiển thị bốn mục đầu tiên; nút **Xem thêm** mở toàn bộ danh sách.
- Mở trang chi tiết khóa học hoặc sách để xem mô tả, nội dung, tác giả/danh mục và sau đó mới mở liên kết video hoặc tài liệu.
- Lọc và tìm sách theo tên, tác giả và danh mục.
- Đăng ký tài khoản học viên, đăng nhập và đăng xuất.
- Làm các bộ quiz lập trình, xem điểm, đáp án và phần giải thích; kết quả được gửi về server để tổng hợp.

### Dành cho quản trị viên

- Quản lý khóa học: tên, mô tả, nội dung chi tiết, ảnh và liên kết video.
- Quản lý sách: tên, tác giả, danh mục, mô tả, nội dung chi tiết, ảnh bìa và liên kết tài liệu.
- Quản lý tài khoản và tạo thêm tài khoản admin.
- Xem thống kê quiz: tổng lượt làm, điểm trung bình, học viên đã đăng nhập tham gia, tỷ lệ câu đúng, kết quả theo đề và các lượt gần đây.
- Các trang quản trị và API quản trị yêu cầu đăng nhập bằng tài khoản admin.

## Công nghệ

- Python 3.10 trở lên
- Flask 3.x
- SQLite
- Pillow để xác thực ảnh tải lên
- HTML, CSS, JavaScript và Jinja templates
- `unittest` cho kiểm thử backend

## Chạy local trên Windows

Mở PowerShell tại thư mục dự án:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Khi chạy local, ứng dụng mặc định dùng cấu hình phát triển và có thể tạo admin local `admin@eschool.com` / `admin123` nếu chưa có tài khoản. Chỉ dùng mặc định này trên máy local mới; không dùng khi triển khai thật. Có thể đặt tài khoản local riêng:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_PASSWORD = "replace-with-a-strong-password"
python app.py
```

Mở `http://127.0.0.1:5000`. Trang đăng nhập admin nằm tại `/login`.

### Biến môi trường và production

Production phải có `APP_ENV=production`, `SECRET_KEY`, `ADMIN_EMAIL` và `ADMIN_PASSWORD` trước khi khởi động. Thiếu `SECRET_KEY` hoặc thông tin admin sẽ làm ứng dụng dừng với `RuntimeError`; production không dùng tài khoản mặc định, không chấp nhận mật khẩu `admin123`, và yêu cầu mật khẩu admin dài ít nhất 12 ký tự. Tài khoản bootstrap chỉ được tạo khi email chưa tồn tại trong database.

Ví dụ nội dung `.env` cho môi trường production (thay các giá trị mẫu bằng secret riêng):

```dotenv
APP_ENV=production
SECRET_KEY=generate-a-long-random-secret-and-store-it-safely
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=use-a-unique-strong-password
```

Ứng dụng đọc biến từ môi trường của tiến trình; `python app.py` không tự nạp tệp `.env`. Hãy dùng secret manager/cấu hình môi trường của nền tảng triển khai hoặc công cụ nạp `.env` đáng tin cậy. Trên PowerShell, có thể thiết lập trực tiếp bằng `$env:APP_ENV = "production"` và `$env:SECRET_KEY = "..."` (tương tự với hai biến admin) trước khi chạy ứng dụng. `SESSION_COOKIE_SECURE` được bật tự động trong production; production cần được phục vụ qua HTTPS.

**Tuyệt đối không đưa `SECRET_KEY`, mật khẩu admin hay bất kỳ secret nào lên Git.** Không commit `.env`; tệp này và thư mục `instance/` đã được loại khỏi Git bằng `.gitignore`. Dùng giá trị ngẫu nhiên, ổn định qua lần restart và lưu secrets riêng tư.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Bộ test dùng database và thư mục upload tạm, không cần xóa database local. Các kiểm thử bao gồm xác thực, quyền admin, CRUD khóa học/sách, trang chi tiết, upload ảnh, API thống kê quiz, các trường hợp dữ liệu sai/giá trị biên, header/cookie bảo mật và smoke test hiệu năng API. Smoke test hiệu năng đo 10 request trong tiến trình cho danh sách 500 khóa học với ngân sách 3 giây; đây không phải kiểm thử tải hay cam kết SLA production.

## Lưu trữ và cấu hình

| Biến môi trường | Mặc định | Mục đích |
|---|---|---|
| `APP_ENV` | `development` | Đặt `production` cho triển khai thật; bật cookie `Secure` và yêu cầu secrets |
| `SECRET_KEY` | Sinh/lưu trong `instance/secret_key` ở local | Ký session Flask; bắt buộc và phải ổn định trong production |
| `ADMIN_EMAIL` | `admin@eschool.com` ở local | Email admin bootstrap; bắt buộc trong production |
| `ADMIN_PASSWORD` | `admin123` ở local | Mật khẩu admin bootstrap; bắt buộc, ít nhất 12 ký tự và không được là `admin123` trong production |
| `SESSION_COOKIE_SECURE` | Tự bật trong production | Có thể đặt `true` để bật cookie `Secure` ngoài production |
| `DATABASE_PATH` | `instance/elearning.sqlite3` | Đường dẫn database SQLite |
| `UPLOAD_FOLDER` | `instance/uploads` | Ảnh khóa học |
| `BOOK_UPLOAD_FOLDER` | `instance/uploads/books` | Ảnh bìa sách |
| `PORT` | `5000` | Cổng Flask development server |
| `AUTH_LOGIN_RATE_LIMIT` | `10` | Số lần đăng nhập tối đa trên mỗi IP trong cửa sổ giới hạn |
| `AUTH_LOGIN_RATE_WINDOW` | `900` | Cửa sổ giới hạn đăng nhập, tính bằng giây |
| `AUTH_REGISTER_RATE_LIMIT` | `5` | Số lần đăng ký tối đa trên mỗi IP trong cửa sổ giới hạn |
| `AUTH_REGISTER_RATE_WINDOW` | `3600` | Cửa sổ giới hạn đăng ký, tính bằng giây |
| `HSTS_ENABLED` | `false` | Bật HSTS khi HTTPS đã được ép buộc ở reverse proxy/host |
| `QUIZ_ATTEMPT_RETENTION_DAYS` | `365` | Số ngày giữ dữ liệu chi tiết của lượt quiz trước khi gộp thống kê tháng |

Ứng dụng tự tạo database, bảng và dữ liệu mẫu khi khởi động. Khi triển khai, cần giữ database và thư mục upload trên persistent storage để không mất dữ liệu sau khi restart. Chỉ đặt `HSTS_ENABLED=true` khi host đã ép buộc HTTPS; không bật trên môi trường HTTP local.

Flask gửi CSP với nonce ngẫu nhiên theo response, chống nhúng trang bằng `frame-ancestors` và `X-Frame-Options`, cùng các header bảo mật khác trên HTML, API và static responses. `script-src` không cho phép `unsafe-inline`; một số inline style và Tailwind CDN hiện vẫn cần `unsafe-inline` trong `style-src`. Mọi request thay đổi trạng thái phải gửi CSRF token gắn với session qua `X-CSRF-Token` (JSON API) hoặc trường form `_csrf_token`; token được cung cấp trong meta tag `csrf-token` và `GET /api/csrf-token`. Không đặt token trong URL. Khi triển khai bản static export, cần cấu hình các HTTP headers tương ứng tại static host; static export không chạy Flask middleware.

Dữ liệu quiz chi tiết được lưu tối đa 365 ngày (có thể cấu hình) rồi chuyển thành thống kê tháng, không còn từng lượt hay liên kết tài khoản. Chạy tác vụ định kỳ bằng `python -m flask --app app archive-expired-quiz-attempts`. Người dùng đã đăng nhập có thể xuất dữ liệu tại `/api/auth/me/data` và xóa tài khoản cùng dữ liệu quiz liên kết tại `DELETE /api/auth/me`. Xem [chính sách vòng đời dữ liệu và hướng dẫn vận hành](docs/privacy-data-lifecycle.md).

## Cấu trúc dự án

```text
app.py                 Flask app factory và cấu hình
controllers.py         Page routes, API, xác thực và quyền truy cập
models.py              SQLite schema, truy vấn và validation
templates/             Trang Jinja và giao diện HTML
assets/css/            Stylesheets
assets/js/             Giao diện tương tác và tìm kiếm
images/                Ảnh và biểu tượng
instance/              Database, secret và upload runtime (không commit)
tests/test_app.py      Kiểm thử tích hợp backend
docs/architecture.md   Kiến trúc, luồng dữ liệu, bảo mật và giới hạn
docs/privacy-data-lifecycle.md  Kiểm kê dữ liệu, lưu giữ, truy cập/xóa và sao lưu
scripts/build_static.py Export templates/assets cho static hosting
```

## Triển khai

`python app.py` chạy Flask development server trên `127.0.0.1`; không dùng server này cho production. Cần một host hỗ trợ Python/WSGI, cấu hình secret và admin riêng, cùng persistent storage cho SQLite và upload. Workflow Azure Static Web Apps chỉ xuất bản file tĩnh; nó không chạy Flask API, đăng nhập, database hay upload backend. Workflow vẫn export và kiểm tra bundle; bước deploy/đóng preview chỉ chạy khi repository có secret `AZURE_STATIC_WEB_APPS_API_TOKEN_WONDERFUL_PLANT_05620E700`, nếu thiếu thì GitHub Actions ghi warning và bỏ qua deploy thay vì đánh dấu job thất bại.

## Tài liệu

- [Kiến trúc và thuyết minh dự án](docs/architecture.md)
- [Quy tắc ứng xử](CODE_OF_CONDUCT.md)
- [Giấy phép](LICENSE)
