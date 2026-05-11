from app.config import Settings


def test_development_prefers_database_url_local():
    s = Settings(
        _env_file=None,
        environment="development",
        database_url="sqlite:////app/data/assistant.db",
        database_url_local="sqlite:///./local_override.db",
    )
    assert s.database_url == "sqlite:///./local_override.db"


def test_production_ignores_database_url_local():
    s = Settings(
        _env_file=None,
        environment="production",
        database_url="sqlite:////app/data/assistant.db",
        database_url_local="sqlite:///./ignored.db",
    )
    assert s.database_url == "sqlite:////app/data/assistant.db"


def test_development_falls_back_when_local_empty():
    s = Settings(
        _env_file=None,
        environment="dev",
        database_url="sqlite:////app/data/assistant.db",
        database_url_local="",
    )
    assert s.database_url == "sqlite:////app/data/assistant.db"
