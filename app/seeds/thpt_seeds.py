"""
THPT Exam Seed Data for EnglishMate
Provides a complete 50-question mock exam conforming to the Ministry of Education & Training (Bộ GD&ĐT) standard format.
"""

from app.extensions import db
from app.backend.exams.models import Exam, ExamQuestion


CLOZE_PASSAGE = (
    "In the modern era, digital literacy has become an essential skill for students worldwide. "
    "It goes beyond mere technical know-how to include critical thinking, information evaluation, "
    "and ethical communication. (25) _____ individuals possess strong digital competencies, they can navigate "
    "online resources effectively. Moreover, learners must be taught how to distinguish between genuine "
    "information and fake news, (26) _____ is becoming widespread across social media platforms. "
    "In addition, schools should provide (27) _____ opportunity for every student to access digital "
    "devices regardless of socioeconomic background. Teachers also need continuous training in order "
    "to (28) _____ educational technology effectively into their curricula. (29) _____, equipping "
    "students with digital skills will empower them to thrive in an increasingly interconnected global workforce."
)

READING_PASSAGE_1 = (
    "Sleep is an indispensable biological function that directly influences human cognitive performance, "
    "emotional stability, and physical health. For adolescents, getting sufficient rest is particularly vital "
    "because the brain undergoes dramatic neurological remodeling during this developmental stage. During "
    "deep sleep, the brain consolidates memories, reorganizing and storing newly acquired facts and concepts "
    "learned throughout the day.\n\n"
    "However, studies show that a staggering number of teenagers suffer from chronic sleep deprivation. "
    "Biological changes during puberty shift the adolescent circadian rhythm, naturally delaying the "
    "sleep-wake cycle by approximately two hours. Consequently, teenagers feel naturally awake later at "
    "night and struggle to wake up early for school. This biological delay is exacerbated by lifestyle factors, "
    "most notably the pervasive use of smartphones and electronic screens right before bedtime. The blue light "
    "emitted by these digital screens suppresses the secretion of melatonin, a hormone responsible for "
    "signaling the body that it is time to rest.\n\n"
    "The repercussions of inadequate sleep extend far beyond morning grogginess. Sleep-deprived students "
    "frequently display impaired concentration, diminished problem-solving skills, and lower academic achievement. "
    "Furthermore, chronic sleep deficits are strongly linked to elevated anxiety and mood disorders. To mitigate "
    "this growing issue, health experts recommend establishing consistent sleep schedules, turning off digital "
    "devices at least one hour before bed, and creating a quiet, dark sleeping environment."
)

READING_PASSAGE_2 = (
    "Rapid urbanization over the past century has transformed the global landscape, replacing lush natural "
    "environments with vast stretches of concrete, asphalt, and steel. While modern metropolitan areas serve as "
    "vibrant centers of economic vitality, innovation, and cultural exchange, they simultaneously present "
    "formidable ecological challenges. Among these, the urban heat island (UHI) effect—where cities experience "
    "significantly higher temperatures than surrounding rural areas—has emerged as a major environmental and "
    "public health concern. Massive buildings and paved surfaces absorb solar radiation throughout the day and "
    "slowly radiate thermal energy into the atmosphere at night, driving up air conditioning demands and deteriorating air quality.\n\n"
    "To counteract these adverse repercussions, architects, urban planners, and environmental scientists are pioneering "
    "innovative approaches known as biophilic urbanism and sustainable green architecture. Rather than treating "
    "nature as an ornamental afterthought, contemporary green architecture seeks to seamlessly integrate living "
    "systems directly into the fabric of built structures. Vertical forests, rooftop gardens, and vegetative facades "
    "are no longer eccentric novelties; they have become critical components of sustainable urban infrastructure.\n\n"
    "One of the most notable advantages of green architecture is its capacity for microclimate regulation. "
    "Vegetation cools urban microclimates through evapotranspiration, the process by which plants absorb water "
    "through their roots and release moisture into the atmosphere. Research indicates that extensive green roofs "
    "can reduce ambient air temperatures by up to three degrees Celsius during peak summer months. Furthermore, "
    "vegetative surfaces act as natural thermal insulation, diminishing heat transfer through rooftops and walls, "
    "thereby lowering energy consumption in buildings.\n\n"
    "Beyond thermal benefits, urban greenery plays a pivotal role in stormwater management and biodiversity preservation. "
    "In conventional cities, impervious surfaces prevent rainwater infiltration, causing severe runoff and overwhelming "
    "municipal drainage systems. Green roofs and bioswales absorb substantial volumes of precipitation, filtering "
    "pollutants and gradually releasing purified water back into the hydrological cycle. Simultaneously, these planted "
    "installations provide crucial stepping-stone habitats for birds, pollinators, and other urban wildlife, fostering "
    "urban biodiversity in densely populated cities.\n\n"
    "Nevertheless, transitioning toward sustainable green cities is not without logistical and financial hurdles. "
    "Retrofitting existing high-rises with soil-bearing vegetated infrastructure entails substantial capital expenditure, "
    "structural reinforcement, and specialized long-term maintenance. Moreover, equitable distribution of urban greenery "
    "remains a pressing social issue, as affluent neighborhoods frequently benefit from green investments while "
    "marginalized areas remain asphalt-dominated. Despite these complexities, embracing green architecture is widely "
    "regarded by municipal authorities as an imperative investment for building climate-resilient and liveable cities of the future."
)


