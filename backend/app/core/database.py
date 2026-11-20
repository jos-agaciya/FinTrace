import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# SQLite needs check_same_thread=False for multithreaded FastAPI workers
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and settings.APP_ENV == "development"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables with safe column migrations for SQLite."""
    import backend.app.models.claim
    import backend.app.models.evidence
    import backend.app.models.analysis
    import backend.app.models.decision
    import backend.app.models.assessment

    Base.metadata.create_all(bind=engine)

    # Safe SQLite migration helper for new evidence columns
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                table_info = conn.execute(text("PRAGMA table_info(evidence);")).fetchall()
                existing_cols = {row[1] for row in table_info}

                new_columns = [
                    ("document_title", "VARCHAR(512)"),
                    ("company_symbol", "VARCHAR(32)"),
                    ("company_isin", "VARCHAR(32)"),
                    ("source_jurisdiction", "VARCHAR(16) DEFAULT 'IN'"),
                    ("exchange", "VARCHAR(32) DEFAULT 'NSE'")
                ]

                for col_name, col_type in new_columns:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE evidence ADD COLUMN {col_name} {col_type};"))
                conn.commit()
            except Exception:
                # Table may not yet be initialized or not an SQLite dialect
                pass
