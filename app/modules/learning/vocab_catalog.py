"""
Vocabulary Taxonomy and Course Catalog Definition
Hierarchical classification: Category -> Subcategory / Course -> Lesson Unit / Topic
"""

VOCAB_CATEGORIES = {
    "cefr": {
        "key": "cefr",
        "title": "Từ vựng Chuẩn CEFR",
        "subtitle": "Khung tham chiếu Châu Âu (A0 - C2)",
        "badge": "Chuẩn Quốc Tế",
        "icon": "ph-globe-hemisphere-west",
        "color": "primary",
        "gradient": "linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%)",
        "description": "Lộ trình 7 bậc từ vựng chuẩn quốc tế giúp xây dựng nền tảng vững chắc từ con số 0 đến thành thạo như người bản xứ.",
        "subcategories": {
            "a0": {
                "key": "a0",
                "title": "A0 - Mới bắt đầu (Starter)",
                "level": "A0",
                "icon": "🌱",
                "color": "#10b981",
                "description": "Từ vựng nhập môn siêu căn bản: Bảng chữ cái, chữ số, màu sắc, lời chào và các đồ vật quen thuộc.",
                "target": "Người mới bắt đầu học tiếng Anh",
                "estimated_words": 150,
            },
            "a1": {
                "key": "a1",
                "title": "A1 - Căn bản (Beginner)",
                "level": "A1",
                "icon": "🥉",
                "color": "#06b6d4",
                "description": "Vốn từ thiết yếu cho các nhu cầu giao tiếp cụ thể hàng ngày: Bản thân, gia đình, nơi ở và công việc đơn giản.",
                "target": "Hiểu và giao tiếp câu ngắn đơn giản",
                "estimated_words": 500,
            },
            "a2": {
                "key": "a2",
                "title": "A2 - Sơ cấp (Elementary)",
                "level": "A2",
                "icon": "🥈",
                "color": "#3b82f6",
                "description": "Mở rộng từ vựng về thói quen, mua sắm, địa điểm xung quanh, việc làm và các hoạt động giải trí.",
                "target": "Tự tin trao đổi thông tin quen thuộc",
                "estimated_words": 1000,
            },
            "b1": {
                "key": "b1",
                "title": "B1 - Trung cấp (Intermediate)",
                "level": "B1",
                "icon": "🥇",
                "color": "#6366f1",
                "description": "Từ vựng diễn đạt quan điểm, mô tả trải nghiệm, sự kiện, ước mơ và kế hoạch tương lai.",
                "target": "Xử lý hầu hết các tình huống khi đi du lịch, giao tiếp",
                "estimated_words": 1500,
            },
            "b2": {
                "key": "b2",
                "title": "B2 - Trung cao cấp (Upper-Intermediate)",
                "level": "B2",
                "icon": "💎",
                "color": "#8b5cf6",
                "description": "Từ vựng học thuật, kinh tế - xã hội, tranh luận logic và văn phong học thuật chuyên nghiệp.",
                "target": "Giao tiếp tự nhiên, đọc hiểu văn bản chuyên ngành",
                "estimated_words": 2000,
            },
            "c1": {
                "key": "c1",
                "title": "C1 - Cao cấp (Advanced)",
                "level": "C1",
                "icon": "👑",
                "color": "#ec4899",
                "description": "Vốn từ sâu rộng, linh hoạt trong ngữ cảnh trang trọng, văn phong ẩn dụ và phân tích phức tạp.",
                "target": "Thành thạo trong môi trường học thuật & công việc cao cấp",
                "estimated_words": 2500,
            },
            "c2": {
                "key": "c2",
                "title": "C2 - Thành thạo (Mastery)",
                "level": "C2",
                "icon": "🏆",
                "color": "#f59e0b",
                "description": "Tương đương trình độ người bản xứ am hiểu sâu rộng, diễn đạt tinh tế mọi sắc thái ngữ nghĩa.",
                "target": "Làm chủ hoàn toàn ngôn ngữ",
                "estimated_words": 3000,
            },
        },
    },
    "toeic": {
        "key": "toeic",
        "title": "Từ vựng Luyện thi TOEIC",
        "subtitle": "Listening & Reading Trọng tâm",
        "badge": "Chứng Chỉ Quốc Tế",
        "icon": "ph-certificate",
        "color": "warning",
        "gradient": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        "description": "Hệ thống từ vựng cốt lõi bám sát cấu trúc đề thi TOEIC quốc tế, tập trung môi trường công sở, thương mại và hợp đồng.",
        "subcategories": {
            "toeic_600": {
                "key": "toeic_600",
                "title": "Bộ 600 từ vựng TOEIC Thiết yếu",
                "level": "B1",
                "icon": "🎯",
                "color": "#f59e0b",
                "description": "50 chủ đề kinh doanh, tài chính, hợp đồng, nhân sự & du lịch thường gặp nhất trong đề thi TOEIC.",
                "target": "Mục tiêu TOEIC 500 - 650+",
                "estimated_words": 600,
            },
            "toeic_hackers": {
                "key": "toeic_hackers",
                "title": "Bộ Hackers TOEIC Vocabulary",
                "level": "B2",
                "icon": "⚡",
                "color": "#ef4444",
                "description": "Lộ trình 30 ngày từ vựng chuyên sâu bám sát đề thi thật ETS mới nhất kèm cụm từ bẫy điểm cao.",
                "target": "Mục tiêu TOEIC 700 - 850+",
                "estimated_words": 900,
            },
            "toeic_parts": {
                "key": "toeic_parts",
                "title": "Từ vựng Trọng tâm theo Part 1 - 7",
                "level": "B1",
                "icon": "📑",
                "color": "#8b5cf6",
                "description": "Phân loại từ vựng theo dạng thức đề thi: Tranh ảnh Part 1, Hỏi đáp Part 2, Đoạn hội thoại Part 3, Đọc hiểu Part 7.",
                "target": "Tối ưu điểm số từng phần thi cụ thể",
                "estimated_words": 750,
            },
        },
    },
    "ielts": {
        "key": "ielts",
        "title": "Từ vựng Học thuật IELTS",
        "subtitle": "General Training & Academic",
        "badge": "IELTS Academic",
        "icon": "ph-graduation-cap",
        "color": "danger",
        "gradient": "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)",
        "description": "Từ vựng học thuật cao cấp, Paraphrasing, Collocations và Idioms giúp bứt phá tiêu chuẩn Lexical Resource trong Writing & Speaking.",
        "subcategories": {
            "ielts_band_5": {
                "key": "ielts_band_5",
                "title": "IELTS Foundation & General (Band 5.0 - 5.5)",
                "level": "B1",
                "icon": "🚀",
                "color": "#06b6d4",
                "description": "Xây dựng nền tảng từ vựng cơ bản phục vụ đời sống, công việc và bài thi IELTS General Training.",
                "target": "IELTS Band 5.0 - 5.5",
                "estimated_words": 600,
            },
            "ielts_band_6_7": {
                "key": "ielts_band_6_7",
                "title": "IELTS Academic Core (Band 6.0 - 7.0)",
                "level": "B2",
                "icon": "🔥",
                "color": "#f97316",
                "description": "Hệ thống từ vựng học thuật theo các chủ đề lớn của IELTS: Education, Environment, Technology, Society.",
                "target": "IELTS Band 6.0 - 7.0",
                "estimated_words": 1000,
            },
            "ielts_band_8_9": {
                "key": "ielts_band_8_9",
                "title": "IELTS Advanced Master (Band 8.0 - 9.0)",
                "level": "C1",
                "icon": "🌟",
                "color": "#ec4899",
                "description": "Vốn từ vựng tinh hoa, cấu trúc phức tạp và phong cách diễn đạt tự nhiên chuẩn học giả.",
                "target": "IELTS Band 8.0 - 9.0",
                "estimated_words": 800,
            },
            "ielts_collocations": {
                "key": "ielts_collocations",
                "title": "Academic Collocations & Idioms",
                "level": "B2",
                "icon": "💡",
                "color": "#10b981",
                "description": "Tổng hợp các cụm từ kết hợp tự nhiên (Collocations) và thành ngữ ăn điểm cho Speaking & Writing Task 2.",
                "target": "Tăng điểm tiêu chuẩn Lexical Resource",
                "estimated_words": 500,
            },
        },
    },
    "specialized": {
        "key": "specialized",
        "title": "Từ vựng Tiếng Anh Chuyên ngành",
        "subtitle": "English for Specific Purposes (ESP)",
        "badge": "Chuyên Ngành ESP",
        "icon": "ph-briefcase",
        "color": "info",
        "gradient": "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
        "description": "Thuật ngữ chuyên sâu dành riêng cho người đi làm trong các lĩnh vực công nghệ, kinh tế, y tế, du lịch và kỹ thuật.",
        "subcategories": {
            "it_tech": {
                "key": "it_tech",
                "title": "Công nghệ thông tin (IT & Software)",
                "level": "B2",
                "icon": "💻",
                "color": "#3b82f6",
                "description": "Thuật ngữ lập trình, hệ điều hành, cơ sở dữ liệu, an ninh mạng, kiến trúc phần mềm và AI.",
                "target": "Lập trình viên, Kỹ sư phần mềm, IT Support",
                "estimated_words": 600,
            },
            "business_finance": {
                "key": "business_finance",
                "title": "Kinh tế, Tài chính & Ngân hàng",
                "level": "B2",
                "icon": "📈",
                "color": "#10b981",
                "description": "Thuật ngữ tài chính doanh nghiệp, đầu tư chứng khoán, kế toán, ngân hàng và thương mại quốc tế.",
                "target": "Chuyên viên tài chính, Kế toán, Ngân hàng",
                "estimated_words": 650,
            },
            "medical": {
                "key": "medical",
                "title": "Y khoa, Dược phẩm & Điều dưỡng",
                "level": "B2",
                "icon": "🩺",
                "color": "#ef4444",
                "description": "Thuật ngữ y khoa lâm sàng, giải phẫu, dược phẩm, bệnh học và chăm sóc bệnh nhân.",
                "target": "Bác sĩ, Dược sĩ, Điều dưỡng, Y tá",
                "estimated_words": 700,
            },
            "hospitality": {
                "key": "hospitality",
                "title": "Du lịch, Nhà hàng & Khách sạn",
                "level": "B1",
                "icon": "🏨",
                "color": "#f59e0b",
                "description": "Nghiệp vụ lễ tân, dịch vụ khách hàng, đặt phòng, tour du lịch và ẩm thực nhà hàng.",
                "target": "Hướng dẫn viên, Quản lý khách sạn & F&B",
                "estimated_words": 500,
            },
            "marketing": {
                "key": "marketing",
                "title": "Marketing, Truyền thông & Sales",
                "level": "B2",
                "icon": "📢",
                "color": "#8b5cf6",
                "description": "Chiến dịch quảng cáo, digital branding, quan hệ công chúng (PR), hành vi người tiêu dùng và bán hàng.",
                "target": "Marketer, Content Creator, Chuyên viên Sales",
                "estimated_words": 550,
            },
            "engineering": {
                "key": "engineering",
                "title": "Kỹ thuật, Cơ khí & Xây dựng",
                "level": "B2",
                "icon": "⚙️",
                "color": "#64748b",
                "description": "Thuật ngữ cơ khí chế tạo, điện tử viễn thông, xây dựng dân dụng và kiểm định an toàn kỹ thuật.",
                "target": "Kỹ sư cơ khí, Điện tử, Kiến trúc sư",
                "estimated_words": 600,
            },
        },
    },
    "topic": {
        "key": "topic",
        "title": "Từ vựng theo Chủ đề Đời sống",
        "subtitle": "Daily Life & Practical Communication",
        "badge": "Giao Tiếp Thực Tế",
        "icon": "ph-sparkle",
        "color": "success",
        "gradient": "linear-gradient(135deg, #059669 0%, #047857 100%)",
        "description": "Từ vựng xoay quanh các chủ đề quen thuộc hàng ngày, giúp bạn giao tiếp lưu loát và tự nhiên trong mọi hoàn cảnh.",
        "subcategories": {
            "daily_life": {
                "key": "daily_life",
                "title": "Đời sống & Sinh hoạt hàng ngày",
                "level": "A1",
                "icon": "🏠",
                "color": "#10b981",
                "description": "Hoạt động thường nhật, sinh hoạt gia đình, nhà cửa, đồ dùng cá nhân và thói quen.",
                "target": "Giao tiếp căn bản trong đời sống",
                "estimated_words": 400,
            },
            "travel": {
                "key": "travel",
                "title": "Du lịch & Phương tiện di chuyển",
                "level": "A2",
                "icon": "✈️",
                "color": "#06b6d4",
                "description": "Sân bay, ga tàu, thủ tục xuất nhập cảnh, hỏi đường, đặt vé và trải nghiệm khám phá.",
                "target": "Tự tin du lịch và khám phá thế giới",
                "estimated_words": 500,
            },
            "food_dining": {
                "key": "food_dining",
                "title": "Ẩm thực, Nấu ăn & Nhà hàng",
                "level": "A2",
                "icon": "🍳",
                "color": "#f59e0b",
                "description": "Nguyên liệu, cách chế biến món ăn, gọi món tại nhà hàng, đánh giá hương vị thức ăn.",
                "target": "Tự tin ăn uống và đặt tiệc quốc tế",
                "estimated_words": 450,
            },
            "relationships": {
                "key": "relationships",
                "title": "Gia đình, Bạn bè & Tình cảm",
                "level": "A2",
                "icon": "❤️",
                "color": "#ec4899",
                "description": "Mối quan hệ họ hàng, bạn bè thân thiết, cảm xúc, tính cách con người và hẹn hò.",
                "target": "Giao tiếp xã hội và biểu đạt cảm xúc",
                "estimated_words": 450,
            },
            "environment": {
                "key": "environment",
                "title": "Môi trường, Khí hậu & Thiên nhiên",
                "level": "B1",
                "icon": "🌿",
                "color": "#22c55e",
                "description": "Thời tiết bốn mùa, động thực vật, ô nhiễm môi trường, biến đổi khí hậu và năng lượng xanh.",
                "target": "Thảo luận về các chủ đề tự nhiên & xã hội",
                "estimated_words": 500,
            },
            "media_tech": {
                "key": "media_tech",
                "title": "Truyền thông, Mạng xã hội & Giải trí",
                "level": "B1",
                "icon": "📱",
                "color": "#6366f1",
                "description": "Internet, mạng xã hội, âm nhạc, điện ảnh, tin tức báo chí và các nền tảng số hiện đại.",
                "target": "Bắt kịp xu hướng truyền thông công nghệ",
                "estimated_words": 500,
            },
        },
    },
}


