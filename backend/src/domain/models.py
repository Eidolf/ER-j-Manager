from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum

class DownloadStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    FINISHED = "FINISHED"
    OFFLINE = "OFFLINE"

class Link(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    url: str
    host: str
    bytes_total: int = 0
    bytes_loaded: int = 0
    status: DownloadStatus = DownloadStatus.STOPPED
    speed: int = 0  # bytes per second
    eta: Optional[int] = None # seconds

class Package(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    save_to: str = "/downloads"
    links: List[Link] = []
    total_bytes: int = 0
    loaded_bytes: int = 0
    child_count: int = 0

class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
