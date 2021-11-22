from typing import Dict, List, Optional

from pydantic import BaseModel


class Comment(BaseModel):
    author: str


class User(BaseModel):
    username: str
    password: Optional[str] = None
    likes: Dict[str, int]
    comments: List[Comment]


class AdminUser(User):
    admin_password: str
