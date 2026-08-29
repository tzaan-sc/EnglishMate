# DANH SÁCH TÍNH NĂNG CHI TIẾT CHO WEB-ENGLISH LEARNING SYSTEM

## 1. AUTHENTICATION & USER MANAGEMENT

### 1.1. User Registration & Login

#### TÍNH NĂNG
- User Registration with email validation - Đăng ký người dùng mới với xác thực email
- User Login with session management - Đăng nhập với quản lý session
- Social Login Integration (Google, Facebook, Apple, LinkedIn) - Đăng nhập qua mạng xã hội
- Password Reset via Email - Khôi phục mật khẩu qua email
- Email Verification System - Xác thực email người dùng
- Two-Factor Authentication (2FA) - Xác thực hai yếu tố
- Biometric Authentication (Fingerprint, Face ID) - Xác thực sinh trắc học
- Magic Link Authentication - Xác thực qua link ma thuật
- Remember Me Functionality - Chức năng "Ghi nhớ đăng nhập"
- Login Attempt Limiting - Giới hạn số lần đăng nhập thất bại
- Session Timeout & Auto-logout - Tự động đăng xuất sau thời gian không hoạt động
- Device Management - Quản lý thiết bị đăng nhập
- Single Sign-On (SSO) - Đăng nhập một lần
- Account Recovery Flow - Quy trình khôi phục tài khoản
- Security Question Backup - Câu hỏi bảo mật dự phòng

#### CÁC NÚT (BUTTONS)
**Trang Login:**
- [Login Button] - Nút đăng nhập chính
- [Forgot Password Link] - Link quên mật khẩu
- [Register Button] - Nút chuyển sang đăng ký
- [Social Login Buttons] - Các nút đăng nhập mạng xã hội (Google, Facebook, Apple, LinkedIn)
- [Show/Hide Password Toggle] - Nút hiển thị/ẩn mật khẩu
- [Remember Me Checkbox] - Checkbox ghi nhớ đăng nhập

**Trang Register:**
- [Register Button] - Nút đăng ký chính
- [Back to Login Link] - Link quay lại đăng nhập
- [Social Register Buttons] - Các nút đăng ký mạng xã hội
- [Terms & Conditions Checkbox] - Checkbox điều khoản sử dụng
- [Privacy Policy Link] - Link chính sách bảo mật

**Trang Forgot Password:**
- [Send Reset Link Button] - Nút gửi link reset
- [Back to Login Link] - Link quay lại đăng nhập
- [Resend Email Button] - Nút gửi lại email (sau khi đã gửi)

**Trang Reset Password:**
- [Reset Password Button] - Nút reset mật khẩu
- [Show/Hide Password Toggles] - Nút hiển thị/ẩn mật khẩu (cả mật khẩu mới và xác nhận)
- [Back to Login Link] - Link quay lại đăng nhập

**Trang Email Verification:**
- [Resend Verification Button] - Nút gửi lại email xác thực
- [Change Email Button] - Nút thay đổi email
- [Continue to Dashboard Button] - Nút tiếp tục đến dashboard

**Trang 2FA Setup:**
- [Enable 2FA Button] - Nút bật 2FA
- [Disable 2FA Button] - Nút tắt 2FA
- [Generate QR Code Button] - Nút tạo mã QR
- [Verify Code Button] - Nút xác thực mã
- [Backup Codes Button] - Nút lấy mã dự phòng
- [Download Backup Codes Button] - Nút tải xuống mã dự phòng

#### BỐ CỤC UI/UX

**Layout Trang Login:**
```
┌─────────────────────────────────────────┐
│           Logo & Branding               │
├─────────────────────────────────────────┤
│                                         │
│        Welcome Back!                    │
│    Please login to your account         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Email Address                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Password [👁️]                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ☐ Remember me    Forgot Password?     │
│                                         │
│  [        Login Button        ]        │
│                                         │
│  ────────── OR ──────────              │
│                                         │
│  [Google] [Facebook] [Apple] [LinkedIn]│
│                                         │
│  Don't have an account? Register →     │
└─────────────────────────────────────────┘
```

**Layout Trang Register:**
```
┌─────────────────────────────────────────┐
│           Logo & Branding               │
├─────────────────────────────────────────┤
│                                         │
│         Create Account                  │
│    Join our learning community          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Full Name                      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Email Address                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Password [👁️]                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Confirm Password [👁️]          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ☐ I agree to Terms & Privacy Policy    │
│                                         │
│  [      Register Button       ]        │
│                                         │
│  ────────── OR ──────────              │
│                                         │
│  [Google] [Facebook] [Apple] [LinkedIn]│
│                                         │
│  Already have an account? Login ←      │
└─────────────────────────────────────────┘
```

**Layout Trang Forgot Password:**
```
┌─────────────────────────────────────────┐
│           Logo & Branding               │
├─────────────────────────────────────────┤
│                                         │
│         Forgot Password                 │
│  Enter your email to reset password     │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Email Address                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [    Send Reset Link Button    ]       │
│                                         │
│  ← Back to Login                        │
└─────────────────────────────────────────┘
```

**Layout Trang Reset Password:**
```
┌─────────────────────────────────────────┐
│           Logo & Branding               │
├─────────────────────────────────────────┤
│                                         │
│         Reset Password                  │
│    Create your new password            │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ New Password [👁️]              │   │
│  └─────────────────────────────────┘   │
│  • Password strength indicator         │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Confirm Password [👁️]          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [    Reset Password Button    ]       │
│                                         │
│  ← Back to Login                        │
└─────────────────────────────────────────┘
```

**Layout Device Management:**
```
┌─────────────────────────────────────────┐
│  ← Back    Device Management            │
├─────────────────────────────────────────┤
│                                         │
│  Current Devices (2)                    │
│  ┌─────────────────────────────────┐   │
│  │ 🖥️  Macbook Pro - Chrome        │   │
│  │    Current session              │   │
│  │    Last active: Just now        │   │
│  │    [Sign Out]                   │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📱  iPhone 13 - Safari          │   │
│  │    Last active: 2 hours ago     │   │
│  │    [Sign Out] [Remove Device]   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Revoke All Other Sessions]           │
└─────────────────────────────────────────┘
```

### 1.2. User Profile Management

#### TÍNH NĂNG
- Profile Information Editing - Chỉnh sửa thông tin hồ sơ
- Avatar Upload & Management - Tải lên và quản lý ảnh đại diện
- Profile Video Introduction - Video giới thiệu hồ sơ
- Password Change - Đổi mật khẩu
- Email Change Request - Yêu cầu đổi email
- Account Deactivation - Vô hiệu hóa tài khoản
- Account Deletion - Xóa tài khoản
- Learning Goal Settings - Thiết lập mục tiêu học tập
- Study Schedule Preferences - Tùy chọn lịch học tập
- Notification Preferences - Tùy chọn thông báo
- Privacy Settings - Cài đặt quyền riêng tư
- Language Preference Settings - Cài đặt ngôn ngữ ưu tiên
- Timezone Settings - Cài đặt múi giờ
- Learning Style Profile - Hồ sơ phong cách học tập
- Personalized Learning Path - Lộ trình học tập cá nhân hóa

#### CÁC NÚT (BUTTONS)
**Trang Profile:**
- [Edit Profile Button] - Nút chỉnh sửa hồ sơ
- [Change Avatar Button] - Nút thay đổi avatar
- [Upload Video Button] - Nút tải lên video giới thiệu
- [Change Password Button] - Nút đổi mật khẩu
- [Change Email Button] - Nút đổi email
- [Settings Button] - Nút cài đặt
- [Deactivate Account Button] - Nút vô hiệu hóa tài khoản
- [Delete Account Button] - Nút xóa tài khoản

**Trang Edit Profile:**
- [Save Changes Button] - Nút lưu thay đổi
- [Cancel Button] - Nút hủy
- [Upload Avatar Button] - Nút tải lên avatar
- [Remove Avatar Button] - Nút xóa avatar
- [Record Video Button] - Nút ghi video
- [Upload Video Button] - Nút tải lên video
- [Remove Video Button] - Nút xóa video

**Trang Settings:**
- [Save Settings Button] - Nút lưu cài đặt
- [Reset to Defaults Button] - Nút đặt lại mặc định
- [Test Notification Button] - Nút kiểm tra thông báo
- [Sync Calendar Button] - Nút đồng bộ lịch
- [Connect Social Accounts Button] - Nút kết nối tài khoản mạng xã hội

**Trang Learning Goals:**
- [Add Goal Button] - Nút thêm mục tiêu
- [Edit Goal Button] - Nút chỉnh sửa mục tiêu
- [Delete Goal Button] - Nút xóa mục tiêu
- [Set Primary Goal Button] - Nút đặt mục tiêu chính
- [Generate AI Suggestions Button] - Nút tạo gợi ý AI

#### BỐ CỤC UI/UX

**Layout Trang Profile:**
```
┌─────────────────────────────────────────┐
│  ← Back    My Profile                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         [Avatar Image]          │   │
│  │       [Change Avatar]           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Full Name: John Doe                   │
│  Username: @johndoe                     │
│  Email: john@example.com               │
│  Member since: January 2024            │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📹 Video Introduction           │   │
│  │ [Watch Video] [Record New]      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Learning Goals:                        │
│  • Reach B2 level in 6 months          │
│  • Learn 500 new words this month      │
│  [Add Goal]                            │
│                                         │
│  [Edit Profile] [Settings]             │
│                                         │
│  [Deactivate Account] [Delete Account] │
└─────────────────────────────────────────┘
```

