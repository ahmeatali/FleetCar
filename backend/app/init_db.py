from sqlalchemy import inspect, text
from .database import engine, SessionLocal
from . import models


def create_tables():
    models.Base.metadata.create_all(bind=engine)
    
    # Auto-migration for SQLite missing columns on existing databases
    try:
        inspector = inspect(engine)
        if "suppliers" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("suppliers")]
            with engine.begin() as conn:
                if "email" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN email VARCHAR;"))
                if "password_hash" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN password_hash VARCHAR;"))
                if "invitation_token" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN invitation_token VARCHAR;"))
                if "invitation_status" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN invitation_status VARCHAR DEFAULT 'Davet Edilmedi';"))
    except Exception as e:
        print(f"[MIGRATION LOG] Auto-migration check: {e}")


def seed():
    """Veritabanı tabloları oluşturulur. Test verileri eklenmez."""
    pass
