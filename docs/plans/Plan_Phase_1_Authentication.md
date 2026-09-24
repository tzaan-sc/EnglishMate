# 🔐 KẾ HOẠCH TRIỂN KHAI GIAI ĐOẠN 1: XÁC THỰC & QUẢN LÝ NGƯỜI DÙNG



---

# Kế hoạch Triển khai Tính năng 1.1: Registration (Đăng ký)

Tài liệu này chi tiết hóa kế hoạch xây dựng và nâng cấp toàn bộ cụm tính năng thuộc **Mục 1.1: Registration (Đăng ký)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5 và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện 7 hạng mục con thuộc Mục 1.1 theo chuẩn sản phẩm:

1. **[x] Đăng ký bằng email/password**: Nâng cấp form đăng ký, hỗ trợ lưu trạng thái xác minh, mật khẩu bảo mật và dữ liệu chuẩn hóa.
2. **[x] Đăng ký bằng Google OAuth**: Tích hợp luồng đăng ký/đăng nhập 1-click qua Google OAuth 2.0 (hỗ trợ mô phỏng môi trường Dev & kết nối thực tế).
3. **[x] Đăng ký bằng Facebook OAuth**: Thêm nút Facebook OAuth chuẩn thương hiệu vào UI và xây dựng route xử lý callback Facebook OAuth.
4. **[x] Email verification (Gửi mã xác nhận OTP)**: Quy trình sinh mã OTP 6 chữ số (hạn 15 phút), gửi mail/hiển thị thông báo xác thực, trang nhập mã `/auth/verify-email/<user_id>` và nút gửi lại mã.
5. **[x] Password strength indicator**: Thanh đo độ mạnh mật khẩu thời gian thực (JS client-side) hiển thị mức độ (Yếu / Trung bình / Mạnh / Rất mạnh) kèm gợi ý cải thiện bên dưới ô nhập mật khẩu.
6. **[x] Terms & conditions checkbox**: Checkbox bắt buộc đồng ý Điều khoản sử dụng kèm Link/Modal hiển thị nội dung Điều khoản trực tiếp.
7. **[x] Privacy policy checkbox**: Checkbox bắt buộc đồng ý Chính sách bảo mật kèm Link/Modal hiển thị nội dung Chính sách bảo mật trực tiếp.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu (`app/modules/auth/models.py`)
Cập nhật bảng `User` để hỗ trợ xác thực Email và OAuth:
- `is_email_verified`: `db.Column(db.Boolean, default=False, nullable=False)`
- `email_verification_code`: `db.Column(db.String(6), nullable=True)`
- `email_verification_expiry`: `db.Column(db.DateTime(timezone=True), nullable=True)`
- `oauth_provider`: `db.Column(db.String(20), nullable=True)` (Google / Facebook)
- `oauth_id`: `db.Column(db.String(100), nullable=True)`

### 2.2. Form Đăng ký (`app/modules/auth/forms.py`)
Nâng cấp `RegisterForm`:
- `terms_agree`: `BooleanField("Tôi đồng ý với Điều khoản sử dụng", validators=[DataRequired(...)])`
- `privacy_agree`: `BooleanField("Tôi đồng ý với Chính sách bảo mật", validators=[DataRequired(...)])`
- Rào chắn kiểm tra độ mạnh mật khẩu ở phía backend (tối thiểu 8 ký tự, có chữ và số).

### 2.3. Routes & Controller (`app/modules/auth/routes.py`)
Bổ sung các endpoint mới:
- `GET/POST /auth/register`: Tạo tài khoản, sinh mã OTP 6 số, gửi thông báo và chuyển sang trang xác minh email.
- `GET/POST /auth/verify-email/<int:user_id>`: Nhập mã OTP xác minh tài khoản.
- `POST /auth/resend-verification/<int:user_id>`: Gửi lại mã OTP xác minh mới.
- `GET /auth/google`: Xử lý Đăng ký/Đăng nhập qua Google.
- `GET /auth/facebook`: Xử lý Đăng ký/Đăng nhập qua Facebook.

