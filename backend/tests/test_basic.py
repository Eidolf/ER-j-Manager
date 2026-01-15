"""Basic tests for the JDownloader Manager API."""


def test_health_check():
    """Test that the app can be imported and basic settings work."""
    from src.core.config import settings
    
    assert settings.PROJECT_NAME == "JDownloader 2 Manager"
    assert settings.API_V1_STR == "/api/v1"


def test_security_module():
    """Test password hashing works correctly."""
    from src.core.security import get_password_hash, verify_password
    
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)
