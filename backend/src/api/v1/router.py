import json
import os
import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm

from pydantic import BaseModel
from src.api import deps
from src.core import security
from src.core.config import settings
from src.domain.models import Package, Token, User
from src.infrastructure.mock_jd_api import MockJDownloaderAPI
from src.infrastructure.settings_manager import settings_manager


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

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/auth/change-password")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    current_settings = settings_manager.load_settings()
    
    # Verify old password
    if payload.old_password != current_settings.admin_password:
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    # Update password
    current_settings.admin_password = payload.new_password
    settings_manager.save_settings(current_settings)
    
    return {"status": "password_updated"}

@router.get("/settings/help/docs")
async def get_api_docs(
    current_user: Annotated[User, Depends(deps.get_current_user)],
):
    """Serve the JDownloader API Reference markdown file."""
    try:
        # Resolve path robustly for both Local (backend/src/...) and Docker (src/...)
        current_file = Path(__file__).resolve()
        
        # Candidates for project root:
        # 1. Docker: /app/src/api/v1/router.py -> 4 parents -> /app
        # 2. Local:  .../backend/src/api/v1/router.py -> 5 parents -> .../project
        
        candidates = [
            current_file.parent.parent.parent.parent,          # Docker (/app)
            current_file.parent.parent.parent.parent.parent,   # Local (.../ER-j-Manager)
        ]
        
        docs_path = None
        for root in candidates:
            p = root / "docs" / "jdownloader_api_reference.md"
            if p.exists():
                docs_path = p
                break
        
        if not docs_path or not docs_path.exists():
            # Fallback debug info
            debug_paths = [str(root / "docs") for root in candidates]
            return {"text": "# Error\nDocumentation file not found.\nChecked paths:\n" + "\n".join(debug_paths)}
            
        return {"text": docs_path.read_text(encoding="utf-8")}
    except Exception as e:
        return {"text": f"# Error\nFailed to load documentation: {e}"}

