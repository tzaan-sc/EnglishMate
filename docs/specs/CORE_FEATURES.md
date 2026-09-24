# DANH SÁCH CHỨC NĂNG CỐT LÕI CHO WEB-ENGLISH LEARNING SYSTEM

## 1. AUTHENTICATION & USER MANAGEMENT

### 1.1. User Registration & Login

#### CHỨC NĂNG CỐT LÕI

**Đăng ký bằng email/password** - Cho phép người dùng tạo tài khoản mới với email và mật khẩu, bao gồm kiểm tra định dạng email hợp lệ, xác thực độ mạnh mật khẩu, và lưu trữ thông tin an toàn vào database.

**Đăng nhập bằng email/password** - Cho phép người dùng đăng nhập với email và mật khẩu đã đăng ký, với session management và remember me functionality.

**Quên mật khẩu** - Cho phép người dùng khôi phục mật khẩu qua email, gửi link reset có hiệu lực trong 1 giờ, yêu cầu đặt mật khẩu mới.

**Đổi mật khẩu** - Cho phép người dùng thay đổi mật khẩu khi đã đăng nhập, yêu cầu nhập mật khẩu cũ để xác thực, mật khẩu mới phải khác mật khẩu cũ.

**Xác thực email** - Gửi mã xác nhận 6 digits đến email sau khi đăng ký, yêu cầu nhập mã để kích hoạt tài khoản, mã có hiệu lực trong 15 phút.

**Đăng xuất** - Cho phép người dùng đăng xuất an toàn, xóa session, xóa cookies, redirect về trang đăng nhập.

#### CÁC NÚT CỐT LÕI

**[Login Button]** - Nút đăng nhập chính với validation, loading state khi đang xử lý, disabled khi form không hợp lệ.

**[Register Button]** - Nút đăng ký mới với validation email/password, loading state khi đang tạo tài khoản, success notification.

**[Forgot Password Link]** - Link đến trang quên mật khẩu, gửi email reset khi nhập email hợp lệ.

**[Reset Password Button]** - Nút đặt lại mật khẩu mới, validation độ mạnh mật khẩu, update password trong database.

**[Change Password Button]** - Nút đổi mật khẩu trong profile, yêu cầu mật khẩu cũ, validation mật khẩu mới.

**[Logout Button]** - Nút đăng xuất, xóa session và cookies, redirect về trang login.

**[Verify Email Button]** - Nút xác thực email với mã 6 digits, validation mã, kích hoạt tài khoản khi thành công.

**[Resend Verification Button]** - Nút gửi lại mã xác thực, countdown 60s, giới hạn 3 lần gửi.

### 1.2. User Profile Management

#### CHỨC NĂNG CỐT LÕI

**Chỉnh sửa hồ sơ cơ bản** - Cho phép người dùng chỉnh sửa tên hiển thị, username, bio, với validation real-time.

**Avatar upload** - Cho phép tải lên ảnh đại diện, support formats (JPG, PNG), max size 2MB, auto-resize.

**Cài đặt thông báo** - Cho phép người dùng tùy chọn nhận thông báo qua email, thông báo trong ứng dụng.

**Cài đặt ngôn ngữ** - Cho phép chọn ngôn ngữ giao diện (English, Vietnamese).

**Cài đặt múi giờ** - Cho phép chọn múi giờ để hiển thị thời gian chính xác.

#### CÁC NÚT CỐT LÕI

**[Edit Profile Button]** - Nút chỉnh sửa thông tin hồ sơ, mở form edit, validation real-time.

**[Upload Avatar Button]** - Nút tải lên ảnh đại diện, file picker, preview ảnh, validation format/size.

**[Save Profile Button]** - Nút lưu thay đổi hồ sơ, validation trước khi lưu, success notification.

**[Update Settings Button]** - Nút cập nhật cài đặt, lưu preferences, apply changes immediately.

**[Cancel Button]** - Nút hủy chỉnh sửa, discard changes, return về view mode.

## 2. VOCABULARY MODULE

### 2.1. Vocabulary Management

#### CHỨC NĂNG CỐT LÕI

**Danh sách từ vựng** - Hiển thị danh sách từ vựng với thông tin cơ bản (từ, phát âm, nghĩa, ví dụ), phân loại theo chủ đề và cấp độ.