### 2.4. Form Giao diện (`app/templates/auth/register.html` & `verify_email.html`)
- Cập nhật `register.html`:
  - Thêm nút Facebook OAuth cạnh/dưới nút Google OAuth (`btn-facebook` phong cách thương hiệu đồng bộ).
  - Thêm Thanh đo độ mạnh mật khẩu (Password Strength Bar) bên dưới ô mật khẩu.
  - Thêm 2 checkbox đồng ý Điều khoản & Chính sách bảo mật kèm link mở Modal Bootstrap.
  - Tích hợp 2 Modal Bootstrap nội dung **Terms of Service** và **Privacy Policy**.
- Tạo mới `app/templates/auth/verify_email.html`:
  - Giao diện nhập mã OTP 6 số đẹp mắt, đồng bộ với `auth-card` hiện tại.
  - Đếm ngược thời gian hết hạn mã OTP và nút Gửi lại mã.

### 2.5. JavaScript & Styling (`app/static/js/app.js` & `app/static/css/app.css`)
- Viết hàm kiểm tra độ mạnh mật khẩu thời gian thực trong `app.js`.
- Bổ sung class `.btn-facebook` và các style hỗ trợ cho thanh đo độ mạnh mật khẩu (`.strength-bar`, `.strength-weak`, `.strength-medium`, `.strength-strong`) đồng bộ 100% màu sắc và font chữ của trang web.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_auth_registration.py`)
1. Test đăng ký tài khoản hợp lệ -> Tài khoản tạo thành công với `is_email_verified=False` và có `email_verification_code`.
2. Test nhập sai mã OTP -> Báo lỗi mã không hợp lệ.
3. Test nhập đúng mã OTP -> Tài khoản chuyển thành `is_email_verified=True`.
4. Test đăng ký thiếu checkbox Điều khoản / Chính sách -> Báo lỗi validation.
5. Test Đăng ký Google / Facebook OAuth simulation -> Đăng nhập / tạo tài khoản thành công.

### Manual Verification
1. Trải nghiệm trực tiếp luồng đăng ký trên giao diện web.
2. Kiểm tra thanh đo độ mạnh mật khẩu hoạt động mượt mà khi gõ chữ.
3. Thử click mở Modal Điều khoản sử dụng và Modal Chính sách bảo mật.
4. Kiểm tra nút OAuth Google và Facebook.
5. Kiểm tra giao diện xác thực OTP email.

---

# Kế hoạch Triển khai Tính năng 1.2: Login (Đăng nhập)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 1.2: Login (Đăng nhập)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5 và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện 8 hạng mục con thuộc Mục 1.2 theo tiêu chuẩn bảo mật nâng cao:

1. **[x] Login bằng email/password**: Đăng nhập tài khoản bằng email và mật khẩu đã đăng ký kèm kiểm tra trạng thái kích hoạt tài khoản.
2. **[x] Login bằng Google OAuth**: Đăng nhập nhanh 1-click qua tài khoản Google (hỗ trợ môi trường thực & demo).
3. **[x] Login bằng Facebook OAuth**: Đăng nhập nhanh 1-click qua tài khoản Facebook (hỗ trợ môi trường thực & demo).
4. **[x] Remember me checkbox**: Ghi nhớ đăng nhập qua Secure HttpOnly Cookies dài hạn.
5. **[x] Forgot password link**: Bổ sung liên kết "Quên mật khẩu?" dẫn tới quy trình khôi phục mật khẩu.
6. **[x] Show/hide password toggle**: Thêm icon con mắt (👁️) hiện/ẩn mật khẩu linh hoạt trên tất cả các ô nhập mật khẩu.
7. **[x] Login attempt limiting (5 attempts)**: Đếm số lần đăng nhập thất bại liên tiếp của tài khoản.
8. **[x] Account lockout after failed attempts**: Tự động khóa tài khoản tạm thời 15 phút sau 5 lần nhập sai mật khẩu để chống dò mật khẩu (Brute-force attack).

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu (`app/modules/auth/models.py` & `patch_db.py`)
Bổ sung các trường bảo mật vào bảng `User`:
- `failed_login_attempts`: `db.Column(db.Integer, nullable=False, default=0)` (Số lần nhập sai mật khẩu liên tiếp).
- `lockout_until`: `db.Column(db.DateTime(timezone=True), nullable=True)` (Thời điểm hết hạn khóa tài khoản).
- `last_login_at`: `db.Column(db.DateTime(timezone=True), nullable=True)` (Thời gian đăng nhập gần nhất).

Các phương thức hỗ trợ trong model `User`:
- `is_locked_out()`: Kiểm tra tài khoản có đang bị khóa hay không và trả về số phút còn lại.
- `record_failed_login()`: Tăng số lần đăng nhập sai. Nếu đạt 5 lần, tự động thiết lập `lockout_until` sau 15 phút.
- `record_successful_login()`: Đặt lại `failed_login_attempts = 0`, xóa `lockout_until` và cập nhật `last_login_at`.

### 2.2. Routes & Business Logic (`app/modules/auth/routes.py`)
Nâng cấp hàm `login()`:
- Kiểm tra tài khoản bị khóa (`is_locked_out()`) trước khi xác thực mật khẩu. Nếu đang khóa, hiển thị thông báo cảnh báo kèm số phút cần chờ.
- Xử lý mật khẩu sai: Gọi `record_failed_login()` và cảnh báo số lần thử còn lại (ví dụ: *"Email hoặc mật khẩu không chính xác. Bạn còn 2 lần thử trước khi bị khóa tài khoản."*).
- Xử lý mật khẩu đúng: Gọi `record_successful_login()` để đặt lại đếm và đăng nhập thành công.

### 2.3. Form Giao diện (`app/templates/auth/login.html`)
- Thêm Nút hiện/ẩn mật khẩu (Show/Hide Password Eye Toggle) bằng icon `bi-eye` / `bi-eye-slash` tích hợp bên phải ô nhập mật khẩu.
- Bổ sung Link **"Quên mật khẩu?"** bố trí tinh tế bên cạnh Checkbox "Ghi nhớ đăng nhập".
- Đảm bảo giữ nguyên 100% bố cục `auth-card`, khoảng cách và màu sắc thương hiệu hiện tại.

### 2.4. JavaScript (`app/static/js/app.js`)
- Tích hợp sự kiện xử lý click vào Nút con mắt để chuyển đổi qua lại giữa `type="password"` và `type="text"`.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_auth_login.py`)
1. Test đăng nhập thành công đặt lại đếm sai về 0.
2. Test nhập sai mật khẩu 1, 2, 3, 4 lần -> Hệ thống đếm đúng số lần và thông báo số lần còn lại.
3. Test nhập sai mật khẩu lần 5 -> Tài khoản bị khóa 15 phút, các lần đăng nhập tiếp theo bị chặn ngay lập tức.
4. Test hết 15 phút khóa -> Tài khoản mở lại bình thường.
5. Test tính năng Nút con mắt (Show/Hide Password) và Link Quên mật khẩu.

