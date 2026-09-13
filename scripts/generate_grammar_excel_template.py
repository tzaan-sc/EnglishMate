import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "app" / "static" / "templates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FILE_PATH = OUTPUT_DIR / "mau_import_12_danh_muc_ngu_phap.xlsx"


def create_template():
    wb = openpyxl.Workbook()

    # -------------------------------------------------------------
    # Sheet 1: Du_Lieu_Ngu_Phap (Main Data Sheet)
    # -------------------------------------------------------------
    ws = wb.active
    ws.title = "Du_Lieu_Ngu_Phap"

    headers = [
        "category",
        "title",
        "level",
        "difficulty",
        "order_index",
        "exam_targets",
        "toeic_parts",
        "toeic_weight",
        "importance",
        "summary",
        "rule_explanation",
        "examples",
        "common_mistakes",
        "tips_tricks"
    ]

    sample_rows = [
        [
            "Từ loại (Parts of Speech)",
            "Noun – Danh từ trong đề thi TOEIC",
            "A2",
            "Medium",
            1,
            "General English, TOEIC",
            "Part 5, Part 6",
            "High",
            "High",
            "Nhận diện hậu tố danh từ (-tion, -ment, -ness, -ity, -er/or) và các vị trí vàng của danh từ trong câu.",
            "1. Vị trí vàng của Danh từ:\n- Sau mạo từ (a/an/the): the decision, an applicant\n- Sau tính từ sở hữu (my/his/their...): their proposal\n- Làm chủ ngữ (S) đứng đầu câu trước động từ\n- Làm tân ngữ (O) đứng sau ngoại động từ hoặc sau giới từ: interested in management\n\n2. Hậu tố nhận diện danh từ chỉ vật/khái niệm: -tion, -sion, -ment, -ance, -ence, -ity, -ness, -ship.\n3. Hậu tố chỉ người: -er, -or, -ant, -ee (employer / employee).",
            "The company announced a significant expansion.|Công ty đã công bố một sự mở rộng đáng kể.\nApplicants must submit all required documents.|Các ứng viên phải nộp toàn bộ tài liệu được yêu cầu.\nCustomer satisfaction is our top priority.|Sự hài lòng của khách hàng là ưu tiên hàng đầu của chúng tôi.",
            "❌ Chọn nhầm đuôi tính từ (-tive, -al, -able) vào vị trí cần danh từ.\n❌ Nhầm lẫn danh từ chỉ người và danh từ chỉ vật (applicant vs application).",
            "💡 Nếu trước chỗ trống là a/an/the/tính từ và sau chỗ trống là giới từ hoặc động từ, 90% chọn DANH TỪ!"
        ],
        [
            "Thì (Tenses)",
            "Present Simple – Thì Hiện Tại Đơn",
            "A1",
            "Easy",
            1,
            "General English, TOEIC, THPT",
            "Part 5, Part 6, Part 7",
            "High",
            "High",
            "Quy tắc chia thì hiện tại đơn diễn tả thói quen, lịch trình và các chính sách vận hành của doanh nghiệp.",
            "1. Cấu trúc:\n[+] S + V(s/es)\n[-] S + do/does not + V-bare\n[?] Do/Does + S + V-bare?\n\n2. Cách dùng trọng tâm:\n- Diễn tả chính sách, quy định công ty (The policy applies to all staff).\n- Diễn tả lịch trình, giờ tàu xe, hội nghị (The seminar begins at 9 AM).",
            "The regional branch opens at 8:00 AM every weekday.|Chi nhánh khu vực mở cửa lúc 8:00 sáng các ngày trong tuần.\nShe oversees all marketing campaigns.|Cô ấy giám sát toàn bộ các chiến dịch tiếp thị.\nFlights to Tokyo depart twice daily.|Các chuyến bay đến Tokyo khởi hành hai lần mỗi ngày.",
            "❌ Quên chia 's/es' với chủ ngữ số ít ngôi thứ 3 (He, She, It, Danh từ số ít).\n❌ Nhầm 'do/does' với 'is/are'.",
            "💡 Dấu hiệu nhận biết kinh điển: always, usually, regularly, frequently, every quarter, on Mondays."
        ],
        [
            "Thì (Tenses)",
            "Present Perfect – Thì Hiện Tại Hoàn Thành",
            "A2",
            "Medium",
            3,
            "General English, TOEIC, IELTS",
            "Part 5, Part 6",
            "High",
            "High",
            "Diễn tả hành động xảy ra trong quá khứ kéo dài đến hiện tại, các thành tựu và kinh nghiệm làm việc.",
            "1. Cấu trúc:\n[+] S + have/has + V3/ed\n[-] S + have/has not + V3/ed\n[?] Have/Has + S + V3/ed?\n\n2. Cách dùng cốt lõi:\n- Hành động bắt đầu trong quá khứ và vẫn đang tiếp diễn (for 10 years, since 2020).\n- Vừa mới hoàn thành (just, already, recently).\n- Chưa làm xong tính đến nay (not yet, so far).",
            "We have increased our annual revenue by 15%.|Chúng tôi đã tăng doanh thu hàng năm thêm 15%.\nMs. Roberts has worked as a senior auditor since 2018.|Cô Roberts đã làm việc như một kiểm toán viên cấp cao từ năm 2018.\nThe committee has not yet approved the final budget.|Ủy ban vẫn chưa phê duyệt ngân sách cuối cùng.",
            "❌ Dùng mốc thời gian quá khứ xác định (in 2020, yesterday, last week) với thì HTHT (Phải dùng Quá khứ đơn!).\n❌ Nhầm lẫn 'since' (mốc thời gian) và 'for' (khoảng thời gian).",
            "💡 Thấy 'since, for, already, recently, lately, over the past 3 years, so far' -> ƯU TIÊN CHỌN NGAY thì Hiện Tại Hoàn Thành!"
        ],
        [
            "Câu bị động (Passive Voice)",
            "Passive Voice – Câu Bị Động Cốt Lõi",
            "B1",
            "Medium",
            1,
            "General English, TOEIC, IELTS",
            "Part 5, Part 6, Part 7",
            "High",
            "High",
            "Quy tắc chuyển đổi chủ động sang bị động và bẫy phân biệt chủ động/bị động phổ biến nhất Part 5.",
            "1. Cấu trúc tổng quát: S + BE + V3/ed (+ by O)\n- Hiện tại đơn: am/is/are + V3/ed\n- Quá khứ đơn: was/were + V3/ed\n- Hiện tại hoàn thành: have/has been + V3/ed\n- Modal verbs: will/can/must be + V3/ed\n\n2. Dấu hiệu xác định Bị động:\n- Chủ ngữ là vật (báo cáo, hợp đồng, sản phẩm... không tự thực hiện hành động).\n- Động từ là ngoại động từ nhưng PHÍA SAU KHÔNG CÓ TÂN NGỮ (thường đi kèm giới từ: by, to, at, in).",
            "All invoices must be submitted by Friday afternoon.|Tất cả hóa đơn phải được nộp trước chiều thứ Sáu.\nThe construction contract was signed yesterday.|Hợp đồng xây dựng đã được ký kết ngày hôm qua.\nFree refreshments will be provided during the break.|Đồ uống miễn phí sẽ được phục vụ trong giờ giải lao.",
            "❌ Không để ý chủ ngữ là vật mà vội vàng chọn động từ chủ động.\n❌ Nội động từ (arrive, happen, occur, remain...) KHÔNG BAO GIỜ chia bị động!",
            "💡 Mẹo TOEIC 5 giây: Nhìn sau chỗ trống nếu KHÔNG CÓ TÂN NGỮ mà có giới từ (by, in, for...) -> 85% chọn BỊ ĐỘNG (be + V3/ed)!"
        ],
        [
            "Mệnh đề & Liên từ (Clauses & Conjunctions)",
            "Conjunctions vs Prepositions – Liên từ và Giới từ chỉ Lý do & Nhượng bộ",
            "B1",
            "Hard",
            5,
            "General English, TOEIC",
            "Part 5, Part 6",
            "High",
            "High",
            "Bẫy kinh điển phân biệt Liên từ (đi với Mệnh đề S + V) và Giới từ (đi với Cụm danh từ / V-ing).",
            "1. Lý do (Bởi vì):\n- Liên từ (+ Clause: S + V): Because, Since, As, Now that\n- Giới từ (+ Noun phrase / V-ing): Because of, Due to, Owing to, On account of\n\n2. Nhượng bộ (Mặc dù):\n- Liên từ (+ Clause: S + V): Although, Even though, Though, While, Whereas\n- Giới từ (+ Noun phrase / V-ing): In spite of, Despite, Regardless of",
            "Although the weather was severe, the shipment arrived on time.|Mặc dù thời tiết rất khắc nghiệt, lô hàng vẫn đến đúng giờ.\nDespite the severe weather, the shipment arrived on time.|Mặc dù thời tiết khắc nghiệt, lô hàng vẫn đến đúng giờ.\nThe flight was delayed because of mechanical failure.|Chuyến bay đã bị hoãn do sự cố kỹ thuật.",
            "❌ Dùng 'Because of' hoặc 'Despite' đi với một mệnh đề hoàn chỉnh có chủ ngữ và vị ngữ.\n❌ Dùng 'Although' nhưng lại thêm 'but' ở mệnh đề sau (Tiếng Anh chỉ chọn 1 trong 2).",
            "💡 Mẹo vàng Part 5: Nhìn ngay sau chỗ trống! Nếu có ĐỘNG TỪ CHIA THÌ (S+V) -> Chọn Liên từ (Because/Although). Nếu chỉ có Cụm danh từ/V-ing -> Chọn Giới từ (Due to/Despite)!"
        ]
    ]

    # Style definitions
    header_fill = PatternFill(start_color="1E1B4B", end_color="1E1B4B", fill_type="solid") # Deep Indigo
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    # Write sample rows
    for row_idx, row_data in enumerate(sample_rows, 2):
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
                horizontal="center" if headers[col_idx-1] in ["level", "difficulty", "order_index", "toeic_weight", "importance"] else "left"
            )
        ws.row_dimensions[row_idx].height = 65

    # Auto column width
    col_widths = {
        "category": 28,
        "title": 36,
        "level": 10,
        "difficulty": 14,
        "order_index": 12,
        "exam_targets": 26,
        "toeic_parts": 18,
        "toeic_weight": 14,
        "importance": 14,
        "summary": 45,
        "rule_explanation": 55,
        "examples": 55,
        "common_mistakes": 45,
        "tips_tricks": 45,
    }
    for col_idx, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = col_widths.get(header, 20)

    # -------------------------------------------------------------
    # Sheet 2: Danh_Muc_Va_Huong_Dan (12 Categories Reference)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Huong_Dan_12_Danh_Muc")

    ws2.cell(row=1, column=1, value="DANH SÁCH 12 DANH MỤC NGỮ PHÁP CHUẨN VÀ CÁC CHỦ ĐIỂM CON KHUYÊN DÙNG").font = Font(name="Segoe UI", size=13, bold=True, color="1E1B4B")
    ws2.row_dimensions[1].height = 30

    guide_headers = ["STT", "Tên Danh Mục Lớn (Category)", "Chủ Điểm Con Gợi Ý (Topics)", "Trọng Tâm TOEIC"]
    for col_num, gh in enumerate(guide_headers, 1):
        cell = ws2.cell(row=3, column=col_num, value=gh)
        cell.fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid") # Emerald
        cell.font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws2.row_dimensions[3].height = 26

    categories_guide = [
        ("1", "Từ loại (Parts of Speech)", "Noun, Pronoun, Verb, Adjective, Adverb, Preposition, Conjunction, Determiner", "High (Part 5 chiếm 30%)"),
        ("2", "Cấu trúc câu (Sentence Structure)", "S + V, S + V + O, S + V + C, S + V + O + O, S + V + O + C, Câu đơn, ghép, phức", "Medium"),
        ("3", "Thì (Tenses)", "12 thì tiếng Anh (Đặc biệt: Hiện tại đơn, Tiếp diễn, Hoàn thành, Quá khứ đơn, Tương lai đơn)", "High (Part 5 & 6)"),
        ("4", "Động từ (Verbs)", "Động từ thường / to be, Transitive/Intransitive, Linking verbs, Modal verbs, Phrasal verbs, Gerund, Infinitive", "High (Gerund & Infinitive rất hay ra)"),
        ("5", "Danh từ & Mạo từ (Nouns & Articles)", "Countable/Uncountable, Singular/Plural, a/an/the, Zero article, Quantifiers (much, many, few...)", "High"),
        ("6", "Đại từ & Từ hạn định (Pronouns & Determiners)", "Personal, Possessive, Reflexive, Demonstratives, Indefinite (each, every, some, any, no)", "High (Đại từ phản thân và từ hạn định)"),
        ("7", "Tính từ & Trạng từ (Adjectives & Adverbs)", "Vị trí tính từ, Vị trí trạng từ, So sánh bằng, hơn, nhất (Comparative, Superlative), too/enough, so/such", "High (So sánh và vị trí trạng từ)"),
        ("8", "Giới từ (Prepositions)", "Prepositions of time, place, direction, sau động từ, sau tính từ, Cụm giới từ cố định", "High (Cụm giới từ cố định Part 5)"),
        ("9", "Câu bị động (Passive Voice)", "Passive cơ bản, Passive theo thì, Modal + Passive, Passive 2 tân ngữ, Get passive, Causative have/get done", "High (Trọng tâm lớn Part 5 & 6)"),
        ("10", "Mệnh đề & Liên từ (Clauses & Conjunctions)", "Relative clauses, Noun clauses, Adverb clauses, Defining/Non-defining, Liên từ nhượng bộ/lý do/điều kiện", "High (Mệnh đề quan hệ rút gọn)"),
        ("11", "Cấu trúc câu nâng cao (Advanced Structures)", "Conditional (If 1, 2, 3, hỗn hợp), Wish/If only, Reported speech, Inversion (Đảo ngữ), Cleft sentences, Subjunctive", "Medium - High (Đảo ngữ câu điều kiện)"),
        ("12", "Cấu trúc đặc biệt & Ngữ pháp ứng dụng", "Question forms, Tag questions, Imperatives, Used to / Be used to, Would rather, Both/Either/Neither, Not only...but also", "Medium - High")
    ]

    for r_idx, r_val in enumerate(categories_guide, 4):
        for c_idx, val in enumerate(r_val, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", horizontal="center" if c_idx in [1, 4] else "left", wrap_text=True)
        ws2.row_dimensions[r_idx].height = 32

    ws2.column_dimensions["A"].width = 8
    ws2.column_dimensions["B"].width = 38
    ws2.column_dimensions["C"].width = 65
    ws2.column_dimensions["D"].width = 30

    wb.save(str(FILE_PATH))
    print(f"[OK] Đã tạo thành công file Excel mẫu tại: {FILE_PATH}")


if __name__ == "__main__":
    create_template()
