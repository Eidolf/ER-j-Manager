from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from src.api.v1.router import router as api_router
from src.core.config import settings

# Telemetry Setup
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

import asyncio
import json
import logging



from src.infrastructure.local_jd_api import LocalJDownloaderAPI

logger = logging.getLogger(__name__)



background_tasks = set()

from pathlib import Path


# Helper (duplicated but safe for now or could be imported)
# src/main.py -> src -> backend
def get_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"

async def check_and_replay_links():
    buffer_file = get_data_dir() / "link_buffer.json"

    logger.info(f"CNL Replay Task Started. Buffer: {buffer_file}")
    
    # Use settings_manager to get current URL (including runtime changes)
    from src.infrastructure.settings_manager import settings_manager
    current_settings = settings_manager.load_settings()
    api = LocalJDownloaderAPI(current_settings.api_url)
    
    
    # DLC Buffer Setup
    buffer_dir = get_data_dir() / "buffer"
    if not buffer_dir.exists():
        buffer_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        await asyncio.sleep(5)
        try:
            # Check if JD is online (local API reachable)
            is_online = False
            try:
                # Use the robust status check we implemented
                status = await api.get_myjd_connection_status()
                # If we get a valid status (even if "MyJD Not Connected" or "Device: ..."), 
                # it means the LOCAL API is responding, which is all we need to add links.
                # Use specific check: if config is reachable, we are good.
                if status: 
                     # Check if we got a valid dict response
                     if isinstance(status, dict) and (status.get("online") or "Device" in status.get("status", "")):
                        is_online = True
                     elif "status" in status: # Fallback
                        is_online = True
            except Exception as e:
                logger.debug(f"Replayer online check failed: {e}")
                pass
                
            if is_online:
                # 1. Process Link Buffer (now contains package objects)
                if buffer_file.exists():
                    buffer_data = []
                    try:
                        with open(buffer_file) as f:
                            buffer_data = json.load(f)
                    except:
                        pass
                    
                    if buffer_data:
                        logger.info(f"JD Online. Replaying {len(buffer_data)} buffered packages...")
                        all_success = True
                        for entry in buffer_data:
                            # Handle both old format (list of strings) and new format (package objects)
                            if isinstance(entry, dict):
                                pkg_name = entry.get("package", "CNL Package")
                                links = entry.get("links", [])
                            else:
                                # Legacy: plain string (single link)
                                pkg_name = None
                                links = [entry] if isinstance(entry, str) else entry
                            
                            if links:
                                # Sanitize links to prevent TypeError if buffer contains objects
                                # (e.g. from older bugs or malformed data)
                                sanitized_links = []
                                for link_item in links:
                                    if isinstance(link_item, str):
                                        sanitized_links.append(link_item)
                                    elif isinstance(link_item, dict) and "url" in link_item:
                                        sanitized_links.append(str(link_item["url"]))
                                    # Ignore others
                                links = sanitized_links
                                
                                if not links:
                                    # If no valid links left, mark as success so we don't retry empty forever
                                    continue

                                try:
                                    res = await api.add_links(links, package_name=pkg_name)
                                    if "ok" not in res and "success" not in res:
                                        logger.error(f"Replay failed for {pkg_name}: {res}")
                                        all_success = False
                                except Exception as e:
                                    logger.error(f"Failed to replay package {pkg_name}: {e}")
                                    all_success = False
                        
                        if all_success:
                            with open(buffer_file, "w") as f:
                                json.dump([], f)
                            logger.info("Link Buffer cleared.")

                # 2. Process DLC Buffer
                if os.path.exists(buffer_dir):
                    for filename in os.listdir(buffer_dir):
                        if filename.endswith(".dlc"):
                            file_path = os.path.join(buffer_dir, filename)
                            logger.info(f"Replaying buffered DLC: {filename}")
                            try:
                                with open(file_path, "rb") as f:
                                    content = f.read()
                                res = await api.add_dlc(content)
                                if res == "ok":
                                    os.remove(file_path)
                                    logger.info(f"DLC {filename} replayed and removed.")
                            except Exception as e:
                                logger.error(f"Failed to replay DLC {filename}: {e}")

        except Exception as e:
            logger.error(f"Replay Task Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    
    # 1. Start Replay Loop
    task = asyncio.create_task(check_and_replay_links())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount CNL Receiver for Remote Extension Access
import src.cnl.receiver
app.mount("/cnl", src.cnl.receiver.app)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def readiness_check():
    return {"status": "ready"}

@app.get("/cwd")
def get_cwd():
    return {"cwd": os.getcwd(), "files": os.listdir(".")}

# PWA Share Target Support - Must be before static mount
@app.get("/share-target")
async def share_target():
    """
    Serve the main SPA for the share target route so the frontend router can handle it.
    This is required because the PWA manifests points to /share-target which might not exist as a file.
    """
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html", media_type="text/html")
    # Fallback for local dev if static doesn't exist (though usually run via Vite there)
    return {"message": "Share Target: Frontend not served statically here"}

import os

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mount static files if they exist (prod/docker)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

FastAPIInstrumentor.instrument_app(app)
