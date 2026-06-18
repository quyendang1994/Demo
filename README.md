# News Facebook Bot

Bot tự động lấy tin tức từ RSS, tạo ảnh 1080x1080 và đăng lên Facebook Page theo lịch cố định.

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Yêu cầu hệ thống](#2-yêu-cầu-hệ-thống)
3. [Cài đặt](#3-cài-đặt)
4. [Cấu hình](#4-cấu-hình)
5. [Lấy Facebook Access Token](#5-lấy-facebook-access-token)
6. [Cách sử dụng](#6-cách-sử-dụng)
7. [Kiến trúc project](#7-kiến-trúc-project)
8. [Nguồn RSS](#8-nguồn-rss)
9. [Tùy chỉnh](#9-tùy-chỉnh)
10. [Xem log](#10-xem-log)
11. [Xử lý lỗi thường gặp](#11-xử-lý-lỗi-thường-gặp)
12. [Chạy 24/7 trên server](#12-chạy-247-trên-server)

---

## 1. Tổng quan

Bot hoạt động theo quy trình sau:

```
RSS Feeds → Lấy tin → Lọc trùng → Tạo ảnh 1080x1080 → Đăng Facebook
```

**Tính năng:**
- Lấy tin từ 5 nguồn báo lớn tại Việt Nam (VnExpress, Tuổi Trẻ, Thanh Niên, BBC Tiếng Việt, Dân Trí)
- Tự động tạo ảnh đẹp với nền gradient, hình thumbnail, số thứ tự
- Đăng lên Facebook Page kèm caption tiếng Việt và hashtag
- Không đăng lại bài cũ (theo dõi bằng file `post_log.json`)
- Tự động retry khi mạng lỗi (tối đa 3 lần)
- Lưu log chi tiết, xoay vòng file khi đầy

---

## 2. Yêu cầu hệ thống

| Yêu cầu | Phiên bản tối thiểu |
|---|---|
| Python | 3.8 trở lên |
| Hệ điều hành | Windows 10/11, macOS, Linux |
| Kết nối internet | Bắt buộc |
| Facebook Page | Phải là admin của Page |

Kiểm tra phiên bản Python:

```powershell
python --version
```

---

## 3. Cài đặt

### Bước 1 — Clone hoặc tải source code

```powershell
git clone https://github.com/quyendang1994/Demo.git
cd Demo
```

Hoặc tải thư mục `Demo_FC` về máy và mở PowerShell tại đó.

### Bước 2 — Tạo virtual environment (khuyến nghị)

```powershell
python -m venv venv
venv\Scripts\activate
```

> Sau khi kích hoạt, terminal sẽ hiện `(venv)` ở đầu dòng.

### Bước 3 — Cài thư viện

```powershell
pip install -r requirements.txt
```

Thư viện sẽ được cài:

| Thư viện | Dùng để |
|---|---|
| `Pillow >= 10.0.0` | Tạo và render ảnh 1080x1080 |
| `requests >= 2.28.0` | Gọi Facebook Graph API, tải ảnh thumbnail |
| `python-dotenv >= 1.0.0` | Đọc file cấu hình `.env` |

### Bước 4 — Tạo file cấu hình

```powershell
copy .env.example .env
```

Sau đó mở file `.env` và điền thông tin thực tế (xem phần [Cấu hình](#4-cấu-hình)).

---

## 4. Cấu hình

Mở file `.env` và chỉnh sửa các giá trị sau:

```env
# === FACEBOOK ===
FB_PAGE_ID=61591105822943
FB_ACCESS_TOKEN=EAAxxxxxxxx...
FB_API_VERSION=v19.0

# === LỊCH ĐĂNG BÀI ===
SCHEDULE_TIMES=07:00,12:00,18:00

# === LẤY TIN TỨC ===
MAX_ITEMS_PER_SOURCE=10
TOTAL_CARDS_ON_IMAGE=5
REQUEST_TIMEOUT=10

# === GIAO DIỆN ===
BRAND_NAME=Tin Tức Hôm Nay

# === THƯ MỤC ===
OUTPUT_DIR=output
LOG_DIR=logs
POST_LOG_PATH=output/post_log.json
FONT_DIR=assets/fonts
```

### Giải thích từng biến

| Biến | Bắt buộc | Mô tả |
|---|---|---|
| `FB_PAGE_ID` | Có | ID của Facebook Page cần đăng bài |
| `FB_ACCESS_TOKEN` | Có | Page Access Token (xem hướng dẫn bên dưới) |
| `FB_API_VERSION` | Không | Phiên bản Facebook API, mặc định `v19.0` |
| `SCHEDULE_TIMES` | Không | Giờ đăng bài, định dạng `HH:MM`, phân cách bằng dấu phẩy. Mặc định `07:00,12:00,18:00` |
| `MAX_ITEMS_PER_SOURCE` | Không | Số tin tối đa lấy từ mỗi nguồn RSS. Mặc định `10` |
| `TOTAL_CARDS_ON_IMAGE` | Không | Số tin hiển thị trên ảnh (tối đa 5). Mặc định `5` |
| `REQUEST_TIMEOUT` | Không | Thời gian chờ tối đa khi gọi HTTP (giây). Mặc định `10` |
| `BRAND_NAME` | Không | Tên thương hiệu hiển thị trên ảnh. Mặc định `Tin Tức Hôm Nay` |
| `OUTPUT_DIR` | Không | Thư mục lưu ảnh đã tạo. Mặc định `output/` |
| `LOG_DIR` | Không | Thư mục lưu file log. Mặc định `logs/` |
| `POST_LOG_PATH` | Không | File theo dõi bài đã đăng. Mặc định `output/post_log.json` |
| `FONT_DIR` | Không | Thư mục chứa font chữ tùy chỉnh. Mặc định `assets/fonts/` |

---

## 5. Lấy Facebook Access Token

### Bước 1 — Tạo ứng dụng Facebook

1. Truy cập [Facebook Developers](https://developers.facebook.com/)
2. Vào **My Apps** → **Create App**
3. Chọn loại **Business** → Đặt tên app → **Create App**

### Bước 2 — Thêm tính năng Pages

1. Trong app vừa tạo, vào **Add Products**
2. Tìm **Facebook Login** → **Set Up**
3. Vào **Settings** → **Basic**, ghi lại `App ID` và `App Secret`

### Bước 3 — Lấy Page Access Token

1. Truy cập [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Chọn app của bạn ở góc phải
3. Click **Generate Access Token**
4. Chọn Page cần đăng bài
5. Tick chọn 2 quyền:
   - `pages_manage_posts`
   - `pages_read_engagement`
6. Click **Generate Token** → Copy token

### Bước 4 — Lấy Page ID

1. Vào trang Facebook Page của bạn
2. Click **About** (Giới thiệu)
3. Kéo xuống cuối, tìm mục **Page ID**

Hoặc dùng Graph API Explorer:
```
GET /me/accounts
```
Kết quả trả về danh sách Pages kèm `id` (Page ID) và `access_token`.

### Lưu ý về token

- Token từ Graph API Explorer chỉ có hiệu lực **1–2 giờ**
- Để dùng lâu dài, cần đổi sang **Long-Lived Token** (có hiệu lực 60 ngày):

```
GET https://graph.facebook.com/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id={APP_ID}
  &client_secret={APP_SECRET}
  &fb_exchange_token={SHORT_LIVED_TOKEN}
```

---

## 6. Cách sử dụng

### Kiểm tra cấu hình trước khi chạy

```powershell
python main.py --check
```

Lệnh này sẽ:
- Kiểm tra `FB_PAGE_ID` và `FB_ACCESS_TOKEN` có được điền chưa
- Gọi Facebook API để xác minh token còn hợp lệ không
- In ra tên Page nếu thành công

Kết quả thành công:
```
[INFO] Kiểm tra cấu hình...
[INFO] Cấu hình hợp lệ.
[INFO] Token hợp lệ. Page: Tin Tức Hôm Nay (id=61591105822943)
```

---

### Chỉ tạo ảnh (không đăng Facebook)

```powershell
python main.py --image
```

Dùng để:
- Kiểm tra giao diện ảnh trước khi đăng thật
- Không cần cấu hình Facebook
- Ảnh được lưu vào `output/news_YYYYMMDD_HHMMSS.jpg`

---

### Chạy ngay một lần (test đầy đủ)

```powershell
python main.py --now
```

Thực hiện toàn bộ pipeline ngay lập tức:
1. Lấy tin từ RSS
2. Tạo ảnh
3. Đăng lên Facebook
4. Lưu log bài đã đăng

Dùng để test trước khi bật chế độ tự động.

---

### Chạy tự động theo lịch (24/7)

```powershell
python main.py
```

Bot sẽ:
- Chạy liên tục, không tắt
- Tự động đăng bài theo giờ trong `SCHEDULE_TIMES` (mặc định: 7h, 12h, 18h)
- In ra thời gian chờ đến lần đăng tiếp theo

```
[INFO] Khởi động News Facebook Bot
[INFO] Brand: Tin Tức Hôm Nay
[INFO] Lịch đăng: 07:00, 12:00, 18:00
[INFO] Nguồn RSS: 5 nguồn
[INFO] Bot đang chạy. Nhấn Ctrl+C để dừng.
[INFO] Lần chạy tiếp theo lúc 12:00 sau 43.2 phút
```

Dừng bot: nhấn `Ctrl + C`

---

### Tóm tắt các lệnh

| Lệnh | Tác dụng | Cần FB Token? |
|---|---|---|
| `python main.py --check` | Kiểm tra cấu hình + token | Có |
| `python main.py --image` | Chỉ tạo ảnh, không đăng | Không |
| `python main.py --now` | Chạy pipeline một lần ngay | Có |
| `python main.py` | Chạy scheduler 24/7 | Có |

---

## 7. Kiến trúc project

```
Demo_FC/
├── main.py                  # Điểm vào chính, xử lý CLI args
├── config.py                # Đọc cấu hình từ .env
├── models.py                # Data models (NewsItem, PostResult)
├── requirements.txt         # Danh sách thư viện
├── .env                     # Cấu hình thực tế (không commit lên git)
├── .env.example             # Mẫu cấu hình
│
├── fetcher/                 # Lấy tin từ RSS
│   ├── sources.py           # Danh sách nguồn RSS
│   └── rss_client.py        # Parse XML, dedup, retry
│
├── renderer/                # Tạo ảnh
│   ├── layout.py            # Kích thước, màu sắc, font size
│   ├── components.py        # Vẽ header, card, footer
│   └── image_builder.py     # Orchestrate toàn bộ quá trình render
│
├── poster/                  # Đăng lên Facebook
│   └── facebook.py          # Gọi Graph API, tạo caption
│
├── scheduler/               # Lập lịch
│   └── timer.py             # DailyScheduler dùng threading.Timer
│
├── utils/                   # Tiện ích
│   ├── retry.py             # Decorator retry với exponential backoff
│   ├── text_utils.py        # Strip HTML, wrap text, format ngày giờ
│   └── post_log.py          # Lưu/đọc danh sách bài đã đăng
│
├── assets/
│   └── fonts/               # Font tùy chỉnh (NotoSans-Bold.ttf, NotoSans-Regular.ttf)
│
├── output/                  # Ảnh đã tạo + post_log.json (tự sinh)
└── logs/                    # File log (tự sinh)
```

### Luồng dữ liệu

```
main.py
  └── run_pipeline()
        ├── fetch_all_sources()      → [NewsItem, ...]
        │     └── RSSClient.fetch()  → parse XML từng nguồn
        │
        ├── PostLog.is_posted()      → lọc bài đã đăng
        │
        ├── ImageBuilder.build()     → tạo ảnh JPG 1080x1080
        │     ├── draw_gradient_background()
        │     ├── draw_header()
        │     ├── draw_news_card() × 5
        │     └── draw_footer()
        │
        └── FacebookPoster.post_photo()  → gọi Graph API
              └── PostLog.mark_posted()  → lưu link đã đăng
```

---

## 8. Nguồn RSS

Bot lấy tin từ 5 nguồn mặc định trong `fetcher/sources.py`:

| Nguồn | RSS URL |
|---|---|
| VnExpress | `https://vnexpress.net/rss/tin-moi-nhat.rss` |
| Tuổi Trẻ | `https://tuoitre.vn/rss/tin-moi-nhat.rss` |
| Thanh Niên | `https://thanhnien.vn/rss/home.rss` |
| BBC Tiếng Việt | `https://feeds.bbci.co.uk/vietnamese/rss.xml` |
| Dân Trí | `https://dantri.com.vn/rss/home.rss` |

### Thêm/bỏ nguồn RSS

Mở `fetcher/sources.py`:

```python
SOURCES: list = [
    RSSSource("VnExpress",   "https://vnexpress.net/rss/tin-moi-nhat.rss", "enclosure"),
    RSSSource("Tuổi Trẻ",   "https://tuoitre.vn/rss/tin-moi-nhat.rss",    "enclosure"),
    # Tắt một nguồn:
    RSSSource("Thanh Niên", "https://thanhnien.vn/rss/home.rss",           "enclosure", enabled=False),
    # Thêm nguồn mới:
    RSSSource("VTV",        "https://vtv.vn/trong-nuoc.rss",               "enclosure"),
]
```

Tham số `image_field`:
- `"enclosure"` — dùng cho hầu hết báo Việt Nam
- `"media_thumbnail"` — dùng cho BBC, một số feed quốc tế
- `None` — không lấy ảnh thumbnail

---

## 9. Tùy chỉnh

### Đổi màu sắc giao diện

Mở `renderer/layout.py`, chỉnh các giá trị màu (định dạng RGB hoặc RGBA):

```python
bg_top: tuple = (13, 27, 42)        # Màu nền trên cùng (navy đậm)
bg_bottom: tuple = (22, 22, 58)     # Màu nền dưới cùng (indigo đậm)
accent: tuple = (0, 168, 232)       # Màu nhấn (cyan)
text_title: tuple = (255, 255, 255) # Màu chữ tiêu đề (trắng)
text_body: tuple = (185, 200, 215)  # Màu chữ mô tả (xám sáng)
text_source: tuple = (0, 210, 255)  # Màu tên nguồn báo (xanh nhạt)
```

### Đổi font chữ

Bot tự động tìm font theo thứ tự ưu tiên:
1. Font hệ thống Windows: Segoe UI → Calibri → Arial
2. Font trong `assets/fonts/`: `NotoSans-Bold.ttf` + `NotoSans-Regular.ttf`
3. Font mặc định của PIL (không hiển thị tiếng Việt tốt)

Để dùng font tùy chỉnh, đặt 2 file vào `assets/fonts/`:
- `NotoSans-Bold.ttf`
- `NotoSans-Regular.ttf`

Tải font Noto Sans tại: https://fonts.google.com/noto/specimen/Noto+Sans

### Đổi số lượng tin trên ảnh

Trong `.env`:
```env
TOTAL_CARDS_ON_IMAGE=3   # Hiển thị 3 tin thay vì 5
```

### Đổi lịch đăng bài

Trong `.env`:
```env
SCHEDULE_TIMES=06:00,11:00,17:00,21:00   # Đăng 4 lần/ngày
```

---

## 10. Xem log

### Log trên terminal

Khi bot đang chạy, log hiển thị trực tiếp với các mức:
- `[INFO]` — hoạt động bình thường
- `[WARNING]` — cảnh báo (ví dụ: không có tin mới)
- `[ERROR]` — lỗi cần chú ý

### Log file

File log được lưu tại `logs/bot.log`, tự động xoay vòng khi đạt 5MB (giữ 3 bản backup).

Xem log thời gian thực:

```powershell
Get-Content logs\bot.log -Wait -Tail 50
```

### File post_log.json

File `output/post_log.json` lưu danh sách link bài đã đăng:

```json
{
  "posted_links": [
    "https://vnexpress.net/...",
    "https://tuoitre.vn/..."
  ],
  "last_posted_at": "2026-06-18T07:00:12.345678",
  "total_posts": 42
}
```

Xóa file này nếu muốn bot đăng lại các bài cũ.

---

## 11. Xử lý lỗi thường gặp

### Lỗi: `Thiếu cấu hình bắt buộc: FB_PAGE_ID`

**Nguyên nhân:** Chưa tạo file `.env` hoặc chưa điền giá trị.

**Cách sửa:**
```powershell
copy .env.example .env
# Mở .env và điền FB_PAGE_ID, FB_ACCESS_TOKEN
```

---

### Lỗi: `Token không hợp lệ: 401`

**Nguyên nhân:** Token đã hết hạn (token ngắn hạn chỉ dùng được 1–2 giờ).

**Cách sửa:** Lấy lại token mới từ Graph API Explorer hoặc đổi sang Long-Lived Token.

---

### Lỗi: `Không lấy được tin tức nào`

**Nguyên nhân:** Mất kết nối internet hoặc tất cả nguồn RSS bị lỗi.

**Cách kiểm tra:**
```powershell
python main.py --image   # Nếu lỗi ở bước fetch thì do mạng
```

---

### Lỗi: Ảnh hiện ký tự lạ thay vì tiếng Việt

**Nguyên nhân:** Không tìm thấy font TrueType hỗ trợ tiếng Việt.

**Cách sửa:** Tải font Noto Sans và đặt vào `assets/fonts/`:
- `NotoSans-Bold.ttf`
- `NotoSans-Regular.ttf`

---

### Lỗi: `ModuleNotFoundError: No module named 'PIL'`

**Nguyên nhân:** Chưa cài thư viện.

**Cách sửa:**
```powershell
pip install -r requirements.txt
```

---

### Lỗi đăng Facebook: `(#200) The user hasn't authorized the application`

**Nguyên nhân:** Token thiếu quyền `pages_manage_posts`.

**Cách sửa:** Lấy lại token và chọn đúng 2 quyền:
- `pages_manage_posts`
- `pages_read_engagement`

---

## 12. Chạy 24/7 trên server

### Windows — dùng Task Scheduler

1. Mở **Task Scheduler** (tìm trong Start Menu)
2. **Create Basic Task** → Đặt tên: `News Facebook Bot`
3. Trigger: **When the computer starts**
4. Action: **Start a program**
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\Demo_FC`
5. Finish

### Windows — dùng NSSM (chạy như Windows Service)

```powershell
# Tải NSSM từ https://nssm.cc/
nssm install NewsFBBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\Demo_FC\main.py"
nssm set NewsFBBot AppDirectory "C:\path\to\Demo_FC"
nssm start NewsFBBot
```

### Linux/macOS — dùng systemd

Tạo file `/etc/systemd/system/newsfbbot.service`:

```ini
[Unit]
Description=News Facebook Bot
After=network.target

[Service]
WorkingDirectory=/path/to/Demo_FC
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt:

```bash
sudo systemctl enable newsfbbot
sudo systemctl start newsfbbot
sudo systemctl status newsfbbot
```

### Linux/macOS — dùng screen (đơn giản nhất)

```bash
screen -S newsbot
python main.py
# Nhấn Ctrl+A rồi D để detach (bot vẫn chạy nền)

# Quay lại xem log:
screen -r newsbot
```