THPT_50_QUESTIONS = [
    # --- PHẦN 1: NGỮ ÂM (CÂU 1 - 2) ---
    {
        "part": "Phần 1: Ngữ âm (Pronunciation)",
        "skill": "PRONUNCIATION",
        "question_text": "Mark the letter A, B, C, or D to indicate the word whose underlined part differs from the other three in pronunciation:\n\nA. look_ed_    B. watch_ed_    C. stopp_ed_    D. decid_ed_",
        "option_a": "looked",
        "option_b": "watched",
        "option_c": "stopped",
        "option_d": "decided",
        "correct_answer": "D",
        "explanation": "Đuôi '-ed' của 'decided' được phát âm là /ɪd/ vì tận cùng là âm /d/. Các từ còn lại phát âm là /t/ vì tận cùng là các âm vô thanh /k/, /tʃ/, /p/."
    },
    {
        "part": "Phần 1: Ngữ âm (Pronunciation)",
        "skill": "PRONUNCIATION",
        "question_text": "Mark the letter A, B, C, or D to indicate the word whose underlined part differs from the other three in pronunciation:\n\nA. gr_ea_t    B. ch_ea_p    C. cl_ea_n    D. m_ea_t",
        "option_a": "great",
        "option_b": "cheap",
        "option_c": "clean",
        "option_d": "meat",
        "correct_answer": "A",
        "explanation": "Phần gạch chân 'ea' trong 'great' phát âm là /eɪ/, trong khi ở 'cheap', 'clean', 'meat' phát âm là /iː/."
    },

    # --- PHẦN 2: TRỌNG ÂM (CÂU 3 - 4) ---
    {
        "part": "Phần 2: Trọng âm (Stress)",
        "skill": "PRONUNCIATION",
        "question_text": "Mark the letter A, B, C, or D to indicate the word that differs from the other three in the position of primary stress:\n\nA. provide    B. listen    C. protect    D. maintain",
        "option_a": "provide",
        "option_b": "listen",
        "option_c": "protect",
        "option_d": "maintain",
        "correct_answer": "B",
        "explanation": "'listen' nhấn trọng âm vào âm tiết thứ 1 (/ˈlɪs.ən/). Các từ 'provide' (/prəˈvaɪd/), 'protect' (/prəˈtekt/), 'maintain' (/meɪnˈteɪn/) đều nhấn trọng âm vào âm tiết thứ 2."
    },
    {
        "part": "Phần 2: Trọng âm (Stress)",
        "skill": "PRONUNCIATION",
        "question_text": "Mark the letter A, B, C, or D to indicate the word that differs from the other three in the position of primary stress:\n\nA. pollution    B. candidate    C. chemical    D. regular",
        "option_a": "pollution",
        "option_b": "candidate",
        "option_c": "chemical",
        "option_d": "regular",
        "correct_answer": "A",
        "explanation": "'pollution' nhấn trọng âm 2 (/pəˈluː.ʃən/ theo quy tắc đuôi -tion). 'candidate' (/ˈkæn.dɪ.dət/), 'chemical' (/ˈkem.ɪ.kəl/), 'regular' (/ˈreɡ.jə.lər/) nhấn trọng âm 1."
    },

    # --- PHẦN 3: NGỮ PHÁP & TỪ VỰNG (CÂU 5 - 18) ---
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "The students are eagerly preparing for their graduation ceremony, ______?",
        "option_a": "aren't they",
        "option_b": "are they",
        "option_c": "don't they",
        "option_d": "do they",
        "correct_answer": "A",
        "explanation": "Câu hỏi đuôi (Tag question): Mệnh đề chính dùng 'are' thể khẳng định và chủ ngữ số nhiều 'The students' (they) -> câu hỏi đuôi phủ định: 'aren't they'."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "The new community library ______ by the mayor next Monday morning.",
        "option_a": "will inaugurate",
        "option_b": "will be inaugurated",
        "option_c": "is inaugurated",
        "option_d": "was inaugurated",
        "correct_answer": "B",
        "explanation": "Câu bị động thì Tương lai đơn (Simple Future Passive): 'next Monday morning' chỉ tương lai -> cấu trúc: 'will be + V3/ed' ('will be inaugurated')."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "She has been keenly interested ______ digital marketing since she entered university.",
        "option_a": "on",
        "option_b": "at",
        "option_c": "in",
        "option_d": "about",
        "correct_answer": "C",
        "explanation": "Cấu trúc cố định: 'interested in something/doing something' (thích thú, quan tâm đến cái gì)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "The more diligently you practice speaking English, ______ you will become.",
        "option_a": "the more confident",
        "option_b": "more confident",
        "option_c": "the most confident",
        "option_d": "confident",
        "correct_answer": "A",
        "explanation": "Cấu trúc so sánh kép (Double comparative): The + comparative + S + V, the + comparative + S + V. 'The more diligently..., the more confident...'"
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "Last night, while my brother ______ for his final examination, the power suddenly went out.",
        "option_a": "is revising",
        "option_b": "was revising",
        "option_c": "revised",
        "option_d": "has revised",
        "correct_answer": "B",
        "explanation": "Sự phối hợp thì Quá khứ tiếp diễn và Quá khứ đơn: Hành động đang diễn ra (was revising) thì hành động khác cắt ngang (went out)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "He bought ______ modern electric vehicle during the exhibition last weekend.",
        "option_a": "a",
        "option_b": "an",
        "option_c": "the",
        "option_d": "Ø (no article)",
        "correct_answer": "A",
        "explanation": "'electric vehicle' là danh từ đếm được số ít, đứng sau tính từ 'modern' (bắt đầu bằng phụ âm /m/) và được nhắc tới lần đầu -> dùng mạo từ 'a'."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "______ their homework, the students went to the schoolyard to play basketball.",
        "option_a": "Having finished",
        "option_b": "Finished",
        "option_c": "To finish",
        "option_d": "Being finished",
        "correct_answer": "A",
        "explanation": "Rút gọn hai mệnh đề cùng chủ ngữ dạng phân từ hoàn thành (Perfect Participle: Having + V3) để nhấn mạnh hành động hoàn thành bài tập xảy ra trước hành động đi chơi bóng rổ."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "VOCABULARY",
        "question_text": "The board of directors expressed great satisfaction with her ______ contribution to the project.",
        "option_a": "valuable",
        "option_b": "value",
        "option_c": "valuably",
        "option_d": "evaluate",
        "correct_answer": "A",
        "explanation": "Trước danh từ 'contribution' cần một tính từ bổ nghĩa. 'valuable' (adj - quý giá/có giá trị)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "VOCABULARY",
        "question_text": "To prevent environmental pollution, local authorities have decided to ______ single-use plastic bags.",
        "option_a": "put off",
        "option_b": "phase out",
        "option_c": "give in",
        "option_d": "take after",
        "correct_answer": "B",
        "explanation": "Phrasal verb 'phase out' nghĩa là loại bỏ dần dần theo từng giai đoạn. 'put off': hoãn; 'give in': nhượng bộ; 'take after': giống ai."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "VOCABULARY",
        "question_text": "The government made a firm ______ to reduce greenhouse gas emissions by 40% before 2035.",
        "option_a": "commitment",
        "option_b": "permission",
        "option_c": "admission",
        "option_d": "transmission",
        "correct_answer": "A",
        "explanation": "Collocation: 'make a commitment to do/doing sth' (đưa ra cam kết làm gì)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "VOCABULARY",
        "question_text": "He is burning the midnight ______ every night to prepare for the upcoming national exam.",
        "option_a": "oil",
        "option_b": "candle",
        "option_c": "gas",
        "option_d": "lamp",
        "correct_answer": "A",
        "explanation": "Idiom: 'burn the midnight oil' (thức khuya học bài/làm việc chăm chỉ)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "We will inform all applicants of the interview results ______.",
        "option_a": "as soon as we have finalized the shortlist",
        "option_b": "when we had finalized the shortlist",
        "option_c": "until we will finalize the shortlist",
        "option_d": "after we finalized the shortlist",
        "correct_answer": "A",
        "explanation": "Sự hòa hợp thì trong mệnh đề chỉ thời gian tương lai: Mệnh đề chính ở thì tương lai đơn (will inform) -> mệnh đề thời gian dùng thì hiện tại đơn / hiện tại hoàn thành (as soon as we have finalized)."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "If she had taken the mentor's advice last month, she ______ in such financial distress right now.",
        "option_a": "wouldn't be",
        "option_b": "won't be",
        "option_c": "hadn't been",
        "option_d": "wouldn't have been",
        "correct_answer": "A",
        "explanation": "Câu điều kiện hỗn hợp loại 3-2 (Mixed Conditional): Mệnh đề If giả định trong quá khứ ('had taken... last month'), mệnh đề chính diễn tả kết quả ở hiện tại ('right now') -> 'would/could + V-bare' ('wouldn't be')."
    },
    {
        "part": "Phần 3: Ngữ pháp & Từ vựng",
        "skill": "GRAMMAR",
        "question_text": "The doctor advised him to cut down on saturated fats ______ his high cholesterol levels.",
        "option_a": "because of",
        "option_b": "although",
        "option_c": "in spite of",
        "option_d": "because",
        "correct_answer": "A",
        "explanation": "'his high cholesterol levels' là một cụm danh từ (Noun phrase) mang nghĩa nguyên nhân -> dùng 'because of'."
    },

    # --- PHẦN 4: GIAO TIẾP XÃ HỘI (CÂU 19 - 20) ---
    {
        "part": "Phần 4: Giao tiếp xã hội (Communication)",
        "skill": "VOCABULARY",
        "question_text": "Laura and Peter are talking after Laura's presentation:\nPeter: 'Congratulations! Your presentation on renewable energy was truly insightful!'\nLaura: '______'",
        "option_a": "Thank you, Peter! I'm glad you found it interesting.",
        "option_b": "You're welcome. It was nothing special.",
        "option_c": "I don't agree with your opinion.",
        "option_d": "Never mind, better luck next time.",
        "correct_answer": "A",
        "explanation": "Đáp lại lời khen ngợi một cách lịch sự, trang trọng: 'Thank you, Peter! I'm glad you found it interesting.'"
    },
    {
        "part": "Phần 4: Giao tiếp xã hội (Communication)",
        "skill": "VOCABULARY",
        "question_text": "Mark and Sophie are discussing online learning:\nMark: 'In my view, online study courses offer learners immense schedule flexibility.'\nSophie: '______. Students can learn at their own pace from anywhere.'",
        "option_a": "I couldn't agree with you more",
        "option_b": "I'm afraid I totally disagree",
        "option_c": "That's not a good idea",
        "option_d": "I doubt that very much",
        "correct_answer": "A",
        "explanation": "Sophie đồng tình và bổ sung lý do ('Students can learn at their own pace...') -> thành ngữ thể hiện sự hoàn toàn đồng ý: 'I couldn't agree with you more' (Tôi hoàn toàn đồng ý với bạn)."
    },

    # --- PHẦN 5: TỪ ĐỒNG NGHĨA (CÂU 21 - 22) ---
    {
        "part": "Phần 5: Từ đồng nghĩa (Closest in Meaning)",
        "skill": "VOCABULARY",
        "question_text": "Mark the letter A, B, C, or D to indicate the word CLOSEST in meaning to the underlined word:\n\nThe scientist presented **compelling** evidence that supported the newly developed climate theory.",
        "option_a": "persuasive",
        "option_b": "doubtful",
        "option_c": "trivial",
        "option_d": "vague",
        "correct_answer": "A",
        "explanation": "'compelling' mang nghĩa thuyết phục, đanh thép (= 'persuasive'). 'doubtful': đáng ngờ; 'trivial': vụn vặt; 'vague': mơ hồ."
    },
    {
        "part": "Phần 5: Từ đồng nghĩa (Closest in Meaning)",
        "skill": "VOCABULARY",
        "question_text": "Mark the letter A, B, C, or D to indicate the word/phrase CLOSEST in meaning to the underlined phrase:\n\nWhen facing sudden emergency situations, remaining **calm and collected** is of utmost importance.",
        "option_a": "composed",
        "option_b": "frightened",
        "option_c": "hesitant",
        "option_d": "agitated",
        "correct_answer": "A",
        "explanation": "'calm and collected' nghĩa là bình tĩnh, điềm tĩnh (= 'composed'). 'frightened': sợ hãi; 'hesitant': do dự; 'agitated': kích động."
    },

    # --- PHẦN 6: TỪ TRÁI NGHĨA (CÂU 23 - 24) ---
    {
        "part": "Phần 6: Từ trái nghĩa (Opposite in Meaning)",
        "skill": "VOCABULARY",
        "question_text": "Mark the letter A, B, C, or D to indicate the word OPPOSITE in meaning to the underlined word:\n\nDue to stringent safety regulations, the construction company implemented **mandatory** safety checks every morning.",
        "option_a": "optional",
        "option_b": "compulsory",
        "option_c": "obligatory",
        "option_d": "imperative",
        "correct_answer": "A",
        "explanation": "'mandatory' mang nghĩa bắt buộc. Trái nghĩa là 'optional' (tự nguyện, tùy chọn). Các từ 'compulsory', 'obligatory', 'imperative' là từ đồng nghĩa."
    },
    {
        "part": "Phần 6: Từ trái nghĩa (Opposite in Meaning)",
        "skill": "VOCABULARY",
        "question_text": "Mark the letter A, B, C, or D to indicate the word/phrase OPPOSITE in meaning to the underlined idiom:\n\nWinning the prestigious scholarship made him feel **on cloud nine** throughout the whole week.",
        "option_a": "extremely sorrowful",
        "option_b": "delighted",
        "option_c": "thrilled",
        "option_d": "ecstatic",
        "correct_answer": "A",
        "explanation": "'on cloud nine' là thành ngữ chỉ cảm giác vô cùng hạnh phúc, sung sướng. Trái nghĩa là 'extremely sorrowful' (vô cùng buồn bã, đau khổ)."
    },

    # --- PHẦN 7: ĐIỀN TỪ VÀO ĐOẠN VĂN (CLOZE TEST) (CÂU 25 - 29) ---
    {
        "part": "Phần 7: Điền từ vào đoạn văn (Cloze Test)",
        "skill": "READING",
        "transcript": CLOZE_PASSAGE,
        "question_text": "Read the passage and choose the best option for (25):\n'(25) _____ individuals possess strong digital competencies, they can navigate online resources effectively.'",
        "option_a": "When",
        "option_b": "Unless",
        "option_c": "Although",
        "option_d": "Despite",
        "correct_answer": "A",
        "explanation": "'When' (Khi mà) diễn tả điều kiện / thời điểm xảy ra hành động phù hợp logic câu: Khi các cá nhân sở hữu năng lực số vững chắc, họ có thể tra cứu thông tin hiệu quả."
    },
    {
        "part": "Phần 7: Điền từ vào đoạn văn (Cloze Test)",
        "skill": "READING",
        "transcript": CLOZE_PASSAGE,
        "question_text": "Read the passage and choose the best option for (26):\n'...distinguish between genuine information and fake news, (26) _____ is becoming widespread across social media platforms.'",
        "option_a": "which",
        "option_b": "who",
        "option_c": "whom",
        "option_d": "whose",
        "correct_answer": "A",
        "explanation": "Đại từ quan hệ 'which' đứng sau dấu phẩy thay thế cho danh từ chỉ sự vật/hiện tượng 'fake news' (hoặc thay cho cả mệnh đề phía trước)."
    },
    {
        "part": "Phần 7: Điền từ vào đoạn văn (Cloze Test)",
        "skill": "READING",
        "transcript": CLOZE_PASSAGE,
        "question_text": "Read the passage and choose the best option for (27):\n'In addition, schools should provide (27) _____ opportunity for every student to access digital devices...'",
        "option_a": "every",
        "option_b": "many",
        "option_c": "several",
        "option_d": "other",
        "correct_answer": "A",
        "explanation": "'opportunity' là danh từ số ít đếm được đi với 'every' (every opportunity: mọi cơ hội). 'many' và 'several' đi với danh từ số nhiều."
    },
    {
        "part": "Phần 7: Điền từ vào đoạn văn (Cloze Test)",
        "skill": "READING",
        "transcript": CLOZE_PASSAGE,
        "question_text": "Read the passage and choose the best option for (28):\n'Teachers also need continuous training in order to (28) _____ educational technology effectively into their curricula.'",
        "option_a": "integrate",
        "option_b": "eliminate",
        "option_c": "neglect",
        "option_d": "postpone",
        "correct_answer": "A",
        "explanation": "Collocation: 'integrate something into something' (tích hợp cái gì vào cái gì). Giáo viên cần được đào tạo để tích hợp công nghệ vào chương trình giảng dạy."
    },
    {
        "part": "Phần 7: Điền từ vào đoạn văn (Cloze Test)",
        "skill": "READING",
        "transcript": CLOZE_PASSAGE,
        "question_text": "Read the passage and choose the best option for (29):\n'(29) _____, equipping students with digital skills will empower them to thrive in an increasingly interconnected global workforce.'",
        "option_a": "Ultimately",
        "option_b": "However",
        "option_c": "Otherwise",
        "option_d": "Instead",
        "correct_answer": "A",
        "explanation": "'Ultimately' (Suy cho cùng / Cuối cùng) đứng đầu câu mang tính kết luận tổng kết toàn bộ ý nghĩa của đoạn văn."
    },

    # --- PHẦN 8: ĐỌC HIỂU VĂN BẢN 1 (CÂU 30 - 34) ---
    {
        "part": "Phần 8: Đọc hiểu văn bản 1 (5 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_1,
        "question_text": "What is the main topic of the passage?",
        "option_a": "The critical role of sleep in adolescent development and challenges they face",
        "option_b": "The technical mechanisms of smartphone blue light radiation",
        "option_c": "Why schools should eliminate early morning examinations",
        "option_d": "How memory storage operates in the human adult brain",
        "correct_answer": "A",
        "explanation": "Toàn bộ bài đọc bàn về tầm quan trọng của giấc ngủ đối với sự phát triển trí tuệ, sinh học của thanh thiếu niên, những nguyên nhân dẫn đến thiếu ngủ và hệ lụy của nó."
    },
    {
        "part": "Phần 8: Đọc hiểu văn bản 1 (5 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_1,
        "question_text": "According to paragraph 1, what takes place in the brain during deep sleep?",
        "option_a": "Memories are consolidated, reorganized, and stored",
        "option_b": "Melatonin production is completely stopped",
        "option_c": "The brain stops processing external information permanently",
        "option_d": "The circadian rhythm is pushed backward by three hours",
        "correct_answer": "A",
        "explanation": "Đoạn 1 nêu rõ: 'During deep sleep, the brain consolidates memories, reorganizing and storing newly acquired facts and concepts...'"
    },
    {
        "part": "Phần 8: Đọc hiểu văn bản 1 (5 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_1,
        "question_text": "The word 'exacerbated' in paragraph 2 is closest in meaning to ______.",
        "option_a": "worsened",
        "option_b": "mitigated",
        "option_c": "prevented",
        "option_d": "resolved",
        "correct_answer": "A",
        "explanation": "'exacerbate' nghĩa là làm trầm trọng thêm (= 'worsen'). Ngữ cảnh: 'This biological delay is exacerbated by lifestyle factors...'"
    },
    {
        "part": "Phần 8: Đọc hiểu văn bản 1 (5 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_1,
        "question_text": "The word 'they' in paragraph 2 refers to ______.",
        "option_a": "teenagers",
        "option_b": "hormones",
        "option_c": "studies",
        "option_d": "biological changes",
        "correct_answer": "A",
        "explanation": "Câu trước: 'Consequently, teenagers feel naturally awake later at night and struggle to wake up early...'. Từ 'they' thay thế cho 'teenagers'."
    },
    {
        "part": "Phần 8: Đọc hiểu văn bản 1 (5 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_1,
        "question_text": "Which of the following is NOT mentioned in paragraph 3 as a consequence of sleep deprivation?",
        "option_a": "Permanent loss of physical vision",
        "option_b": "Impaired concentration",
        "option_c": "Diminished problem-solving skills",
        "option_d": "Elevated anxiety and mood disorders",
        "correct_answer": "A",
        "explanation": "Đoạn 3 liệt kê: impaired concentration, diminished problem-solving skills, lower academic achievement, elevated anxiety và mood disorders. Mất thị lực vĩnh viễn ('Permanent loss of physical vision') hoàn toàn không được nhắc đến."
    },

    # --- PHẦN 9: ĐỌC HIỂU VĂN BẢN 2 (CÂU 35 - 42) ---
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "Which of the following best serves as the most suitable title for the passage?",
        "option_a": "Sustainable Green Architecture: Reshaping Resilient Cities of the Future",
        "option_b": "The Financial Collapse of Traditional Construction Companies",
        "option_c": "The History of Asphalt Roads in Metropolitan Centers",
        "option_d": "Why Modern High-Rises Are Being Totally Abandoned",
        "correct_answer": "A",
        "explanation": "Tiêu đề bao quát toàn bộ nội dung: Kiến trúc xanh bền vững giúp chống lại hiệu ứng đảo nhiệt đô thị, quản lý nguồn nước và kiến tạo các thành phố tương lai có khả năng chống chịu khí hậu."
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "According to paragraph 1, what causes the urban heat island (UHI) effect?",
        "option_a": "Paved surfaces and dense buildings absorbing and slowly radiating solar heat",
        "option_b": "The total absence of solar radiation in rural regions",
        "option_c": "Excessive amounts of vegetation planted on sidewalks",
        "option_d": "Cooling systems generating massive ice blocks in high-rises",
        "correct_answer": "A",
        "explanation": "Đoạn 1 nêu: 'Massive buildings and paved surfaces absorb solar radiation throughout the day and slowly radiate thermal energy into the atmosphere at night...'"
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "The term 'evapotranspiration' in paragraph 3 is explained as a process where plants ______.",
        "option_a": "absorb water through their roots and release moisture into the atmosphere",
        "option_b": "store solar energy directly into underground soil cavities",
        "option_c": "prevent moisture from evaporating into the air",
        "option_d": "consume concrete pollutants to produce synthetic nutrients",
        "correct_answer": "A",
        "explanation": "Đoạn 3 định nghĩa rõ: 'evapotranspiration, the process by which plants absorb water through their roots and release moisture into the atmosphere.'"
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "The word 'eccentric' in paragraph 2 is closest in meaning to ______.",
        "option_a": "unconventional",
        "option_b": "ordinary",
        "option_c": "predictable",
        "option_d": "traditional",
        "correct_answer": "A",
        "explanation": "'eccentric' nghĩa là kỳ lạ, khác thường, độc đáo (= 'unconventional'). 'ordinary': bình thường; 'predictable': có thể đoán trước; 'traditional': truyền thống."
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "According to paragraph 3, research indicates that extensive green roofs can reduce ambient temperatures by ______.",
        "option_a": "up to three degrees Celsius",
        "option_b": "exactly ten degrees Fahrenheit",
        "option_c": "over fifteen degrees Celsius",
        "option_d": "less than half a degree Celsius",
        "correct_answer": "A",
        "explanation": "Đoạn 3 viết: 'Research indicates that extensive green roofs can reduce ambient air temperatures by up to three degrees Celsius during peak summer months.'"
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "The word 'impervious' in paragraph 4 is closest in meaning to ______.",
        "option_a": "impenetrable to liquid",
        "option_b": "highly flexible",
        "option_c": "transparent",
        "option_d": "porous and soft",
        "correct_answer": "A",
        "explanation": "'impervious surfaces' là bề mặt không thấm nước (bê tông, nhựa đường không cho nước ngấm qua) = 'impenetrable to liquid'."
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "The word 'they' in paragraph 2 refers to ______.",
        "option_a": "vertical forests, rooftop gardens, and vegetative facades",
        "option_b": "metropolitan areas",
        "option_c": "paved surfaces",
        "option_d": "ecological challenges",
        "correct_answer": "A",
        "explanation": "Câu trước liệt kê: 'Vertical forests, rooftop gardens, and vegetative facades are no longer eccentric novelties; they have become critical components...'"
    },
    {
        "part": "Phần 9: Đọc hiểu văn bản 2 (8 câu)",
        "skill": "READING",
        "transcript": READING_PASSAGE_2,
        "question_text": "Which of the following can be inferred from the final paragraph?",
        "option_a": "Widespread green adoption requires overcoming socio-economic and structural constraints",
        "option_b": "Municipal governments will ban private rooftops by next decade",
        "option_c": "Marginalized areas currently have more green roofs than wealthy zones",
        "option_d": "Retrofitting high-rises requires zero long-term maintenance",
        "correct_answer": "A",
        "explanation": "Đoạn cuối nhấn mạnh những thách thức về tài chính, gia cố kết cấu và sự phân bổ công bằng xã hội giữa các khu vực giàu có và khó khăn, cho thấy để nhân rộng kiến trúc xanh cần vượt qua các rào cản kết cấu và kinh tế xã hội."
    },

    # --- PHẦN 10: TÌM LỖI SAI (ERROR IDENTIFICATION) (CÂU 43 - 45) ---
    {
        "part": "Phần 10: Tìm lỗi sai (Error Identification)",
        "skill": "GRAMMAR",
        "question_text": "Mark the letter A, B, C, or D to indicate the underlined part that needs correction:\n\nThe **young manager** (A) with his **dedicated team members** (B) **have completed** (C) the comprehensive market report **on time** (D).",
        "option_a": "young manager",
        "option_b": "dedicated team members",
        "option_c": "have completed",
        "option_d": "on time",
        "correct_answer": "C",
        "explanation": "Lỗi hòa hợp chủ ngữ - vị ngữ (Subject-verb agreement): Chủ ngữ chính là 'The young manager' (danh từ số ít), cụm 'with his dedicated team members' là thành phần xen giữa -> động từ phải chia số ít là 'has completed' chứ không phải 'have completed'."
    },
    {
        "part": "Phần 10: Tìm lỗi sai (Error Identification)",
        "skill": "GRAMMAR",
        "question_text": "Mark the letter A, B, C, or D to indicate the underlined part that needs correction:\n\n**Every morning** (A), John **walks** (B) to the office, **greeted** (C) his colleagues warmly, and **starts** (D) reviewing urgent customer emails.",
        "option_a": "Every morning",
        "option_b": "walks",
        "option_c": "greeted",
        "option_d": "starts",
        "correct_answer": "C",
        "explanation": "Lỗi cấu trúc song song (Parallel structure): Câu diễn tả thói quen hằng ngày ở hiện tại đơn ('walks', 'starts') -> 'greeted' (quá khứ) phải sửa thành 'greets'."
    },
    {
        "part": "Phần 10: Tìm lỗi sai (Error Identification)",
        "skill": "VOCABULARY",
        "question_text": "Mark the letter A, B, C, or D to indicate the underlined part that needs correction:\n\nThe committee conducted an **exhausted** (A) investigation into the incident to **ensure** (B) that **all relevant facts** (C) were thoroughly **clarified** (D).",
        "option_a": "exhausted",
        "option_b": "ensure",
        "option_c": "all relevant facts",
        "option_d": "clarified",
        "correct_answer": "A",
        "explanation": "Lỗi dùng từ dễ gây nhầm lẫn (Confusing words): 'exhausted' nghĩa là kiệt sức/mệt lử. Ở đây cần dùng tính từ 'exhaustive' (mang tính thấu đáo, toàn diện, sâu sát: an exhaustive investigation)."
    },

    # --- PHẦN 11: BIẾN ĐỔI & KẾT HỢP CÂU (CÂU 46 - 50) ---
    {
        "part": "Phần 11: Biến đổi câu (Sentence Transformation)",
        "skill": "GRAMMAR",
        "question_text": "It is compulsory for all high school students to wear school uniforms on Monday mornings.",
        "option_a": "All high school students must wear school uniforms on Monday mornings.",
        "option_b": "All high school students may wear school uniforms on Monday mornings.",
        "option_c": "All high school students needn't wear school uniforms on Monday mornings.",
        "option_d": "All high school students shouldn't wear school uniforms on Monday mornings.",
        "correct_answer": "A",
        "explanation": "'It is compulsory for sb to do sth' (Bắt buộc ai phải làm gì) tương đương với động từ khuyết thiếu 'must + V-bare' (phải làm gì)."
    },
    {
        "part": "Phần 11: Biến đổi câu (Sentence Transformation)",
        "skill": "GRAMMAR",
        "question_text": "'I will send you the detailed assignment guidelines tonight,' said the teacher to her students.",
        "option_a": "The teacher told her students that she would send them the detailed assignment guidelines that night.",
        "option_b": "The teacher told her students that she will send them the detailed assignment guidelines tonight.",
        "option_c": "The teacher asked her students if she would send them the detailed assignment guidelines that night.",
        "option_d": "The teacher advised her students to send her the detailed assignment guidelines tonight.",
        "correct_answer": "A",
        "explanation": "Chuyển câu trực tiếp sang gián tiếp: 'said to her students' -> 'told her students that', lùi thì 'will send' -> 'would send', đổi ngôi 'I' -> 'she', 'you' -> 'them', trạng từ 'tonight' -> 'that night'."
    },
    {
        "part": "Phần 11: Biến đổi câu (Sentence Transformation)",
        "skill": "GRAMMAR",
        "question_text": "No other candidate in the final round is as articulate as Emily.",
        "option_a": "Emily is the most articulate candidate in the final round.",
        "option_b": "Emily is less articulate than any candidate in the final round.",
        "option_c": "Emily is as articulate as other candidates in the final round.",
        "option_d": "Other candidates in the final round are more articulate than Emily.",
        "correct_answer": "A",
        "explanation": "Biến đổi từ so sánh bằng phủ định 'No other... is as articulate as Emily' sang so sánh nhất 'Emily is the most articulate candidate in the final round' (Emily là ứng viên ăn nói lưu loát nhất)."
    },
    {
        "part": "Phần 11: Kết hợp câu (Sentence Combining)",
        "skill": "GRAMMAR",
        "question_text": "He didn't check the weather forecast beforehand. He got completely soaked in the heavy downpour.",
        "option_a": "If he had checked the weather forecast beforehand, he wouldn't have got completely soaked in the heavy downpour.",
        "option_b": "If he checked the weather forecast beforehand, he wouldn't get soaked in the heavy downpour.",
        "option_c": "Unless he had checked the weather forecast, he wouldn't have got soaked in the heavy downpour.",
        "option_d": "Had he not checked the weather forecast beforehand, he would have got soaked in the heavy downpour.",
        "correct_answer": "A",
        "explanation": "Hai sự việc đã xảy ra trong quá khứ -> Dùng câu điều kiện loại 3 để diễn tả sự việc trái với thực tế quá khứ: If + S + had + V3, S + would + have + V3."
    },
    {
        "part": "Phần 11: Kết hợp câu (Sentence Combining)",
        "skill": "GRAMMAR",
        "question_text": "The keynote speaker arrived at the conference hall. The opening ceremony commenced immediately after that.",
        "option_a": "No sooner had the keynote speaker arrived at the conference hall than the opening ceremony commenced.",
        "option_b": "Scarcely had the keynote speaker arrived at the conference hall when the opening ceremony had commenced.",
        "option_c": "Hardly had the opening ceremony commenced when the keynote speaker arrived at the conference hall.",
        "option_d": "Not until the opening ceremony commenced did the keynote speaker arrive at the conference hall.",
        "correct_answer": "A",
        "explanation": "Cấu trúc đảo ngữ chỉ hành động vừa mới xảy ra thì hành động khác tiếp nối ngay: 'No sooner had + S + V3/ed + than + S + V2/ed' (Ngay sau khi diễn giả đến thì buổi lễ khai mạc lập tức bắt đầu)."
    }
]


