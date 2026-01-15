"""Basic tests for the JDownloader Manager API."""


def test_health_check():
    """Test that the app can be imported and basic settings work."""
    from src.core.config import settings
    
    assert settings.PROJECT_NAME == "JDownloader 2 Manager"
    assert settings.API_V1_STR == "/api/v1"


def test_token_creation():
    """Test JWT token creation works."""
    from src.core.security import create_access_token
    from datetime import timedelta
    
    token = create_access_token(data={"sub": "testuser"}, expires_delta=timedelta(minutes=5))
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long
