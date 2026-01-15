from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


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
    eta: int | None = None # seconds

class Package(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    save_to: str = "/downloads"
    links: list[Link] = []
    total_bytes: int = 0
    loaded_bytes: int = 0
    child_count: int = 0
    speed: int = 0  # Aggregated speed from all links (bytes per second)

class User(BaseModel):
    username: str
    full_name: str | None = None
    email: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