def seed_thpt_exams():
    """
    Seed standard 50-question National High School Graduation (THPT Quốc Gia) English mock exams.
    """
    thpt_exam = Exam.query.filter_by(category="THPT").first()
    if not thpt_exam:
        thpt_exam = Exam(
            title="Đề Thi Thử Tốt Nghiệp THPT Quốc Gia Môn Tiếng Anh (Chuẩn Cấu Trúc Bộ GD&ĐT)",
            category="THPT",
            duration=60,
            duration_minutes=60,
            difficulty="Medium",
            question_bank="THPT National Bank",
            selection_type="random",
            question_count=len(THPT_50_QUESTIONS),
            is_published=True,
            is_active=True
        )
        db.session.add(thpt_exam)
        db.session.flush()

    # If questions do not exist yet for this exam, bulk insert them
    existing_q_count = ExamQuestion.query.filter_by(exam_id=thpt_exam.id).count()
    if existing_q_count < len(THPT_50_QUESTIONS):
        # Clear any partial questions
        ExamQuestion.query.filter_by(exam_id=thpt_exam.id).delete()
        
        questions_to_add = []
        for q_data in THPT_50_QUESTIONS:
            eq = ExamQuestion(
                exam_id=thpt_exam.id,
                skill=q_data.get("skill", "GENERAL"),
                part=q_data.get("part", "THPT Exam"),
                type=q_data.get("type", "SINGLE_CHOICE"),
                question_text=q_data.get("question_text"),
                option_a=q_data.get("option_a"),
                option_b=q_data.get("option_b"),
                option_c=q_data.get("option_c"),
                option_d=q_data.get("option_d"),
                correct_answer=q_data.get("correct_answer"),
                transcript=q_data.get("transcript"),
                explanation=q_data.get("explanation")
            )
            questions_to_add.append(eq)
            
        db.session.bulk_save_objects(questions_to_add)
        thpt_exam.question_count = len(THPT_50_QUESTIONS)
        db.session.commit()

    return thpt_exam
