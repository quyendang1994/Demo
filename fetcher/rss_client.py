import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from models import NewsItem
from fetcher.sources import RSSSource, SOURCES, ImageField
from utils.retry import retry
from utils.text_utils import strip_html

logger = logging.getLogger(__name__)

NAMESPACES = {
    "media": "http://search.yahoo.com/mrss/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


class RSSClient:
    def __init__(self, timeout: int = 10, max_items: int = 10):
        self.timeout = timeout
        self.max_items = max_items

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(URLError, HTTPError, ET.ParseError, Exception))
    def fetch(self, source: RSSSource) -> list:
        raw_bytes = self._download(source.url)
        xml_text = raw_bytes.decode("utf-8", errors="replace")
        # Một số feed dùng encoding khác trong XML declaration — xử lý bằng cách strip declaration
        if xml_text.startswith("<?xml"):
            xml_text = xml_text.split("?>", 1)[-1].strip()
        root = ET.fromstring(xml_text)
        items = root.findall(".//item")[: self.max_items]
        result = []
        for item in items:
            try:
                news_item = self._parse_item(item, source)
                if news_item:
                    result.append(news_item)
            except Exception as e:
                logger.debug(f"Bỏ qua item lỗi từ {source.name}: {e}")
        return result

    def _download(self, url: str) -> bytes:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 NewsBot/1.0 (+bot)"})
        with urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def _parse_item(self, item: ET.Element, source: RSSSource) -> Optional[NewsItem]:
        title = self._text(item, "title")
        if not title:
            return None
        description = strip_html(self._text(item, "description"))
        link = self._text(item, "link") or self._text(item, "guid")
        pub_date = self._parse_date(self._text(item, "pubDate") or self._text(item, "dc:date"))
        image_url = self._extract_image(item, source.image_field)
        return NewsItem(
            title=title.strip(),
            description=description[:300] if description else "",
            link=link or "",
            pub_date=pub_date,
            source=source.name,
            image_url=image_url,
        )

    def _text(self, element: ET.Element, tag: str) -> str:
        # Thử tìm tag thường, sau đó thử với namespace
        child = element.find(tag)
        if child is None:
            for prefix, uri in NAMESPACES.items():
                child = element.find(f"{{{uri}}}{tag.split(':')[-1]}")
                if child is not None:
                    break
        if child is None:
            return ""
        return (child.text or "").strip()

    def _extract_image(self, item: ET.Element, field: ImageField) -> Optional[str]:
        if field == "enclosure":
            enc = item.find("enclosure")
            if enc is not None:
                url = enc.get("url", "")
                mime = enc.get("type", "")
                if url and ("image" in mime or url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                    return url
        elif field == "media_thumbnail":
            for prefix, uri in NAMESPACES.items():
                thumb = item.find(f"{{{uri}}}thumbnail")
                if thumb is not None:
                    return thumb.get("url")
            # Thử media:content
            for prefix, uri in NAMESPACES.items():
                content_el = item.find(f"{{{uri}}}content")
                if content_el is not None:
                    url = content_el.get("url", "")
                    if url:
                        return url
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date và luôn trả về naive datetime (không timezone) để so sánh được."""
        if not date_str:
            return datetime.now()
        try:
            dt = parsedate_to_datetime(date_str)
            # Chuyển về naive datetime (bỏ timezone info)
            return dt.replace(tzinfo=None)
        except Exception:
            pass
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except Exception:
                pass
        return datetime.now()


def _deduplicate(items: list) -> list:
    seen, result = set(), []
    for item in items:
        key = hashlib.md5(item.title[:60].lower().encode("utf-8")).hexdigest()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def fetch_all_sources(sources: list, timeout: int = 10, max_items_per_source: int = 10) -> list:
    """Lấy tin từ tất cả nguồn RSS, sort theo ngày, deduplicate."""
    client = RSSClient(timeout=timeout, max_items=max_items_per_source)
    all_items = []
    for source in sources:
        if not source.enabled:
            continue
        try:
            items = client.fetch(source)
            all_items.extend(items)
            logger.info(f"Lấy được {len(items)} tin từ {source.name}")
        except Exception as e:
            logger.error(f"Không lấy được tin từ {source.name}: {e}")
    all_items.sort(key=lambda x: x.pub_date, reverse=True)
    deduped = _deduplicate(all_items)
    logger.info(f"Tổng cộng {len(deduped)} tin (sau dedup từ {len(all_items)})")
    return deduped
