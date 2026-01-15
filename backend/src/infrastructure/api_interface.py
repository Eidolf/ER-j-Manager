from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import Package

class JDownloaderAPI(ABC):
    @abstractmethod
    async def get_packages(self) -> List[Package]:
        """Retrieve list of packages."""
        pass

    @abstractmethod
    async def get_linkgrabber_packages(self) -> List[Package]:
        """Retrieve list of packages from LinkGrabber."""
        pass

    @abstractmethod
    async def add_links(self, links: List[str]) -> str:
        """Add links and return a package/link ID."""
        pass

    @abstractmethod
    async def start_downloads(self) -> None:
        """Start all downloads."""
        pass

    @abstractmethod
    async def stop_downloads(self) -> None:
        """Stop all downloads."""
        pass

    @abstractmethod
    async def set_download_directory(self, package_ids: List[str], directory: str) -> None:
        pass

    @abstractmethod
    async def add_dlc(self, file_content: bytes) -> str:
        pass
