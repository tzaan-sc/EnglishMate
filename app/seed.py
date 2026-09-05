"""Create the local database and deterministic demo content."""
from app import create_app
from app.extensions import db
from app.modules.learning.models import Lesson, Question, Vocabulary
from app.modules.auth.models import User


LESSONS = [
    # --- LISTENING ---
    ("A1", "Listening", "Daily Morning Routine Dialogue", "Lắng nghe hội thoại chào buổi sáng và lịch trình thường ngày của hai người bạn.",
     "Listen to Emma and David talking about their daily morning habits. Notice the time expressions: at 7:00, in the morning, before breakfast.\n\nTips: Focus on stressed words and numbers. Don't worry if you miss small words like 'a' or 'the'.",
     "Emma: What time do you usually wake up?\nDavid: I wake up at 6:30 AM every day.\nEmma: Do you have coffee before breakfast?"),
    ("A2", "Listening", "Catching Airport Announcements", "Nghe thông báo chuyến bay, giờ lên máy bay và cửa khởi hành tại sân bay.",
     "Airport announcements contain key information: flight numbers, gate changes, boarding times, and final calls.\n\nTips: Predict the keywords before listening (Flight, Gate, Delay, Boarding). Write down numbers immediately.",
     "Flight VN123 to Da Nang is now boarding at Gate 4.\nPassengers requiring special assistance please approach the desk.\nThis is the final boarding call."),
    ("B1", "Listening", "Ordering at a Local Café", "Nghe cuộc hội thoại đặt đồ uống, món ăn và thanh toán hóa đơn.",
     "Café conversations often involve choices, sizes, custom orders (milk type, ice levels), and payment methods.\n\nUseful phrases: Would you like anything else? Can I get that iced? Takeaway or have here?",
     "Barista: Good morning! What can I get for you today?\nCustomer: Could I have a medium cappuccino with oat milk, please?\nBarista: Sure! For here or to go?"),
    ("B2", "Listening", "City Tour Guide Podcast", "Luyện nghe bài thuyết minh hướng dẫn viên du lịch về lịch sử và văn hóa thành phố.",
     "In audio guides and podcasts, the speaker uses transitions (First, Next, As we turn right, Historically) to guide listeners through landmarks.",
     "On your left, you can see the historic clock tower built in 1892.\nNotice the intricate architecture influenced by French design."),
    ("C1", "Listening", "Global Technology & AI Discussion", "Nghe bài thảo luận chuyên sâu về tác động của trí tuệ nhân tạo đối với thị trường việc làm.",
     "Academic and business discussions use specialized vocabulary, nuanced viewpoints, and rhetorical questions to engage the listener.",
     "The rapid integration of generative AI poses unprecedented questions for workforce adaptation and productivity metrics."),

    # --- READING ---
    ("A1", "Reading", "A Simple Postcard from London", "Đọc bưu thiếp chào mừng ngắn mô tả các điểm đến thú vị tại London.",
     "Postcards use friendly, informal language with short descriptive sentences about weather, places, and food.\n\nFocus on adjectives: sunny, delicious, exciting, beautiful.",
     "Dear Tom, Greetings from London! The weather is lovely today. We visited Big Ben and rode the London Eye. See you soon!"),
    ("A2", "Reading", "Hotel Services & Guest Information", "Đọc bảng hướng dẫn tiện ích khách sạn, giờ ăn sáng và nội quy lưu trú.",
     "Information brochures use headings, bullet points, and clear timing guides to help guests find services quickly.",
     "Breakfast is served from 6:30 to 10:00 AM on the 2nd floor.\nFree Wi-Fi is available across all rooms.\nCheck-out time is 12:00 PM."),
    ("B1", "Reading", "Reading for the Main Idea", "Đọc nhanh bài viết ngắn về lối sống tối giản để nhận diện ý chính.",
     "Skimming means reading quickly to understand the main idea. Look at the title, first sentence of each paragraph, and repeated keywords.",
     "Minimalism is not about owning nothing; it is about making room for what truly matters in daily life."),
    ("B2", "Reading", "Professional Workplace Email", "Đọc và phân tích email trao đổi dự án, thời hạn bàn giao và phản hồi khách hàng.",
     "Workplace emails follow a structured layout: greeting, purpose statement, key action items, and polite closing.",
     "I am writing to provide an update regarding the Q3 product release schedule.\nPlease find the revised milestones attached for your review."),
    ("C1", "Reading", "Sustainable Energy & Future Cities", "Bài phân tích học thuật về năng lượng tái tạo và xu hướng quy hoạch đô thị bền vững.",
     "Complex reading texts require understanding cohesion, academic vocabulary, contrasting arguments, and statistical evidence.",
     "Transitioning towards circular economy paradigms requires cross-sectoral collaboration between policymakers and municipal planners."),

    # --- SPEAKING ---
    ("A1", "Speaking", "Introducing Yourself Confidently", "Tự giới thiệu bản thân ngắn gọn, tự nhiên về nghề nghiệp và sở thích cá nhân.",
     "A friendly introduction includes your name, hometown, work/studies, and an interesting hobby.\n\nUseful patterns: Hi, I'm... I work as a... In my free time, I like...",
     "Hi everyone, my name is Alex. I'm from Da Nang and I work as a web developer.\nIn my free time, I love playing badminton."),
    ("A2", "Speaking", "Asking for Directions in the City", "Hỏi đường, hỏi vị trí trạm xe buýt và hiểu chỉ dẫn phương hướng cơ bản.",
     "Use polite question openers: Excuse me, could you tell me where the station is? How do I get to the supermarket?",
     "Excuse me, is there a pharmacy near here?\nGo straight for two blocks, then turn left at the traffic light.\nIt will be on your right."),
    ("B1", "Speaking", "Expressing Personal Opinions", "Nêu và bảo vệ quan điểm cá nhân một cách mạch lạc với các liên từ nối.",
     "Structure your answer: State your view -> Give a clear reason -> Provide a concrete example -> Conclude.",
     "In my view, remote working offers better work-life balance.\nFor instance, employees save two hours of commuting each day."),
    ("B2", "Speaking", "Job Interview Mastery", "Luyện trả lời các câu hỏi phỏng vấn tuyển dụng thông dụng với cấu trúc STAR.",
     "When answering behavioral interview questions, use Situation - Task - Action - Result to deliver concise, compelling stories.",
     "In my previous role, I was tasked with leading a 5-member team to revamp our client portal, resulting in a 35% speed improvement."),
    ("C1", "Speaking", "Negotiation & Meeting Strategies", "Kỹ năng đàm phán, thuyết phục đối tác và điều phối cuộc họp chiến lược.",
     "Effective business negotiation involves active listening, hedging language, concession strategies, and summarizing agreements.",
     "While we appreciate your proposal, we would need greater flexibility on the payment milestones before finalizing the contract."),

    # --- WRITING ---
    ("A1", "Writing", "Writing a Daily Routine Note", "Viết đoạn ghi chú ngắn mô tả các hoạt động quen thuộc trong ngày.",
     "Use simple present tense and chronological sequencers: First, Then, After that, Finally.\n\nKeep sentences short and check subject-verb agreement.",
     "First, I wake up at 7 AM. Then, I eat breakfast with my family. In the afternoon, I study English online."),
    ("A2", "Writing", "Writing an Invitation Message", "Viết tin nhắn mời bạn bè tham gia bữa tiệc sinh nhật và hướng dẫn chuẩn bị.",
     "Include essential details: occasion, date, time, location, RSVP deadline, and what guests might need to bring.",
     "Hey Sarah! I'm hosting a birthday dinner this Saturday at 7 PM at Bistro Garden. Hope you can make it! Let me know by Friday."),
    ("B1", "Writing", "Writing a Friendly Holiday Email", "Viết email thân mật kể về chuyến du lịch nghỉ dưỡng đáng nhớ cho người thân.",
     "Combine past simple and past continuous to tell an engaging story about your travel experiences and memorable moments.",
     "We had an amazing time exploring the old town. While we were walking along the beach, we witnessed a breathtaking sunset."),
    ("B2", "Writing", "Formal Business Request Letter", "Viết thư khiếu nại dịch vụ hoặc yêu cầu hỗ trợ kỹ thuật theo quy chuẩn trang trọng.",
     "Use formal tone, passive voice where appropriate, and precise language. Avoid slang and contractions.",
     "I am writing to formally request an expedited review of application reference #89412 due to urgent project constraints."),
    ("C1", "Writing", "Persuasive Essay & Argumentation", "Viết bài luận nghị luận xã hội với cấu trúc lập luận chặt chẽ và dẫn chứng thuyết phục.",
     "Structure: Introduction with a clear thesis statement, topic sentences for each body paragraph, counterarguments, and a decisive conclusion.",
     "Proponents argue that rapid automation increases overall economic efficiency; however, this viewpoint overlooks transition disparities."),
]