### Manual Verification
1. Truy cập `/auth/login` và thử bấm vào Icon con mắt 👁️ ở ô Mật khẩu để kiểm tra ẩn/hiện chữ.
2. Thử nhập sai mật khẩu 5 lần liên tiếp để nghiệm thu thông báo khóa tài khoản 15 phút.
3. Thử đăng nhập thành công và kiểm tra phiên làm việc (Remember me).

---

# Kế hoạch Triển khai Tính năng 1.3: Password Recovery (Khôi phục mật khẩu)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 1.3: Password Recovery (Khôi phục mật khẩu)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5 và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện 6 hạng mục con thuộc Mục 1.3 theo đúng tiêu chuẩn an toàn bảo mật:

1. **[x] Forgot password form**: Form nhập email để yêu cầu khôi phục mật khẩu với validation định dạng email.
2. **[x] Send reset email**: Sinh Token bảo mật ngẫu nhiên mã hóa 32-bytes, giả lập/gửi thông báo chứa đường dẫn khôi phục mật khẩu tới email người dùng.
3. **[x] Password reset link (expiring in 1 hour)**: Tuyến đường `/auth/reset-password/<token>` có hiệu lực chính xác trong 1 giờ (`reset_token_expiry`). Từ chối truy cập và báo lỗi nếu token không hợp lệ hoặc quá hạn.
4. **[x] New password validation**: Tích hợp thanh đo độ mạnh mật khẩu thời gian thực (Password Strength Indicator) trên giao diện đổi mật khẩu mới.
5. **[x] Confirm new password**: Ô nhập lại mật khẩu mới để xác nhận (`EqualTo("password")`).
6. **[x] Password reset success notification**: Đổi mật khẩu thành công, mở khóa các lần đăng nhập sai trước đó, xóa token và hiển thị thông báo thành công chuyển về trang Đăng nhập.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/auth/models.py` & `patch_db.py`)
Bổ sung các trường bảo mật khôi phục mật khẩu vào bảng `User`:
- `reset_token`: `db.Column(db.String(100), nullable=True)` (Mã bí mật dạng token an toàn).
- `reset_token_expiry`: `db.Column(db.DateTime(timezone=True), nullable=True)` (Thời điểm hết hạn token - 1 giờ).

Phương thức trong model `User`:
- `generate_reset_token()`: Sinh token bằng `secrets.token_urlsafe(32)` và đặt `reset_token_expiry` sau 1 giờ.
- `verify_reset_token(token)`: Kiểm tra token khớp và còn trong thời hạn 1 giờ.

### 2.2. Forms (`app/modules/auth/forms.py`)
- `ForgotPasswordForm`: Nhập email tài khoản.
- `ResetPasswordForm`: Nhập `password` mới (tối thiểu 6 ký tự) và `confirm_password` khớp nhau.

### 2.3. Routes & Business Logic (`app/modules/auth/routes.py`)
- `GET/POST /auth/forgot-password`:
  - Người dùng nhập email -> Nếu email tồn tại, sinh `reset_token` (hạn 1 giờ) và tạo liên kết `reset_url`.
  - Hiển thị thông báo thành công kèm đường dẫn khôi phục trực tiếp để kiểm thử thuận tiện.
- `GET/POST /auth/reset-password/<token>`:
  - Kiểm tra `verify_reset_token(token)`. Nếu sai hoặc hết hạn 1 giờ, báo lỗi và chuyển hướng về `/auth/forgot-password`.
  - Nếu hợp lệ, hiển thị form đặt lại mật khẩu mới. Khi submit: cập nhật mật khẩu mới (`set_password`), xóa token, mở khóa tài khoản và hiển thị thông báo thành công.

### 2.4. Form Giao diện (`forgot_password.html` & `reset_password.html`)
- **`app/templates/auth/forgot_password.html`**: Form nhập email gọn gàng, đồng bộ với `auth-card` hiện tại.
- **`app/templates/auth/reset_password.html`**: Form nhập mật khẩu mới & xác nhận mật khẩu, tích hợp Thanh đo độ mạnh mật khẩu và Nút con mắt (👁️) hiện/ẩn mật khẩu.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_auth_password_recovery.py`)
1. Test sinh token khôi phục mật khẩu hợp lệ với hạn 1 giờ.
2. Test thử truy cập đường dẫn khôi phục với token sai hoặc quá hạn 1 giờ -> Hệ thống báo lỗi hết hạn.
3. Test đặt lại mật khẩu thành công -> Mật khẩu mới được lưu, token bị hủy, đăng nhập bằng mật khẩu mới thành công.

