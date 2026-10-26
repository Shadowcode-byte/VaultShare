from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# check_same_thread only matters for SQLite (used in local/dev testing);
# harmless to pass for Postgres since it's ignored there via connect_args guard.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

# SQLite does NOT enforce foreign key constraints by default — Postgres
# (this project's production target) always does. Without this, a bug
# that violates a foreign key (e.g. deleting a row another table still
# references) would pass every test against the SQLite dev database
# and only surface for the first time in production. This makes local
# testing actually catch that class of bug instead of hiding it.
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
