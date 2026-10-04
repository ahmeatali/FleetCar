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
                if "color" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN color VARCHAR;"))
                if "contract_start_date" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN contract_start_date VARCHAR;"))
                if "contract_end_date" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN contract_end_date VARCHAR;"))
                if "monthly_rent" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN monthly_rent FLOAT;"))
                if "monthly_km_limit" not in veh_columns:
                    conn.execute(text("ALTER TABLE vehicles ADD COLUMN monthly_km_limit INTEGER;"))
                optional_vehicle_columns = {
                    "version": "VARCHAR", "engine_no": "VARCHAR", "horsepower": "INTEGER",
                    "cylinder_count": "INTEGER", "transmission": "VARCHAR", "seat_count": "INTEGER",
                    "trunk_volume_l": "INTEGER", "tire_size": "VARCHAR", "registration_date": "VARCHAR",
                    "traffic_insurance_policy_no": "VARCHAR", "traffic_insurance_expiry_date": "VARCHAR",
                    "casco_policy_no": "VARCHAR", "casco_insurance_expiry_date": "VARCHAR",
                    "hgs_no": "VARCHAR", "hgs_balance": "FLOAT", "hgs_last_reload_date": "VARCHAR",
                    "hgs_active": "BOOLEAN DEFAULT 0", "delivery_date": "VARCHAR", "delivered_by": "VARCHAR",
                    "received_by": "VARCHAR", "delivery_location": "VARCHAR", "delivery_notes": "TEXT",
                    "contract_no": "VARCHAR", "contract_duration_months": "INTEGER", "contract_committed_km": "INTEGER",
                    "contract_signed_at": "VARCHAR", "erp_id": "VARCHAR", "assignment_user": "VARCHAR",
                    "operating_company": "VARCHAR", "vehicle_group": "VARCHAR", "current_month_km": "INTEGER",
                    "next_service_due_date": "VARCHAR", "next_service_due_km": "INTEGER", "gps_latitude": "FLOAT",
                    "gps_longitude": "FLOAT", "gps_location_label": "VARCHAR", "gps_last_seen_at": "VARCHAR"
                }
                with engine.begin() as conn:
                    for column_name, column_type in optional_vehicle_columns.items():
                        if column_name not in veh_columns:
                            conn.execute(text(f"ALTER TABLE vehicles ADD COLUMN {column_name} {column_type};"))

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

        if "tire_records" in inspector.get_table_names():
            tire_columns = [c["name"] for c in inspector.get_columns("tire_records")]
            with engine.begin() as conn:
                if "inspected_at" not in tire_columns:
                    conn.execute(text("ALTER TABLE tire_records ADD COLUMN inspected_at VARCHAR;"))
                if "tread_depth_mm" not in tire_columns:
                    conn.execute(text("ALTER TABLE tire_records ADD COLUMN tread_depth_mm FLOAT;"))

        if "requests" in inspector.get_table_names():
            request_columns = [c["name"] for c in inspector.get_columns("requests")]
            if "completed_at" not in request_columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE requests ADD COLUMN completed_at VARCHAR;"))

        if "customer_portal_users" in inspector.get_table_names():
            user_columns = [c["name"] for c in inspector.get_columns("customer_portal_users")]
            if "password_hash" not in user_columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE customer_portal_users ADD COLUMN password_hash VARCHAR;"))
    except Exception as e:
        print(f"[MIGRATION LOG] Auto-migration check: {e}")


def seed():
    """Veritabanı tabloları oluşturulur. Test verileri eklenmez."""
    pass
