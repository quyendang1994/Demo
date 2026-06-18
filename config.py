import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Facebook
    FB_PAGE_ID: str = os.getenv("FB_PAGE_ID", "")
    FB_ACCESS_TOKEN: str = os.getenv("FB_ACCESS_TOKEN", "")
    FB_API_VERSION: str = os.getenv("FB_API_VERSION", "v19.0")

    # Schedule — comma-separated HH:MM times
    SCHEDULE_TIMES: list = os.getenv("SCHEDULE_TIMES", "07:00,12:00,18:00").split(",")

    # News settings
    MAX_ITEMS_PER_SOURCE: int = int(os.getenv("MAX_ITEMS_PER_SOURCE", "10"))
    TOTAL_CARDS_ON_IMAGE: int = int(os.getenv("TOTAL_CARDS_ON_IMAGE", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))

    # Paths
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))
    POST_LOG_PATH: Path = Path(os.getenv("POST_LOG_PATH", "output/post_log.json"))
    FONT_DIR: Path = Path(os.getenv("FONT_DIR", "assets/fonts"))

    # Image
    CANVAS_SIZE: tuple = (1080, 1080)
    BRAND_NAME: str = os.getenv("BRAND_NAME", "Tin Tức Hôm Nay")

    def validate(self):
        missing = []
        if not self.FB_PAGE_ID:
            missing.append("FB_PAGE_ID")
        if not self.FB_ACCESS_TOKEN:
            missing.append("FB_ACCESS_TOKEN")
        if missing:
            raise ValueError(
                f"Thiếu cấu hình bắt buộc: {', '.join(missing)}\n"
                "Vui lòng sao chép .env.example thành .env và điền thông tin."
            )


config = Config()