**Layout Trang Edit Profile:**
```
┌─────────────────────────────────────────┐
│  ← Back    Edit Profile                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         [Avatar Preview]        │   │
│  │    [Upload] [Remove]            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Full Name                              │
│  ┌─────────────────────────────────┐   │
│  │ John Doe                       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Username                               │
│  ┌─────────────────────────────────┐   │
│  │ @johndoe                       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Bio                                    │
│  ┌─────────────────────────────────┐   │
│  │ Passionate English learner...  │   │
│  │ (max 500 characters)           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Location                               │
│  ┌─────────────────────────────────┐   │
│  │ Ho Chi Minh City, Vietnam      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Save Changes] [Cancel]               │
└─────────────────────────────────────────┘
```

**Layout Trang Settings:**
```
┌─────────────────────────────────────────┐
│  ← Back    Settings                    │
├─────────────────────────────────────────┤
│                                         │
│  Account Settings                        │
│  ┌─────────────────────────────────┐   │
│  │ ☑ Email notifications          │   │
│  │ ☑ Push notifications            │   │
│  │ ☐ SMS notifications             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Learning Preferences                    │
│  ┌─────────────────────────────────┐   │
│  │ Daily goal: 30 minutes          │   │
│  │ [▼]                             │   │
│  │                                 │   │
│  │ Preferred time: Morning         │   │
│  │ [▼]                             │   │
│  │                                 │   │
│  │ Learning style: Visual          │   │
│  │ [▼]                             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Privacy Settings                       │
│  ┌─────────────────────────────────┐   │
│  │ Profile visibility: Public      │   │
│  │ [▼]                             │   │
│  │                                 │   │
│  │ Show progress to: Friends only  │   │
│  │ [▼]                             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Save Settings] [Reset to Defaults]   │
└─────────────────────────────────────────┘
```

