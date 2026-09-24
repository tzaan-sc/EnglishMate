# 🔑 Hướng Dẫn Cấu Hình Google OAuth 2.0 (Đăng Nhập 1-Click)

Tài liệu hướng dẫn từng bước lấy bộ khóa **Google Client ID & Client Secret** để kích hoạt tính năng Đăng ký / Đăng nhập 1-click bằng Google trên EnglishMate.

---

## 🌐 Bước 1: Truy Cập Google Cloud Console
1. Truy cập trang quản lý thông tin xác thực của Google: [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Đăng nhập bằng tài khoản Google của bạn.

---

## 📁 Bước 2: Tạo Dự Án Mới (New Project)
1. Nhấn vào danh sách dự án ở góc trên bên trái (cạnh logo Google Cloud).
2. Nhấn nút **New Project** (Dự án mới).
3. Đặt tên dự án (Ví dụ: `EnglishMate`) và nhấn **Create** (Tạo).

---

## 📋 Bước 3: Cấu Hình Màn Hình Đồng Ý OAuth (OAuth Consent Screen)
1. Ở menu bên trái, chọn: **APIs & Services** -> **OAuth consent screen**.
2. Chọn loại người dùng: **External** -> Nhấn **Create**.
3. Điền thông tin cơ bản:
   - **App name**: `EnglishMate`
   - **User support email**: Chọn email của bạn
   - **Developer contact information**: Nhập email của bạn
4. Nhấn **SAVE AND CONTINUE** qua tất cả các bước cho đến khi hoàn tất.

---

## 🔐 Bước 4: Tạo Khóa OAuth Client ID
1. Ở menu bên trái, chọn tab **Credentials** (Thông tin xác thực).
2. Nhấn **+ CREATE CREDENTIALS** -> Chọn **OAuth client ID**.
3. Thiết lập thông số:
   - **Application type**: Chọn `Web application`
   - **Name**: `EnglishMate Web`
   - **Authorized redirect URIs**: Nhấn **+ ADD URI** và thêm 2 đường dẫn sau:
     + `http://127.0.0.1:5000/auth/google/callback`
     + `http://localhost:5000/auth/google/callback`
4. Nhấn nút **CREATE** (Tạo).

---

## ⚙️ Bước 5: Cấu Hình Tệp `.env`
Sao chép Client ID và Client Secret, sau đó mở tệp `.env` tại thư mục gốc dự án và cập nhật:

```ini
GOOGLE_CLIENT_ID=chuoi_client_id_cua_ban.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=chuoi_client_secret_cua_ban
```

Khởi động lại server (`python run.py`) và bấm nút Google trên trang Đăng nhập để trải nghiệm!
