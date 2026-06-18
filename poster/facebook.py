import logging
from datetime import datetime
from pathlib import Path

import requests

from models import NewsItem, PostResult
from utils.retry import retry

logger = logging.getLogger(__name__)

HASHTAGS = "#TinTuc #ViệtNam #TinNong #ThoiSu #NewsBotVN"


class FacebookPoster:
    BASE_URL = "https://graph.facebook.com"

    def __init__(self, page_id: str, access_token: str, api_version: str = "v19.0"):
        self.page_id = page_id
        self.token = access_token
        self.version = api_version
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "NewsBot/1.0"

    @retry(max_attempts=2, delay=5.0, backoff=2.0, exceptions=(requests.RequestException,))
    def post_photo(self, image_path: Path, caption: str) -> PostResult:
        """Đăng ảnh lên Facebook Page."""
        url = f"{self.BASE_URL}/{self.version}/{self.page_id}/photos"
        with open(image_path, "rb") as f:
            response = self.session.post(
                url,
                data={"access_token": self.token, "caption": caption},
                files={"source": (image_path.name, f, "image/jpeg")},
                timeout=60,
            )
        if not response.ok:
            logger.error(f"Facebook API lỗi {response.status_code}: {response.text[:500]}")
            response.raise_for_status()
        data = response.json()
        post_id = data.get("post_id") or data.get("id", "")
        logger.info(f"Đăng thành công! post_id={post_id}")
        return PostResult(success=True, post_id=post_id, image_path=str(image_path))

    def build_caption(self, items: list) -> str:
        """Tạo caption tiếng Việt cho bài đăng Facebook."""
        now = datetime.now()
        weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        date_str = f"{weekdays[now.weekday()]}, {now.strftime('%d/%m/%Y')}"

        lines = [
            f"📰 TIN TỨC NỔI BẬT HÔM NAY – {date_str}",
            "─" * 36,
            "",
        ]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.title}")
            if item.link:
                lines.append(f"   👉 {item.link}")
            lines.append("")

        lines += [
            "─" * 36,
            HASHTAGS,
        ]
        return "\n".join(lines)

    def verify_token(self) -> bool:
        """Kiểm tra token còn hợp lệ không."""
        try:
            url = f"{self.BASE_URL}/{self.version}/me"
            resp = self.session.get(
                url,
                params={"access_token": self.token, "fields": "id,name"},
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                logger.info(f"Token hợp lệ. Page: {data.get('name')} (id={data.get('id')})")
                return True
            logger.error(f"Token không hợp lệ: {resp.status_code} {resp.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Không kiểm tra được token: {e}")
            return False
