from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core import security
from src.core.config import settings
from src.domain.models import Link, Package, Token, User
from src.infrastructure.mock_jd_api import MockJDownloaderAPI
from src.api import deps
from src.infrastructure.settings_manager import settings_manager
import os
import json
from pathlib import Path

# Helper for data path
def get_data_dir() -> Path:
    # backend/src/api/v1/router.py -> ... -> backend/data
    return Path(__file__).resolve().parent.parent.parent.parent / "data"

def get_buffer_file() -> Path:
    return get_data_dir() / "link_buffer.json"

def get_dlc_buffer_dir() -> Path:
    d = get_data_dir() / "buffer"
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
    return d

from src.api.v1.endpoints import settings as settings_endpoint

router = APIRouter()
router.include_router(settings_endpoint.router, prefix="/settings", tags=["settings"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    # Dynamic auth from settings
    current_settings = settings_manager.load_settings()
    if form_data.username != "admin" or form_data.password != current_settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/downloads", response_model=List[Package])
async def get_downloads(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    return await api.get_packages()

@router.get("/linkgrabber", response_model=List[Package])
async def get_linkgrabber(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    return await api.get_linkgrabber_packages()

@router.post("/linkgrabber/confirm-all")
async def confirm_all_linkgrabber(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.confirm_all_linkgrabber()
    return {"status": "confirmed"}

@router.post("/linkgrabber/move")
async def move_to_dl(
    package_ids: List[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.move_to_dl(package_ids)
    return {"status": "moved"}

@router.post("/downloads/links", response_model=str)
async def add_links(
    links: List[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    try:
        pkg_id = await api.add_links(links)
        return str(pkg_id)
    except Exception as e:
        # Buffer if connection failed
        buffer_file = get_buffer_file()
        if not buffer_file.parent.exists():
             buffer_file.parent.mkdir(parents=True, exist_ok=True)
             
        buffer_data = []
        if buffer_file.exists():
            try:
                with open(buffer_file, "r") as f:
                    buffer_data = json.load(f)
            except:
                pass
        
        buffer_data.extend(links)
        with open(buffer_file, "w") as f:
            json.dump(buffer_data, f)
            
        return "buffered-offline"

@router.post("/downloads/start")
async def start_downloads(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    resp = await api.start_downloads()
    return {"status": "started", "jd_response": resp}

@router.post("/linkgrabber/delete")
async def delete_linkgrabber_packages(
    package_ids: List[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.remove_linkgrabber_packages(package_ids)
    return {"status": "deleted"}

@router.post("/downloads/delete")
async def delete_download_packages(
    package_ids: List[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.remove_download_packages(package_ids)
    return {"status": "deleted"}

@router.post("/linkgrabber/set-directory")
async def set_linkgrabber_directory(
    payload: dict,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    # payload: { packageIds: [], directory: "" }
    package_ids = payload.get("packageIds", [])
    directory = payload.get("directory", "")
    if package_ids and directory:
        await api.set_download_directory(package_ids, directory)
    return {"status": "updated"}

@router.post("/downloads/stop")
async def stop_downloads(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.stop_downloads()
    return {"status": "stopped"}

from fastapi import UploadFile, File

@router.post("/linkgrabber/add-file")
async def add_container_file(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)],
    file: UploadFile = File(...)
):
    content = await file.read()
    
    try:
        result = await api.add_dlc(content)
        if result != "ok":
             # Some API error not conn related
             raise HTTPException(status_code=400, detail=result)
        return {"status": "added", "filename": file.filename}

    except Exception as e:
         # Buffer if connection failed (or other error but we assume conn for now essentially)
         # Save DLC to backend/data/buffer/
         buffer_dir = get_dlc_buffer_dir()
             
         import time
         # Use timestamp to avoid collision
         safe_name = f"{int(time.time())}_{file.filename}"
         file_path = buffer_dir / safe_name
         
         with open(file_path, "wb") as f:
             f.write(content)
             
         return {"status": "buffered", "filename": file.filename}

@router.get("/linkgrabber/buffer")
async def get_link_buffer(
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    buffer_file = get_buffer_file()
    
    count = 0
    links = []
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                links = json.load(f)
                count = len(links)
        except:
            pass
    return {"count": count, "links": links}

@router.post("/linkgrabber/buffer/replay")
async def replay_link_buffer(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    buffer_file = get_buffer_file()

    links = []
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                links = json.load(f)
        except:
            pass

    if not links:
        return {"status": "empty", "message": "Buffer is empty"}

    # Attempt replay
    try:
        # Check help first to fail fast on connection
        await api.get_help() 
        result = await api.add_links(links)
        
        if "ok" in result or "success" in result:
             with open(buffer_file, "w") as f:
                json.dump([], f)
             return {"status": "replayed", "count": len(links)}
        else:
             raise HTTPException(status_code=500, detail=f"JD Error: {result}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection Failed: {str(e)}")

@router.get("/system/status")
async def get_system_status(
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)],
):
    # Check JD Connection
    jd_online = False
    try:
        # Simple check, help or version
        await api.get_help()
        jd_online = True
    except:
        jd_online = False

    # Check Buffer (now contains package objects)
    buffer_file = get_buffer_file()
    buffer_count = 0
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                buffer_data = json.load(f)
                # Count total links across all packages
                for entry in buffer_data:
                    if isinstance(entry, dict):
                        buffer_count += len(entry.get("links", []))
                    else:
                        buffer_count += 1  # Legacy format: single link
        except:
            pass

    # Check DLC Buffer
    dlc_buffer_dir = get_dlc_buffer_dir()
    
    if dlc_buffer_dir.exists():
        try:
             files = [f for f in os.listdir(dlc_buffer_dir) if f.endswith(".dlc")]
             buffer_count += len(files)
        except:
             pass

    return {
        "jd_online": jd_online,
        "buffer_count": buffer_count
    }

@router.post("/system/buffer/replay")
async def system_buffer_replay(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    return await replay_link_buffer(current_user, api)

@router.get("/buffer/details")
async def get_buffer_details(
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """Get detailed buffer contents including packages and DLC files."""
    buffer_file = get_buffer_file()
    dlc_buffer_dir = get_dlc_buffer_dir()
    
    # Get link packages
    packages = []
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                packages = json.load(f)
        except:
            pass
    
    # Get DLC files
    dlc_files = []
    if dlc_buffer_dir.exists():
        try:
            for filename in os.listdir(dlc_buffer_dir):
                if filename.endswith(".dlc"):
                    file_path = dlc_buffer_dir / filename
                    dlc_files.append({
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "timestamp": os.path.getmtime(file_path)
                    })
        except:
            pass
    
    return {
        "packages": packages,
        "dlc_files": dlc_files
    }

@router.delete("/buffer/package/{index}")
async def delete_buffer_package(
    index: int,
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """Delete a specific package from the buffer by index."""
    buffer_file = get_buffer_file()
    
    if not buffer_file.exists():
        raise HTTPException(status_code=404, detail="Buffer file not found")
    
    try:
        with open(buffer_file, "r") as f:
            packages = json.load(f)
        
        if index < 0 or index >= len(packages):
            raise HTTPException(status_code=404, detail="Package index out of range")
        
        deleted = packages.pop(index)
        
        with open(buffer_file, "w") as f:
            json.dump(packages, f)
        
        return {"status": "deleted", "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buffer/dlc/{filename}")
async def delete_buffer_dlc(
    filename: str,
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """Delete a specific DLC file from the buffer."""
    dlc_buffer_dir = get_dlc_buffer_dir()
    file_path = dlc_buffer_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="DLC file not found")
    
    try:
        os.remove(file_path)
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buffer/clear")
async def clear_buffer(
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """Clear the entire buffer (both links and DLC files)."""
    buffer_file = get_buffer_file()
    dlc_buffer_dir = get_dlc_buffer_dir()
    
    deleted_packages = 0
    deleted_dlcs = 0
    
    # Clear link buffer
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                packages = json.load(f)
                deleted_packages = len(packages)
            with open(buffer_file, "w") as f:
                json.dump([], f)
        except:
            pass
    
    # Clear DLC buffer
    if dlc_buffer_dir.exists():
        try:
            for filename in os.listdir(dlc_buffer_dir):
                if filename.endswith(".dlc"):
                    os.remove(dlc_buffer_dir / filename)
                    deleted_dlcs += 1
        except:
            pass
    
    return {
        "status": "cleared",
        "deleted_packages": deleted_packages,
        "deleted_dlcs": deleted_dlcs
    }

# CNL Proxy Endpoints for Browser Extension
# These endpoints allow the browser extension to forward CNL requests

from src.cnl.decrypter import CNLDecrypter
from fastapi import Form
import re

@router.post("/cnl/flash/check")
async def cnl_proxy_check():
    """CNL check endpoint for browser extension."""
    return "JDownloader"

@router.post("/cnl/flash/addcrypted")
@router.post("/cnl/flash/addcrypted2")
@router.post("/cnl/flash/add")
async def cnl_proxy_add(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    crypted: str = Form(...),
    jk: str = Form(...),
    passwords: str = Form(None),
    source: str = Form(None),
    package: str = Form(None)
):
    """
    CNL add endpoint for browser extension.
    Accepts the same parameters as the local CNL receiver and buffers the links.
    """
    # Extract key from JK
    key_match = re.search(r"return ['\"]([0-9a-fA-F]+)['\"]", jk)
    if not key_match:
        raise HTTPException(status_code=400, detail="Invalid JK format")
    
    key = key_match.group(1)
    
    # Decrypt
    decrypted_text = CNLDecrypter.decrypt(crypted, key)
    if not decrypted_text:
        raise HTTPException(status_code=400, detail="Decryption failed")
    
    links = CNLDecrypter.extract_links(decrypted_text)
    
    if not links:
        raise HTTPException(status_code=400, detail="No links found")
    
    # Buffer the links
    buffer_file = get_buffer_file()
    buffer_data = []
    if buffer_file.exists():
        try:
            with open(buffer_file, "r") as f:
                buffer_data = json.load(f)
        except:
            pass
    
    package_entry = {
        "package": package or source or "CNL Package",
        "links": links,
        "passwords": passwords
    }
    buffer_data.append(package_entry)
    
    with open(buffer_file, "w") as f:
        json.dump(buffer_data, f)
    
    return {"status": "success", "links_added": len(links), "package": package_entry["package"]}
