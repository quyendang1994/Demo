import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_LOG_ENTRIES = 500


class PostLog:
    """Theo dõi các link bài đã đăng để tránh đăng lại."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Không đọc được post log: {e}. Tạo mới.")
        return {"posted_links": [], "last_posted_at": None, "total_posts": 0}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def is_posted(self, link: str) -> bool:
        return link in self._data["posted_links"]

    def mark_posted(self, links: list):
        existing = self._data["posted_links"]
        for link in links:
            if link not in existing:
                existing.append(link)
        # Giữ MAX_LOG_ENTRIES gần nhất
        if len(existing) > MAX_LOG_ENTRIES:
            self._data["posted_links"] = existing[-MAX_LOG_ENTRIES:]
        self._data["last_posted_at"] = datetime.now().isoformat()
        self._data["total_posts"] = self._data.get("total_posts", 0) + 1
        self._save()
        logger.info(f"Đã lưu {len(links)} link vào post log (tổng: {self._data['total_posts']} lần đăng)")
