from sqlalchemy import inspect, text
from .database import engine, SessionLocal
from . import models


def create_tables():
    models.Base.metadata.create_all(bind=engine)
    
    # Auto-migration for SQLite missing columns on existing databases
    try:
        inspector = inspect(engine)
        if "admin_users" in inspector.get_table_names():
            admin_columns = [c["name"] for c in inspector.get_columns("admin_users")]
            with engine.begin() as conn:
                if "reset_token" not in admin_columns:
                    conn.execute(text("ALTER TABLE admin_users ADD COLUMN reset_token VARCHAR;"))
                if "reset_token_expires" not in admin_columns:
                    conn.execute(text("ALTER TABLE admin_users ADD COLUMN reset_token_expires VARCHAR;"))

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
                if "is_email_verified" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN is_email_verified BOOLEAN DEFAULT 1;"))
                conn.execute(text("UPDATE suppliers SET is_email_verified = 1 WHERE is_email_verified IS NULL OR is_email_verified = 0;"))
                if "verification_token" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN verification_token VARCHAR;"))
                if "reset_token" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN reset_token VARCHAR;"))
                if "reset_token_expires" not in columns:
                    conn.execute(text("ALTER TABLE suppliers ADD COLUMN reset_token_expires VARCHAR;"))

        if "vehicles" in inspector.get_table_names():
            veh_columns = [c["name"] for c in inspector.get_columns("vehicles")]
            with engine.begin() as conn:
                if "gps_device_id" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN gps_device_id VARCHAR;"))
                if "utts_code" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN utts_code VARCHAR;"))

        if "customers" in inspector.get_table_names():
            cust_columns = [c["name"] for c in inspector.get_columns("customers")]
            with engine.begin() as conn:
                if "password_hash" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN password_hash VARCHAR;"))
                if "invitation_token" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN invitation_token VARCHAR;"))
                if "invitation_status" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN invitation_status VARCHAR DEFAULT 'Davet Edilmedi';"))
                if "documents_uploaded" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN documents_uploaded BOOLEAN DEFAULT 0;"))
                if "documents" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN documents JSON DEFAULT '{}';"))
                if "is_email_verified" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN is_email_verified BOOLEAN DEFAULT 1;"))
                conn.execute(text("UPDATE customers SET is_email_verified = 1 WHERE is_email_verified IS NULL OR is_email_verified = 0;"))
                if "verification_token" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN verification_token VARCHAR;"))
                if "reset_token" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN reset_token VARCHAR;"))
                if "reset_token_expires" not in cust_columns:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN reset_token_expires VARCHAR;"))

        if "quotes" in inspector.get_table_names():
            quote_columns = [c["name"] for c in inspector.get_columns("quotes")]
            with engine.begin() as conn:
                if "items" not in quote_columns:
                    conn.execute(text("ALTER TABLE quotes ADD COLUMN items JSON DEFAULT '[]';"))
                if "details" not in quote_columns:
                    conn.execute(text("ALTER TABLE quotes ADD COLUMN details JSON DEFAULT '{}';"))
    except Exception as e:
        print(f"[MIGRATION LOG] Auto-migration check: {e}")


def seed():
    """Veritabanı tabloları oluşturulur. Test verileri eklenmez."""
    pass
