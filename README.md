# EnglishMate

EnglishMate là website học tiếng Anh chạy local, hướng tới sinh viên và người tự học. Ứng dụng kết hợp bài học theo cấp độ, kho từ vựng, flashcard, quiz có giải thích, theo dõi tiến độ và khu vực quản trị nội dung.

## Công nghệ

- Backend: Python 3.10+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- Database: SQLite
- Frontend: Jinja2, Bootstrap 5, CSS/JavaScript thuần
- Test: pytest với SQLite in-memory

## Cài đặt và chạy

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
python run.py
```

Mở `http://127.0.0.1:5000`. Database được tạo tại `instance/englishmate.db`.

Nếu PowerShell chặn script kích hoạt môi trường ảo, có thể chạy trực tiếp `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` và `.\.venv\Scripts\python.exe run.py`.

## Tài khoản demo

| Quyền | Email | Mật khẩu |
|---|---|---|
| Admin | `admin@example.com` | `admin123` |
| User | `user1@example.com` | `user123` |
| User | `user2@example.com` | `user123` |

Các tài khoản này chỉ dùng cho môi trường local/demo.

## Chức năng

- Đăng ký, đăng nhập, đăng xuất; hash mật khẩu và khóa/mở tài khoản.
- Dashboard hiển thị bài đã học, quiz, điểm trung bình, số từ đã học và bài gợi ý.
- Bài học lọc theo level/kỹ năng, xem chi tiết và ghi nhận hoàn thành.
- Từ vựng tìm kiếm/lọc theo level/chủ đề và đánh dấu đã học.
- Flashcard lật bằng CSS/JS, ghi nhận “Biết rồi” hoặc “Chưa nhớ”.
- Quiz tối đa 10 câu theo level/chủ đề, lưu attempt và giải thích từng đáp án.
- Trang tiến độ với lịch sử quiz và thống kê cá nhân.
- Admin thống kê hệ thống; thêm/sửa/ẩn bài học; thêm/sửa/xóa từ; tìm và khóa user.
- Trang lỗi 403/404 và thông báo phản hồi cho các thao tác.

## Dữ liệu mẫu

Lệnh `python -m app.seed` chạy an toàn nhiều lần: dữ liệu chỉ được thêm khi bảng tương ứng đang trống. Seed tạo 3 tài khoản, 12 bài học, 60 từ vựng và 40 câu quiz ở A1–B2, trải trên 8 chủ đề.

## Chạy test

```powershell
pytest
```

Bộ test bao phủ đăng ký/login/logout, tài khoản bị khóa, phân quyền admin, danh sách bài học, hoàn thành bài và lưu kết quả quiz.

## Cấu trúc chính

```text
app/
├── blueprints/       # main, auth, learning, admin
├── static/           # CSS và JavaScript flashcard
├── templates/        # giao diện Jinja2
├── config.py         # cấu hình dev/test và biến môi trường
├── extensions.py     # SQLAlchemy, LoginManager, CSRF
├── models.py         # 8 database models
└── seed.py           # dữ liệu demo
tests/                # pytest
run.py                # entry point
```

## Quyết định triển khai

- Bài học dùng xóa mềm (`is_active=False`) để không phá dữ liệu tiến độ đã liên kết.
- Từ vựng đã có lịch sử học sẽ không được xóa; admin nhận cảnh báo.
- Mỗi user chỉ đọc được attempt của chính họ; route kết quả luôn lọc theo `current_user.id`.
- Secret key local có giá trị mặc định thuận tiện, nhưng production phải đặt `SECRET_KEY` qua `.env`/biến môi trường.
- Bootstrap và font được nạp từ CDN; phần CSS tùy chỉnh vẫn định nghĩa toàn bộ nhận diện và bố cục chính.

## Kiểm tra thủ công gợi ý

1. Đăng ký tài khoản mới và đăng nhập/đăng xuất.
2. Xem dashboard, mở bài học và đánh dấu hoàn thành.
3. Tìm từ vựng, đánh dấu đã học và ôn flashcard.
4. Làm quiz, xem giải thích đáp án và trang tiến độ.
5. Đăng nhập admin, thêm/sửa/ẩn lesson và thêm/sửa/xóa vocabulary.
6. Khóa/mở một user; xác nhận admin không thể tự khóa chính mình.

