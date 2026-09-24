# 🗄️ Hướng Dẫn Đồng Bộ Dữ Liệu PostgreSQL ↔ SQLite

## Hiểu rõ trước khi làm

```
PostgreSQL (instance chính)          SQLite (dự phòng / test local)
  └── englishmate DB (server)    ≠     └── instance/englishmate.db (file)
```

**Hai DB này HOÀN TOÀN ĐỘC LẬP.** Không có đồng bộ tự động.
Chỉ có **cơ chế fallback** khi khởi động app: nếu PostgreSQL không kết nối được → app tự chuyển sang SQLite.

---

## Trường hợp 1: Muốn SQLite có cùng data mẫu như PostgreSQL

> Tình huống: PostgreSQL đang có data, bạn muốn test offline với SQLite.

```powershell
# Bước 1: Mở file .env, comment out dòng DATABASE_URL
#   Trước:  DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
#   Sau:    # DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate

# Bước 2: Chạy seed để nạp data mẫu vào SQLite
python -m app.seed
python -m app.seed_toeic

# Bước 3: Bỏ comment dòng postgresql trong .env để dùng lại PostgreSQL
#   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
```

> ⚠️ Đây là **data mẫu cứng** (hardcode trong seed.py), không phải copy từ PostgreSQL sang.
> Nếu PostgreSQL đã có data thực (do user nhập), cách này **không copy** data thực đó sang SQLite.

---

## Trường hợp 2: Muốn copy data thực từ PostgreSQL → SQLite

> Tình huống: PostgreSQL đã có nhiều từ vựng/câu hỏi thật do người dùng nhập, muốn backup/test bằng SQLite.

```powershell
# Bước 1: Export data từ PostgreSQL ra file CSV (dùng pgAdmin hoặc lệnh psql)
# Cách A: Dùng pgAdmin → chuột phải vào bảng → "Export/Import" → chọn CSV
# Cách B: Dùng lệnh psql
psql -U postgres -p 5433 -d englishmate -c "\copy vocabulary TO 'vocab_backup.csv' CSV HEADER"
psql -U postgres -p 5433 -d englishmate -c "\copy question TO 'questions_backup.csv' CSV HEADER"

# Bước 2: Comment out DATABASE_URL trong .env (để app dùng SQLite)
#   # DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate

# Bước 3: Seed cấu trúc bảng vào SQLite trước
python -m app.seed

# Bước 4: Vào Admin web → /admin/import → Upload file CSV vừa export
# (hoặc dùng script import nếu có)

# Bước 5: Bỏ comment DATABASE_URL để dùng lại PostgreSQL
#   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
```

---

## Trường hợp 3: Muốn copy data từ SQLite → PostgreSQL

> Tình huống: Đã test và nhập data ở SQLite local, muốn đưa lên PostgreSQL.

```powershell
# Bước 1: Export từ SQLite ra CSV
# Dùng DB Browser for SQLite: File → Export → Table as CSV
# Hoặc dùng Python:
python -c "
import sqlite3, csv
conn = sqlite3.connect('instance/englishmate.db')
for table in ['vocabulary', 'question', 'lesson']:
    rows = conn.execute(f'SELECT * FROM {table}').fetchall()
    cols = [d[0] for d in conn.execute(f'SELECT * FROM {table}').description]
    with open(f'{table}_from_sqlite.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f'Exported {len(rows)} rows from {table}')
conn.close()
"

# Bước 2: Bảo đảm DATABASE_URL trong .env trỏ đúng PostgreSQL
#   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate

# Bước 3: Vào Admin web → /admin/import → Upload các file CSV vừa export
```

---

## Trường hợp 4: Switch nhanh giữa PostgreSQL và SQLite để test

> Tình huống: Muốn chạy thử app với từng DB mà không sửa .env thủ công.

Tạo file `.env.postgresql` và `.env.sqlite` riêng:

**`.env.postgresql`:**
```
DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
SECRET_KEY=dev-only-secret-key-12345
```

**`.env.sqlite`:**
```
# Không có DATABASE_URL → app tự dùng SQLite
SECRET_KEY=dev-only-secret-key-12345
```

Sau đó switch bằng lệnh:
```powershell
# Dùng PostgreSQL
Copy-Item .env.postgresql .env

# Dùng SQLite
Copy-Item .env.sqlite .env

# Rồi restart app
python run.py
```

---

## Tóm tắt nhanh

| Muốn làm gì | Làm thế nào |
|---|---|
| SQLite có data mẫu (users, từ vựng cơ bản) | Comment `DATABASE_URL` → `python -m app.seed` |
| Copy data thực từ PostgreSQL sang SQLite | Export CSV từ pgAdmin → Import vào SQLite qua Admin web |
| Copy data từ SQLite sang PostgreSQL | Export CSV từ SQLite → Import vào PostgreSQL qua Admin web |
| Switch nhanh giữa 2 DB | Tạo 2 file `.env.postgresql` / `.env.sqlite`, dùng `Copy-Item` để switch |
| Xem data SQLite | Cài **DB Browser for SQLite** hoặc extension **SQLite Viewer** (VS Code) mở file `instance/englishmate.db` |

---

> **Lời khuyên:** Trong môi trường **development**, dùng SQLite cho tiện (không cần PostgreSQL chạy).
> Khi **deploy production**, dùng PostgreSQL. Dùng `python -m app.seed` để có data mẫu ở cả 2 môi trường.
