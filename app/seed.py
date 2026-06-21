"""Create the local database and deterministic demo content."""
from app import create_app
from app.extensions import db
from app.models import Lesson, Question, User, Vocabulary


LESSONS = [
    ("A1", "Vocabulary", "My morning routine", "Nói về những việc bạn làm mỗi sáng.",
     "A routine is something you do regularly. Use the present simple for daily habits.\n\nStructure: I/You/We/They + base verb. With He/She/It, add -s or -es.\n\nFrequency words such as always, usually, often, sometimes and never help describe how often an action happens.",
     "I usually wake up at seven.\nShe brushes her teeth before breakfast.\nWe never skip breakfast."),
    ("A1", "Grammar", "Present simple essentials", "Nắm chắc thì hiện tại đơn qua ngữ cảnh quen thuộc.",
     "Use the present simple for facts, habits and repeated actions.\n\nPositive: She works here. Negative: She does not work here. Question: Does she work here?\n\nRemember that do becomes does with he, she and it.",
     "Water boils at 100°C.\nDo you play football?\nHe doesn't drink coffee."),
    ("A1", "Speaking", "Introducing yourself", "Tự giới thiệu ngắn gọn và tự nhiên.",
     "A friendly introduction can include your name, hometown, work or studies, and one personal interest. Keep each sentence short and make eye contact.\n\nUseful starters: My name is..., I'm from..., I study..., In my free time, I enjoy...",
     "Hi, I'm Lan. I'm from Da Nang.\nI study information technology.\nIn my free time, I enjoy reading."),
    ("A2", "Grammar", "Talking about the past", "Kể lại một trải nghiệm đã kết thúc.",
     "Use the past simple for completed actions at a known time in the past. Regular verbs usually end in -ed; irregular verbs change form.\n\nQuestions use did + subject + base verb.",
     "We visited Hue last summer.\nShe bought a new book yesterday.\nDid you enjoy the trip?"),
    ("A2", "Vocabulary", "Food and ordering", "Gọi món lịch sự tại nhà hàng.",
     "When ordering food, polite phrases make the conversation smoother. Start with Could I have... or I'd like... Ask about ingredients with Does this contain...?\n\nUse some with uncountable nouns and plural countable nouns.",
     "I'd like the vegetable soup, please.\nCould we have some water?\nDoes this dish contain peanuts?"),
    ("A2", "Listening", "Catching key information", "Nghe có mục tiêu thay vì cố hiểu từng từ.",
     "Before listening, predict the people, place and likely vocabulary. During the first listen, focus on the main idea. On the second listen, note names, times, prices and places.\n\nIt is normal not to understand every word.",
     "Listen for stressed words.\nWrite numbers as soon as you hear them.\nUse context to guess unknown words."),
    ("B1", "Reading", "Reading for the main idea", "Đọc nhanh để nhận ra ý chính của văn bản.",
     "Skimming means reading quickly to understand the main idea. Look at the title, first sentence of each paragraph and repeated words.\n\nScanning is different: move your eyes quickly to find one specific fact.",
     "Skim an article before reading closely.\nScan a timetable for the departure time.\nSummarize each paragraph in five words."),
    ("B1", "Grammar", "Present perfect in context", "Kết nối trải nghiệm quá khứ với hiện tại.",
     "Form the present perfect with have/has + past participle. Use it for experiences without a finished time, recent events with a present result, and situations continuing until now.\n\nDo not use it with yesterday or last year.",
     "I have visited Singapore twice.\nShe has just finished her report.\nWe have lived here since 2020."),
    ("B1", "Speaking", "Giving your opinion", "Nêu và bảo vệ quan điểm một cách mạch lạc.",
     "State your view, give a reason and add an example. Helpful linking phrases include In my view, because, for example, however and therefore. Acknowledge another opinion before disagreeing politely.",
     "In my view, public transport should be cheaper.\nI see your point, but I think differently.\nFor example, buses reduce traffic."),
    ("B2", "Vocabulary", "Workplace communication", "Giao tiếp rõ ràng trong môi trường công việc.",
     "Professional communication is concise, specific and respectful. In emails, use a clear subject line, state the purpose early and finish with the requested next step.\n\nReplace vague words with dates, names and measurable outcomes.",
     "Could you send the draft by Friday?\nLet's clarify the next steps.\nI appreciate your quick response."),
    ("B2", "Reading", "Understanding tone and purpose", "Nhận biết thái độ ẩn sau lựa chọn từ ngữ.",
     "Tone is the writer's attitude toward a subject. Notice adjectives, intensifiers, punctuation and what the writer chooses to emphasize. Purpose may be to inform, persuade, criticize or entertain.",
     "Neutral reports favor factual language.\nRhetorical questions can signal persuasion.\nStrong adjectives often reveal attitude."),
    ("B2", "Grammar", "Conditionals for real life", "Dùng câu điều kiện để nói về khả năng và giả định.",
     "The first conditional describes a real future possibility: if + present, will + verb. The second conditional describes an unlikely or imaginary situation: if + past, would + verb.\n\nUse a comma when the if-clause comes first.",
     "If it rains, we'll stay inside.\nIf I had more time, I would learn Spanish.\nWhat would you do if you won?"),
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
