import asyncio
import random
from typing import List, Dict
from uuid import UUID, uuid4
from src.domain.models import Package, Link, DownloadStatus
from src.infrastructure.api_interface import JDownloaderAPI

class MockJDownloaderAPI(JDownloaderAPI):
    def __init__(self):
        self._packages: Dict[str, Package] = {}
        # Seed some data
        self._seed_data()
        
    def _seed_data(self):
        pkg_id = str(uuid4())
        self._packages[pkg_id] = Package(
            uuid=pkg_id,
            name="Ubuntu 24.04 ISO",
            links=[
                Link(uuid=str(uuid4()), name="ubuntu-24.04-desktop-amd64.iso", url="https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso", host="releases.ubuntu.com", bytes_total=4900000000, bytes_loaded=1200000000, status=DownloadStatus.RUNNING, speed=5200000),
                Link(uuid=str(uuid4()), name="SHA256SUMS", url="https://releases.ubuntu.com/24.04/SHA256SUMS", host="releases.ubuntu.com", bytes_total=1024, bytes_loaded=1024, status=DownloadStatus.FINISHED)
            ]
        )
        
        pkg_id_2 = str(uuid4())
        self._packages[pkg_id_2] = Package(
            uuid=pkg_id_2,
            name="Cyberpunk Assets Pack",
            links=[
                Link(uuid=str(uuid4()), name="neon_city_v2.zip", url="https://assets.example.com/neon.zip", host="assets.example.com", bytes_total=150000000, status=DownloadStatus.PAUSED)
            ]
        )

    async def get_packages(self) -> List[Package]:
        # Simulate network latency
        await asyncio.sleep(0.1)
        return list(self._packages.values())

    async def get_linkgrabber_packages(self) -> List[Package]:
        await asyncio.sleep(0.1)
        # return dummy linkgrabber item
        return [
            Package(
                uuid=str(uuid4()),
                name="LinkGrabber: Collected Links",
                status=DownloadStatus.STOPPED,
                total_bytes=0,
                loaded_bytes=0,
                links=[]
            )
        ]

    async def add_links(self, links: List[str], package_name: str = "New Package"):
        await asyncio.sleep(0.2)
        pkg_id = str(uuid4())
        new_links = []
        for url in links:
            new_links.append(Link(uuid=str(uuid4()), name=url.split("/")[-1] or "file", url=url, host="unknown", bytes_total=random.randint(1000000, 100000000)))
            
        self._packages[pkg_id] = Package(uuid=pkg_id, name=package_name, links=new_links)
        return pkg_id

    async def start_downloads(self):
        for pkg in self._packages.values():
            for link in pkg.links:
                if link.status == DownloadStatus.PAUSED or link.status == DownloadStatus.STOPPED:
                    link.status = DownloadStatus.RUNNING
    
    async def stop_downloads(self):
        for pkg in self._packages.values():
            for link in pkg.links:
                if link.status == DownloadStatus.RUNNING:
                    link.status = DownloadStatus.STOPPED

    async def confirm_all_linkgrabber(self) -> None:
        # Move all linkgrabber items to main list (mock behavior: just clear list or move)
        # For simplicity, we just clear the list in mock or log it
        pass

    async def move_to_dl(self, package_ids: List[str]) -> None:
        # Mock move
        pass

    async def get_help(self) -> str:
        return """
        Mock JDownloader API v1.0
        -------------------------
        Available namespaces:
        - linkgrabberv2
        - downloadsV2
        - downloadcontroller
        ...
        """

    async def remove_linkgrabber_packages(self, package_ids: List[str]) -> None:
        # Mock remove
        pass

    async def remove_download_packages(self, package_ids: List[str]) -> None:
        # Mock remove
        pass

    async def set_download_directory(self, package_ids: List[str], directory: str) -> None:
        pass

    async def add_dlc(self, file_content: bytes) -> str:
        return "ok"

jd_api = MockJDownloaderAPI()
