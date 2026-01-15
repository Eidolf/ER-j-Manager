from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from src.core.config import settings
from src.domain.models import TokenData
from src.infrastructure.api_interface import JDownloaderAPI
from src.infrastructure.local_jd_api import LocalJDownloaderAPI
from src.infrastructure.mock_jd_api import MockJDownloaderAPI

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")

from src.infrastructure.settings_manager import settings_manager

_jd_api = None
_last_settings_hash = None

def get_jd_api() -> Generator[JDownloaderAPI, None, None]:
    global _jd_api, _last_settings_hash
    
    current_settings = settings_manager.load_settings()
    # Simple hash based on string representation to detect change
    current_hash = str(current_settings.model_dump())
    
    if _jd_api is None or _last_settings_hash != current_hash:
        _last_settings_hash = current_hash
        if current_settings.use_mock:
            _jd_api = MockJDownloaderAPI()
        else:
            _jd_api = LocalJDownloaderAPI(base_url=current_settings.api_url)
            
    yield _jd_api

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    return token_data
