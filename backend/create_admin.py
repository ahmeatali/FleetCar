#!/usr/bin/env python3
"""
FleetCar — Admin Kullanıcısı Oluşturma Scripti
Kullanımı:
  1. İnteraktif olarak:
     python create_admin.py

  2. Parametreler ile:
     python create_admin.py --email admin@fleetcar.com --password yoursecretpassword
"""

import sys
import argparse
import datetime
from app.database import SessionLocal, engine
from app import models
from app.auth import hash_password

def main():
    parser = argparse.ArgumentParser(description="FleetCar Yönetici Hesabı Oluşturucu")
    parser.add_argument("--email", help="Yönetici E-posta Adresi")
    parser.add_argument("--password", help="Yönetici Şifresi")

    args = parser.parse_args()

    # Tabloları oluştur
    models.Base.metadata.create_all(bind=engine)

    email = args.email
    if not email:
        email = input("🔑 Yönetici E-posta Adresi: ").strip()

    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("🔒 Yönetici Şifresi: ").strip()

    if not email or not password:
        print("❌ E-posta adresi ve şifre boş bırakılamaz!")
        sys.exit(1)

    db = SessionLocal()
    try:
        email_clean = email.lower().strip()
        existing = db.query(models.AdminUser).filter(models.AdminUser.email == email_clean).first()
        
        hashed = hash_password(password)

        if existing:
            existing.password_hash = hashed
            db.commit()
            print(f"✅ [{email_clean}] e-postasına sahip yöneticinin şifresi başarıyla güncellendi!")
        else:
            new_admin = models.AdminUser(
                email=email_clean,
                password_hash=hashed,
                created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            db.add(new_admin)
            db.commit()
            print(f"🎉 [{email_clean}] yöneticisi başarıyla veritabanına oluşturuldu!")

    except Exception as e:
        db.rollback()
        print(f"❌ Hata oluştu: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
