import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

from renderer.layout import Layout, layout as default_layout
from renderer.components import (
    draw_gradient_background,
    draw_header,
    draw_news_card,
    draw_footer,
)

logger = logging.getLogger(__name__)

SYSTEM_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"),
    ("C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/calibri.ttf"),
    ("C:/Windows/Fonts/arialbd.ttf",  "C:/Windows/Fonts/arial.ttf"),
]


class ImageBuilder:
    def __init__(self, brand_name: str = "Tin Tức Hôm Nay",
                 font_dir: Optional[Path] = None,
                 canvas_size: tuple = (1080, 1080)):
        self.brand_name = brand_name
        self.font_dir = font_dir or Path("assets/fonts")
        self.layout = default_layout
        self.fonts = self._load_fonts()

    def _find_font_pair(self) -> tuple:
        """Tìm cặp font bold + regular hỗ trợ tiếng Việt."""
        # Thử system fonts
        for bold_path, regular_path in SYSTEM_FONT_CANDIDATES:
            try:
                ImageFont.truetype(bold_path, 10)
                ImageFont.truetype(regular_path, 10)
                logger.info(f"Dùng system font: {bold_path}")
                return bold_path, regular_path
            except Exception:
                continue
        # Thử bundled fonts
        bundled_bold = self.font_dir / "NotoSans-Bold.ttf"
        bundled_reg = self.font_dir / "NotoSans-Regular.ttf"
        if bundled_bold.exists() and bundled_reg.exists():
            logger.info(f"Dùng bundled font: {bundled_bold}")
            return str(bundled_bold), str(bundled_reg)
        # Fallback: default PIL font (không hỗ trợ tiếng Việt tốt)
        logger.warning("Không tìm thấy font TrueType. Dùng default font (có thể không hiện tiếng Việt).")
        return None, None

    def _load_fonts(self) -> dict:
        L = self.layout
        bold_path, regular_path = self._find_font_pair()

        def tf(path, size):
            if path:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        return {
            "header": tf(bold_path, L.size_header_brand),
            "date":   tf(regular_path, L.size_header_date),
            "badge":  tf(bold_path, L.size_badge),
            "title":  tf(bold_path, L.size_title),
            "body":   tf(regular_path, L.size_body),
            "source": tf(regular_path, L.size_source),
            "footer": tf(regular_path, L.size_footer),
        }

    def _download_thumbnail(self, url: str, target_h: int) -> Optional[Image.Image]:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 NewsBot/1.0"})
            with urlopen(req, timeout=5) as resp:
                data = resp.read()
            img = Image.open(BytesIO(data)).convert("RGBA")
            # Crop to 2:3 aspect ratio (thumb_w : card_h)
            ratio = self.layout.thumb_w / target_h
            src_w, src_h = img.size
            src_ratio = src_w / src_h
            if src_ratio > ratio:
                new_w = int(src_h * ratio)
                left = (src_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, src_h))
            else:
                new_h = int(src_w / ratio)
                top = (src_h - new_h) // 2
                img = img.crop((0, top, src_w, top + new_h))
            return img
        except Exception as e:
            logger.debug(f"Không tải được thumbnail ({url[:60]}...): {e}")
            return None

    def build(self, items: list, output_path: Path) -> Path:
        L = self.layout
        now = datetime.now()

        # Canvas RGBA
        img = Image.new("RGBA", (L.canvas_w, L.canvas_h), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        # 1. Background gradient
        draw_gradient_background(img, L)

        # 2. Chọn top N items
        selected = items[: L.num_cards]

        # 3. Tải thumbnails song song (fail-silent)
        thumbs = []
        for item in selected:
            th = self._download_thumbnail(item.image_url, L.card_h) if item.image_url else None
            thumbs.append(th)

        # 4. Header
        draw_header(draw, L, self.brand_name, now, self.fonts)

        # 5. Các card tin tức
        for i, (item, thumb) in enumerate(zip(selected, thumbs)):
            draw_news_card(draw, img, item, i, L, self.fonts, thumb)

        # 6. Footer
        source_names = list(dict.fromkeys(item.source for item in selected))
        draw_footer(draw, L, self.fonts, source_names)

        # 7. Lưu ảnh
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_rgb = img.convert("RGB")
        img_rgb.save(str(output_path), "JPEG", quality=92, optimize=True)
        logger.info(f"Đã lưu ảnh: {output_path} ({output_path.stat().st_size // 1024} KB)")
        return output_path