**Tìm kiếm từ vựng** - Cho phép tìm kiếm từ vựng theo từ tiếng Anh hoặc nghĩa tiếng Việt, filtering theo chủ đề và cấp độ.

**Chi tiết từ vựng** - Hiển thị chi tiết thông tin từ: phát âm, loại từ, nghĩa, ví dụ tiếng Anh và Việt, chủ đề, cấp độ.

**Đánh dấu từ đã học** - Cho phép người dùng đánh dấu từ đã học, theo dõi tiến độ học từ vựng.

**Thêm từ vào yêu thích** - Cho phép người dùng thêm từ vào danh sách yêu thích để truy cập nhanh.

#### CÁC NÚT CỐT LÕI

**[Search Button]** - Nút tìm kiếm từ vựng, filter theo chủ đề/cấp độ, hiển thị kết quả.

**[View Detail Button]** - Nút xem chi tiết từ, hiển thị đầy đủ thông tin, phát âm audio.

**[Mark as Learned Button]** - Nút đánh dấu đã học, update progress, đổi trạng thái nút.

**[Add to Favorites Button]** - Nút thêm vào yêu thích, lưu vào danh sách favorites, icon heart.

**[Play Pronunciation Button]** - Nút phát âm từ, sử dụng text-to-speech, audio player basic.

**[Filter Button]** - Nút lọc theo chủ đề (Business, Daily Life, Education, etc.) và cấp độ (A1, A2, B1, B2).

### 2.2. Flashcard Learning

#### CHỨC NĂNG CỐT LÕI

**Hệ thống Flashcard** - Hiển thị từ vựng dưới dạng thẻ, mặt trước là từ tiếng Anh, mặt sau là nghĩa và ví dụ.

**Lật thẻ** - Cho phép người dùng lật thẻ để xem nghĩa, tap hoặc click để flip.

**Đánh giá nhớ** - Sau khi lật thẻ, người dùng đánh giá: "Đã nhớ" hoặc "Chưa nhớ" để hệ thống lên lịch ôn tập.

**Lên lịch ôn tập** - Hệ thống tự động lên lịch ôn tập dựa trên đánh giá nhớ, sử dụng spaced repetition cơ bản.

**Bộ flashcard theo chủ đề** - Cho phép chọn bộ flashcard theo chủ đề hoặc cấp độ để học tập có mục tiêu.

#### CÁC NÚT CỐT LÕI

**[Start Session Button]** - Nút bắt đầu phiên flashcard, chọn bộ thẻ, hiển thị số lượng thẻ.

**[Flip Card Button]** - Nút lật thẻ, animation flip, hiển thị mặt sau của thẻ.

**[Know Button]** - Nút "Đã nhớ", lên lịch ôn tập sau thời gian dài hơn, chuyển thẻ tiếp theo.