VOCAB_GROUPS = {
    "Daily Life": [("routine", "thói quen"), ("wake up", "thức dậy"), ("prepare", "chuẩn bị"), ("usually", "thường xuyên"), ("tidy", "gọn gàng"), ("relax", "thư giãn"), ("schedule", "lịch trình"), ("habit", "thói quen")],
    "School": [("subject", "môn học"), ("assignment", "bài tập"), ("revise", "ôn tập"), ("grade", "điểm số"), ("lecture", "bài giảng"), ("research", "nghiên cứu"), ("deadline", "hạn chót"), ("knowledge", "kiến thức")],
    "Work": [("colleague", "đồng nghiệp"), ("meeting", "cuộc họp"), ("project", "dự án"), ("salary", "lương"), ("efficient", "hiệu quả"), ("negotiate", "đàm phán"), ("responsibility", "trách nhiệm"), ("achievement", "thành tựu")],
    "Travel": [("journey", "hành trình"), ("luggage", "hành lý"), ("departure", "khởi hành"), ("destination", "điểm đến"), ("book", "đặt chỗ"), ("explore", "khám phá"), ("accommodation", "chỗ ở"), ("itinerary", "lịch trình chuyến đi")],
    "Food": [("ingredient", "nguyên liệu"), ("delicious", "ngon"), ("recipe", "công thức"), ("spicy", "cay"), ("portion", "khẩu phần"), ("nutritious", "bổ dưỡng"), ("appetite", "sự ngon miệng")],
    "Technology": [("device", "thiết bị"), ("password", "mật khẩu"), ("download", "tải xuống"), ("network", "mạng"), ("software", "phần mềm"), ("privacy", "quyền riêng tư"), ("innovative", "đổi mới")],
    "Health": [("exercise", "tập thể dục"), ("healthy", "khỏe mạnh"), ("symptom", "triệu chứng"), ("treatment", "điều trị"), ("recover", "hồi phục"), ("balanced", "cân bằng"), ("well-being", "sức khỏe toàn diện")],
    "Environment": [("nature", "thiên nhiên"), ("recycle", "tái chế"), ("pollution", "ô nhiễm"), ("climate", "khí hậu"), ("conserve", "bảo tồn"), ("sustainable", "bền vững"), ("biodiversity", "đa dạng sinh học")],
}