@router.get("/downloads", response_model=list[Package])
async def get_downloads(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    return await api.get_packages()

@router.get("/linkgrabber", response_model=list[Package])
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
    # Manual implementation to ensure directory is set
    pkgs = await api.get_linkgrabber_packages()
    ids = [p.uuid for p in pkgs]
    
    if not ids:
        return {"status": "confirmed", "count": 0}

    # Check for default path setting
    current_settings = settings_manager.load_settings()
    if current_settings.use_default_download_path and current_settings.default_download_path:
        print(f"[Router] Applying default download path: {current_settings.default_download_path}")
        await api.set_download_directory(ids, current_settings.default_download_path)
        # Give JD a moment to apply the change before moving
        await asyncio.sleep(0.2)

    await api.confirm_all_linkgrabber()
    return {"status": "confirmed", "count": len(ids)}

@router.post("/linkgrabber/move")
async def move_to_dl(
    package_ids: list[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    # Check for default path setting
    current_settings = settings_manager.load_settings()
    if current_settings.use_default_download_path and current_settings.default_download_path:
        print(f"[Router] Applying default download path to selected: {current_settings.default_download_path}")
        await api.set_download_directory(package_ids, current_settings.default_download_path)
        await asyncio.sleep(0.2)
        
    await api.move_to_dl(package_ids)
    return {"status": "moved"}

@router.post("/downloads/links", response_model=str)
async def add_links(
    links: list[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    try:
        pkg_id = await api.add_links(links)
        return str(pkg_id)
    except Exception:
        # Buffer if connection failed
        buffer_file = get_buffer_file()
        if not buffer_file.parent.exists():
             buffer_file.parent.mkdir(parents=True, exist_ok=True)
             
        buffer_data = []
        if buffer_file.exists():
            try:
                with open(buffer_file) as f:
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
    package_ids: list[str],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.remove_linkgrabber_packages(package_ids)
    return {"status": "deleted"}

@router.post("/downloads/delete")
async def delete_download_packages(
    package_ids: list[str],
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

from fastapi import File, UploadFile


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

    except Exception:
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
            with open(buffer_file) as f:
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
            with open(buffer_file) as f:
                links = json.load(f)
        except:
            pass

    if not links:
        return {"status": "empty", "message": "Buffer is empty"}

    # Attempt replay
    try:
        # Check help first to fail fast on connection
        await api.get_help() 
        
        count = 0
        for entry in links:
             # Handle package objects
             if isinstance(entry, dict):
                 pkg_links = entry.get("links", [])
                 pkg_name = entry.get("package", "CNL Package")
                 if pkg_links:
                     await api.add_links(pkg_links, package_name=pkg_name)
                     count += 1
             else:
                 # Legacy string link
                 if entry:
                     await api.add_links([entry])
                     count += 1

        with open(buffer_file, "w") as f:
            json.dump([], f)
        return {"status": "replayed", "count": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection Failed: {e!s}")

@router.get("/system/status")
async def get_system_status(
    response: Response,
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)],
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    
    # Check JD Connection
    jd_online = False
    myjd_status = {"online": False, "status": "Unknown"}
    try:
        # Simple check, help or version
        await api.get_help()
        jd_online = True
    except Exception:
        jd_online = False

    if jd_online:
        try:
            # Get detailed MyJD Status
            myjd_status = await api.get_myjd_connection_status()
        except:
             myjd_status = {"online": False, "status": "Unknown (Error)"}

    # Check Buffer (now contains package objects)
    buffer_file = get_buffer_file()
    buffer_count = 0
    if buffer_file.exists():
        try:
            with open(buffer_file) as f:
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
        "buffer_count": buffer_count,
        "myjd_connection": myjd_status
    }

@router.post("/system/restart")
async def restart_system(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.restart_jd()
    return {"status": "restarting"}

@router.post("/system/shutdown")
async def shutdown_system(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    api: Annotated[MockJDownloaderAPI, Depends(deps.get_jd_api)]
):
    await api.shutdown_jd()
    return {"status": "shutting_down"}

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
            with open(buffer_file) as f:
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
        with open(buffer_file) as f:
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
            with open(buffer_file) as f:
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

import re

from fastapi import Form

from src.cnl.decrypter import CNLDecrypter


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
            with open(buffer_file) as f:
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

@router.get("/extension/edge.crx")
async def get_edge_extension():
    """Serve the generated CRX extension for Android."""
    # Robust path resolution for Docker and Local
    # We look for 'static/edge.crx' in the project root (backend/ or /app/)
    
    # 1. Try relative to CWD (works if CWD is correct)
    candidates = [
        Path("static/edge.crx"),
        # 2. Try relative to this file: .../src/api/v1/router.py -> .../static/edge.crx
        # Local: backend/src/api/v1/router.py -> backend/static/edge.crx (4 parents up)
        Path(__file__).resolve().parent.parent.parent.parent / "static" / "edge.crx",
        # Docker: /app/src/api/v1/router.py -> /app/static/edge.crx (4 parents up)
        Path(__file__).resolve().parent.parent.parent.parent / "static" / "edge.crx",
        # Docker absolute path fallback
        Path("/app/static/edge.crx")
    ]

    crx_path = None
    for p in candidates:
        if p.exists():
            crx_path = p
            break
            
    if not crx_path:
        raise HTTPException(status_code=404, detail="Extension file not found")

    return FileResponse(
        path=crx_path, 
        filename="edge.crx", 
        media_type="application/x-chrome-extension",
        headers={"Content-Disposition": "attachment; filename=edge.crx"}
    )

@router.get("/extension/edge.zip")
async def get_edge_extension_zip():
    """Serve the zipped extension for Android."""
    candidates = [
        Path("static/edge.zip"),
        Path(__file__).resolve().parent.parent.parent.parent / "static" / "edge.zip",
        Path("/app/static/edge.zip")
    ]

    zip_path = None
    for p in candidates:
        if p.exists():
            zip_path = p
            break
            
    if not zip_path:
        raise HTTPException(status_code=404, detail="Extension zip not found")

    return FileResponse(
        path=zip_path, 
        filename="edge.zip", 
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=edge.zip"}
    )

@router.get("/browser-extension.zip")
async def get_browser_extension_zip():
    """Serve the zipped browser extension source code."""
    candidates = [
        Path("static/browser-extension.zip"),
        Path(__file__).resolve().parent.parent.parent.parent / "static" / "browser-extension.zip",
        Path("/app/static/browser-extension.zip")
    ]

    zip_path = None
    for p in candidates:
        if p.exists():
            zip_path = p
            break
            
    if not zip_path:
        raise HTTPException(status_code=404, detail="Browser extension zip not found")

    return FileResponse(
        path=zip_path, 
        filename="browser-extension.zip", 
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=browser-extension.zip"}
    )
