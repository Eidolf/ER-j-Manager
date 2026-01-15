import httpx
from typing import List
from src.domain.models import Package, Link, DownloadStatus
from src.infrastructure.api_interface import JDownloaderAPI

class LocalJDownloaderAPI(JDownloaderAPI):
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def _query_links(self, endpoint: str) -> List[dict]:
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "packageUUIDs": [], 
                    "metaInfo": True,
                    "status": True,
                    "bytesTotal": True,
                    "bytesLoaded": True,
                    "url": True,
                    "priority": True,
                    "eta": True
                }
                resp = await client.post(f"{self.base_url}/{endpoint}", json=params)
                if resp.status_code != 200:
                    return []
                return resp.json().get("data", [])
            except:
                return []

    async def _query_packages(self, endpoint: str) -> List[Package]:
        # Determine link endpoint based on package endpoint
        link_endpoint = "downloadsV2/queryLinks" if "downloads" in endpoint else "linkgrabberv2/queryLinks"
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. Fetch Packages
                pkg_params = {
                    "saveTo": True,
                    "childCount": True,
                    "hosts": True,
                    "status": True,
                    "bytesTotal": True,
                    "bytesLoaded": True,
                    "speed": True
                }
                pkg_resp = await client.post(f"{self.base_url}/{endpoint}", json=pkg_params)
                if pkg_resp.status_code != 200:
                    raise Exception(f"JD API Status {pkg_resp.status_code}")
                
                pkg_data = pkg_resp.json().get("data", [])

                # 2. Fetch Links (to populate children)
                raw_links = await self._query_links(link_endpoint)
                
                # Group links by packageUUID
                links_by_pkg = {}
                for l in raw_links:
                    pid = str(l.get("packageUUID", "0"))
                    if pid not in links_by_pkg:
                        links_by_pkg[pid] = []
                    
                    links_by_pkg[pid].append(Link(
                        uuid=str(l.get("uuid", "0")),
                        name=l.get("name", "Unknown"),
                        url=l.get("url", ""),
                        host=l.get("host", ""),
                        bytes_total=l.get("bytesTotal", 0),
                        bytes_loaded=l.get("bytesLoaded", 0),
                        status=DownloadStatus.FINISHED if l.get("finished", False) else DownloadStatus.RUNNING, # Simplified
                        speed=l.get("speed", 0),
                        eta=l.get("eta", None)
                    ))

                packages = []
                for p in pkg_data:
                    uuid = str(p.get("uuid", "0"))
                    pk = Package(
                        uuid=uuid,
                        name=p.get("name", "Unknown"),
                        status=DownloadStatus.RUNNING if p.get("enabled", True) else DownloadStatus.STOPPED,
                        total_bytes=p.get("bytesTotal", 0),
                        loaded_bytes=p.get("bytesLoaded", 0),
                        child_count=p.get("childCount", 0),
                        links=links_by_pkg.get(uuid, [])
                    )
                    packages.append(pk)
                return packages
            except httpx.RequestError as e:
                print(f"JD API Connection Error ({endpoint}): {str(e)}")
                raise Exception(f"Connection Failed: {str(e)}")
            except Exception as e:
                print(f"JD API Unexpected Error ({endpoint}): {str(e)}")
                raise

    async def get_packages(self) -> List[Package]:
        return await self._query_packages("downloadsV2/queryPackages")

    async def get_linkgrabber_packages(self) -> List[Package]:
        return await self._query_packages("linkgrabberv2/queryPackages")

    async def add_links(self, links: List[str], package_name: str = None) -> str:
        async with httpx.AsyncClient() as client:
            endpoint = "/linkgrabberv2/addLinks"
            payload = {
                "links": "\n".join(links),
                "autostart": False, # User requested no autostart
                "deepDecrypt": True,
                "packageName": package_name  # Optional package name for grouping
            }
            try:
                print(f"[JD-API] Adding Links: {self.base_url}{endpoint} | Package: {package_name}")
                resp = await client.post(f"{self.base_url}{endpoint}", json=payload)
                print(f"[JD-API] Add Links Response: {resp.status_code} | {resp.text}")
                
                if resp.status_code != 200:
                     print("[JD-API] Fallback to linkcollector/addLinks")
                     resp = await client.post(f"{self.base_url}/linkcollector/addLinks", params={
                        "links": ",".join(links),
                        "autostart": False,
                        "deepDecrypt": True
                     })
                     print(f"[JD-API] Fallback Response: {resp.status_code} | {resp.text}")

                return "ok" if resp.status_code == 200 else f"error: {resp.text}"
            except Exception as e:
                print(f"[JD-API] Add Links Exception: {e}")
                raise e

    async def start_downloads(self) -> None:
        async with httpx.AsyncClient() as client:
            print(f"[JD-API] Starting Downloads: {self.base_url}/downloadcontroller/start")
            resp = await client.post(f"{self.base_url}/downloadcontroller/start")
            print(f"[JD-API] Start Response: {resp.status_code} | {resp.text}")
            return resp.json()

    async def stop_downloads(self) -> None:
        async with httpx.AsyncClient() as client:
            print(f"[JD-API] Stopping Downloads: {self.base_url}/downloadcontroller/stop")
            resp = await client.post(f"{self.base_url}/downloadcontroller/stop")
            print(f"[JD-API] Stop Response: {resp.status_code} | {resp.text}")

    async def move_to_dl(self, package_ids: List[str]) -> None:
        async with httpx.AsyncClient() as client:
            current_pkgs = await self.get_linkgrabber_packages()
            print(f"[JD-API] Debug - Available LinkGrabber IDs: {[p.uuid for p in current_pkgs]}")
            
            # Convert to ints
            try:
                int_ids = [int(pid) for pid in package_ids]
            except:
                int_ids = []

            # Trial 1: packageIds (int lists), no linkIds
            payloads = [
                {"packageIds": int_ids, "startDownloads": True},
                {"packageIds": int_ids, "linkIds": [], "startDownloads": True},
                {"packageUUIDs": package_ids, "startDownloads": True}, # Strings
            ]

            for i, p in enumerate(payloads):
                print(f"[JD-API] Move Trial {i+1}: {p}")
                resp = await client.post(f"{self.base_url}/linkgrabberv2/moveToDownloadlist", json=p)
                print(f"[JD-API] Response {i+1}: {resp.status_code} | {resp.text!r}")
                if resp.status_code == 200:
                    return

            print("[JD-API] All Move trials failed.")

    async def confirm_all_linkgrabber(self) -> None:
        async with httpx.AsyncClient() as client:
            pkgs = await self.get_linkgrabber_packages()
            ids = [p.uuid for p in pkgs]
            if ids:
                await self.move_to_dl(ids)

    async def get_help(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/help")
            if resp.status_code != 200:
                raise Exception(f"JD Help Status {resp.status_code}")
            return resp.text

    async def remove_linkgrabber_packages(self, package_ids: List[str]) -> None:
         async with httpx.AsyncClient() as client:
            try:
                int_ids = [int(pid) for pid in package_ids if pid.isdigit()]
            except:
                int_ids = []
            
            # JD API uses RPC style with "params" array matching method signature
            # removeLinks signature: (long[] linkIds, long[] packageIds)
            endpoint = "/linkgrabberv2/removeLinks"
            payload = {"params": [ [], int_ids ]}

            await client.post(f"{self.base_url}{endpoint}", json=payload)

    async def remove_download_packages(self, package_ids: List[str]) -> None:
         async with httpx.AsyncClient() as client:
            try:
                int_ids = [int(pid) for pid in package_ids if pid.isdigit()]
            except:
                int_ids = []

            # downloadsV2/removeLinks(long[] linkIds, long[] packageIds)
            endpoint = "/downloadsV2/removeLinks"
            payload = {"params": [ [], int_ids ]}

            await client.post(f"{self.base_url}{endpoint}", json=payload)

    async def move_to_dl(self, package_ids: List[str]) -> None:
        async with httpx.AsyncClient() as client:
            try:
                int_ids = [int(pid) for pid in package_ids if pid.isdigit()]
            except:
                int_ids = []

            # moveToDownloadlist(long[] linkIds, long[] packageIds)
            endpoint = "/linkgrabberv2/moveToDownloadlist"
            payload = {"params": [ [], int_ids ]}
            
            # We must set startDownloads=True via a separate call or assuming this moves it to list where it starts if global start is on.
            # Actually, moveToDownloadlist just moves. To start we might need logic, but user experience said it started.
            # In V2, moveToDownloadlist usually autostarts if settings allow.
            # Ref: https://my.jdownloader.org/developers/#tag_linkgrabberv2
            
            await client.post(f"{self.base_url}{endpoint}", json=payload)
            # We can also force strict start if needed, but simple move is usually what "Start" means in this context.

    async def set_download_directory(self, package_ids: List[str], directory: str) -> None:
        async with httpx.AsyncClient() as client:
            try:
                int_ids = [int(pid) for pid in package_ids if pid.isdigit()]
            except:
                int_ids = []

            # setDownloadDirectory(String directory, long[] packageIds)
            endpoint = "/linkgrabberv2/setDownloadDirectory"
            payload = {"params": [ directory, int_ids ]}

            await client.post(f"{self.base_url}{endpoint}", json=payload)

    async def add_dlc(self, file_content: bytes) -> str:
        async with httpx.AsyncClient() as client:
            # /linkgrabberv2/addContainer usually takes the raw string content of the DLC if valid
            # Or mapped as "content" param. 
            # Reference: https://my.jdownloader.org/developers/#tag_linkgrabberv2
            # It seems addContainer accepts "String type, String content".
            # "type" is usually "DLC".
            
            # However some JD APIs accept base64. Let's try raw text first as DLC is ASCII/XML-ish but often binary.
            # Actually DLC is encrypted binary. It should be passed as a string (Base64 is safest).
            
            import base64
            b64_content = base64.b64encode(file_content).decode('ascii')
            
            endpoint = "/linkgrabberv2/addContainer"
            # Signature: addContainer(String type, String content)
            payload = {"params": ["DLC", b64_content]}
            
            print(f"[JD-API] Adding DLC: {endpoint}")
            resp = await client.post(f"{self.base_url}{endpoint}", json=payload)
            print(f"[JD-API] Add DLC Response: {resp.status_code} | {resp.text}")
            
            if resp.status_code == 200:
                return "ok"
            else:
                 # Fallback trial: LinkCollector logic?
                 return f"error: {resp.text}"
