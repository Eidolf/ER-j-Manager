
import asyncio
from src.infrastructure.mock_jd_api import MockJDownloaderAPI
from src.api.v1.router import get_system_status

async def test_status():
    api = MockJDownloaderAPI()
    status = await get_system_status(api)
    print(f"Status Response: {status}")
    assert "myjd_connection" in status
    assert status["myjd_connection"]["status"] == "Connected (Mock)"
    print("Verification Successful!")

if __name__ == "__main__":
    asyncio.run(test_status())
