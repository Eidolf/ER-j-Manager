from typing import Annotated

from fastapi import APIRouter, Depends

from src.api import deps
from src.api.deps import oauth2_scheme
from src.infrastructure.mock_jd_api import MockJDownloaderAPI
from src.infrastructure.settings_manager import JDSettings, settings_manager

router = APIRouter()

@router.get("", response_model=JDSettings)
async def get_settings(token: str = Depends(oauth2_scheme)):
    return settings_manager.load_settings()

@router.post("", response_model=JDSettings)
async def update_settings(settings: JDSettings, token: str = Depends(oauth2_scheme)):
    settings_manager.save_settings(settings)
    return settings

@router.post("/test", response_model=dict)
async def test_connnection(settings: JDSettings, token: str = Depends(oauth2_scheme)):
    from src.infrastructure.local_jd_api import LocalJDownloaderAPI
    # Create temp API instance with provided settings
    api = LocalJDownloaderAPI(base_url=settings.api_url)
    try:
        # Try a simple get_packages call (or we could expose a verify method)
        # get_packages calls /downloadsV2/queryPackages which is a valid check
        await api.get_packages()
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/help")
async def get_help_text(
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    return {"text": await api.get_help()}