### Manual Verification
1. Truy cập `/auth/forgot-password`, nhập email và bấm gửi.
2. Thử truy cập liên kết khôi phục nhận được.
3. Gõ mật khẩu mới, kiểm tra thanh đo độ mạnh và nút con mắt (👁️).
4. Tiến hành đặt lại mật khẩu và đăng nhập lại bằng mật khẩu mới.

---

# Kế hoạch Triển khai Tính năng 1.4: Profile Management (Quản lý hồ sơ)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 1.4: Profile Management (Quản lý hồ sơ)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, modal, card và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện 9 hạng mục con thuộc Mục 1.4 theo đúng tiêu chuẩn an toàn bảo mật và UX liền mạch:

1. **[x] View profile information**: Trang cá nhân hiển thị đẩy đủ Username, Tên đầy đủ, Email, Ảnh đại diện, Ngày tạo tài khoản, Ngày đăng nhập gần nhất, Trạng thái tài khoản.
2. **[x] Edit full name**: Chỉnh sửa và lưu Tên đầy đủ (`full_name`).
3. **[x] Edit email (with verification)**: Đổi email bằng cách gửi mã OTP xác thực 6 chữ số tới email mới trước khi cho phép cập nhật email vào CSDL.
4. **[x] Change password (current + new + confirm)**: Đổi mật khẩu yêu cầu nhập Mật khẩu hiện tại (kiểm tra chính xác mới cho đổi) + Mật khẩu mới + Nhập lại mật khẩu mới.
5. **[x] Upload avatar**: Tải lên ảnh đại diện (hỗ trợ JPG, PNG, WEBP, GIF, tối đa 5MB), tự động cắt/lưu vào thư mục `app/static/uploads/avatars/`.
6. **[x] Delete account (with confirmation)**: Xóa tài khoản vĩnh viễn có Modal xác nhận + yêu cầu nhập mật khẩu xác nhận để bảo mật tuyệt đối.
7. **[x] Account deactivation**: Vô hiệu hóa tài khoản tạm thời (`is_active = False`) kèm Modal xác nhận và tự động đăng xuất.
8. **[x] View account creation date**: Hiển thị ngày tạo tài khoản định dạng thân thiện (ví dụ: `29/08/2026`).
9. **[x] View last login date**: Hiển thị ngày & giờ đăng nhập gần nhất (ví dụ: `29/08/2026 13:30`).

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/auth/models.py` & `patch_db.py`)
Bổ sung các trường quản lý hồ sơ vào bảng `User`:
- `full_name`: `db.Column(db.String(100), nullable=True)` (Tên đầy đủ của người dùng).
- `avatar`: `db.Column(db.String(255), nullable=True, default="default_avatar.png")` (Tên file ảnh đại diện).
- `pending_email`: `db.Column(db.String(120), nullable=True)` (Email mới đang chờ xác thực OTP).
- `pending_email_otp`: `db.Column(db.String(6), nullable=True)` (Mã OTP xác thực email mới).
- `pending_email_expiry`: `db.Column(db.DateTime(timezone=True), nullable=True)` (Thời hạn OTP email mới - 15 phút).

### 2.2. Forms (`app/modules/auth/forms.py` & `app/modules/main/forms.py`)
Tạo các Form quản lý hồ sơ:
- `EditProfileForm`: `full_name` (Tên đầy đủ), `avatar` (FileField với FileAllowed).
- `ChangeEmailForm`: `new_email` (Validation định dạng & kiểm tra trùng lặp).
- `VerifyNewEmailForm`: `otp_code` (Mã OTP 6 chữ số).
- `ChangePasswordForm`: `current_password`, `new_password`, `confirm_password`.
- `DeleteAccountForm`: `confirm_password` (Mật khẩu xác nhận xóa tài khoản).

### 2.3. Controller & Routes (`app/modules/main/routes.py` hoặc `app/modules/auth/routes.py`)
- `GET /profile`: Trang quản lý hồ sơ tích hợp các tab/thẻ thông tin cá nhân.
- `POST /profile/edit-info`: Cập nhật tên đầy đủ & upload avatar.
- `POST /profile/change-email`: Tạo mã OTP xác thực email mới và chuyển tới `/profile/verify-email`.
- `POST /profile/verify-email`: Xác nhận mã OTP email mới, cập nhật `user.email = user.pending_email`.
- `POST /profile/change-password`: Kiểm tra mật khẩu hiện tại ➔ Đổi mật khẩu mới.
- `POST /profile/deactivate`: Đặt `user.is_active = False`, đăng xuất người dùng và thông báo.
- `POST /profile/delete`: Kiểm tra mật khẩu xác nhận ➔ Xóa dữ liệu tài khoản vĩnh viễn (`db.session.delete(user)`).

### 2.4. Giao diện Người dùng (`app/templates/main/profile.html`)
- Xây dựng trang Hồ sơ cá nhân `profile.html` sử dụng layout đồng bộ với Dashboard/Settings hiện tại.
- Modal xác nhận vô hiệu hóa tài khoản & Modal xác nhận xóa tài khoản an toàn.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_profile_management.py`)
1. Test xem thông tin hồ sơ và ngày tạo / ngày đăng nhập gần nhất.
2. Test sửa tên đầy đủ & cập nhật thành công.
3. Test quy trình đổi email có mã OTP xác thực.
4. Test đổi mật khẩu (nhập sai mật khẩu cũ ➔ báo lỗi; nhập đúng ➔ đổi thành công).
5. Test upload avatar ảnh đại diện.
6. Test vô hiệu hóa tài khoản và kiểm tra không thể đăng nhập lại.
7. Test xóa tài khoản vĩnh viễn và xác minh dữ liệu bị xóa khỏi CSDL.