def get_category_info(cat_key: str):
    """Get category configuration by key"""
    if not cat_key:
        return None
    return VOCAB_CATEGORIES.get(cat_key.lower().strip())


def get_subcategory_info(cat_key: str, subcat_key: str):
    """Get subcategory configuration by category key and subcategory key"""
    cat = get_category_info(cat_key)
    if not cat:
        return None
    if not subcat_key:
        return None
    return cat["subcategories"].get(subcat_key.lower().strip())


def normalize_category_key(raw_val: str) -> str:
    """Normalize raw category string to standard key"""
    if not raw_val:
        return "cefr"
    v = raw_val.lower().strip()
    if "toeic" in v:
        return "toeic"
    if "ielts" in v:
        return "ielts"
    if any(x in v for x in ["special", "esp", "nganh", "chuyen"]):
        return "specialized"
    if any(x in v for x in ["topic", "chu de", "de tai", "life", "doi song"]):
        return "topic"
    return "cefr"


def normalize_subcategory_key(cat_key: str, raw_subcat: str, level: str = None, topic: str = None) -> str:
    """Normalize raw subcategory string to valid key under the given category"""
    cat = get_category_info(cat_key)
    if not cat:
        return "a1"
    
    subcats = cat["subcategories"]
    if raw_subcat:
        rs = raw_subcat.lower().strip().replace("-", "_").replace(" ", "_")
        for k in subcats.keys():
            if k == rs or k in rs or rs in k:
                return k

    # Fallback based on level or topic
    if cat_key == "cefr":
        lvl = (level or "A1").lower().strip()
        if lvl in subcats:
            return lvl
        return "a1"
    
    if cat_key == "toeic":
        if topic and ("hacker" in topic.lower()):
            return "toeic_hackers"
        if topic and ("part" in topic.lower()):
            return "toeic_parts"
        return "toeic_600"

    if cat_key == "ielts":
        if level in ["C1", "C2"] or (topic and "8" in topic):
            return "ielts_band_8_9"
        if topic and ("collocation" in topic.lower() or "idiom" in topic.lower()):
            return "ielts_collocations"
        if level in ["B2"] or (topic and "6" in topic or "7" in topic):
            return "ielts_band_6_7"
        return "ielts_band_5"

    if cat_key == "specialized":
        tp = (topic or "").lower()
        if "it" in tp or "software" in tp or "tech" in tp or "code" in tp:
            return "it_tech"
        if "finance" in tp or "bank" in tp or "tai chinh" in tp or "kinh te" in tp:
            return "business_finance"
        if "medic" in tp or "y te" in tp or "duoc" in tp or "health" in tp:
            return "medical"
        if "hotel" in tp or "du lich" in tp or "tour" in tp or "hospitality" in tp:
            return "hospitality"
        if "market" in tp or "sale" in tp or "quang cao" in tp:
            return "marketing"
        return "engineering"

    if cat_key == "topic":
        tp = (topic or "").lower()
        if "travel" in tp or "du lich" in tp:
            return "travel"
        if "food" in tp or "am thuc" in tp or "cook" in tp:
            return "food_dining"
        if "relat" in tp or "family" in tp or "gia dinh" in tp:
            return "relationships"
        if "env" in tp or "nature" in tp or "thien nhien" in tp:
            return "environment"
        if "media" in tp or "social" in tp:
            return "media_tech"
        return "daily_life"

    return list(subcats.keys())[0]
