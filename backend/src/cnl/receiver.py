import json
import logging

from fastapi import FastAPI, Form, Response
from fastapi.middleware.cors import CORSMiddleware

from .decrypter import CNLDecrypter

# Setup Logging
logger = logging.getLogger("CNLReceiver")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="JDownloader CNL Receiver")

# 1. Enable CORS for all domains (CNL requirement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path

# Robust Path Resolution
# receiver.py is in backend/src/cnl/
# We want backend/data/
BASE_DIR = Path(__file__).resolve().parent.parent.parent # backend/src/cnl -> backend/src -> backend
DATA_DIR = BASE_DIR / "data"
BUFFER_FILE = DATA_DIR / "link_buffer.json"

if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# 2. Flash Helper Check
@app.get("/flash/check")
async def flash_check():
    # JD returns "JDownloader"
    return Response(content="JDownloader", media_type="text/plain")

@app.get("/flash")
async def flash_check_root():
    return Response(content="JDownloader", media_type="text/plain")

@app.get("/jdcheck.js")
async def jdcheck_js():
    return Response(content="jdownloader=true;", media_type="application/javascript")
    
# 3. Crossdomain Policy (Flash legacy but sometimes checked)
@app.get("/crossdomain.xml")
async def crossdomain():
    content = """<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
<allow-access-from domain="*" />
</cross-domain-policy>"""
    return Response(content=content, media_type="application/xml")

# 4. Add Crypted Links
@app.post("/flash/addcrypted")
@app.post("/flash/addcrypted2")
@app.post("/flash/add")
async def add_crypted(
    crypted: str = Form(...),
    jk: str = Form(...),
    passwords: str | None = Form(None),
    source: str | None = Form(None),
    package: str | None = Form(None)  # Package name for grouping
):
    print(f"DEBUG: Received CNL payload from {source}, package: {package}")
    logger.info(f"Received CNL payload. Source: {source}, Package: {package}")
    
    # 1. Extract Key from JK (Javascript Key)
    # Simple regex extraction for standard "return 'HEX'" pattern
    import re
    key_match = re.search(r"return ['\"]([0-9a-fA-F]+)['\"]", jk)
    if not key_match:
        print("DEBUG: Could not extract key from JK")
        logger.error("Could not extract key from JK")
        return Response(content="failed", status_code=400)
    
    key = key_match.group(1)
    
    # 2. Decrypt
    decrypted_text = CNLDecrypter.decrypt(crypted, key)
    if not decrypted_text:
        print("DEBUG: Decryption failed")
        logger.error("Decryption failed")
        return Response(content="failed", status_code=400)
        
    links = CNLDecrypter.extract_links(decrypted_text)
    print(f"DEBUG: Decrypted {len(links)} links for package '{package}'")
    logger.info(f"Decrypted {len(links)} links.")
    
    # 3. Buffer Links (as structured package)
    buffer_data = []
    if BUFFER_FILE.exists():
        try:
            with open(BUFFER_FILE) as f:
                buffer_data = json.load(f)
        except:
            buffer_data = []
    
    # Store as package object for grouped replay
    # Format: {"package": "name", "links": [...], "passwords": "..."}
    package_entry = {
        "package": package or source or "CNL Package",
        "links": links,
        "passwords": passwords
    }
    buffer_data.append(package_entry)
    
    try:
        with open(BUFFER_FILE, "w") as f:
            json.dump(buffer_data, f)
        print("DEBUG: Links buffered successfully")
    except Exception as e:
        print(f"DEBUG: Failed to write to buffer: {e}")
        
    logger.info("Links buffered.")
    
    # 4. Trigger Cross-Origin Success (Pixel/Iframe response)
    # JD usually just returns success.
    # Return "success" text
    return Response(content="success", media_type="text/plain")

@app.get("/health")
def health():
    return {"status": "running"}