### Manual Verification
1. Truy cập `/profile` trên giao diện web.
2. Thử sửa tên đầy đủ, chọn ảnh avatar và nhấn **Lưu thay đổi**.
3. Thử quy trình đổi email kèm OTP xác thực.
4. Thử đổi mật khẩu mới và đăng xuất / đăng nhập lại bằng mật khẩu mới.
5. Thử nghiệm vô hiệu hóa và xóa tài khoản trên Modal xác nhận.

---

# Kế hoạch Triển khai Tính năng 1.5: Session Management (Quản lý phiên đăng nhập)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 1.5: Session Management (Quản lý phiên đăng nhập)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, modal, toast và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện 6 hạng mục con thuộc Mục 1.5 theo đúng tiêu chuẩn an toàn bảo mật phiên làm việc:

1. **[x] Auto logout after inactivity (30 minutes)**: Tự động hủy phiên và đăng xuất người dùng nếu không phát sinh hoạt động trong 30 phút (1800 giây).
2. **[x] Manual logout button**: Nút đăng xuất thủ công (đã sẵn có trên Sidebar & Header, bổ sung quản lý phiên).
3. **[x] Logout from all devices**: Cho phép hủy tất cả các phiên đăng nhập khác (hoặc toàn bộ thiết bị) chỉ với 1 cú nhấp chuột.
4. **[x] View active sessions**: Trang/Thẻ xem danh sách các phiên đăng nhập đang hoạt động (Địa chỉ IP, Trình duyệt, Hệ điều hành, Thời gian truy cập gần nhất, Đánh dấu phiên hiện tại).
5. **[x] Revoke specific session**: Đăng xuất / Hủy một phiên làm việc cụ thể trên thiết bị khác.
6. **[x] Session timeout warning (5 minutes before)**: Khi còn 5 phút nữa là hết hạn 30 phút (sau 25 phút không hoạt động), hiển thị Popup Modal cảnh báo kèm đồng hồ đếm ngược `5:00` và nút **"Tiếp tục phiên làm việc"** để gia hạn lại 30 phút.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/auth/models.py` & `patch_db.py`)
Tạo model `UserSession` lưu vết phiên đăng nhập:
- `id`: Primary Key String (Session Token / UUID).
- `user_id`: ForeignKey liên kết `user.id`.
- `ip_address`: Địa chỉ IP của thiết bị.
- `user_agent`: Thông tin trình duyệt & Hệ điều hành.
- `device_info`: Tóm tắt thiết bị (ví dụ: `Chrome trên Windows`).
- `last_activity`: Thời điểm tương tác gần nhất.
- `created_at`: Ngày tạo phiên đăng nhập.
- `is_active`: Trạng thái phiên.

### 2.2. Kiểm soát Phiên tự động (Middleware `before_request` & Keep-Alive API)
- **`app/modules/auth/routes.py`**:
  - `before_request`: Kiểm tra thời gian tương tác gần nhất trong session. Nếu quá 30 phút ➔ Tự động đăng xuất, thu hồi phiên và thông báo hết hạn.
  - `POST /auth/ping-session`: API nhận tín hiệu keep-alive từ client để gia hạn thời gian 30 phút khi người dùng nhấn nút tiếp tục.
- **Quản lý phiên trong Profile (`app/modules/main/routes.py`)**:
  - `GET /profile` hoặc `/sessions`: Lấy danh sách `UserSession.query.filter_by(user_id=user.id, is_active=True)`.
  - `POST /sessions/revoke/<session_id>`: Hủy 1 phiên cụ thể.
  - `POST /sessions/revoke-all`: Hủy tất cả phiên khác ngoại trừ phiên hiện tại.

### 2.3. Cảnh báo Hết hạn Phiên Client-side (`app/static/js/session_timeout.js`)
- Lắng nghe các sự kiện người dùng (`mousemove`, `keydown`, `click`, `scroll`) để reset đếm thời gian 30 phút client-side.
- Khi người dùng không tương tác trong **25 phút** ➔ Kích hoạt Modal Cảnh báo hết phiên kèm đồng hồ đếm ngược 300 giây (`5:00`).
- Nếu người dùng bấm **"Tiếp tục làm việc"** ➔ Gọi `fetch('/auth/ping-session', {method: 'POST'})` và ẩn Modal.
- Nếu đồng hồ chạm `0:00` ➔ Tự động chuyển hướng về `/auth/login?timeout=1`.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_session_management.py`)
1. Test ghi nhận `UserSession` khi đăng nhập thành công.
2. Test xem danh sách phiên đang hoạt động (`/sessions` hoặc trong Profile).
3. Test API gia hạn phiên `POST /auth/ping-session`.
4. Test hủy 1 phiên đăng nhập cụ thể (`POST /sessions/revoke/<id>`).
5. Test hủy tất cả các phiên làm việc khác (`POST /sessions/revoke-all`).
6. Test tự động đăng xuất sau 30 phút không hoạt động.

