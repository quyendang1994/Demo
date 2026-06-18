import logging
from datetime import datetime
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from renderer.layout import Layout
from utils.text_utils import format_viet_datetime, wrap_text_to_lines

logger = logging.getLogger(__name__)


def draw_gradient_background(img: Image.Image, layout: Layout) -> None:
    draw = ImageDraw.Draw(img)
    top = layout.bg_top
    bot = layout.bg_bottom
    for y in range(layout.canvas_h):
        t = y / layout.canvas_h
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(0, y), (layout.canvas_w, y)], fill=(r, g, b))


def draw_header(draw: ImageDraw.Draw, layout: Layout, brand_name: str,
                now: datetime, fonts: dict) -> None:
    # Logo circle
    logo_r = 22
    logo_cx = layout.padding + logo_r
    logo_cy = layout.header_h // 2
    draw.ellipse(
        [logo_cx - logo_r, logo_cy - logo_r, logo_cx + logo_r, logo_cy + logo_r],
        fill=layout.accent,
    )
    initials = "".join(w[0].upper() for w in brand_name.split()[:2])
    font_logo = fonts.get("badge") or fonts.get("title")
    bbox = draw.textbbox((0, 0), initials, font=font_logo)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (logo_cx - tw // 2, logo_cy - th // 2 - bbox[1]),
        initials,
        font=font_logo,
        fill=(255, 255, 255),
    )

    # Brand name
    bx = logo_cx + logo_r + 14
    by = logo_cy
    font_brand = fonts.get("header")
    bbox = draw.textbbox((0, 0), brand_name.upper(), font=font_brand)
    th = bbox[3] - bbox[1]
    draw.text(
        (bx, by - th // 2 - bbox[1]),
        brand_name.upper(),
        font=font_brand,
        fill=layout.text_header,
    )

    # Date/time at right
    date_str = format_viet_datetime(now)
    font_date = fonts.get("date") or fonts.get("source")
    bbox = draw.textbbox((0, 0), date_str, font=font_date)
    dw = bbox[2] - bbox[0]
    dh = bbox[3] - bbox[1]
    draw.text(
        (layout.canvas_w - layout.padding - dw, logo_cy - dh // 2 - bbox[1]),
        date_str,
        font=font_date,
        fill=layout.text_body,
    )

    # Separator line
    sep_y = layout.header_h - 1
    draw.line(
        [(layout.padding, sep_y), (layout.canvas_w - layout.padding, sep_y)],
        fill=layout.separator,
        width=1,
    )


def draw_news_card(
    draw: ImageDraw.Draw,
    img: Image.Image,
    item,
    index: int,
    layout: Layout,
    fonts: dict,
    thumb: Optional[Image.Image],
) -> None:
    cx = layout.card_x
    cy = layout.card_y(index)
    cw = layout.card_w
    ch = layout.card_h

    # Card background (semi-transparent overlay)
    overlay = Image.new("RGBA", (cw, ch), layout.card_fill)
    img.alpha_composite(overlay, dest=(cx, cy))

    # Card border
    draw.rounded_rectangle(
        [cx, cy, cx + cw, cy + ch],
        radius=layout.corner_r,
        outline=layout.card_outline,
        width=1,
    )

    # Badge (numbered circle)
    badge_r = 20
    badge_cx = cx + layout.padding // 2 + badge_r - 4
    badge_cy = cy + ch // 2
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
        fill=layout.accent,
    )
    badge_text = str(index + 1)
    font_badge = fonts.get("badge")
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (badge_cx - bw // 2, badge_cy - bh // 2 - bbox[1]),
        badge_text,
        font=font_badge,
        fill=(255, 255, 255),
    )

    # Thumbnail (right side)
    thumb_x = cx + cw - layout.thumb_w - 10
    if thumb:
        try:
            th_resized = thumb.resize((layout.thumb_w, ch - 16), Image.LANCZOS)
            th_resized = th_resized.convert("RGBA")
            img.alpha_composite(th_resized, dest=(thumb_x, cy + 8))
        except Exception as e:
            logger.debug(f"Không thể dán thumbnail: {e}")
            thumb = None

    # Text zone
    text_x = badge_cx + badge_r + 14
    text_right = (thumb_x - 10) if thumb else (cx + cw - 12)
    text_w = text_right - text_x

    # Title (2 dòng max)
    font_title = fonts.get("title")
    title_wrapped = wrap_text_to_lines(item.title, font_title, draw, text_w, max_lines=2)
    title_bbox = draw.textbbox((0, 0), title_wrapped, font=font_title)
    title_h = title_bbox[3] - title_bbox[1]

    # Body (1 dòng)
    font_body = fonts.get("body")
    body_text = item.description or ""
    body_wrapped = wrap_text_to_lines(body_text, font_body, draw, text_w, max_lines=1) if body_text else ""
    body_bbox = draw.textbbox((0, 0), body_wrapped, font=font_body) if body_wrapped else (0, 0, 0, 0)
    body_h = body_bbox[3] - body_bbox[1]

    # Source
    font_source = fonts.get("source")
    source_text = f"● {item.source}"
    source_bbox = draw.textbbox((0, 0), source_text, font=font_source)
    source_h = source_bbox[3] - source_bbox[1]

    # Vertical centering
    total_text_h = title_h + (6 + body_h if body_wrapped else 0) + 6 + source_h
    text_y = cy + (ch - total_text_h) // 2

    draw.text((text_x, text_y - title_bbox[1]), title_wrapped, font=font_title, fill=layout.text_title)
    cur_y = text_y + title_h + 6
    if body_wrapped:
        draw.text((text_x, cur_y - body_bbox[1]), body_wrapped, font=font_body, fill=layout.text_body)
        cur_y += body_h + 6
    draw.text((text_x, cur_y - source_bbox[1]), source_text, font=font_source, fill=layout.text_source)


def draw_footer(draw: ImageDraw.Draw, layout: Layout, fonts: dict, source_names: list) -> None:
    footer_y = layout.canvas_h - layout.footer_h + 10
    sources_str = " • ".join(source_names)
    footer_text = f"Nguồn: {sources_str}"
    font_footer = fonts.get("footer")
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    fw = bbox[2] - bbox[0]
    draw.text(
        ((layout.canvas_w - fw) // 2, footer_y - bbox[1]),
        footer_text,
        font=font_footer,
        fill=layout.text_footer,
    )
