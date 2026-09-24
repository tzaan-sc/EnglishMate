# 📧 Hướng Dẫn Cấu Hình Gmail SMTP (Gửi Email Thật)

Dự án **EnglishMate** đã được tích hợp sẵn dịch vụ gửi email thật (SMTP Email Service). Để hệ thống gửi email xác thực OTP và liên kết khôi phục mật khẩu trực tiếp vào hòm thư Gmail của học viên, bạn chỉ cần thực hiện 4 bước sau:

---

## 🔒 Bước 1: Bật Xác Minh 2 Bước Cho Tài Khoản Google
1. Truy cập trang [Quản lý tài khoản Google](https://myaccount.google.com/).
2. Chọn mục **Bảo mật** (Security) ở menu bên trái.
3. Tại phần **Cách bạn đăng nhập vào Google**, chọn **Xác minh 2 bước** (2-Step Verification) và tiến hành **Bật** (Turn ON).

---

## 🔑 Bước 2: Tạo Mật Khẩu Ứng Dụng (App Password - 16 ký tự)
1. Truy cập trực tiếp: [Tạo Mật khẩu ứng dụng của Google](https://myaccount.google.com/apppasswords).
2. Tại ô **App name** (Tên ứng dụng): Nhập `EnglishMate` và nhấn **Tạo** (Create).
3. Google sẽ cấp mã Mật khẩu ứng dụng gồm 16 ký tự (ví dụ: `abcd efgh ijkl mnop`).
4. **Sao chép (Copy)** chuỗi 16 ký tự này (loại bỏ khoảng trắng).

---

## ⚙️ Bước 3: Cấu Hình Tệp `.env` Trong Dự Án
Mở tệp `.env` tại thư mục gốc dự án (`d:\GITHUB\web-english\.env`) và điền thông số:

```ini
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=email_gmail_cua_ban@gmail.com
MAIL_PASSWORD=chuoi_16_ky_tu_mat_khau_ung_dung
MAIL_DEFAULT_SENDER=EnglishMate <email_gmail_cua_ban@gmail.com>
```

> **Lưu ý:** Thay `email_gmail_cua_ban@gmail.com` và `chuoi_16_ky_tu_mat_khau_ung_dung` bằng thông tin thực tế của bạn.

---

## 🚀 Bước 4: Khởi Động Lại & Kiểm Thử
1. Lưu tệp `.env`.
2. Khởi chạy lại server: `python run.py`.
3. Truy cập `/auth/forgot-password`, nhập email và nhấn gửi.
4. Kiểm tra hộp thư Gmail, bạn sẽ nhận được email giao diện chuẩn từ EnglishMate!
