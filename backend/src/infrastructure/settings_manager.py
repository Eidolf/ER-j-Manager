import json
import os

from pydantic import BaseModel

from src.core.config import settings as app_settings

SETTINGS_FILE = "data/settings.json"

class JDSettings(BaseModel):
    jd_host: str = "127.0.0.1"
    jd_port: int = 3128
    use_mock: bool = False
    admin_password: str = "admin"
    default_download_path: str = ""
    use_default_download_path: bool = False

    @property
    def api_url(self) -> str:
        # Clean host if user added protocol
        clean_host = self.jd_host.replace("http://", "").replace("https://", "").rstrip("/")
        return f"http://{clean_host}:{self.jd_port}"

class SettingsManager:
    def __init__(self):
        self.file_path = SETTINGS_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            # Create default settings
            default_settings = JDSettings(
                jd_host="127.0.0.1",
                jd_port=3128,
                use_mock=app_settings.USE_MOCK_API, # Use env var as initial default
                admin_password="admin"
            )
            self.save_settings(default_settings)

    def load_settings(self) -> JDSettings:
        try:
            with open(self.file_path) as f:
                data = json.load(f)
            return JDSettings(**data)
        except Exception:
            # Fallback
            return JDSettings()

    def save_settings(self, settings: JDSettings):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(settings.model_dump(), f, indent=4)

settings_manager = SettingsManager()
