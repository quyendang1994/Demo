import re
from datetime import datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import ImageDraw, ImageFont


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts)


def strip_html(raw: str) -> str:
    """Loại bỏ HTML tags và unescape entities, trả về plain text."""
    if not raw:
        return ""
    parser = _HTMLStripper()
    try:
        parser.feed(raw)
        text = parser.get_text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text: str, max_chars: int, suffix: str = "...") -> str:
    """Cắt ngắn văn bản nếu vượt quá độ dài tối đa."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)].rstrip() + suffix


def wrap_text_to_lines(text: str, font, draw, max_width_px: int, max_lines: int = 2) -> str:
    """
    Wrap text dựa theo pixel width (hỗ trợ tiếng Việt).
    Trả về chuỗi đã wrap, cắt ở max_lines với '...' nếu cần.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width_px:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            if len(lines) >= max_lines:
                break

    if current_line and len(lines) < max_lines:
        lines.append(current_line)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last:
            test = last.rstrip() + "..."
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width_px:
                lines[-1] = test
                break
            last = last[:-1]

    # Nếu dòng cuối bị cắt nhưng còn nhiều từ hơn
    result = "\n".join(lines)
    remaining_words = text[len(" ".join(lines).replace("...", "").replace("\n", " ")):].strip()
    if remaining_words and not result.endswith("..."):
        last_line = lines[-1]
        while last_line:
            test = last_line.rstrip() + "..."
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width_px:
                lines[-1] = test
                break
            last_line = last_line[:-1]
        result = "\n".join(lines)

    return result


WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def format_viet_datetime(dt: datetime) -> str:
    """Trả về chuỗi ngày giờ tiếng Việt: 'Thứ Tư, 17/06/2026 · 07:00'"""
    weekday = WEEKDAYS_VI[dt.weekday()]
    return f"{weekday}, {dt.strftime('%d/%m/%Y')} · {dt.strftime('%H:%M')}"