**[Don't Know Button]** - Nút "Chưa nhớ", lên lịch ôn tập sớm hơn, lặp lại thẻ trong phiên.

**[Next Card Button]** - Nút thẻ tiếp theo, skip thẻ hiện tại, không đánh giá.

**[Previous Card Button]** - Nút thẻ trước, quay lại thẻ đã qua, thay đổi đánh giá nếu cần.

**[Shuffle Button]** - Nút xáo trộn thứ tự thẻ, randomize để tăng tính hiệu quả.

**[Complete Session Button]** - Nút hoàn thành phiên, hiển thị kết quả, thống kê performance.

## 3. LEARNING MODULE

### 3.1. Lesson Management

#### CHỨC NĂNG CỐT LÕI

**Danh sách bài học** - Hiển thị danh sách bài học phân loại theo cấp độ (A1-C2) và kỹ năng (Grammar, Vocabulary, Reading, Listening, Speaking).

**Chi tiết bài học** - Hiển thị nội dung bài học với văn bản giải thích, ví dụ, bài tập thực hành.

**Tiến độ bài học** - Theo dõi tiến độ hoàn thành bài học của người dùng, đánh dấu bài học đã hoàn thành.

**Đánh dấu bài học yêu thích** - Cho phép người dùng đánh dấu bài học yêu thích để truy cập nhanh.

**Lọc bài học** - Cho phép lọc bài học theo cấp độ, kỹ năng, chủ đề, trạng thái (đang học, đã hoàn thành).

#### CÁC NÚT CỐT LÕI

**[Start Lesson Button]** - Nút bắt đầu bài học, load nội dung, bắt đầu tracking tiến độ.

**[Continue Lesson Button]** - Nút tiếp tục bài học đang dở, resume từ vị trí dừng.

**[Complete Lesson Button]** - Nút hoàn thành bài học, đánh dấu completed, update progress.

**[Bookmark Lesson Button]** - Nút đánh dấu bài học yêu thích, lưu vào danh sách bookmarks.

**[Filter Button]** - Nút lọc bài học theo cấp độ, kỹ năng, trạng thái.

**[Search Button]** - Nút tìm kiếm bài học theo tiêu đề hoặc nội dung.

**[Next Section Button]** - Nút phần tiếp theo trong bài học, navigation nội dung.

**[Previous Section Button]** - Nút phần trước, quay lại nội dung đã xem.

### 3.2. Grammar Learning

#### CHỨC NĂNG CỐT LÕI

**Giải thích ngữ pháp** - Hiển thị quy tắc ngữ pháp với ví dụ minh họa, giải thích rõ ràng dễ hiểu.

**Bài tập ngữ pháp** - Cung cấp bài tập thực hành để áp dụng quy tắc ngữ pháp vừa học.

**Kiểm tra đáp án** - Cho phép người dùng kiểm tra đáp án bài tập, hiển thị kết quả đúng/sai.

**Giải thích đáp án** - Hiển thị giải thích chi tiết cho từng đáp án, giúp người dùng hiểu lỗi sai.

**Theo dõi tiến độ ngữ pháp** - Theo dõi tiến độ học ngữ pháp theo từng chủ đề.

#### CÁC NÚT CỐT LÕI

**[View Rule Button]** - Nút xem quy tắc ngữ pháp, hiển thị giải thích và ví dụ.

**[Start Exercise Button]** - Nút bắt đầu bài tập, load câu hỏi, bắt đầu tracking.

**[Submit Answer Button]** - Nút gửi đáp án, kiểm tra đúng/sai, hiển thị kết quả.

**[Show Solution Button]** - Nút hiển thị đáp án đúng, giải thích chi tiết.

**[Next Exercise Button]** - Nút bài tập tiếp theo, load câu hỏi mới.

**[Retry Exercise Button]** - Nút làm lại bài tập, reset answers, thử lại.

**[View Progress Button]** - Nút xem tiến độ ngữ pháp, thống kê theo chủ đề.

## 4. EXAMS & ASSESSMENT MODULE

### 4.1. Quiz System

#### CHỨC NĂNG CỐT LÕI

**Danh sách quiz** - Hiển thị danh sách quiz phân loại theo chủ đề và cấp độ độ khó.

**Làm quiz** - Cho phép người dùng làm quiz với câu hỏi trắc nghiệm,有时间限制 tùy chọn.

**Kết quả quiz** - Hiển thị kết quả quiz với điểm số, số câu đúng/sai, thống kê chi tiết.

**Xem lại đáp án** - Cho phép người dùng xem lại đáp án và giải thích sau khi hoàn thành.

**Lịch sử quiz** - Theo dõi lịch sử làm quiz của người dùng, hiển thị tiến độ theo thời gian.

#### CÁC NÚT CỐT LÕI

**[Start Quiz Button]** - Nút bắt đầu quiz, load câu hỏi, bắt đầu timer.

**[Submit Answer Button]** - Nút gửi đáp án cho từng câu hỏi hoặc toàn bộ quiz.

**[Next Question Button]** - Nút câu hỏi tiếp theo, navigation trong quiz.

**[Previous Question Button]** - Nút câu hỏi trước, quay lại và thay đổi đáp án.

**[Submit Quiz Button]** - Nút nộp bài quiz, tính điểm, hiển thị kết quả.

**[View Results Button]** - Nút xem kết quả chi tiết, thống kê performance.

**[Review Answers Button]** - Nút xem lại đáp án, hiển thị giải thích.

**[Retake Quiz Button]** - Nút làm lại quiz, reset câu hỏi, thử lại.

### 4.2. Exam Management (Admin)

#### CHỨC NĂNG CỐT LÕI

**Tạo quiz mới** - Cho phép admin tạo quiz mới với câu hỏi, đáp án, giải thích.

**Chỉnh sửa quiz** - Cho phép admin chỉnh sửa quiz hiện có, thêm/sửa/xóa câu hỏi.

**Quản lý ngân hàng câu hỏi** - Cho phép admin quản lý ngân hàng câu hỏi dùng cho quiz.

**Xóa quiz** - Cho phép admin xóa quiz không còn cần thiết.

**Xem thống kê quiz** - Cho phép admin xem thống kê performance của quiz.

#### CÁC NÚT CỐT LÕI

**[Create Quiz Button]** - Nút tạo quiz mới, form tạo quiz, thêm câu hỏi.

**[Edit Quiz Button]** - Nút chỉnh sửa quiz, load existing quiz, modify nội dung.

**[Delete Quiz Button]** - Nút xóa quiz, confirmation dialog, xóa từ database.

**[Add Question Button]** - Nút thêm câu hỏi vào quiz, form câu hỏi, validation.

**[Edit Question Button]** - Nút chỉnh sửa câu hỏi, modify question/answers/explanation.

**[Delete Question Button]** - Nút xóa câu hỏi, remove khỏi quiz.

**[View Statistics Button]** - Nút xem thống kê quiz, performance data, user results.

**[Publish Quiz Button]** - Nút xuất bản quiz, make available to users.

## 5. DASHBOARD & PROGRESS TRACKING

### 5.1. Personal Dashboard

#### CHỨC NĂNG CỐT LÕI

**Tổng quan tiến độ** - Hiển thị tổng quan tiến độ học tập: số bài học hoàn thành, số từ đã học, điểm trung bình quiz.

**Streak ngày học** - Hiển thị chuỗi ngày học liên tiếp, động viên người dùng học đều đặn.

**Bài học đề xuất** - Đề xuất bài học tiếp theo dựa trên tiến độ và level hiện tại.

**Hoạt động gần đây** - Hiển thị hoạt động học tập gần đây của người dùng.

**Mục tiêu học tập** - Hiển thị mục tiêu học tập và tiến độ đạt được.

#### CÁC NÚT CỐT LÕI

**[Continue Learning Button]** - Nút tiếp tục học, resume bài học đang dở hoặc đề xuất bài học mới.

**[View Progress Button]** - Nút xem tiến độ chi tiết, thống kê đầy đủ.

**[Set Goals Button]** - Nút đặt mục tiêu học tập, form mục tiêu, track progress.

**[View Activity Button]** - Nút xem hoạt động chi tiết, timeline activities.

**[Start Recommended Lesson Button]** - Nút bắt đầu bài học được đề xuất, direct đến lesson.

### 5.2. Progress Tracking

#### CHỨC NĂNG CỐT LÕI

**Thống kê chi tiết** - Hiển thị thống kê chi tiết theo từng kỹ năng: từ vựng, ngữ pháp, đọc, nghe, nói.

**Biểu đồ tiến độ** - Hiển thị biểu đồ tiến độ theo thời gian, giúp người dùng thấy sự cải thiện.

**Lịch sử hoạt động** - Hiển thị lịch sử hoạt động học tập chi tiết theo thời gian.

**So sánh với mục tiêu** - So sánh tiến độ thực tế với mục tiêu đã đặt.

**Xuất báo cáo** - Cho phép xuất báo cáo tiến độ để lưu hoặc chia sẻ.

#### CÁC NÚT CỐT LÕI

**[View Detailed Stats Button]** - Nút xem thống kê chi tiết, breakdown theo kỹ năng.

**[View Charts Button]** - Nút xem biểu đồ, visual progress representation.

**[Export Report Button]** - Nút xuất báo cáo, download progress report.

**[Adjust Goals Button]** - Nút điều chỉnh mục tiêu, modify existing goals.

**[View History Button]** - Nút xem lịch sử, chronological activity list.

## 6. ADMIN MANAGEMENT

### 6.1. User Management (Admin)

#### CHỨC NĂNG CỐT LÕI

**Danh sách người dùng** - Hiển thị danh sách tất cả người dùng với thông tin cơ bản.

**Chỉnh sửa người dùng** - Cho phép admin chỉnh sửa thông tin người dùng cơ bản.

**Vô hiệu hóa tài khoản** - Cho phép admin vô hiệu hóa tài khoản người dùng vi phạm.

**Xóa người dùng** - Cho phép admin xóa người dùng (với caution).

**Thống kê người dùng** - Hiển thị thống kê người dùng: tổng số, active, inactive, new registrations.

#### CÁC NÚT CỐT LÕI

**[Add User Button]** - Nút thêm người dùng mới, form registration admin.

**[Edit User Button]** - Nút chỉnh sửa thông tin người dùng, modify profile.

**[Deactivate User Button]** - Nút vô hiệu hóa tài khoản, disable login access.

**[Delete User Button]** - Nút xóa người dùng, confirmation dialog, hard delete.

**[View Statistics Button]** - Nút xem thống kê người dùng, dashboard analytics.

**[Export Users Button]** - Nút xuất danh sách người dùng, CSV export.

### 6.2. Content Management (Admin)

#### CHỨC NĂNG CỐT LÕI

**Quản lý bài học** - Cho phép admin tạo, chỉnh sửa, xóa bài học.

**Quản lý từ vựng** - Cho phép admin thêm, chỉnh sửa, xóa từ vựng.

**Quản lý câu hỏi** - Cho phép admin quản lý ngân hàng câu hỏi cho quiz.

**Xem thống kê nội dung** - Cho phép admin xem thống kê sử dụng nội dung.

**Phê duyệt nội dung** - Cho phép admin phê duyệt nội dung do người dùng tạo (nếu có).

#### CÁC NÚT CỐT LÕI

**[Create Lesson Button]** - Nút tạo bài học mới, form lesson creation.

**[Edit Lesson Button]** - Nút chỉnh sửa bài học, modify existing content.

**[Delete Lesson Button]** - Nút xóa bài học, confirmation dialog.

**[Add Vocabulary Button]** - Nút thêm từ vựng mới, form vocabulary entry.

**[Edit Vocabulary Button]** - Nút chỉnh sửa từ vựng, modify word details.

**[Delete Vocabulary Button]** - Nút xóa từ vựng, remove from database.

**[View Content Stats Button]** - Nút xem thống kê nội dung, usage analytics.

**[Publish Content Button]** - Nút xuất bản nội dung, make available to users.

## SUMMARY

### TỔNG QUAN CỐT LÕI

* **Tổng số module:** 6
* **Tổng số sub-module:** 12
* **Tổng số chức năng cốt lõi:** 50+
* **Tổng số nút cốt lõi:** 80+

### CÁC MODULE CỐT LÕI

1. **Authentication & User Management** - Xác thực và quản lý người dùng cơ bản
2. **Vocabulary Module** - Quản lý và học từ vựng với flashcard
3. **Learning Module** - Học bài học và ngữ pháp
4. **Exams & Assessment Module** - Hệ thống quiz và đánh giá
5. **Dashboard & Progress Tracking** - Dashboard và theo dõi tiến độ
6. **Admin Management** - Quản trị hệ thống cơ bản

### PHƯƠNG PHÁP XÁC ĐỊNH CỐT LÕI

- **Tập trung vào MVP** - Minimum Viable Product cho hệ thống học tiếng Anh
- **Dựa trên codebase hiện tại** - Các tính năng đã có trong hệ thống
- **Loại bỏ nâng cao** - Không bao gồm AI, ML, VR/AR, blockchain, IoT
- **Cơ bản nhưng đầy đủ** - Đủ để một hệ thống học tập hoạt động hiệu quả
- **Scalable** - Có thể mở rộng thêm tính năng nâng cao sau này

### TÍNH NĂNG ĐÃ LOẠI BỎ (CHO PHIÊN BẢN NÂNG CAO)

- AI Tutor & Virtual Assistant
- Advanced Speech Recognition
- Advanced Analytics & Machine Learning
- Smart Content Recommendation
- Advanced Social Features
- Productivity & Time Management
- Gamification Features nâng cao
- VR/AR Learning
- Blockchain & Web3
- IoT Integration
- Biometric Authentication nâng cao

Danh sách này tập trung vào các chức năng cốt lõi cần thiết để xây dựng một hệ thống học tiếng Anh cơ bản nhưng đầy đủ chức năng, phù hợp cho MVP hoặc phiên bản đầu tiên của sản phẩm.