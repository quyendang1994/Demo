from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    title: str
    description: str
    link: str
    pub_date: datetime
    source: str
    image_url: Optional[str] = None


@dataclass
class PostResult:
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None
    image_path: Optional[str] = None
