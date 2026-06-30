from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TopProduct(BaseModel):
    term: str
    mention_count: int


class ChannelActivity(BaseModel):
    channel_name: str
    total_posts: int
    avg_views: float
    total_images: int
    first_post_date: Optional[datetime]
    last_post_date: Optional[datetime]


class MessageResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    views: int
    forwards: int
    message_date: Optional[datetime]


class VisualContentStat(BaseModel):
    channel_name: str
    total_messages: int
    messages_with_images: int
    image_percentage: float