#!/usr/bin/env python3
"""
FleetCar — Admin Kullanıcısı Oluşturma Scripti
Kullanımı:
  python create_admin.py --email admin@fleetcar.com --password secretpassword
"""

import sys
import io
import argparse
import datetime

# Safe terminal encoding configuration
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

from app.database import SessionLocal, engine
from app import models
from app.auth import hash_password

def main():
    parser = argparse.ArgumentParser(description="FleetCar Yonetici Hesabi Olusturucu")
    parser.add_argument("--email", help="Yonetici E-posta Adresi")
    parser.add_argument("--password", help="Yonetici Sifresi")

    args = parser.parse_args()

    # Tablolari olustur
    models.Base.metadata.create_all(bind=engine)

    email = args.email
    if not email:
        email = input("Yonetici E-posta Adresi: ").strip()

    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Yonetici Sifresi: ").strip()

    if not email or not password:
        print("[HATA] E-posta adresi ve sifre bos birakilamaz!")
        sys.exit(1)

    db = SessionLocal()
    try:
        email_clean = email.lower().strip()
        existing = db.query(models.AdminUser).filter(models.AdminUser.email == email_clean).first()
        
        hashed = hash_password(password)

        if existing:
            existing.password_hash = hashed
            db.commit()
            print(f"[BASARILI] [{email_clean}] yoneticisinin sifresi basariyla guncellendi!")
        else:
            new_admin = models.AdminUser(
                email=email_clean,
                password_hash=hashed,
                created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.add(new_admin)
            db.commit()
            print(f"[BASARILI] [{email_clean}] yoneticisi basariyla veritabanina olusturuldu!")

    except Exception as e:
        db.rollback()
        err_msg = str(e).encode('ascii', errors='backslashreplace').decode('ascii')
        print(f"[HATA] Veritabani hatasi: {err_msg}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
