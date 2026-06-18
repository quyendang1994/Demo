from dataclasses import dataclass
from typing import Optional, Literal

ImageField = Literal["enclosure", "media_thumbnail", None]


@dataclass
class RSSSource:
    name: str
    url: str
    image_field: ImageField = "enclosure"
    enabled: bool = True


SOURCES: list = [
    RSSSource("VnExpress",       "https://vnexpress.net/rss/tin-moi-nhat.rss",       "enclosure"),
    RSSSource("Tuổi Trẻ",       "https://tuoitre.vn/rss/tin-moi-nhat.rss",          "enclosure"),
    RSSSource("Thanh Niên",     "https://thanhnien.vn/rss/home.rss",                 "enclosure"),
    RSSSource("BBC Tiếng Việt", "https://feeds.bbci.co.uk/vietnamese/rss.xml",       "media_thumbnail"),
    RSSSource("Dân Trí",        "https://dantri.com.vn/rss/home.rss",               "enclosure"),
]