### Manual Verification
1. Đăng nhập vào hệ thống ➔ Vào trang Hồ sơ/Phiên đăng nhập ➔ Xem danh sách thiết bị đang hoạt động.
2. Mở trình duyệt ẩn danh (hoặc thiết bị khác) đăng nhập cùng tài khoản ➔ Thấy 2 phiên xuất hiện.
3. Bấm nút **"Đăng xuất khỏi thiết bị này"** ➔ Phiên kia bị hủy ngay lập tức.
4. Chờ thử nghiệm đếm ngược cảnh báo 5 phút trước khi hết phiên.

---

# Kế hoạch Triển khai Tính năng 1.6: Role & Permission Management (Quản lý vai trò & quyền hạn)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 1.6: Role & Permission Management (Quản lý vai trò & quyền hạn)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng các component Bootstrap 5, badge, modal, table và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 9 hạng mục con thuộc Mục 1.6 theo đúng mô hình Kiểm soát Truy cập Dựa trên Vai trò (RBAC - Role-Based Access Control) mở rộng:

1. **[x] User role assignment (USER/ADMIN/MODERATOR)**: Phân các vai trò người dùng mặc định và tùy chỉnh cho thành viên.
2. **[x] Role-based access control (RBAC)**: Kiểm soát truy cập trang web & API dựa trên vai trò và danh sách quyền hạn.
3. **[x] Custom role creation**: Cho phép Quản trị viên khởi tạo các Vai trò tùy chỉnh mới (Ví dụ: `TEACHER`, `CONTENT_EDITOR`, `ASSISTANT`).
4. **[x] Permission granularity**: Chi tiết hóa quyền hạn theo từng hành động cụ thể (ví dụ: `lessons:read`, `lessons:write`, `lessons:delete`, `users:manage`, `audit:read`).
5. **[x] Admin audit logs**: Nhật ký hệ thống tự động ghi lại toàn bộ các thao tác quản trị của Admin/Moderator (người thực hiện, hành động, đối tượng bị tác động, IP, thời gian).
6. **[x] Permission management interface**: Giao diện Quản lý Vai trò & Quyền hạn trực quan tại `/admin/roles`.
7. **[x] Role inheritance system**: Hệ thống kế thừa vai trò (Cấu trúc vai trò cha - vai trò con, vai trò con tự động nhận toàn bộ quyền của vai trò cha).
8. **[x] Temporary role assignment**: Phân vai trò có thời hạn (Hệ thống tự động hủy vai trò sau ngày/giờ hết hạn `expires_at`).
9. **[x] Permission templates**: Các mẫu quyền hạn dựng sẵn giúp nhanh chóng gán nhóm quyền (ví dụ: `Mẫu Quản trị Nội dung`, `Mẫu Quản lý Người dùng`).

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/admin/models.py` & `patch_db.py`)
Bổ sung các bảng dữ liệu quản lý phân quyền và nhật ký:

- **`Permission`**: Danh mục quyền hạn hệ thống (`name`, `description`, `category`).
- **`Role`**: Danh mục vai trò (`name`, `description`, `is_custom`, `parent_id` cho tính năng Kế thừa vai trò).
- **`RolePermission`**: Bảng liên kết Vai trò và Quyền hạn.
- **`UserRole`**: Bảng gán Vai trò cho Người dùng (`user_id`, `role_id`, `expires_at` cho Phân vai trò tạm thời).
- **`AuditLog`**: Bảng Nhật ký kiểm tra Admin (`user_id`, `action`, `target_type`, `target_id`, `details`, `ip_address`, `created_at`).

### 2.2. Helper Functions & Decorator kiểm tra quyền (`app/modules/admin/utils.py`)
- `has_permission(user, permission_name)`: Kiểm tra xem user có quyền hay không (bao gồm kiểm tra Admin, kiểm tra vai trò tạm thời chưa hết hạn, và kiểm tra Kế thừa vai trò từ `parent_id`).
- `@permission_required(permission_name)`: Decorator bảo vệ các route controller.
- `log_audit_action(user_id, action, target_type, target_id, details)`: Helper tự động ghi Audit Log khi admin thực hiện thao tác.

### 2.3. Controller & Routes (`app/modules/admin/routes.py`)
- `GET/POST /admin/roles`: Xem danh sách vai trò, tạo vai trò mới (chọn Kế thừa vai trò & chọn Permission Template).
- `POST /admin/roles/<role_id>/edit`: Chỉnh sửa danh sách quyền cho vai trò.
- `POST /admin/roles/<role_id>/delete`: Xóa vai trò tùy chỉnh.
- `POST /admin/users/<user_id>/assign-role`: Phân vai trò cho người dùng (hỗ trợ nhập Ngày hết hạn cho vai trò tạm thời).
- `GET /admin/audit-logs`: Xem nhật ký kiểm tra Admin Audit Logs với tìm kiếm & lọc theo hành động / thời gian.

### 2.4. Giao diện Quản trị (`app/templates/admin/`)
- `roles.html` [NEW]: Giao diện Quản lý Vai trò, Quyền hạn, Mẫu quyền & Kế thừa.
- `audit_logs.html` [NEW]: Giao diện Nhật ký kiểm tra Admin Audit Logs.
- `users.html` [UPDATE]: Tích hợp Modal Phân vai trò kèm Ngày hết hạn tạm thời.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_role_permission.py`)
1. Test tạo Vai trò tùy chỉnh kèm danh sách Quyền hạn.
2. Test Kế thừa vai trò (Role Inheritance: Vai trò con kế thừa quyền của Vai trò cha).
3. Test Phân vai trò tạm thời có thời hạn `expires_at` (hết hạn ➔ mất quyền).
4. Test Kiểm soát truy cập RBAC với Decorator `@permission_required`.
5. Test ghi nhận và truy vấn Admin Audit Logs.

### Manual Verification
1. Truy cập `/admin/roles` ➔ Thao tác tạo Vai trò tùy chỉnh mới và áp dụng Mẫu quyền.
2. Truy cập `/admin/users` ➔ Gán vai trò mới hoặc vai trò tạm thời cho 1 học viên.
3. Kiểm tra trang `/admin/audit-logs` để nghiệm thu nhật ký thao tác vừa thực hiện.