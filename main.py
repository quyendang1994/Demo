"""
News Facebook Bot
-----------------
Lấy tin tức mới nhất từ RSS, tạo ảnh 1080x1080, đăng lên Facebook theo lịch.

Cách dùng:
  python main.py            # Chạy ở chế độ scheduler (24/7)
  python main.py --now      # Chạy ngay một lần (test)
  python main.py --image    # Chỉ tạo ảnh, không đăng Facebook
  python main.py --check    # Kiểm tra cấu hình và token Facebook
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path

from config import config
from fetcher.rss_client import fetch_all_sources
from fetcher.sources import SOURCES
from models import PostResult
from poster.facebook import FacebookPoster
from renderer.image_builder import ImageBuilder
from scheduler.timer import DailyScheduler
from utils.post_log import PostLog


def _setup_logging(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "bot.log"
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console: INFO+ với UTF-8 để hiển thị tiếng Việt trên Windows
    import io
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ch = logging.StreamHandler(utf8_stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(ch)

    # File: DEBUG+ với rotation 5MB x 3 backup
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(fh)


def _cleanup_old_images(output_dir: Path, keep: int = 10):
    images = sorted(output_dir.glob("news_*.jpg"), key=lambda p: p.stat().st_mtime)
    for old in images[:-keep]:
        try:
            old.unlink()
            logging.getLogger(__name__).debug(f"Xóa ảnh cũ: {old.name}")
        except Exception:
            pass


logger = logging.getLogger(__name__)


def run_pipeline(image_only: bool = False) -> bool:
    """Thực hiện toàn bộ pipeline: fetch → render → post."""
    logger.info("=" * 50)
    logger.info("Pipeline bắt đầu")

    # 1. Lấy tin tức — 1 tin mới nhất mỗi nguồn
    items = fetch_all_sources(
        SOURCES,
        timeout=config.REQUEST_TIMEOUT,
        max_items_per_source=1,
    )
    if not items:
        logger.warning("Không lấy được tin tức nào. Dừng pipeline.")
        return False
    logger.info(f"Có {len(items)} tin sau dedup")

    # 2. Lọc bài đã đăng
    post_log = PostLog(config.POST_LOG_PATH)
    fresh_items = [i for i in items if not post_log.is_posted(i.link)]
    if len(fresh_items) < 3:
        logger.info(f"Chỉ có {len(fresh_items)} bài mới, dùng tất cả tin tức.")
        fresh_items = items

    # 3. Render ảnh
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = config.OUTPUT_DIR / f"news_{timestamp}.jpg"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    builder = ImageBuilder(
        brand_name=config.BRAND_NAME,
        font_dir=config.FONT_DIR,
        canvas_size=config.CANVAS_SIZE,
    )
    image_path = builder.build(fresh_items, output_path)
    logger.info(f"Ảnh đã tạo: {image_path}")

    if image_only:
        logger.info("Chế độ --image: bỏ qua bước đăng Facebook.")
        return True

    # 4. Đăng lên Facebook
    poster = FacebookPoster(
        page_id=config.FB_PAGE_ID,
        access_token=config.FB_ACCESS_TOKEN,
        api_version=config.FB_API_VERSION,
    )
    caption = poster.build_caption(fresh_items[: config.TOTAL_CARDS_ON_IMAGE])
    try:
        result: PostResult = poster.post_photo(image_path, caption)
        if result.success:
            logger.info(f"Đăng Facebook thành công! post_id={result.post_id}")
            post_log.mark_posted([i.link for i in fresh_items[: config.TOTAL_CARDS_ON_IMAGE]])
        else:
            logger.error(f"Đăng Facebook thất bại: {result.error}")
    except Exception as e:
        logger.error(f"Lỗi khi đăng Facebook: {e}", exc_info=True)
        return False

    # 5. Dọn ảnh cũ
    _cleanup_old_images(config.OUTPUT_DIR, keep=10)
    logger.info("Pipeline hoàn thành.")
    return True


def main():
    _setup_logging(config.LOG_DIR)

    args = sys.argv[1:]

    # Chế độ --check: kiểm tra cấu hình
    if "--check" in args:
        logger.info("Kiểm tra cấu hình...")
        try:
            config.validate()
            logger.info("Cấu hình hợp lệ.")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        poster = FacebookPoster(config.FB_PAGE_ID, config.FB_ACCESS_TOKEN, config.FB_API_VERSION)
        ok = poster.verify_token()
        sys.exit(0 if ok else 1)

    # Chế độ --image: chỉ tạo ảnh (không cần FB config)
    if "--image" in args:
        run_pipeline(image_only=True)
        return

    # Chế độ --now: chạy pipeline ngay (cần FB config)
    if "--now" in args:
        try:
            config.validate()
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        success = run_pipeline()
        sys.exit(0 if success else 1)

    # Chế độ mặc định: scheduler 24/7
    try:
        config.validate()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Khởi động News Facebook Bot")
    logger.info(f"Brand: {config.BRAND_NAME}")
    logger.info(f"Lịch đăng: {', '.join(config.SCHEDULE_TIMES)}")
    logger.info(f"Nguồn RSS: {len([s for s in SOURCES if s.enabled])} nguồn")

    scheduler = DailyScheduler(config.SCHEDULE_TIMES, run_pipeline)
    scheduler.start()

    logger.info("Bot đang chạy. Nhấn Ctrl+C để dừng.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Nhận tín hiệu dừng. Đang tắt...")
        scheduler.stop()
        logger.info("Bot đã dừng.")


if __name__ == "__main__":
    main()