**Layout Trang Learning Goals:**
```
┌─────────────────────────────────────────┐
│  ← Back    Learning Goals               │
├─────────────────────────────────────────┤
│                                         │
│  [Generate AI Suggestions] [Add Goal]   │
│                                         │
│  Active Goals (3)                       │
│  ┌─────────────────────────────────┐   │
│  │ 🎯 Reach B2 level               │   │
│  │    Target: December 2024        │   │
│  │    Progress: ████████░░ 80%     │   │
│  │    [Edit] [Delete] [Set Primary]│   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📚 Learn 500 new words          │   │
│  │    Target: This month          │   │
│  │    Progress: ██████░░░░ 60%     │   │
│  │    [Edit] [Delete]              │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 🎤 Improve speaking skills     │   │
│  │    Target: 3 months             │   │
│  │    Progress: ███░░░░░░░ 30%     │   │
│  │    [Edit] [Delete]              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Completed Goals (5) [Show All]        │
│  ┌─────────────────────────────────┐   │
│  │ ✓ Complete A1 level            │   │
│  │    Completed: March 2024       │   │
│  │    [View Details]              │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 1.3. Role & Permission Management

#### TÍNH NĂNG
- User Role Assignment (USER, ADMIN, MODERATOR, TEACHER, STUDENT) - Phân vai trò người dùng
- Role-based Access Control - Kiểm soát truy cập dựa trên vai trò
- Custom Role Creation - Tạo vai trò tùy chỉnh
- Permission Granularity - Chi tiết hóa quyền hạn
- Moderator Permissions - Quyền hạn của người điều hành
- Teacher Permissions - Quyền hạn giáo viên
- Admin Audit Logs - Nhật ký kiểm tra của admin
- Permission Management Interface - Giao diện quản lý quyền hạn
- Role Inheritance System - Hệ thống kế thừa vai trò
- Temporary Role Assignment - Phân vai trò tạm thời
- Permission Templates - Mẫu quyền hạn
- Audit Trail for Permission Changes - Nhật ký thay đổi quyền hạn

#### CÁC NÚT (BUTTONS)
**Trang User Management (Admin):**
- [Add User Button] - Nút thêm người dùng
- [Edit User Button] - Nút chỉnh sửa người dùng
- [Delete User Button] - Nút xóa người dùng
- [Change Role Button] - Nút thay đổi vai trò
- [View Permissions Button] - Nút xem quyền hạn
- [Assign Role Button] - Nút gán vai trò
- [Revoke Role Button] - Nút thu hồi vai trò
- [View Activity Log Button] - Nút xem nhật ký hoạt động
- [Export Users Button] - Nút xuất danh sách người dùng
- [Import Users Button] - Nút nhập danh sách người dùng

**Trang Role Management:**
- [Create Role Button] - Nút tạo vai trò
- [Edit Role Button] - Nút chỉnh sửa vai trò
- [Delete Role Button] - Nút xóa vai trò
- [Clone Role Button] - Nút sao chép vai trò
- [View Permissions Button] - Nút xem quyền hạn
- [Assign Permissions Button] - Nút gán quyền hạn
- [Remove Permission Button] - Nút xóa quyền hạn
- [View Users in Role Button] - Nút xem người dùng trong vai trò

**Trang Permission Templates:**
- [Create Template Button] - Nút tạo mẫu
- [Edit Template Button] - Nút chỉnh sửa mẫu
- [Delete Template Button] - Nút xóa mẫu
- [Apply Template Button] - Nút áp dụng mẫu
- [Duplicate Template Button] - Nút sao chép mẫu

#### BỐ CỤC UI/UX

**Layout Trang User Management:**
```
┌─────────────────────────────────────────┐
│  User Management    [Add User] [Export] │
├─────────────────────────────────────────┤
│  Search: [_______________] [Filter]      │
│  Role: [All ▼] Status: [All ▼]          │
├─────────────────────────────────────────┤
│  Name           Email       Role  Action │
│  ────────────────────────────────────── │
│  John Doe       john@...    ADMIN [Edit]│
│  Jane Smith     jane@...    USER  [Edit]│
│  Bob Johnson    bob@...     MOD   [Edit]│
│  ────────────────────────────────────── │
│  Showing 1-3 of 150 users               │
│  [Previous] [1] [2] [3] ... [Next]      │
└─────────────────────────────────────────┘
```

**Layout Trang Edit User Role:**
```
┌─────────────────────────────────────────┐
│  ← Back    Edit User Role               │
├─────────────────────────────────────────┤
│                                         │
│  User: John Doe (john@example.com)      │
│  Current Role: ADMIN                    │
│                                         │
│  Assign New Role:                       │
│  ┌─────────────────────────────────┐   │
│  │ [▼ USER]                       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Available Roles:                       │
│  • USER - Basic access                  │
│  • ADMIN - Full system access           │
│  • MODERATOR - Content moderation       │
│  • TEACHER - Course management          │
│  • STUDENT - Learning access            │
│                                         │
│  Temporary Assignment:                  │
│  ☐ Assign temporarily                  │
│  Expires: [Date picker]                 │
│                                         │
│  [Save Changes] [Cancel]                │
└─────────────────────────────────────────┘
```

**Layout Trang Role Management:**
```
┌─────────────────────────────────────────┐
│  Role Management    [Create Role]       │
├─────────────────────────────────────────┤
│                                         │
│  System Roles (5)                       │
│  ┌─────────────────────────────────┐   │
│  │ ADMIN                           │   │
│  │ Full system access              │   │
│  │ 25 users assigned               │   │
│  │ [Edit] [View Permissions]       │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ USER                            │   │
│  │ Basic learning access           │   │
│  │ 125 users assigned              │   │
│  │ [Edit] [View Permissions]       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Custom Roles (3)                       │
│  ┌─────────────────────────────────┐   │
│  │ CONTENT_EDITOR                 │   │
│  │ Can edit lessons and vocabulary │   │
│  │ 8 users assigned               │   │
│  │ [Edit] [Clone] [Delete]        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Create Custom Role]                   │
└─────────────────────────────────────────┘
```

## 2. AI TUTOR & VIRTUAL ASSISTANT

### 2.1. AI Tutor System

#### TÍNH NĂNG
- 24/7 AI Tutor Availability - Gia sư AI sẵn sàng 24/7
- Natural Language Conversations - Cuộc hội thoại ngôn ngữ tự nhiên
- Personalized Learning Conversations - Cuộc hội thoại học tập cá nhân hóa
- Context-aware Responses - Phản hồi có ngữ cảnh
- Multi-turn Dialog Management - Quản lý hội thoại nhiều vòng
- Emotional Intelligence Integration - Tích hợp trí tuệ cảm xúc
- Learning History Awareness - Nhận thức lịch sử học tập
- Adaptive Teaching Strategies - Chiến lược dạy thích ứng
- Question Generation - Tạo câu hỏi
- Explanation Generation - Tạo giải thích
- Real-time Error Correction - Sửa lỗi thời gian thực
- Learning Pacing Adjustment - Điều chỉnh tốc độ học
- Motivational Support - Hỗ trợ động viên
- Cultural Context Explanation - Giải thích ngữ cảnh văn hóa
- Idiom & Expression Teaching - Dạy thành ngữ và cách diễn đạt
- Pronunciation Coaching - Huấn luyện phát âm

#### CÁC NÚT (BUTTONS)
**AI Tutor Interface:**
- [Start Conversation Button] - Nút bắt đầu hội thoại
- [Voice Input Button] - Nút nhập giọng nói
- [Text Input Button] - Nút nhập văn bản
- [Send Message Button] - Nút gửi tin nhắn
- [Clear Chat Button] - Nút xóa chat
- [Save Conversation Button] - Nút lưu hội thoại
- [Export Chat Button] - Nút xuất chat
- [Topic Selection Button] - Nút chọn chủ đề
- [Difficulty Level Button] - Nút chọn cấp độ độ khó
- [Practice Mode Button] - Nút chế độ luyện tập
- [Explanation Request Button] - Nút yêu cầu giải thích
- [Example Request Button] - Nút yêu cầu ví dụ
- [Translation Button] - Nút dịch
- [Pronunciation Practice Button] - Nút luyện phát âm
- [Cultural Context Button] - Nút ngữ cảnh văn hóa
- [Feedback Button] - Nút phản hồi

#### BỐ CỤC UI/UX

**Layout AI Tutor Interface:**
```
┌─────────────────────────────────────────┐
│  ← Back    AI Tutor                    │
├─────────────────────────────────────────┤
│  Topic: [Grammar ▼] Level: [B1 ▼]      │
│  Mode: [Conversation ▼]                 │
├─────────────────────────────────────────┤
│                                         │
│  💬 AI Tutor Conversation               │
│  ┌─────────────────────────────────┐   │
│  │ AI: Hello! I'm your AI tutor.   │   │
│  │    What would you like to learn │   │
│  │    today?                        │   │
│  │    [9:00 AM]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ You: I want to practice past    │   │
│  │    tense.                       │   │
│  │    [9:01 AM]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ AI: Great choice! Let's start   │   │
│  │    with a simple exercise. Can  │   │
│  │    you complete this sentence?  │   │
│  │    "I ___ to the store          │   │
│  │    yesterday."                  │   │
│  │    [9:01 AM]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ [🎤] [Type your message...]     │   │
│  │       [Send] [📎] [🌐]         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Quick Actions:                        │
│  [Explain] [Example] [Practice]       │
│  [Translate] [Pronunciation] [Cultural]│
└─────────────────────────────────────────┘
```

**Layout AI Tutor Practice Mode:**
```
┌─────────────────────────────────────────┐
│  ← Back    Practice Mode               │
├─────────────────────────────────────────┤
│  Exercise: Past Tense Practice         │
│  Difficulty: B1    Time: 5:00           │
├─────────────────────────────────────────┤
│                                         │
│  Question 1 of 10                        │
│  ┌─────────────────────────────────┐   │
│  │ Complete the sentence:         │   │
│  │ "I ___ (go) to the store       │   │
│  │  yesterday."                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Your Answer:                           │
│  ┌─────────────────────────────────┐   │
│  │ went                           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ✓ Correct! Great job!                 │
│                                         │
│  AI Feedback:                          │
│  "Perfect! 'Went' is the past tense   │
│   of 'go'. Remember that irregular     │
│   verbs like 'go' have special past    │
│   tense forms."                        │
│                                         │
│  [Next Question] [Skip] [Get Hint]     │
└─────────────────────────────────────────┘
```

### 2.2. Virtual Assistant Features

#### TÍNH NĂNG
- Voice-activated Assistant - Trợ lý kích hoạt bằng giọng nói
- Smart Schedule Management - Quản lý lịch thông minh
- Learning Reminders - Nhắc nhở học tập
- Progress Summary Generation - Tạo tóm tắt tiến độ
- Quick Learning Tips - Mẹo học tập nhanh
- Vocabulary Word of the Day - Từ vựng trong ngày
- Grammar Tip of the Day - Mẹo ngữ pháp trong ngày
- Learning Statistics Update - Cập nhật thống kê học tập
- Personalized Recommendations - Đề xuất cá nhân hóa
- Study Session Planning - Lập kế hoạch phiên học
- Break Time Reminders - Nhắc nhở thời gian nghỉ
- Motivational Messages - Tin nhắn động viên
- Achievement Celebrations - Chúc mừng thành tích
- Learning Goal Tracking - Theo dõi mục tiêu học tập
- Smart Content Discovery - Khám phá nội dung thông minh
- Quick Access to Resources - Truy cập nhanh tài nguyên

#### CÁC NÚT (BUTTONS)
**Virtual Assistant Interface:**
- [Activate Voice Button] - Nút kích hoạt giọng nói
- [Settings Button] - Nút cài đặt
- [Schedule Button] - Nút lịch
- [Reminders Button] - Nút nhắc nhở
- [Progress Button] - Nút tiến độ
- [Tips Button] - Nút mẹo
- [Word of the Day Button] - Nút từ vựng trong ngày
- [Recommendations Button] - Nút đề xuất
- [Quick Actions Button] - Nút hành động nhanh
- [Custom Commands Button] - Nút lệnh tùy chỉnh
- [History Button] - Nút lịch sử
- [Feedback Button] - Nút phản hồi

#### BỐ CỤC UI/UX

**Layout Virtual Assistant Dashboard:**
```
┌─────────────────────────────────────────┐
│  Virtual Assistant    [Settings] [⚙️]  │
├─────────────────────────────────────────┤
│                                         │
│  [🎤 Tap to speak or type command]      │
│                                         │
│  Quick Commands:                        │
│  [📅 Schedule] [⏰ Reminders]          │
│  [📊 Progress] [💡 Tips]               │
│  [📚 Word of Day] [🎯 Goals]           │
│                                         │
│  Today's Overview:                      │
│  ┌─────────────────────────────────┐   │
│  │ 📖 Study time: 45 minutes       │   │
│  │ 📝 Words learned: 12             │   │
│  │ 🔥 Streak: 7 days                │   │
│  │ ⭐ XP earned: 150                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Upcoming Reminders:                   │
│  • Review vocabulary at 2:00 PM        │
│  • Complete lesson at 4:00 PM          │
│                                         │
│  Recent Achievements:                   │
│  🏆 Completed 5-day streak!             │
│  🎯 Reached 100 words learned!         │
│                                         │
│  [View All Activity]                    │
└─────────────────────────────────────────┘
```

**Layout Smart Schedule Manager:**
```
┌─────────────────────────────────────────┐
│  ← Back    Smart Schedule              │
├─────────────────────────────────────────┤
│  [Today] [Week] [Month] [AI Plan]       │
├─────────────────────────────────────────┤
│                                         │
│  Today's Schedule - August 29, 2024    │
│                                         │
│  9:00 AM - 9:30 AM                     │
│  ┌─────────────────────────────────┐   │
│  │ 📖 Vocabulary Review           │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  10:00 AM - 11:00 AM                   │
│  ┌─────────────────────────────────┐   │
│  │ 📚 Grammar Lesson: Past Tense   │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  2:00 PM - 2:30 PM                     │
│  ┌─────────────────────────────────┐   │
│  │ 🎧 Listening Practice          │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Add Session] [AI Optimize Schedule]  │
└─────────────────────────────────────────┘
```

### 2.3. AI-powered Writing Assistant

#### TÍNH NĂNG
- Real-time Grammar Checking - Kiểm tra ngữ pháp thời gian thực
- Spelling Correction - Sửa chính tả
- Style Suggestions - Gợi ý phong cách
- Vocabulary Enhancement - Nâng cao từ vựng
- Sentence Structure Improvement - Cải thiện cấu trúc câu
- Tone Adjustment - Điều chỉnh giọng văn
- Plagiarism Detection - Phát hiện đạo văn
- Readability Analysis - Phân tích độ đọc
- Citation Suggestions - Gợi ý trích dẫn
- Paragraph Organization - Tổ chức đoạn văn
- Coherence Checking - Kiểm tra tính mạch lạc
- Writing Style Templates - Mẫu phong cách viết
- Formal/Informal Conversion - Chuyển đổi trang trọng/thông thường
- Academic Writing Assistance - Hỗ trợ viết học thuật
- Business Writing Assistance - Hỗ trợ viết kinh doanh
- Creative Writing Prompts - Đề bài viết sáng tạo

#### CÁC NÚT (BUTTONS)
**Writing Assistant Interface:**
- [New Document Button] - Nút tài liệu mới
- [Open Document Button] - Nút mở tài liệu
- [Save Document Button] - Nút lưu tài liệu
- [Export Document Button] - Nút xuất tài liệu
- [Check Grammar Button] - Nút kiểm tra ngữ pháp
- [Check Spelling Button] - Nút kiểm tra chính tả
- [Enhance Vocabulary Button] - Nút nâng cao từ vựng
- [Improve Structure Button] - Nút cải thiện cấu trúc
- [Adjust Tone Button] - Nút điều chỉnh giọng văn
- [Check Plagiarism Button] - Nút kiểm tra đạo văn
- [Analyze Readability Button] - Nút phân tích độ đọc
- [Apply Suggestions Button] - Nút áp dụng gợi ý
- [Ignore Suggestion Button] - Nút bỏ qua gợi ý
- [Get Writing Prompt Button] - Nút lấy đề bài viết
- [Use Template Button] - Nút sử dụng mẫu
- [Share Document Button] - Nút chia sẻ tài liệu

#### BỐ CỤC UI/UX

**Layout Writing Assistant Interface:**
```
┌─────────────────────────────────────────┐
│  ← Back    Writing Assistant           │
├─────────────────────────────────────────┤
│  [New] [Open] [Save] [Export] [Share]  │
├─────────────────────────────────────────┤
│  Document: My Essay    [Auto-save: ON] │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┬──────────────────┐│
│  │                  │                  ││
│  │   Text Editor    │  AI Suggestions  ││
│  │                  │                  ││
│  │  "I went to      │  🔴 Grammar:     ││
│  │   the store      │  "I goed" →      ││
│  │   yesterday."   │  "I went"        ││
│  │                  │  [Apply] [Ignore]││
│  │                 [▼]│                  ││
│  │                  │  🟡 Style:        ││
│  │                  │  Consider using  ││
│  │                  │  more varied     ││
│  │                  │  sentence        ││
│  │                  │  structures      ││
│  │                  │  [Apply] [Ignore]││
│  │                  │                  ││
│  │                  │  🟢 Vocabulary:   ││
│  │                  │  "store" →       ││
│  │                  │  "market"        ││
│  │                  │  [Apply] [Ignore]││
│  │                  │                  ││
│  └──────────────────┴──────────────────┘│
│                                         │
│  [Check Grammar] [Check Spelling]       │
│  [Enhance Vocab] [Improve Structure]    │
│  [Adjust Tone] [Check Plagiarism]      │
└─────────────────────────────────────────┘
```

**Layout Writing Templates:**
```
┌─────────────────────────────────────────┐
│  ← Back    Writing Templates            │
├─────────────────────────────────────────┤
│  Category: [All ▼] Level: [All ▼]       │
├─────────────────────────────────────────┤
│                                         │
│  Academic Writing                        │
│  ┌─────────────────────────────────┐   │
│  │ 📄 Essay Structure              │   │
│  │    Standard 5-paragraph essay    │   │
│  │    [Use Template] [Preview]     │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📄 Research Paper               │   │
│  │    Academic research format     │   │
│  │    [Use Template] [Preview]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Business Writing                       │
│  ┌─────────────────────────────────┐   │
│  │ 📄 Email Template               │   │
│  │    Professional email format     │   │
│  │    [Use Template] [Preview]     │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📄 Report Template              │   │
│  │    Business report structure    │   │
│  │    [Use Template] [Preview]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Creative Writing                       │
│  ┌─────────────────────────────────┐   │
│  │ 📄 Story Template               │   │
│  │    Narrative story structure    │   │
│  │    [Use Template] [Preview]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Create Custom Template]               │
└─────────────────────────────────────────┘
```

### 2.4. AI Speech Coach

#### TÍNH NĂNG
- Real-time Pronunciation Analysis - Phân tích phát âm thời gian thực
- Accent Reduction Training - Huấn luyện giảm giọng
- Intonation & Stress Training - Huấn luyện ngữ điệu và trọng âm
- Fluency Coaching - Huấn luyện độ trôi chảy
- Speech Pattern Analysis - Phân tích mẫu giọng nói
- Articulation Exercises - Bài tập phát âm
- Voice Recording & Comparison - Ghi âm và so sánh giọng nói
- Native Speaker Comparison - So sánh với người bản xứ
- Progress Tracking for Speaking - Theo dõi tiến độ nói
- Personalized Accent Training - Huấn luyện giọng cá nhân hóa
- Speech Tempo Control - Kiểm soát tốc độ nói
- Volume & Clarity Training - Huấn luyện âm lượng và độ rõ
- Conversation Practice Scenarios - Kịch bản luyện hội thoại
- Public Speaking Preparation - Chuẩn bị nói trước công chúng
- Presentation Skills Training - Huấn luyện kỹ năng thuyết trình
- Interview Preparation - Chuẩn bị phỏng vấn

#### CÁC NÚT (BUTTONS)
**Speech Coach Interface:**
- [Start Recording Button] - Nút bắt đầu ghi âm
- [Stop Recording Button] - Nút dừng ghi âm
- [Play Recording Button] - Nút phát ghi âm
- [Compare with Native Button] - Nút so sánh với bản xứ
- [Get Feedback Button] - Nút lấy phản hồi
- [Practice Word Button] - Nút luyện từ
- [Practice Phrase Button] - Nút luyện cụm từ
- [Practice Conversation Button] - Nút luyện hội thoại
- [Accent Training Button] - Nút huấn luyện giọng
- [Intonation Practice Button] - Nút luyện ngữ điệu
- [Fluency Training Button] - Nút huấn luyện độ trôi chảy
- [View Progress Button] - Nút xem tiến độ
- [Custom Exercise Button] - Nút bài tập tùy chỉnh
- [Scenario Practice Button] - Nút luyện kịch bản
- [Save Recording Button] - Nút lưu ghi âm
- [Share Recording Button] - Nút chia sẻ ghi âm

#### BỐ CỤC UI/UX

**Layout Speech Coach Interface:**
```
┌─────────────────────────────────────────┐
│  ← Back    AI Speech Coach             │
├─────────────────────────────────────────┤
│  Mode: [Pronunciation ▼] Level: [B1 ▼] │
├─────────────────────────────────────────┤
│                                         │
│  Word: "Pronunciation"                  │
│  ┌─────────────────────────────────┐   │
│  │  /prəˌnʌnsiˈeɪʃən/              │   │
│  │  [▶ Play native pronunciation] │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        [🎤 Record]               │   │
│  │    Tap to start recording       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Your Recording:                        │
│  ┌─────────────────────────────────┐   │
│  │  [▶ Play] [🗑️ Delete] [💾 Save] │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Analysis:                              │
│  ┌─────────────────────────────────┐   │
│  │ Accuracy: 85%                   │   │
│  │ ████████████░░░░░░░░░░░          │   │
│  │                                 │   │
│  │ 🔴 Stress: "nun" needs emphasis │   │
│  │ 🟡 Intonation: Good effort      │   │
│  │ 🟢 Clarity: Excellent            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Try Again] [Next Word] [Get Detailed]│
└─────────────────────────────────────────┘
```

**Layout Conversation Practice:**
```
┌─────────────────────────────────────────┐
│  ← Back    Conversation Practice        │
├─────────────────────────────────────────┤
│  Scenario: [Job Interview ▼]            │
├─────────────────────────────────────────┤
│                                         │
│  AI Interviewer:                        │
│  ┌─────────────────────────────────┐   │
│  │ "Tell me about yourself."        │   │
│  │ [▶ Play] [Show Script]          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Your Response:                         │
│  ┌─────────────────────────────────┐   │
│  │        [🎤 Record Response]     │   │
│  │    Tap when ready to answer     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Feedback:                              │
│  ┌─────────────────────────────────┐   │
│  │ 🟢 Fluency: Good flow           │   │
│  │ 🟡 Vocabulary: Use more          │   │
│  │    professional terms           │   │
│  │ 🔴 Grammar: Watch verb tenses   │   │
│  │                                 │   │
│  │ Suggestion: "I have experience  │   │
│  │ in..." → "I possess experience  │   │
│  │ in..."                          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Next Question] [Try Again] [Hint]    │
└─────────────────────────────────────────┘
```

## 3. VOCABULARY MODULE

### 3.1. Vocabulary Management

#### TÍNH NĂNG
- Word Database with Pronunciation - Cơ sở dữ liệu từ với phát âm
- Word Definition & Examples - Định nghĩa và ví dụ từ
- Word Categorization by Topic - Phân loại từ theo chủ đề
- Word Categorization by Level - Phân loại từ theo cấp độ
- Part of Speech Tagging - Gán loại từ
- Word Frequency Ranking - Xếp hạng tần suất từ
- Word Etymology Information - Thông tin nguồn gốc từ
- Word Usage Statistics - Thống kê sử dụng từ

#### CÁC NÚT (BUTTONS)
**Vocabulary List Interface:**
- [Add Word Button] - Nút thêm từ
- [Edit Word Button] - Nút chỉnh sửa từ
- [Delete Word Button] - Nút xóa từ
- [Search Button] - Nút tìm kiếm
- [Filter Button] - Nút lọc
- [Sort Button] - Nút sắp xếp
- [Import Words Button] - Nút nhập từ
- [Export Words Button] - Nút xuất từ
- [Mark as Learned Button] - Nút đánh dấu đã học
- [Add to Favorites Button] - Nút thêm vào yêu thích
- [Play Pronunciation Button] - Nút phát phát âm
- [View Examples Button] - Nút xem ví dụ
- [Practice Word Button] - Nút luyện từ
- [Share Word Button] - Nút chia sẻ từ
- [Report Word Button] - Nút báo cáo từ

**Word Detail Interface:**
- [Edit Word Button] - Nút chỉnh sửa từ
- [Delete Word Button] - Nút xóa từ
- [Play Pronunciation Button] - Nút phát phát âm
- [Add Example Button] - Nút thêm ví dụ
- [Add Synonym Button] - Nút thêm từ đồng nghĩa
- [Add Antonym Button] - Nút thêm từ trái nghĩa
- [Add Related Word Button] - Nút thêm từ liên quan
- [View Etymology Button] - Nút xem nguồn gốc
- [View Usage Statistics Button] - Nút xem thống kê sử dụng
- [Mark as Learned Button] - Nút đánh dấu đã học
- [Add to Set Button] - Nút thêm vào bộ
- [Share Word Button] - Nút chia sẻ từ

#### BỐ CỤC UI/UX

**Layout Vocabulary List:**
```
┌─────────────────────────────────────────┐
│  Vocabulary    [Add Word] [Import]      │
├─────────────────────────────────────────┤
│  Search: [_______________] [🔍]         │
│  Topic: [All ▼] Level: [All ▼]         │
│  Sort: [Alphabetical ▼]                 │
├─────────────────────────────────────────┤
│                                         │
│  Words (250)                            │
│  ┌─────────────────────────────────┐   │
│  │ ✓ abandon /əˈbændən/            │   │
│  │    v. bỏ rơi, từ bỏ             │   │
│  │    Topic: Daily Life • A2       │   │
│  │    [▶] [⭐] [📚] [⋮]           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ability /əˈbɪləti/              │   │
│  │    n. khả năng, năng lực        │   │
│  │    Topic: Skills • A1          │   │
│  │    [▶] [⭐] [📚] [⋮]           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ able /ˈeɪbl/                   │   │
│  │    adj. có thể, có khả năng    │   │
│  │    Topic: Skills • A1          │   │
│  │    [▶] [⭐] [📚] [⋮]           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Load More]                            │
└─────────────────────────────────────────┘
```

**Layout Word Detail:**
```
┌─────────────────────────────────────────┐
│  ← Back    Word Details                │
├─────────────────────────────────────────┤
│                                         │
│  abandon /əˈbændən/ [▶] [🔊]            │
│                                         │
│  Part of Speech: verb                   │
│  Level: A2    Topic: Daily Life          │
│  Frequency: Common                       │
│                                         │
│  Definitions:                           │
│  1. bỏ rơi, từ bỏ (to leave something) │
│  2. từ bỏ, chối bỏ (to give up)         │
│                                         │
│  Examples:                              │
│  ┌─────────────────────────────────┐   │
│  │ "The baby was abandoned by its  │   │
│  │  mother."                       │   │
│  │  [▶] [Translate]               │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ "He abandoned his car in the  │   │
│  │  street."                       │   │
│  │  [▶] [Translate]               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Synonyms: desert, leave, forsake       │
│  Antonyms: keep, retain, maintain       │
│                                         │
│  Related Words: abandonment,           │
│  abandoned (adj.)                      │
│                                         │
│  [Mark as Learned] [Add to Set]         │
│  [Practice] [Share] [Edit] [Delete]    │
└─────────────────────────────────────────┘
```

### 3.2. Vocabulary Learning Features

#### TÍNH NĂNG
- Flashcard System with Spaced Repetition - Hệ thống flashcard với lặp lại ngắt quãng
- Vocabulary Quiz Generator - Trình tạo quiz từ vựng
- Word Context Sentences - Câu ngữ cảnh từ
- Word Association Exercises - Bài tập liên kết từ
- Antonym & Synonym Learning - Học từ trái nghĩa và đồng nghĩa
- Word Family Learning - Học họ từ
- Collocation Learning - Học collocation
- Idiom & Phrase Learning - Học thành ngữ và cụm từ

#### CÁC NÚT (BUTTONS)
**Flashcard Interface:**
- [Start Session Button] - Nút bắt đầu phiên
- [Flip Card Button] - Nút lật thẻ
- [Know Button] - Nút biết
- [Don't Know Button] - Nút không biết
- [Skip Button] - Nút bỏ qua
- [Next Card Button] - Nút thẻ tiếp theo
- [Previous Card Button] - Nút thẻ trước
- [Shuffle Cards Button] - Nút xáo trộn thẻ
- [Reset Progress Button] - Nút đặt lại tiến độ
- [View Statistics Button] - Nút xem thống kê
- [Customize Deck Button] - Nút tùy chỉnh bộ
- [Share Deck Button] - Nút chia sẻ bộ

**Quiz Interface:**
- [Start Quiz Button] - Nút bắt đầu quiz
- [Submit Answer Button] - Nút gửi câu trả lời
- [Next Question Button] - Nút câu hỏi tiếp theo
- [Skip Question Button] - Nút bỏ qua câu hỏi
- [Hint Button] - Nút gợi ý
- [Review Answers Button] - Nút xem lại câu trả lời
- [Retry Quiz Button] - Nút làm lại quiz
- [View Results Button] - Nút xem kết quả
- [Customize Quiz Button] - Nút tùy chỉnh quiz

#### BỐ CỤC UI/UX

**Layout Flashcard Interface:**
```
┌─────────────────────────────────────────┐
│  ← Back    Flashcards                  │
├─────────────────────────────────────────┤
│  Deck: Daily Vocabulary • 50 cards     │
│  Progress: 25/50 completed             │
├─────────────────────────────────────────┤
│                                         │
│         ┌───────────────────┐           │
│         │                   │           │
│         │     abandon       │           │
│         │   /əˈbændən/      │           │
│         │                   │           │
│         │   [Tap to flip]   │           │
│         │                   │           │
│         └───────────────────┘           │
│                                         │
│  Card 26 of 50                          │
│  ████████████░░░░░░░░░░░░░░░░          │
│                                         │
│  [Previous] [Flip] [Next]               │
│                                         │
│  [🔀 Shuffle] [📊 Stats] [⚙️ Settings]  │
└─────────────────────────────────────────┘
```

**Layout Flashcard Back:**
```
┌─────────────────────────────────────────┐
│  ← Back    Flashcards                  │
├─────────────────────────────────────────┤
│  Deck: Daily Vocabulary • 50 cards     │
├─────────────────────────────────────────┤
│                                         │
│         ┌───────────────────┐           │
│         │   abandon        │           │
│         │   /əˈbændən/      │           │
│         │                   │           │
│         │  v. bỏ rơi,       │           │
│         │  từ bỏ            │           │
│         │                   │           │
│         │  "The baby was    │           │
│         │  abandoned..."    │           │
│         │                   │           │
│         └───────────────────┘           │
│                                         │
│  How well did you know this?            │
│  [Again] [Hard] [Good] [Easy]          │
│                                         │
│  [Previous] [Flip] [Next]               │
└─────────────────────────────────────────┘
```

**Layout Vocabulary Quiz:**
```
┌─────────────────────────────────────────┐
│  ← Back    Vocabulary Quiz             │
├─────────────────────────────────────────┤
│  Question 5 of 20    Score: 4/4         │
│  Time: 8:30                               │
├─────────────────────────────────────────┤
│                                         │
│  What does "abandon" mean?              │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ○ A. to keep something         │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ● B. to leave something        │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ C. to build something        │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ D. to buy something          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Submit] [Skip] [Hint] [50:50]         │
└─────────────────────────────────────────┘
```

### 3.3. Vocabulary Progress Tracking

#### TÍNH NĂNG
- Learned Words Counter - Bộ đếm từ đã học
- Review Schedule System - Hệ thống lịch ôn tập
- Mastery Level Tracking - Theo dõi cấp độ thành thạo
- Weak Word Identification - Xác định từ yếu
- Vocabulary Growth Chart - Biểu đồ phát triển từ vựng
- Daily Vocabulary Goals - Mục tiêu từ vựng hàng ngày
- Review Reminder System - Hệ thống nhắc nhở ôn tập
- Vocabulary Statistics Dashboard - Dashboard thống kê từ vựng

#### CÁC NÚT (BUTTONS)
**Progress Dashboard:**
- [View Details Button] - Nút xem chi tiết
- [Set Goal Button] - Nút đặt mục tiêu
- [Adjust Schedule Button] - Nút điều chỉnh lịch
- [Review Now Button] - Nút ôn tập ngay
- [View Weak Words Button] - Nút xem từ yếu
- [Export Progress Button] - Nút xuất tiến độ
- [Share Progress Button] - Nút chia sẻ tiến độ
- [View Analytics Button] - Nút xem phân tích
- [Customize Dashboard Button] - Nút tùy chỉnh dashboard

**Review Schedule Interface:**
- [Add Review Session Button] - Nút thêm phiên ôn tập
- [Edit Session Button] - Nút chỉnh sửa phiên
- [Delete Session Button] - Nút xóa phiên
- [Complete Session Button] - Nút hoàn thành phiên
- [Reschedule Button] - Nút lên lịch lại
- [Optimize Schedule Button] - Nút tối ưu lịch
- [Auto-schedule Button] - Nút lên lịch tự động

#### BỐ CỤC UI/UX

**Layout Vocabulary Progress Dashboard:**
```
┌─────────────────────────────────────────┐
│  Vocabulary Progress    [Settings]     │
├─────────────────────────────────────────┤
│                                         │
│  Overall Progress                        │
│  ┌─────────────────────────────────┐   │
│  │ 📚 Total Words: 500/1000         │   │
│  │ ████████████████░░░░░░░░░░░░░  │   │
│  │ 50% mastered                     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Today's Goal: 10 words                 │
│  ┌─────────────────────────────────┐   │
│  │ ✅ 8/10 completed               │   │
│  │ ██████████░░░░░░░░░░░░░░░░░░░  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Mastery Levels:                         │
│  ┌─────────────────────────────────┐   │
│  │ 🟢 Mastered: 200 words         │   │
│  │ 🟡 Familiar: 150 words         │   │
│  │ 🟠 Learning: 100 words         │   │
│  │ 🔴 New: 50 words               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Upcoming Reviews:                      │
│  • 25 words due today                  │
│  • 15 words due tomorrow               │
│  • 40 words due this week              │
│                                         │
│  [Review Now] [View Weak Words]         │
│  [View Analytics] [Adjust Schedule]    │
└─────────────────────────────────────────┘
```

**Layout Review Schedule:**
```
┌─────────────────────────────────────────┐
│  ← Back    Review Schedule             │
├─────────────────────────────────────────┤
│  [Today] [Week] [Month] [AI Optimize]  │
├─────────────────────────────────────────┤
│                                         │
│  Today - August 29, 2024                │
│                                         │
│  9:00 AM - Morning Review               │
│  ┌─────────────────────────────────┐   │
│  │ 📚 25 words due for review     │   │
│  │ Priority: High                  │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  2:00 PM - Afternoon Review            │
│  ┌─────────────────────────────────┐   │
│  │ 📚 15 words due for review     │   │
│  │ Priority: Medium                │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  7:00 PM - Evening Review              │
│  ┌─────────────────────────────────┐   │
│  │ 📚 40 words due for review     │   │
│  │ Priority: Low                   │   │
│  │ [Start] [Reschedule] [Skip]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Add Session] [Auto-schedule]         │
└─────────────────────────────────────────┘
```

## 4. LEARNING MODULE

### 4.1. Lesson Management

#### TÍNH NĂNG
- Lesson Creation & Editing - Tạo và chỉnh sửa bài học
- Lesson Categorization by Level (A1-C2) - Phân loại bài học theo cấp độ
- Lesson Categorization by Skill (Reading, Writing, Listening, Speaking, Grammar) - Phân loại theo kỹ năng
- Lesson Progress Tracking - Theo dõi tiến độ bài học
- Lesson Completion Marking - Đánh dấu hoàn thành bài học
- Lesson Search & Filter - Tìm kiếm và lọc bài học
- Lesson Bookmarking - Đánh dấu bài học yêu thích
- Lesson Recommendations - Đề xuất bài học dựa trên trình độ
- Lesson Difficulty Assessment - Đánh giá độ khó bài học
- Prerequisite Lesson System - Hệ thống bài học tiên quyết

#### CÁC NÚT (BUTTONS)
**Lesson List Interface:**
- [Start Lesson Button] - Nút bắt đầu bài học
- [Continue Lesson Button] - Nút tiếp tục bài học
- [Bookmark Lesson Button] - Nút đánh dấu bài học
- [Filter Button] - Nút lọc
- [Search Button] - Nút tìm kiếm
- [Sort Button] - Nút sắp xếp
- [View Progress Button] - Nút xem tiến độ
- [Share Lesson Button] - Nút chia sẻ bài học
- [Report Issue Button] - Nút báo cáo vấn đề
- [Download Materials Button] - Nút tải tài liệu

**Lesson Content Interface:**
- [Next Section Button] - Nút phần tiếp theo
- [Previous Section Button] - Nút phần trước
- [Complete Lesson Button] - Nút hoàn thành bài học
- [Bookmark Section Button] - Nút đánh dấu phần
- [Take Notes Button] - Nút ghi chú
- [Ask Question Button] - Nút đặt câu hỏi
- [Translate Button] - Nút dịch
- [Listen Button] - Nút nghe
- [Practice Button] - Nút luyện tập
- [View Resources Button] - Nút xem tài nguyên
- [Exit Lesson Button] - Nút thoát bài học

**Admin Lesson Management:**
- [Create Lesson Button] - Nút tạo bài học
- [Edit Lesson Button] - Nút chỉnh sửa bài học
- [Delete Lesson Button] - Nút xóa bài học
- [Duplicate Lesson Button] - Nút sao chép bài học
- [Publish Lesson Button] - Nút xuất bản bài học
- [Unpublish Lesson Button] - Nút hủy xuất bản bài học
- [Preview Lesson Button] - Nút xem trước bài học
- [Set Prerequisites Button] - Nút đặt tiên quyết
- [Manage Content Button] - Nút quản lý nội dung
- [View Analytics Button] - Nút xem phân tích

#### BỐ CỤC UI/UX

**Layout Lesson List:**
```
┌─────────────────────────────────────────┐
│  Lessons    [Search] [Filter] [Sort]    │
├─────────────────────────────────────────┤
│  Level: [All ▼] Skill: [All ▼]         │
│  Status: [All ▼] Progress: [All ▼]      │
├─────────────────────────────────────────┤
│                                         │
│  Recommended for You                    │
│  ┌─────────────────────────────────┐   │
│  │ 📖 Past Tense Basics            │   │
│  │    Grammar • A1 • 15 min        │   │
│  │    [▶ Start] [⭐ Bookmark]      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  In Progress (3)                        │
│  ┌─────────────────────────────────┐   │
│  │ 📖 Present Perfect              │   │
│  │    Grammar • A2 • 20 min        │   │
│  │    Progress: 60%                │   │
│  │    [▶ Continue] [⭐]           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Completed (5)                          │
│  ┌─────────────────────────────────┐   │
│  │ ✓ Present Simple                │   │
│  │    Grammar • A1 • 10 min        │   │
│  │    Completed yesterday          │   │
│  │    [🔄 Review] [⭐]             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [View All Lessons]                     │
└─────────────────────────────────────────┘
```

**Layout Lesson Content:**
```
┌─────────────────────────────────────────┐
│  ← Back    Past Tense Basics           │
├─────────────────────────────────────────┤
│  Progress: ████████░░░░ 80%             │
│  Section 4 of 5                         │
├─────────────────────────────────────────┤
│                                         │
│  Section 4: Irregular Verbs             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📖 Content                      │   │
│  │                                 │   │
│  │ Some verbs have irregular past  │   │
│  │ tense forms that don't follow  │   │
│  │ the regular -ed pattern.       │   │
│  │                                 │   │
│  │ Common irregular verbs:         │   │
│  │ • go → went                    │   │
│  │ • see → saw                    │   │
│  │ • eat → ate                    │   │
│  │                                 │   │
│  │ [▶ Listen] [🌐 Translate]      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📝 Practice                     │   │
│  │ Complete the sentence:         │   │
│  │ "I ___ (see) him yesterday."   │   │
│  │ [saw]                           │   │
│  │ [Check Answer]                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [📝 Notes] [❓ Ask] [⭐ Bookmark]     │
│  [Previous] [Next Section]              │
└─────────────────────────────────────────┘
```

**Layout Admin Lesson Editor:**
```
┌─────────────────────────────────────────┐
│  ← Back    Edit Lesson                 │
├─────────────────────────────────────────┤
│  [Save] [Preview] [Publish] [Delete]    │
├─────────────────────────────────────────┤
│                                         │
│  Lesson Title                           │
│  ┌─────────────────────────────────┐   │
│  │ Past Tense Basics              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Description                            │
│  ┌─────────────────────────────────┐   │
│  │ Learn the basics of past tense │   │
│  │ in English...                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Level: [A1 ▼]  Skill: [Grammar ▼]     │
│  Duration: 15 minutes  Difficulty: [1 ▼]│
│                                         │
│  Prerequisites:                         │
│  [Present Simple ▼] [+ Add]             │
│                                         │
│  Content Sections:                      │
│  ┌─────────────────────────────────┐   │
│  │ 1. Introduction [Edit] [Delete]│   │
│  │ 2. Regular Verbs [Edit] [Del] │   │
│  │ 3. Practice [Edit] [Delete]    │   │
│  │ [+ Add Section]               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Resources:                             │
│  [📎 Upload File] [+ Add Link]         │
└─────────────────────────────────────────┘
```

### 4.2. Grammar Learning

#### TÍNH NĂNG
- Grammar Rule Explanations - Giải thích quy tắc ngữ pháp
- Grammar Exercises - Bài tập ngữ pháp
- Grammar Quiz Generation - Tạo quiz ngữ pháp
- Error Correction Exercises - Bài tập sửa lỗi
- Fill-in-the-blank Exercises - Bài tập điền vào chỗ trống
- Grammar Progress Analytics - Phân tích tiến độ ngữ pháp
- Common Mistakes Database - Cơ sở dữ liệu lỗi thường gặp
- Grammar Reference Materials - Tài liệu tham khảo ngữ pháp

#### CÁC NÚT (BUTTONS)
**Grammar Lesson Interface:**
- [Start Exercise Button] - Nút bắt đầu bài tập
- [View Rule Button] - Nút xem quy tắc
- [Practice Button] - Nút luyện tập
- [Quiz Me Button] - Nút quiz tôi
- [View Examples Button] - Nút xem ví dụ
- [Common Mistakes Button] - Nút lỗi thường gặp
- [Reference Button] - Nút tham khảo
- [Notes Button] - Nút ghi chú
- [Progress Button] - Nút tiến độ

**Grammar Exercise Interface:**
- [Submit Answer Button] - Nút gửi câu trả lời
- [Check Answer Button] - Nút kiểm tra câu trả lời
- [Show Solution Button] - Nút hiển thị giải pháp
- [Next Exercise Button] - Nút bài tập tiếp theo
- [Previous Exercise Button] - Nút bài tập trước
- [Hint Button] - Nút gợi ý
- [Explanation Button] - Nút giải thích
- [Try Again Button] - Nút thử lại

#### BỐ CỤC UI/UX

**Layout Grammar Lesson:**
```
┌─────────────────────────────────────────┐
│  ← Back    Present Perfect Tense        │
├─────────────────────────────────────────┤
│  Progress: ██████░░░░░░░ 40%             │
├─────────────────────────────────────────┤
│                                         │
│  Rule: Present Perfect Tense             │
│  ┌─────────────────────────────────┐   │
│  │ Form: have/has + past participle│   │
│  │                                 │   │
│  │ Use:                            │   │
│  │ • Actions in the past with      │   │
│  │   present relevance            │   │
│  │ • Experiences                  │   │
│  │ • Recent changes               │   │
│  │                                 │   │
│  │ Examples:                       │   │
│  │ • I have finished my homework. │   │
│  │ • She has lived here for 5     │   │
│  │   years.                        │   │
│  │                                 │   │
│  │ [▶ Listen] [🌐 Translate]      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [View Examples] [Common Mistakes]       │
│  [Start Exercise] [Quiz Me]             │
└─────────────────────────────────────────┘
```

**Layout Grammar Exercise:**
```
┌─────────────────────────────────────────┐
│  ← Back    Grammar Exercise            │
├─────────────────────────────────────────┤
│  Exercise 3 of 10    Score: 2/2         │
├─────────────────────────────────────────┤
│                                         │
│  Choose the correct form:               │
│  "She ___ (work) here for 5 years."    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ○ A. work                      │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ● B. has worked               │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ C. working                   │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ D. works                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Submit] [Show Solution] [Hint]        │
└─────────────────────────────────────────┘
```

## 5. EXAMS & ASSESSMENT MODULE

### 5.1. Exam Management

#### TÍNH NĂNG
- Exam Creation Interface - Giao diện tạo đề thi
- Exam Template System - Hệ thống mẫu đề thi
- Question Bank Management - Quản lý ngân hàng câu hỏi
- Random Question Selection - Chọn câu hỏi ngẫu nhiên
- Exam Duration Settings - Cài đặt thời gian thi
- Exam Difficulty Configuration - Cấu hình độ khó đề thi
- Exam Categories (TOEIC, IELTS, TOEFL, Custom) - Phân loại đề thi
- Exam Versioning - Phiên bản hóa đề thi
- Exam Preview & Testing - Xem trước và kiểm tra đề thi

#### CÁC NÚT (BUTTONS)
**Exam List Interface:**
- [Create Exam Button] - Nút tạo đề thi
- [Take Exam Button] - Nút làm đề thi
- [Practice Mode Button] - Nút chế độ luyện tập
- [View Results Button] - Nút xem kết quả
- [Filter Button] - Nút lọc
- [Search Button] - Nút tìm kiếm
- [Sort Button] - Nút sắp xếp
- [Share Exam Button] - Nút chia sẻ đề thi

**Exam Creation Interface:**
- [Save Exam Button] - Nút lưu đề thi
- [Preview Exam Button] - Nút xem trước đề thi
- [Publish Exam Button] - Nút xuất bản đề thi
- [Add Question Button] - Nút thêm câu hỏi
- [Import Questions Button] - Nút nhập câu hỏi
- [Use Template Button] - Nút sử dụng mẫu
- [Randomize Questions Button] - Nút xáo trộn câu hỏi
- [Set Time Limit Button] - Nút đặt giới hạn thời gian
- [Configure Difficulty Button] - Nút cấu hình độ khó
- [Add Section Button] - Nút thêm phần

**Question Bank Interface:**
- [Add Question Button] - Nút thêm câu hỏi
- [Edit Question Button] - Nút chỉnh sửa câu hỏi
- [Delete Question Button] - Nút xóa câu hỏi
- [Duplicate Question Button] - Nút sao chép câu hỏi
- [Import Questions Button] - Nút nhập câu hỏi
- [Export Questions Button] - Nút xuất câu hỏi
- [Tag Question Button] - Nút gắn thẻ câu hỏi
- [Categorize Question Button] - Nút phân loại câu hỏi
- [Search Questions Button] - Nút tìm kiếm câu hỏi
- [Filter Questions Button] - Nút lọc câu hỏi

#### BỐ CỤC UI/UX

**Layout Exam List:**
```
┌─────────────────────────────────────────┐
│  Exams    [Create Exam] [Practice]     │
├─────────────────────────────────────────┤
│  Category: [All ▼] Level: [All ▼]      │
│  Status: [All ▼] Time: [All ▼]         │
├─────────────────────────────────────────┤
│                                         │
│  Available Exams (15)                    │
│  ┌─────────────────────────────────┐   │
│  │ 📝 TOEIC Practice Test #1       │   │
│  │    120 minutes • 200 questions  │   │
│  │    Best score: 750/990          │   │
│  │    [▶ Take] [📊 Results]       │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📝 IELTS Reading Practice      │   │
│  │    60 minutes • 40 questions   │   │
│  │    Not attempted yet           │   │
│  │    [▶ Take] [📖 Practice]     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Completed Exams (8)                     │
│  ┌─────────────────────────────────┐   │
│  │ ✓ Grammar Quiz #5              │   │
│  │    15 minutes • 20 questions   │   │
│  │    Score: 18/20 (90%)          │   │
│  │    [🔄 Retake] [📊 Details]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [View All Exams]                       │
└─────────────────────────────────────────┘
```

**Layout Exam Creation:**
```
┌─────────────────────────────────────────┐
│  ← Back    Create Exam                 │
├─────────────────────────────────────────┤
│  [Save] [Preview] [Publish] [Cancel]    │
├─────────────────────────────────────────┤
│                                         │
│  Exam Title                             │
│  ┌─────────────────────────────────┐   │
│  │ TOEIC Practice Test #2          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Category: [TOEIC ▼]  Level: [B1 ▼]    │
│  Duration: [120] minutes               │
│  Total Questions: [200]                 │
│  Passing Score: [60]%                    │
│                                         │
│  Exam Structure:                         │
│  ┌─────────────────────────────────┐   │
│  │ Part 1: Listening (45 min)      │   │
│  │   100 questions [Edit] [Delete] │   │
│  │                                 │   │
│  │ Part 2: Reading (75 min)        │   │
│  │   100 questions [Edit] [Delete] │   │
│  │                                 │   │
│  │ [+ Add Part]                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Questions:                             │
│  [Select from Bank] [Import] [Create]   │
│  Currently: 0/200 questions selected     │
│                                         │
│  Settings:                              │
│  ☑ Randomize question order             │
│  ☑ Show results immediately             │
│  ☐ Allow retake                        │
│  ☐ Time limit per question             │
└─────────────────────────────────────────┘
```

**Layout Question Bank:**
```
┌─────────────────────────────────────────┐
│  Question Bank    [Add Question]       │
├─────────────────────────────────────────┤
│  Search: [_______________] [🔍]         │
│  Type: [All ▼] Level: [All ▼]          │
│  Topic: [All ▼] Difficulty: [All ▼]     │
├─────────────────────────────────────────┤
│                                         │
│  Questions (1,250)                      │
│  ┌─────────────────────────────────┐   │
│  │ Q1: What is the past tense of  │   │
│  │    "go"?                        │   │
│  │    Type: Multiple Choice        │   │
│  │    Level: A1 • Grammar         │   │
│  │    [Edit] [Duplicate] [Delete] │   │
│  │    [Add to Exam]               │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ Q2: Choose the correct word:  │   │
│  │    "I ___ to the store..."    │   │
│  │    Type: Fill in the blank     │   │
│  │    Level: A2 • Grammar         │   │
│  │    [Edit] [Duplicate] [Delete] │   │
│  │    [Add to Exam]               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Load More] [Import] [Export]          │
└─────────────────────────────────────────┘
```

### 5.2. Exam Taking Experience

#### TÍNH NĂNG
- Countdown Timer - Đồng hồ đếm ngược
- Question Navigation - Điều hướng câu hỏi
- Flag Questions for Review - Đánh dấu câu hỏi để xem lại
- Auto-save Progress - Tự động lưu tiến độ
- Pause & Resume Functionality - Chức năng tạm dừng và tiếp tục
- Full-screen Mode - Chế độ toàn màn hình
- Anti-cheating Measures - Biện pháp chống gian lận

#### CÁC NÚT (BUTTONS)
**Exam Interface:**
- [Start Exam Button] - Nút bắt đầu thi
- [Submit Exam Button] - Nút nộp bài thi
- [Pause Button] - Nút tạm dừng
- [Resume Button] - Nút tiếp tục
- [Next Question Button] - Nút câu hỏi tiếp theo
- [Previous Question Button] - Nút câu hỏi trước
- [Flag Question Button] - Nút đánh dấu câu hỏi
- [Jump to Question Button] - Nút nhảy đến câu hỏi
- [Full Screen Button] - Nút toàn màn hình
- [Exit Full Screen Button] - Nút thoát toàn màn hình
- [Review Flagged Button] - Nút xem lại đánh dấu
- [Submit Early Button] - Nút nộp sớm

#### BỐ CỤC UI/UX

**Layout Exam Taking Interface:**
```
┌─────────────────────────────────────────┐
│  ← Exit    TOEIC Practice Test         │
├─────────────────────────────────────────┤
│  Time: 1:45:30    Question: 45/200      │
│  [⏸ Pause] [🚩 Flagged: 3] [📊]       │
├─────────────────────────────────────────┤
│                                         │
│  Question Navigator                     │
│  [1] [2] [3] ... [45] ... [200]        │
│  ⭐ = Flagged ✓ = Answered             │
├─────────────────────────────────────────┤
│                                         │
│  Question 45:                           │
│  ┌─────────────────────────────────┐   │
│  │ Read the passage and answer:   │   │
│  │                                 │   │
│  │ [Passage text here...]         │   │
│  │                                 │   │
│  │ What is the main idea?         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ○ A. To describe...            │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ● B. To explain...             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ C. To compare...             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ ○ D. To analyze...             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [🚩 Flag] [Previous] [Next] [Submit]   │
└─────────────────────────────────────────┘
```

**Layout Exam Summary Before Submit:**
```
┌─────────────────────────────────────────┐
│  ← Back    Exam Summary                │
├─────────────────────────────────────────┤
│                                         │
│  Exam Progress                          │
│  ┌─────────────────────────────────┐   │
│  │ Total Questions: 200            │   │
│  │ Answered: 180                    │   │
│  │ Skipped: 15                      │   │
│  │ Flagged: 5                       │   │
│  │                                 │   │
│  │ ████████████████░░░░░░░░░░░░░  │   │
│  │ 90% completed                   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Time Remaining: 14:30                  │
│                                         │
│  Flagged Questions (5):                  │
│  • Question 23 - Grammar               │
│  • Question 45 - Reading               │
│  • Question 78 - Listening             │
│  • Question 120 - Vocabulary           │
│  • Question 167 - Grammar              │
│                                         │
│  [Review Flagged] [Submit Exam]         │
│  [Continue Exam]                        │
└─────────────────────────────────────────┘
```

### 5.3. Exam Results & Analytics

#### TÍNH NĂNG
- Instant Score Calculation - Tính điểm tức thì
- Detailed Answer Review - Xem lại chi tiết câu trả lời
- Performance Analytics by Skill - Phân tích hiệu suất theo kỹ năng
- Time Spent per Question - Thời gian dành cho mỗi câu hỏi
- Comparison with Peers - So sánh với người học khác
- Historical Performance Tracking - Theo dõi hiệu suất lịch sử
- Strength & Weakness Analysis - Phân tích điểm mạnh/yếu
- Improvement Suggestions - Đề xuất cải thiện

#### CÁC NÚT (BUTTONS)
**Results Interface:**
- [View Detailed Results Button] - Nút xem kết quả chi tiết
- [Review Answers Button] - Nút xem lại câu trả lời
- [Download Report Button] - Nút tải báo cáo
- [Share Results Button] - Nút chia sẻ kết quả
- [Retake Exam Button] - Nút làm lại đề thi
- [View Analytics Button] - Nút xem phân tích
- [Compare with Peers Button] - Nút so sánh với người khác
- [View History Button] - Nút xem lịch sử
- [Get Recommendations Button] - Nút lấy đề xuất
- [Print Certificate Button] - Nút in chứng chỉ

**Analytics Interface:**
- [View Performance Chart Button] - Nút xem biểu đồ hiệu suất
- [Analyze Strengths Button] - Nút phân tích điểm mạnh
- [Analyze Weaknesses Button] - Nút phân tích điểm yếu
- [Compare Time Spent Button] - Nút so sánh thời gian
- [View Progress Over Time Button] - Nút xem tiến độ theo thời gian
- [Export Analytics Button] - Nút xuất phân tích
- [Set Improvement Goals Button] - Nút đặt mục tiêu cải thiện

#### BỐ CỤC UI/UX

**Layout Exam Results:**
```
┌─────────────────────────────────────────┐
│  ← Back    Exam Results                │
├─────────────────────────────────────────┤
│  TOEIC Practice Test #1                │
│  Completed: August 29, 2024            │
├─────────────────────────────────────────┤
│                                         │
│  Overall Score                          │
│  ┌─────────────────────────────────┐   │
│  │      750 / 990                 │   │
│  │     76%                        │   │
│  │  ████████████████░░░░░░░░░░░░░  │   │
│  │  Passed!                       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Performance by Section:                 │
│  ┌─────────────────────────────────┐   │
│  │ Listening: 380/495 (77%)       │   │
│  │ ████████████████░░░░░░░░░░░░░  │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ Reading: 370/495 (75%)         │   │
│  │ ████████████████░░░░░░░░░░░░░  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Time Analysis:                         │
│  • Total time: 1:58:30                  │
│  • Average per question: 35s           │
│  • Fastest section: Part 1 (20s/q)      │
│  • Slowest section: Part 7 (45s/q)      │
│                                         │
│  [View Detailed Answers] [Analytics]    │
│  [Retake Exam] [Share Results]           │
└─────────────────────────────────────────┘
```

**Layout Performance Analytics:**
```
┌─────────────────────────────────────────┐
│  ← Back    Performance Analytics        │
├─────────────────────────────────────────┤
│  [Weekly] [Monthly] [All Time]          │
├─────────────────────────────────────────┤
│                                         │
│  Score Trend                            │
│  ┌─────────────────────────────────┐   │
│  │    📈 Chart Here               │   │
│  │    Score progression over time │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Strengths                              │
│  ┌─────────────────────────────────┐   │
│  │ 🟢 Grammar: 85% average         │   │
│  │ 🟢 Vocabulary: 82% average      │   │
│  │ 🟡 Listening: 77% average       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Areas for Improvement                  │
│  ┌─────────────────────────────────┐   │
│  │ 🔴 Reading: 75% average        │   │
│  │    Suggestion: Practice more   │   │
│  │    reading comprehension       │   │
│  │                                 │   │
│  │ 🔴 Writing: 68% average        │   │
│  │    Suggestion: Focus on essay  │   │
│  │    structure and grammar       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Get Personalized Study Plan]          │
│  [View Detailed Report]                  │
└─────────────────────────────────────────┘
```

## 6. DASHBOARD & PROGRESS TRACKING

### 6.1. Personal Dashboard

#### TÍNH NĂNG
- Personal Learning Dashboard - Dashboard học tập cá nhân
- Overall Progress Overview - Tổng quan tiến độ
- Skill-specific Progress - Tiến độ theo kỹ năng cụ thể
- Time Spent Learning - Thời gian học tập
- Activity Heatmap - Bản đồ nhiệt hoạt động
- Learning Calendar - Lịch học tập
- Performance Trends - Xu hướng hiệu suất
- Goal Completion Tracking - Theo dõi hoàn thành mục tiêu

#### CÁC NÚT (BUTTONS)
**Dashboard Interface:**
- [Start Learning Button] - Nút bắt đầu học
- [Continue Course Button] - Nút tiếp tục khóa học
- [View Progress Button] - Nút xem tiến độ
- [Set Goals Button] - Nút đặt mục tiêu
- [View Schedule Button] - Nút xem lịch
- [View Achievements Button] - Nút xem thành tích
- [Customize Dashboard Button] - Nút tùy chỉnh dashboard
- [Share Progress Button] - Nút chia sẻ tiến độ
- [Get Recommendations Button] - Nút lấy đề xuất
- [View Analytics Button] - Nút xem phân tích

#### BỐ CỤC UI/UX

**Layout Personal Dashboard:**
```
┌─────────────────────────────────────────┐
│  Welcome, John!    [⚙️ Settings]      │
├─────────────────────────────────────────┤
│                                         │
│  Today's Overview                        │
│  ┌─────────────────────────────────┐   │
│  │ 🔥 7-day streak!                │   │
│  │                                 │   │
│  │ 📖 45/60 minutes studied        │   │
│  │ ████████████░░░░░░░░░░░░░░░░  │   │
│  │                                 │   │
│  │ 📚 12/20 words learned          │   │
│  │ ████████████░░░░░░░░░░░░░░░░  │   │
│  │                                 │   │
│  │ ⭐ 150 XP earned today          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Quick Actions:                         │
│  [📖 Continue Lesson] [📝 Practice]    │
│  [🗣️ Speaking] [🎧 Listening]           │
│                                         │
│  This Week's Progress                   │
│  ┌─────────────────────────────────┐   │
│  │    📊 Activity Heatmap          │   │
│  │    M T W T F S S                │   │
│  │    ██ ██ ██ ██ ██ ░ ░          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Current Goals:                         │
│  ┌─────────────────────────────────┐   │
│  │ 🎯 Reach B2 level              │   │
│  │    80% completed               │   │
│  │    [View Details]              │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ 📚 Learn 500 words              │   │
│  │    60% completed               │   │
│  │    [View Details]              │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Recent Achievements:                   │
│  🏆 7-day streak champion               │
│  🎯 100 words milestone                │
│  ⭐ Grammar master                     │
│                                         │
│  [View All Progress] [Set New Goals]    │
└─────────────────────────────────────────┘
```

## SUMMARY

- **Tổng số module:** 6 (đã chi tiết hóa)
- **Tổng số sub-module:** 16
- **Tổng số feature:** 150+
- **Tổng số buttons được mô tả:** 200+
- **Tổng số layout được thiết kế:** 20+

### Các module đã chi tiết hóa:
1. **Authentication & User Management** - Quản lý người dùng và xác thực
2. **AI Tutor & Virtual Assistant** - Gia sư AI và trợ lý ảo
3. **Vocabulary Module** - Module từ vựng
4. **Learning Module** - Module học tập
5. **Exams & Assessment Module** - Module thi và đánh giá
6. **Dashboard & Progress Tracking** - Dashboard và theo dõi tiến độ

### Các module cần mở rộng thêm:
- Advanced Speech Recognition
- Advanced Analytics & Machine Learning
- Smart Content Recommendation
- Advanced Social Features
- Productivity & Time Management
- Virtual Reality & Augmented Reality
- Developer Tools & API
- Accessibility & Inclusivity
- Mobile & Cross-platform
- Advanced Security
- Intelligent Content Creation
- Blockchain & Web3 Features
- Internet of Things Integration

Tài liệu này cung cấp chi tiết về các nút (buttons) và bố cục (layouts) cần thiết cho việc phát triển giao diện người dùng cho từng module, giúp các nhà phát triển có thể trực tiếp triển khai mà không cần phải suy nghĩ nhiều về thiết kế UI/UX.