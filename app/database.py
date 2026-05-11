from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Ensure the directory for a SQLite file exists (creates `/app/data` etc. before connect)."""
    if ":memory:" in database_url or not database_url.startswith("sqlite"):
        return
    try:
        u = make_url(database_url)
    except Exception:
        return
    if u.drivername != "sqlite" or not u.database or u.database == ":memory:":
        return
    path = Path(u.database)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
_ensure_sqlite_parent_dir(settings.database_url)
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Import models before create_all so SQLAlchemy registers their metadata.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
