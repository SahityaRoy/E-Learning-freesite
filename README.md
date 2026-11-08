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

Đặt thông tin admin trước lần chạy đầu tiên. Hãy dùng mật khẩu riêng và một secret ngẫu nhiên:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_PASSWORD = "replace-with-a-strong-password"
python app.py
```

Mở `http://127.0.0.1:5000`. Trang đăng nhập admin nằm tại `/login`.

Nếu không cấu hình `ADMIN_EMAIL` và `ADMIN_PASSWORD`, ứng dụng dùng mặc định `admin@eschool.com` / `admin123`. Chỉ dùng thông tin mặc định cho máy local mới; không dùng khi triển khai thật. Tài khoản bootstrap chỉ được tạo khi email chưa tồn tại trong database.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Bộ test dùng database và thư mục upload tạm, không cần xóa database local. Các kiểm thử bao gồm xác thực, quyền admin, CRUD khóa học/sách, trang chi tiết, upload ảnh, API thống kê quiz, các trường hợp dữ liệu sai/giá trị biên, header/cookie bảo mật và smoke test hiệu năng API. Smoke test hiệu năng đo 10 request trong tiến trình cho danh sách 500 khóa học với ngân sách 3 giây; đây không phải kiểm thử tải hay cam kết SLA production.

## Lưu trữ và cấu hình

| Biến môi trường | Mặc định | Mục đích |
|---|---|---|
| `SECRET_KEY` | Tạo/lưu trong `instance/secret_key` | Ký session Flask; cần đặt giá trị ổn định khi triển khai |
| `ADMIN_EMAIL` | `admin@eschool.com` | Email admin bootstrap ban đầu |
| `ADMIN_PASSWORD` | `admin123` | Mật khẩu admin bootstrap ban đầu |
| `DATABASE_PATH` | `instance/elearning.sqlite3` | Đường dẫn database SQLite |
| `UPLOAD_FOLDER` | `instance/uploads` | Ảnh khóa học |
| `BOOK_UPLOAD_FOLDER` | `static/uploads/books` | Ảnh bìa sách |
| `PORT` | `5000` | Cổng Flask development server |
| `AUTH_LOGIN_RATE_LIMIT` | `10` | Số lần đăng nhập tối đa trên mỗi IP trong cửa sổ giới hạn |
| `AUTH_LOGIN_RATE_WINDOW` | `900` | Cửa sổ giới hạn đăng nhập, tính bằng giây |
| `AUTH_REGISTER_RATE_LIMIT` | `5` | Số lần đăng ký tối đa trên mỗi IP trong cửa sổ giới hạn |
| `AUTH_REGISTER_RATE_WINDOW` | `3600` | Cửa sổ giới hạn đăng ký, tính bằng giây |

Ứng dụng tự tạo database, bảng và dữ liệu mẫu khi khởi động. Khi triển khai, cần giữ database và thư mục upload trên persistent storage để không mất dữ liệu sau khi restart.

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
scripts/build_static.py Export templates/assets cho static hosting
```

## Triển khai

`python app.py` chạy Flask development server trên `127.0.0.1`; không dùng server này cho production. Cần một host hỗ trợ Python/WSGI, cấu hình secret và admin riêng, cùng persistent storage cho SQLite và upload. Workflow Azure Static Web Apps hiện có chỉ xuất bản file tĩnh; nó không chạy Flask API, đăng nhập, database hay upload backend.

## Tài liệu

- [Kiến trúc và thuyết minh dự án](docs/architecture.md)
- [Quy tắc ứng xử](CODE_OF_CONDUCT.md)
- [Giấy phép](LICENSE)
