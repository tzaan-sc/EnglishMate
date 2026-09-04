"""
Seed comprehensive vocabulary across all 5 major categories:
1. CEFR (A0, A1, A2, B1, B2, C1, C2)
2. TOEIC (600 Essential words, Hackers TOEIC, Parts 1-7)
3. IELTS (Band 5, Band 6-7, Band 8-9, Collocations)
4. SPECIALIZED (IT, Business/Finance, Medical, Hospitality, Marketing, Engineering)
5. TOPIC (Daily Life, Travel, Food, Relationships, Environment, Media/Tech)
"""

import csv
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app import create_app
from app.extensions import db
from app.modules.learning.models import Vocabulary, VocabularyProgress

app = create_app()

def run_seed():
    with app.app_context():
        print("--- Starting Comprehensive Vocabulary Seeding ---")
        
        # Clear existing draft vocabulary if any
        existing_count = Vocabulary.query.count()
        print(f"Current vocabulary count in DB: {existing_count}")
        
        # We can clear vocabulary and vocabulary progress cleanly
        print("Clearing draft vocabulary rows...")
        VocabularyProgress.query.delete()
        Vocabulary.query.delete()
        db.session.commit()

        new_vocab_items = []

        # 1. LOAD TOEIC 600 FROM final_toeic.csv
        csv_toeic = root_dir / "csv_templates" / "data" / "final_toeic.csv"
        if csv_toeic.exists():
            print(f"Loading TOEIC words from {csv_toeic}...")
            with open(csv_toeic, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    w = r.get("word", "").strip()
                    if not w:
                        continue
                    topic = r.get("topic", "").strip() or "General Business"
                    new_vocab_items.append(Vocabulary(
                        word=w,
                        pronunciation=r.get("pronunciation", "").strip() or "/.../",
                        part_of_speech=r.get("part_of_speech", "").strip() or "noun",
                        meaning_vi=r.get("meaning_vi", "").strip(),
                        example_en=r.get("example_en", "").strip() or f"The term '{w}' is commonly used in business.",
                        example_vi=r.get("example_vi", "").strip() or f"Thuật ngữ '{w}' thường được dùng trong kinh doanh.",
                        category="toeic",
                        subcategory="toeic_600",
                        lesson_unit=topic,
                        topic=topic,
                        level=r.get("level", "B1").strip() or "B1",
                        image_url=r.get("image_url", "").strip() or None,
                        collocations=r.get("collocations", "").strip() or None,
                        synonyms=r.get("synonyms", "").strip() or None,
                        antonyms=r.get("antonyms", "").strip() or None,
                    ))
            print(f"Loaded {len(new_vocab_items)} TOEIC 600 words.")

        # 2. SEED CEFR CURRICULUM (A0 -> C2)
        cefr_data = [
            # A0 - Starter
            {"word": "hello", "pronunciation": "/həˈləʊ/", "pos": "interjection", "meaning": "xin chào", "en": "Hello, how are you today?", "vi": "Xin chào, hôm nay bạn thế nào?", "cat": "cefr", "sub": "a0", "unit": "Unit 1: Greetings & Basics", "topic": "Greetings", "lvl": "A0", "colloc": "say hello; hello there", "syn": "hi; greetings"},
            {"word": "goodbye", "pronunciation": "/ɡʊdˈbaɪ/", "pos": "interjection", "meaning": "tạm biệt", "en": "Goodbye, see you tomorrow!", "vi": "Tạm biệt, hẹn gặp lại bạn ngày mai!", "cat": "cefr", "sub": "a0", "unit": "Unit 1: Greetings & Basics", "topic": "Greetings", "lvl": "A0", "colloc": "say goodbye; wave goodbye", "syn": "bye; farewell"},
            {"word": "thank you", "pronunciation": "/ˈθæŋk juː/", "pos": "phrase", "meaning": "cảm ơn bạn", "en": "Thank you very much for your help.", "vi": "Cảm ơn bạn rất nhiều vì sự giúp đỡ.", "cat": "cefr", "sub": "a0", "unit": "Unit 1: Greetings & Basics", "topic": "Greetings", "lvl": "A0", "colloc": "thank you very much", "syn": "thanks; grateful"},
            {"word": "apple", "pronunciation": "/ˈæp.əl/", "pos": "noun", "meaning": "quả táo", "en": "I eat a fresh red apple every morning.", "vi": "Tôi ăn một quả táo đỏ tươi mỗi sáng.", "cat": "cefr", "sub": "a0", "unit": "Unit 2: Colors & Food", "topic": "Food", "lvl": "A0", "colloc": "fresh apple; red apple", "syn": ""},
            {"word": "blue", "pronunciation": "/bluː/", "pos": "adjective", "meaning": "màu xanh da trời", "en": "The sky is bright blue and sunny.", "vi": "Bầu trời có màu xanh da trời sáng và có nắng.", "cat": "cefr", "sub": "a0", "unit": "Unit 2: Colors & Food", "topic": "Colors", "lvl": "A0", "colloc": "deep blue; bright blue", "syn": "azure; navy"},
            {"word": "family", "pronunciation": "/ˈfæm.əl.i/", "pos": "noun", "meaning": "gia đình", "en": "I love spending weekend time with my family.", "vi": "Tôi thích dành thời gian cuối tuần bên gia đình.", "cat": "cefr", "sub": "a0", "unit": "Unit 3: People & Family", "topic": "Family", "lvl": "A0", "colloc": "close family; family member", "syn": "relatives; household"},
            {"word": "mother", "pronunciation": "/ˈmʌð.ər/", "pos": "noun", "meaning": "mẹ", "en": "My mother is a wonderful teacher.", "vi": "Mẹ tôi là một giáo viên tuyệt vời.", "cat": "cefr", "sub": "a0", "unit": "Unit 3: People & Family", "topic": "Family", "lvl": "A0", "colloc": "loving mother; mother and child", "syn": "mom; mama"},
            {"word": "father", "pronunciation": "/ˈfɑː.ðər/", "pos": "noun", "meaning": "bố, cha", "en": "His father works in a local hospital.", "vi": "Bố của anh ấy làm việc ở bệnh viện địa phương.", "cat": "cefr", "sub": "a0", "unit": "Unit 3: People & Family", "topic": "Family", "lvl": "A0", "colloc": "caring father; proud father", "syn": "dad; papa"},
            {"word": "number", "pronunciation": "/ˈnʌm.bər/", "pos": "noun", "meaning": "con số, số", "en": "Write down your phone number here.", "vi": "Hãy viết số điện thoại của bạn ở đây.", "cat": "cefr", "sub": "a0", "unit": "Unit 4: Numbers & Objects", "topic": "Numbers", "lvl": "A0", "colloc": "lucky number; phone number", "syn": "digit; figure"},
            {"word": "house", "pronunciation": "/haʊs/", "pos": "noun", "meaning": "ngôi nhà", "en": "They live in a beautiful white house.", "vi": "Họ sống trong một ngôi nhà màu trắng xinh đẹp.", "cat": "cefr", "sub": "a0", "unit": "Unit 4: Numbers & Objects", "topic": "House", "lvl": "A0", "colloc": "big house; dream house", "syn": "home; residence"},

            # A1 - Beginner
            {"word": "breakfast", "pronunciation": "/ˈbrek.fəst/", "pos": "noun", "meaning": "bữa ăn sáng", "en": "I usually have bread and eggs for breakfast.", "vi": "Tôi thường ăn bánh mì và trứng cho bữa sáng.", "cat": "cefr", "sub": "a1", "unit": "Unit 1: Daily Routines", "topic": "Daily Routine", "lvl": "A1", "colloc": "have breakfast; make breakfast", "syn": "morning meal"},
            {"word": "routine", "pronunciation": "/ruːˈtiːn/", "pos": "noun", "meaning": "thói quen sinh hoạt hàng ngày", "en": "Exercising is part of my morning routine.", "vi": "Tập thể dục là một phần trong thói quen buổi sáng của tôi.", "cat": "cefr", "sub": "a1", "unit": "Unit 1: Daily Routines", "topic": "Daily Routine", "lvl": "A1", "colloc": "daily routine; workout routine", "syn": "schedule; habit"},
            {"word": "commute", "pronunciation": "/kəˈmjuːt/", "pos": "verb", "meaning": "đi lại (từ nhà đến chỗ làm)", "en": "She commutes to work by bus every day.", "vi": "Cô ấy đi làm bằng xe buýt mỗi ngày.", "cat": "cefr", "sub": "a1", "unit": "Unit 1: Daily Routines", "topic": "Transportation", "lvl": "A1", "colloc": "daily commute; commute by train", "syn": "travel; journey"},
            {"word": "library", "pronunciation": "/ˈlaɪ.brər.i/", "pos": "noun", "meaning": "thư viện", "en": "Students borrow books from the city library.", "vi": "Sinh viên mượn sách từ thư viện thành phố.", "cat": "cefr", "sub": "a1", "unit": "Unit 2: City & Places", "topic": "Places", "lvl": "A1", "colloc": "public library; visit library", "syn": "book repository"},
            {"word": "weather", "pronunciation": "/ˈweð.ər/", "pos": "noun", "meaning": "thời tiết", "en": "The weather is sunny and warm today.", "vi": "Thời tiết hôm nay có nắng và ấm áp.", "cat": "cefr", "sub": "a1", "unit": "Unit 2: City & Places", "topic": "Weather", "lvl": "A1", "colloc": "bad weather; nice weather", "syn": "climate; forecast"},
            {"word": "friendly", "pronunciation": "/ˈfrend.li/", "pos": "adjective", "meaning": "thân thiện, hòa đồng", "en": "The local people are very friendly and kind.", "vi": "Người dân địa phương rất thân thiện và tốt bụng.", "cat": "cefr", "sub": "a1", "unit": "Unit 3: Personality & Hobbies", "topic": "Personality", "lvl": "A1", "colloc": "friendly smile; eco-friendly", "syn": "welcoming; warm", "ant": "hostile; rude"},
            {"word": "hobby", "pronunciation": "/ˈhɒb.i/", "pos": "noun", "meaning": "sở thích", "en": "Photography is his favorite outdoor hobby.", "vi": "Nhiếp ảnh là sở thích ngoài trời yêu thích của anh ấy.", "cat": "cefr", "sub": "a1", "unit": "Unit 3: Personality & Hobbies", "topic": "Hobbies", "lvl": "A1", "colloc": "favorite hobby; pursue a hobby", "syn": "pastime; interest"},

            # A2 - Elementary
            {"word": "comfortable", "pronunciation": "/ˈkʌm.fə.tə.bəl/", "pos": "adjective", "meaning": "thoải mái, tiện nghi", "en": "This sofa is extremely comfortable to sit on.", "vi": "Chiếc ghế sofa này ngồi cực kỳ thoải mái.", "cat": "cefr", "sub": "a2", "unit": "Unit 1: Living & Accommodation", "topic": "Housing", "lvl": "A2", "colloc": "feel comfortable; comfortable life", "syn": "cozy; restful", "ant": "uncomfortable"},
            {"word": "neighbor", "pronunciation": "/ˈneɪ.bər/", "pos": "noun", "meaning": "hàng xóm", "en": "Our neighbor helped us water the plants.", "vi": "Người hàng xóm đã giúp chúng tôi tưới cây.", "cat": "cefr", "sub": "a2", "unit": "Unit 1: Living & Accommodation", "topic": "Community", "lvl": "A2", "colloc": "next-door neighbor; friendly neighbor", "syn": "community member"},
            {"word": "discount", "pronunciation": "/ˈdɪs.kaʊnt/", "pos": "noun", "meaning": "sự giảm giá, chiết khấu", "en": "They offer a 20% discount for all students.", "vi": "Họ giảm giá 20% cho tất cả học sinh sinh viên.", "cat": "cefr", "sub": "a2", "unit": "Unit 2: Shopping & Services", "topic": "Shopping", "lvl": "A2", "colloc": "offer a discount; student discount", "syn": "price reduction; markdown"},
            {"word": "delicious", "pronunciation": "/dɪˈlɪʃ.əs/", "pos": "adjective", "meaning": "ngon miệng", "en": "She cooked a delicious dinner for her guests.", "vi": "Cô ấy đã nấu một bữa tối rất ngon cho các vị khách.", "cat": "cefr", "sub": "a2", "unit": "Unit 2: Shopping & Services", "topic": "Food", "lvl": "A2", "colloc": "delicious meal; look delicious", "syn": "tasty; yummy", "ant": "disgusting; tasteless"},
            {"word": "explore", "pronunciation": "/ɪkˈsplɔːr/", "pos": "verb", "meaning": "khám phá, thám hiểm", "en": "We want to explore new islands this summer.", "vi": "Chúng tôi muốn khám phá các hòn đảo mới vào mùa hè này.", "cat": "cefr", "sub": "a2", "unit": "Unit 3: Travel & Vacations", "topic": "Travel", "lvl": "A2", "colloc": "explore possibilities; explore the world", "syn": "discover; investigate"},

            # B1 - Intermediate
            {"word": "accomplish", "pronunciation": "/əˈkʌm.plɪʃ/", "pos": "verb", "meaning": "hoàn thành, đạt được thành tựu", "en": "She accomplished all her study goals this term.", "vi": "Cô ấy đã hoàn thành mọi mục tiêu học tập trong kỳ này.", "cat": "cefr", "sub": "b1", "unit": "Unit 1: Personal Achievement", "topic": "Education", "lvl": "B1", "colloc": "accomplish a mission; accomplish a task", "syn": "achieve; fulfill", "ant": "fail; abandon"},
            {"word": "confident", "pronunciation": "/ˈkɒn.fɪ.dənt/", "pos": "adjective", "meaning": "tự tin", "en": "He feels confident about passing the English exam.", "vi": "Anh ấy cảm thấy tự tin về việc sẽ vượt qua kỳ thi tiếng Anh.", "cat": "cefr", "sub": "b1", "unit": "Unit 1: Personal Achievement", "topic": "Psychology", "lvl": "B1", "colloc": "feel confident; highly confident", "syn": "self-assured; positive", "ant": "insecure; timid"},
            {"word": "collaboration", "pronunciation": "/kəˌlæb.əˈreɪ.ʃən/", "pos": "noun", "meaning": "sự cộng tác, hợp tác", "en": "Successful projects require close collaboration.", "vi": "Các dự án thành công đòi hỏi sự hợp tác chặt chẽ.", "cat": "cefr", "sub": "b1", "unit": "Unit 2: Workplace Skills", "topic": "Workplace", "lvl": "B1", "colloc": "in collaboration with; close collaboration", "syn": "cooperation; teamwork", "ant": "rivalry; competition"},
            {"word": "efficient", "pronunciation": "/ɪˈfɪʃ.ənt/", "pos": "adjective", "meaning": "hiệu quả, tiết kiệm thời gian", "en": "Modern trains provide an efficient way to travel.", "vi": "Tàu hỏa hiện đại mang lại cách di chuyển rất hiệu quả.", "cat": "cefr", "sub": "b1", "unit": "Unit 2: Workplace Skills", "topic": "Productivity", "lvl": "B1", "colloc": "energy efficient; highly efficient", "syn": "effective; productive", "ant": "inefficient; wasteful"},

            # B2 - Upper-Intermediate
            {"word": "resilient", "pronunciation": "/rɪˈzɪl.jənt/", "pos": "adjective", "meaning": "kiên cường, có khả năng phục hồi nhanh", "en": "The company proved resilient during economic crises.", "vi": "Công ty đã chứng tỏ sự kiên cường trong các cuộc khủng hoảng kinh tế.", "cat": "cefr", "sub": "b2", "unit": "Unit 1: Overcoming Adversity", "topic": "Mindset", "lvl": "B2", "colloc": "highly resilient; resilient spirit", "syn": "tough; adaptable; robust", "ant": "fragile; vulnerable"},
            {"word": "innovative", "pronunciation": "/ˈɪn.ə.veɪ.tɪv/", "pos": "adjective", "meaning": "mang tính đổi mới, sáng tạo đột phá", "en": "They created an innovative solution for green energy.", "vi": "Họ đã tạo ra một giải pháp đột phá cho năng lượng xanh.", "cat": "cefr", "sub": "b2", "unit": "Unit 2: Technology & Society", "topic": "Technology", "lvl": "B2", "colloc": "innovative idea; innovative design", "syn": "creative; cutting-edge; novel", "ant": "outdated; obsolete"},
            {"word": "comprehensive", "pronunciation": "/ˌkɒm.prɪˈhen.sɪv/", "pos": "adjective", "meaning": "toàn diện, bao quát", "en": "The report offers a comprehensive view of global trade.", "vi": "Báo cáo đưa ra một cái nhìn toàn diện về thương mại toàn cầu.", "cat": "cefr", "sub": "b2", "unit": "Unit 2: Technology & Society", "topic": "Research", "lvl": "B2", "colloc": "comprehensive guide; comprehensive review", "syn": "thorough; all-inclusive", "ant": "limited; partial"},

            # C1 - Advanced
            {"word": "procrastinate", "pronunciation": "/prəˈkræs.tɪ.neɪt/", "pos": "verb", "meaning": "chần chừ, trì hoãn công việc", "en": "People often procrastinate when facing difficult tasks.", "vi": "Mọi người thường trì hoãn khi đối mặt với những nhiệm vụ khó khăn.", "cat": "cefr", "sub": "c1", "unit": "Unit 1: Human Psychology", "topic": "Psychology", "lvl": "C1", "colloc": "tend to procrastinate; chronic procrastinator", "syn": "delay; postpone; put off", "ant": "expedite; accelerate"},
            {"word": "ambiguous", "pronunciation": "/æmˈbɪɡ.ju.əs/", "pos": "adjective", "meaning": "mơ hồ, đa nghĩa, không rõ ràng", "en": "The instructions were ambiguous and caused confusion.", "vi": "Các chỉ dẫn rất mơ hồ và gây ra sự nhầm lẫn.", "cat": "cefr", "sub": "c1", "unit": "Unit 1: Human Psychology", "topic": "Communication", "lvl": "C1", "colloc": "highly ambiguous; ambiguous wording", "syn": "vague; equivocal; obscure", "ant": "explicit; crystal-clear"},
            {"word": "meticulous", "pronunciation": "/məˈtɪk.jə.ləs/", "pos": "adjective", "meaning": "tỉ mỉ, cẩn thận từng chi tiết", "en": "He did meticulous research before writing the book.", "vi": "Anh ấy đã nghiên cứu tỉ mỉ trước khi viết cuốn sách.", "cat": "cefr", "sub": "c1", "unit": "Unit 2: Scientific Rigor", "topic": "Science", "lvl": "C1", "colloc": "meticulous attention to detail; meticulous planning", "syn": "thorough; painstaking; diligent", "ant": "careless; sloppy"},

            # C2 - Mastery
            {"word": "ubiquitous", "pronunciation": "/juːˈbɪk.wɪ.təs/", "pos": "adjective", "meaning": "có mặt ở khắp nơi, phổ biến rộng khắp", "en": "Smartphones have become ubiquitous in modern society.", "vi": "Điện thoại thông minh đã trở nên phổ biến ở khắp mọi nơi trong xã hội hiện đại.", "cat": "cefr", "sub": "c2", "unit": "Unit 1: Modern Phenomena", "topic": "Sociology", "lvl": "C2", "colloc": "ubiquitous presence; ubiquitous technology", "syn": "omnipresent; pervasive; universal", "ant": "rare; scarce"},
            {"word": "ephemeral", "pronunciation": "/ɪˈfem.ər.əl/", "pos": "adjective", "meaning": "phù du, sớm nở tối tàn, ngắn ngủi", "en": "Fame on social media can be surprisingly ephemeral.", "vi": "Sự nổi tiếng trên mạng xã hội có thể ngắn ngủi đến bất ngờ.", "cat": "cefr", "sub": "c2", "unit": "Unit 1: Modern Phenomena", "topic": "Philosophy", "lvl": "C2", "colloc": "ephemeral nature; ephemeral pleasure", "syn": "transient; fleeting; momentary", "ant": "permanent; eternal"},
            {"word": "serendipity", "pronunciation": "/ˌser.ənˈdɪp.ə.ti/", "pos": "noun", "meaning": "sự may mắn tình cờ phát hiện điều quý giá", "en": "Finding that rare historic book was pure serendipity.", "vi": "Tìm thấy cuốn sách lịch sử hiếm đó hoàn toàn là sự tình cờ may mắn.", "cat": "cefr", "sub": "c2", "unit": "Unit 2: Rhetoric & Eloquence", "topic": "Language", "lvl": "C2", "colloc": "happy serendipity; moment of serendipity", "syn": "fluke; happy chance; fortune"},
        ]

        for item in cefr_data:
            new_vocab_items.append(Vocabulary(
                word=item["word"],
                pronunciation=item["pronunciation"],
                part_of_speech=item["pos"],
                meaning_vi=item["meaning"],
                example_en=item["en"],
                example_vi=item["vi"],
                category=item["cat"],
                subcategory=item["sub"],
                lesson_unit=item["unit"],
                topic=item["topic"],
                level=item["lvl"],
                collocations=item.get("colloc"),
                synonyms=item.get("syn"),
                antonyms=item.get("ant"),
            ))

        # 3. SEED IELTS CURRICULUM
        ielts_data = [
            # IELTS Band 5
            {"word": "essential", "pronunciation": "/ɪˈsen.ʃəl/", "pos": "adjective", "meaning": "thiết yếu, cực kỳ quan trọng", "en": "Water is essential for all living creatures.", "vi": "Nước là thiết yếu cho mọi sinh vật sống.", "sub": "ielts_band_5", "unit": "Unit 1: Daily Foundations", "topic": "General", "lvl": "B1", "colloc": "play an essential role; essential requirement", "syn": "crucial; vital; fundamental"},
            {"word": "convenient", "pronunciation": "/kənˈviː.ni.ənt/", "pos": "adjective", "meaning": "tiện lợi, thuận tiện", "en": "Online shopping is very convenient for busy workers.", "vi": "Mua sắm trực tuyến rất tiện lợi cho người bận rộn.", "sub": "ielts_band_5", "unit": "Unit 1: Daily Foundations", "topic": "Lifestyle", "lvl": "B1", "colloc": "convenient location; convenient time", "syn": "handy; accessible"},
            {"word": "opportunity", "pronunciation": "/ˌɒp.əˈtjuː.nə.ti/", "pos": "noun", "meaning": "cơ hội, thời cơ", "en": "Studying abroad offers a great opportunity to travel.", "vi": "Du học mang lại cơ hội tuyệt vời để đi du lịch.", "sub": "ielts_band_5", "unit": "Unit 2: Education & Future", "topic": "Education", "lvl": "B1", "colloc": "golden opportunity; grab an opportunity", "syn": "chance; prospect"},

            # IELTS Band 6-7
            {"word": "detrimental", "pronunciation": "/ˌdet.rɪˈmen.təl/", "pos": "adjective", "meaning": "có hại, gây tổn hại nghiêm trọng", "en": "Excessive screen time has detrimental effects on children's health.", "vi": "Dành quá nhiều thời gian trước màn hình gây hại cho sức khỏe của trẻ em.", "sub": "ielts_band_6_7", "unit": "Unit 1: Technology & Well-being", "topic": "Health & Tech", "lvl": "B2", "colloc": "detrimental impact; detrimental effect on", "syn": "harmful; damaging; adverse", "ant": "beneficial; advantageous"},
            {"word": "sustainable", "pronunciation": "/səˈsteɪ.nə.bəl/", "pos": "adjective", "meaning": "bền vững, thân thiện môi trường", "en": "We must transition to sustainable energy sources immediately.", "vi": "Chúng ta phải chuyển đổi sang các nguồn năng lượng bền vững ngay lập tức.", "sub": "ielts_band_6_7", "unit": "Unit 2: Environmental Challenges", "topic": "Environment", "lvl": "B2", "colloc": "sustainable development; sustainable practice", "syn": "eco-friendly; renewable", "ant": "unsustainable; depleting"},
            {"word": "ubiquity", "pronunciation": "/juːˈbɪk.wə.ti/", "pos": "noun", "meaning": "sự hiện diện khắp mọi nơi", "en": "The ubiquity of social media has reshaped human communication.", "vi": "Sự hiện diện khắp nơi của mạng xã hội đã định hình lại cách con người giao tiếp.", "sub": "ielts_band_6_7", "unit": "Unit 1: Technology & Well-being", "topic": "Society", "lvl": "B2", "colloc": "the ubiquity of internet", "syn": "omnipresence; prevalence"},

            # IELTS Band 8-9
            {"word": "juxtaposition", "pronunciation": "/ˌdʒʌk.stə.pəˈzɪʃ.ən/", "pos": "noun", "meaning": "sự đặt cạnh nhau để tương phản", "en": "The juxtaposition of extreme wealth and poverty in the city is striking.", "vi": "Sự tương phản giữa sự giàu có tột bậc và cái nghèo trong thành phố thật đáng kinh ngạc.", "sub": "ielts_band_8_9", "unit": "Unit 1: Sophisticated Discourse", "topic": "Sociology", "lvl": "C1", "colloc": "stark juxtaposition; deliberate juxtaposition", "syn": "contrast; comparison; proximity"},
            {"word": "quintessential", "pronunciation": "/ˌkwɪn.tɪˈsen.ʃəl/", "pos": "adjective", "meaning": "điển hình nhất, tinh túy nhất", "en": "Afternoon tea is the quintessential British tradition.", "vi": "Trà chiều là truyền thống điển hình và tinh túy nhất của nước Anh.", "sub": "ielts_band_8_9", "unit": "Unit 1: Sophisticated Discourse", "topic": "Culture", "lvl": "C1", "colloc": "quintessential example; quintessential style", "syn": "archetypal; classic; prototypical"},

            # IELTS Collocations
            {"word": "play a crucial role", "pronunciation": "/pleɪ ə ˈkruː.ʃəl rəʊl/", "pos": "phrase", "meaning": "đóng vai trò quyết định, then chốt", "en": "Early childhood education plays a crucial role in cognitive development.", "vi": "Giáo dục mầm non đóng một vai trò then chốt trong sự phát triển nhận thức.", "sub": "ielts_collocations", "unit": "Unit 1: Academic High-Scoring Collocations", "topic": "Education", "lvl": "B2", "colloc": "play a crucial role in", "syn": "be of paramount importance"},
            {"word": "pose a threat to", "pronunciation": "/pəʊz ə θret tuː/", "pos": "phrase", "meaning": "đặt ra mối đe dọa đối với", "en": "Deforestation poses a severe threat to biodiversity worldwide.", "vi": "Nạn phá rừng đặt ra một mối đe dọa nghiêm trọng đối với đa dạng sinh học toàn cầu.", "sub": "ielts_collocations", "unit": "Unit 1: Academic High-Scoring Collocations", "topic": "Environment", "lvl": "B2", "colloc": "pose a grave threat to", "syn": "endanger; jeopardize"},
        ]

        for item in ielts_data:
            new_vocab_items.append(Vocabulary(
                word=item["word"],
                pronunciation=item["pronunciation"],
                part_of_speech=item["pos"],
                meaning_vi=item["meaning"],
                example_en=item["en"],
                example_vi=item["vi"],
                category="ielts",
                subcategory=item["sub"],
                lesson_unit=item["unit"],
                topic=item["topic"],
                level=item["lvl"],
                collocations=item.get("colloc"),
                synonyms=item.get("syn"),
                antonyms=item.get("ant"),
            ))

        # 4. SEED SPECIALIZED (ESP)
        esp_data = [
            # IT & Software
            {"word": "repository", "pronunciation": "/rɪˈpɒz.ɪ.tər.i/", "pos": "noun", "meaning": "kho lưu trữ mã nguồn (Git)", "en": "Developers clone the project repository from GitHub.", "vi": "Các lập trình viên sao chép kho mã nguồn dự án từ GitHub.", "sub": "it_tech", "unit": "Unit 1: Version Control & Git", "topic": "Software Dev", "lvl": "B2", "colloc": "remote repository; git repository", "syn": "repo; storage; archive"},
            {"word": "scalability", "pronunciation": "/ˌskeɪ.ləˈbɪl.ə.ti/", "pos": "noun", "meaning": "khả năng mở rộng hệ thống", "en": "Cloud computing provides high scalability for modern web apps.", "vi": "Điện toán đám mây mang lại khả năng mở rộng cao cho các ứng dụng web hiện đại.", "sub": "it_tech", "unit": "Unit 2: Cloud Architecture & DevOps", "topic": "Architecture", "lvl": "B2", "colloc": "system scalability; high scalability", "syn": "extensibility; capacity"},
            {"word": "vulnerability", "pronunciation": "/ˌvʌl.nər.əˈbɪl.ə.ti/", "pos": "noun", "meaning": "lỗ hổng bảo mật", "en": "The security audit detected a critical software vulnerability.", "vi": "Cuộc kiểm tra bảo mật đã phát hiện một lỗ hổng phần mềm nghiêm trọng.", "sub": "it_tech", "unit": "Unit 3: Cybersecurity", "topic": "Security", "lvl": "B2", "colloc": "security vulnerability; zero-day vulnerability", "syn": "flaw; security hole; weakness"},

            # Business & Finance
            {"word": "liquidity", "pronunciation": "/lɪˈkwɪd.ə.ti/", "pos": "noun", "meaning": "tính thanh khoản (tiền mặt sẵn có)", "en": "Commercial banks must maintain sufficient liquidity at all times.", "vi": "Các ngân hàng thương mại phải luôn duy trì đủ tính thanh khoản.", "sub": "business_finance", "unit": "Unit 1: Banking & Asset Management", "topic": "Banking", "lvl": "B2", "colloc": "market liquidity; high liquidity", "syn": "cash flow; solvency"},
            {"word": "dividend", "pronunciation": "/ˈdɪv.ɪ.dend/", "pos": "noun", "meaning": "cổ tức (lợi nhuận chia cho cổ đông)", "en": "The company announced an annual dividend payout of $2 per share.", "vi": "Công ty thông báo chi trả cổ tức hàng năm 2 đô la cho mỗi cổ phiếu.", "sub": "business_finance", "unit": "Unit 2: Stock Market & Equity", "topic": "Investment", "lvl": "B2", "colloc": "pay a dividend; quarterly dividend", "syn": "yield; payout; return"},

            # Medical
            {"word": "diagnosis", "pronunciation": "/ˌdaɪ.əɡˈnəʊ.sɪs/", "pos": "noun", "meaning": "sự chẩn đoán bệnh", "en": "Early diagnosis is crucial for successful cancer treatment.", "vi": "Chẩn đoán sớm có vai trò quyết định đối với việc điều trị ung thư thành công.", "sub": "medical", "unit": "Unit 1: Clinical Practice & Diagnosis", "topic": "Clinical", "lvl": "B2", "colloc": "medical diagnosis; early diagnosis", "syn": "identification; assessment"},
            {"word": "prescription", "pronunciation": "/prɪˈskrɪp.ʃən/", "pos": "noun", "meaning": "đơn thuốc, toa thuốc", "en": "You need a valid doctor's prescription to buy antibiotics.", "vi": "Bạn cần có đơn thuốc hợp lệ của bác sĩ để mua kháng sinh.", "sub": "medical", "unit": "Unit 2: Pharmacy & Therapeutics", "topic": "Pharmacy", "lvl": "B1", "colloc": "write a prescription; fill a prescription", "syn": "doctor's order; medication script"},

            # Hospitality
            {"word": "concierge", "pronunciation": "/kɒn.siˈeəʒ/", "pos": "noun", "meaning": "nhân viên hỗ trợ khách sạn", "en": "The hotel concierge booked premium theater tickets for us.", "vi": "Nhân viên hỗ trợ khách sạn đã đặt vé xem kịch hạng sang cho chúng tôi.", "sub": "hospitality", "unit": "Unit 1: Hotel Front Desk & Guest Services", "topic": "Hotel", "lvl": "B1", "colloc": "ask the concierge; concierge service", "syn": "guest attendant; information officer"},
            {"word": "complimentary", "pronunciation": "/ˌkɒm.plɪˈmen.tər.i/", "pos": "adjective", "meaning": "miễn phí kèm theo (dịch vụ khách sạn)", "en": "Guests receive a complimentary breakfast buffet each morning.", "vi": "Khách được phục vụ tiệc buffet sáng miễn phí mỗi sáng.", "sub": "hospitality", "unit": "Unit 1: Hotel Front Desk & Guest Services", "topic": "Hotel Services", "lvl": "B1", "colloc": "complimentary breakfast; complimentary drinks", "syn": "free of charge; courtesy"},

            # Marketing
            {"word": "demographic", "pronunciation": "/ˌdem.əˈɡræf.ɪk/", "pos": "noun", "meaning": "nhân khẩu học (nhóm khách hàng mục tiêu)", "en": "The ad campaign successfully targeted the 18-25 demographic.", "vi": "Chiến dịch quảng cáo đã nhắm mục tiêu thành công vào nhóm nhân khẩu học từ 18-25 tuổi.", "sub": "marketing", "unit": "Unit 1: Market Research & Audience", "topic": "Marketing Strategy", "lvl": "B2", "colloc": "target demographic; key demographic", "syn": "target audience; consumer group"},

            # Engineering
            {"word": "blueprint", "pronunciation": "/ˈbluː.prɪnt/", "pos": "noun", "meaning": "bản thiết kế kỹ thuật, bản vẽ chi tiết", "en": "The civil engineer reviewed the architectural blueprints carefully.", "vi": "Kỹ sư xây dựng đã xem xét kỹ lưỡng các bản vẽ kỹ thuật kiến trúc.", "sub": "engineering", "unit": "Unit 1: Technical Design & Drawings", "topic": "Architecture", "lvl": "B2", "colloc": "architectural blueprint; design blueprint", "syn": "schematic; technical drawing; diagram"},
        ]

        for item in esp_data:
            new_vocab_items.append(Vocabulary(
                word=item["word"],
                pronunciation=item["pronunciation"],
                part_of_speech=item["pos"],
                meaning_vi=item["meaning"],
                example_en=item["en"],
                example_vi=item["vi"],
                category="specialized",
                subcategory=item["sub"],
                lesson_unit=item["unit"],
                topic=item["topic"],
                level=item["lvl"],
                collocations=item.get("colloc"),
                synonyms=item.get("syn"),
                antonyms=item.get("ant"),
            ))

        # 5. SEED TOPIC (Daily Life Topics)
        topic_data = [
            # Travel & Transport
            {"word": "boarding pass", "pronunciation": "/ˈbɔː.dɪŋ ˌpɑːs/", "pos": "noun", "meaning": "thẻ lên máy bay", "en": "Please show your passport and boarding pass at the gate.", "vi": "Vui lòng xuất trình hộ chiếu và thẻ lên máy bay tại cửa khởi hành.", "sub": "travel", "unit": "Unit 1: Airport & Flights", "topic": "Airport", "lvl": "A2", "colloc": "print boarding pass; digital boarding pass", "syn": "flight ticket"},
            {"word": "itinerary", "pronunciation": "/aɪˈtɪn.ər.ər.i/", "pos": "noun", "meaning": "lịch trình chuyến đi chi tiết", "en": "We planned a 5-day sightseeing itinerary in Japan.", "vi": "Chúng tôi đã lên lịch trình tham quan chi tiết 5 ngày ở Nhật Bản.", "sub": "travel", "unit": "Unit 2: Sightseeing & Planning", "topic": "Vacation", "lvl": "B1", "colloc": "travel itinerary; detailed itinerary", "syn": "travel plan; schedule; route"},

            # Food & Dining
            {"word": "appetizer", "pronunciation": "/ˈæp.ə.taɪ.zər/", "pos": "noun", "meaning": "món khai vị", "en": "We ordered garlic bread and soup as an appetizer.", "vi": "Chúng tôi đã gọi bánh mì bơ tỏi và súp làm món khai vị.", "sub": "food_dining", "unit": "Unit 1: Restaurant & Menus", "topic": "Dining Out", "lvl": "A2", "colloc": "serve an appetizer; appetizer platter", "syn": "starter; first course"},
            {"word": "ingredient", "pronunciation": "/ɪnˈɡriː.di.ənt/", "pos": "noun", "meaning": "nguyên liệu nấu ăn, thành phần", "en": "Fresh organic herbs are key ingredients in this dish.", "vi": "Các loại rau thơm hữu cơ tươi là nguyên liệu chủ chốt trong món ăn này.", "sub": "food_dining", "unit": "Unit 2: Home Cooking & Recipes", "topic": "Cooking", "lvl": "A2", "colloc": "fresh ingredient; key ingredient", "syn": "component; element"},

            # Relationships
            {"word": "acquaintance", "pronunciation": "/əˈkweɪn.təns/", "pos": "noun", "meaning": "người quen (chưa thân thiết)", "en": "He is not a close friend, just a business acquaintance.", "vi": "Anh ấy không phải là bạn thân, chỉ là một người quen trong công việc.", "sub": "relationships", "unit": "Unit 1: Friends & Social Circle", "topic": "Social Relations", "lvl": "B1", "colloc": "casual acquaintance; make one's acquaintance", "syn": "contact; associate"},

            # Environment
            {"word": "biodiversity", "pronunciation": "/ˌbaɪ.əʊ.daɪˈvɜː.sə.ti/", "pos": "noun", "meaning": "sự đa dạng sinh học", "en": "The Amazon rainforest is famous for its rich biodiversity.", "vi": "Rừng mưa nhiệt đới Amazon nổi tiếng với sự đa dạng sinh học phong phú.", "sub": "environment", "unit": "Unit 1: Nature Conservation", "topic": "Ecology", "lvl": "B1", "colloc": "preserve biodiversity; rich biodiversity", "syn": "ecological diversity"},

            # Media & Tech
            {"word": "algorithm", "pronunciation": "/ˈæl.ɡə.rɪ.ðəm/", "pos": "noun", "meaning": "thuật toán gợi ý nội dung", "en": "The social network uses an algorithm to personalize video feeds.", "vi": "Mạng xã hội sử dụng thuật toán để cá nhân hóa luồng video.", "sub": "media_tech", "unit": "Unit 1: Digital Media & Trends", "topic": "Social Media", "lvl": "B1", "colloc": "search algorithm; feed algorithm", "syn": "formula; computational procedure"},
        ]

        for item in topic_data:
            new_vocab_items.append(Vocabulary(
                word=item["word"],
                pronunciation=item["pronunciation"],
                part_of_speech=item["pos"],
                meaning_vi=item["meaning"],
                example_en=item["en"],
                example_vi=item["vi"],
                category="topic",
                subcategory=item["sub"],
                lesson_unit=item["unit"],
                topic=item["topic"],
                level=item["lvl"],
                collocations=item.get("colloc"),
                synonyms=item.get("syn"),
                antonyms=item.get("ant"),
            ))

        print(f"Adding total of {len(new_vocab_items)} structured vocabulary items into Database...")
        db.session.add_all(new_vocab_items)
        db.session.commit()
        print(f"✅ Successfully seeded {Vocabulary.query.count()} words across all 5 major categories!")

if __name__ == "__main__":
    run_seed()