def build_vocabulary():
    rows = []
    levels = ["A1", "A2", "B1", "B2"]
    pos = ["noun", "verb", "adjective", "adverb"]
    for topic_index, (topic, words) in enumerate(VOCAB_GROUPS.items()):
        for word_index, (word, meaning) in enumerate(words):
            level = levels[min(3, (word_index + topic_index % 2) // 2)]
            rows.append(dict(word=word, pronunciation=f"/{word.replace(' ', '·')}/", part_of_speech=pos[(word_index + topic_index) % 4],
                             meaning_vi=meaning, example_en=f"I use the word ‘{word}’ in a real conversation.",
                             example_vi=f"Tôi dùng từ ‘{word}’ trong một cuộc trò chuyện thực tế.", topic=topic, level=level))
    return rows[:60]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        if not User.query.first():
            for username, email, password, role in [
                ("admin", "admin@example.com", "admin123", "ADMIN"),
                ("user1", "user1@example.com", "user123", "USER"),
                ("user2", "user2@example.com", "user123", "USER"),
            ]:
                user = User(username=username, email=email, role=role)
                user.set_password(password)
                db.session.add(user)

        if not Lesson.query.first():
            for level, skill, title, description, content, examples in LESSONS:
                db.session.add(Lesson(level=level, skill=skill, title=title, short_description=description,
                                      content=content, examples=examples))

        vocab_rows = build_vocabulary()
        if not Vocabulary.query.first():
            db.session.add_all(Vocabulary(**row) for row in vocab_rows)
            db.session.flush()

        if not Question.query.first():
            meanings = [row["meaning_vi"] for row in vocab_rows]
            option_keys = ["A", "B", "C", "D"]
            for i, row in enumerate(vocab_rows[:40]):
                correct_index = i % 4
                distractors = [meanings[(i + step * 7 + 3) % len(meanings)] for step in range(1, 4)]
                choices = distractors[:]
                choices.insert(correct_index, row["meaning_vi"])
                db.session.add(Question(question_text=f"Từ ‘{row['word']}’ có nghĩa là gì?",
                    option_a=choices[0], option_b=choices[1], option_c=choices[2], option_d=choices[3],
                    correct_option=option_keys[correct_index], explanation=f"‘{row['word']}’ nghĩa là ‘{row['meaning_vi']}’.",
                    level=row["level"], topic=row["topic"]))
        db.session.commit()
        print(f"Seed complete: {User.query.count()} users, {Lesson.query.count()} lessons, "
              f"{Vocabulary.query.count()} words, {Question.query.count()} questions.")


if __name__ == "__main__":
    seed()
