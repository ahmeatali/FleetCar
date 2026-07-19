"""
FleetCar — SQLite Seed Data
Tabloları oluşturur ve yoksa başlangıç verilerini ekler (idempotent).
"""
from .database import engine, SessionLocal
from . import models


def create_tables():
    models.Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # Daha önce seed edildiyse tekrar çalıştırma
        if db.query(models.Supplier).count() > 0:
            return

        # ── Suppliers ──────────────────────────────────────────
        suppliers = [
            models.Supplier(id=1, name="OtoPratik Maslak",           type="servis",      phone="+90 212 555 0101", location="Maslak, İstanbul",                  city="İstanbul", district="Maslak",        services=["Periyodik Bakım","Fren Sistemi","Balata Değişimi","Akü Değişimi"],               contract_type="Anlaşmalı"),
            models.Supplier(id=2, name="Borusan Oto Servis",          type="servis",      phone="+90 212 555 0102", location="Avcılar, İstanbul",                  city="İstanbul", district="Avcılar",       services=["Periyodik Bakım","Motor Onarımı","Elektrik Arıza","Garanti Kapsamı"],            contract_type="Yetkili"),
            models.Supplier(id=3, name="Lassa Bayi - Seçkin Oto",     type="lastik",      phone="+90 216 555 0201", location="Kadıköy, İstanbul",                  city="İstanbul", district="Kadıköy",       services=["Lastik Değişimi","Balans Ayarı","Lastik Oteli","Rot Ayarı"],                     contract_type="Yetkili"),
            models.Supplier(id=4, name="Michelin - Uzman Lastik",     type="lastik",      phone="+90 212 555 0202", location="Kağıthane, İstanbul",                city="İstanbul", district="Kağıthane",     services=["Lastik Değişimi","Lastik Oteli","Rot Ayarı","Basınç Kontrolü"],                  contract_type="Anlaşmalı"),
            models.Supplier(id=5, name="7/24 Acil Yol Yardım & Çekici", type="yol_yardim", phone="+90 850 555 0301", location="Tüm Türkiye",                     city="İstanbul", district="Tüm İlçeler",   services=["Çekici Hizmeti","Akü Takviye","Yol Kenarı Yardım","Lastik Tamiri"],             contract_type="Anlaşmalı"),
            models.Supplier(id=6, name="Güven Çekici Hizmetleri",    type="yol_yardim",  phone="+90 850 555 0302", location="Marmara Bölgesi",                    city="Kocaeli",  district="Gebze",         services=["Çekici Hizmeti","Kurtarıcı Hizmeti","Kaza Nakli"],                               contract_type="Yetkili"),
            models.Supplier(id=7, name="Enterprise Filo Kiralama",   type="ikame_arac",  phone="+90 850 555 0401", location="Havalimanları & Merkez Ofisler",      city="Ankara",   district="Çankaya",       services=["Ekonomik Segment İkame","SUV Segment İkame","Lüks Segment İkame"],               contract_type="Yetkili"),
            models.Supplier(id=8, name="Sixt Rent a Car",            type="ikame_arac",  phone="+90 850 555 0402", location="İstanbul & Ankara & İzmir",          city="İzmir",    district="Menderes",      services=["Sedan Segment İkame","Hafif Ticari İkame","Elektrikli Araç İkame"],             contract_type="Anlaşmalı"),
        ]
        db.add_all(suppliers)
        db.flush()

        # ── Customers ──────────────────────────────────────────
        customers = [
            models.Customer(
                id=1,
                company_name="Tekno Holding",
                legal_title="Tekno Holding Anonim Şirketi",
                email="info@teknoholding.com",
                phone="+90 212 999 8877",
                registered_vehicles_count=15,
                status="Aktif",
                address="Maslak Plazalar No: 18, Kat: 14, Şişli, İstanbul",
                contract_amount=425000.0,
                signed_at="2026-07-10 14:30"
            )
        ]
        db.add_all(customers)
        db.flush()

        # ── Vehicles ───────────────────────────────────────────
        vehicles = [
            models.Vehicle(id="VF3RENAULTMEGANE1",  chassis_no="VF3RENAULTMEGANE1",  plate="34 ABC 123", brand="Renault",    model="Megane E-Tech",  year=2024, fuel="Elektrik", status="Aktif",               mileage=12500, license_serial_no="AA123456", inspection_date="2026-05-12", vehicle_segment="C", vehicle_type="Hatchback",    tire_change_date="2025-11-20", last_service_date="2025-12-10", last_service_mileage=10000, is_active=True, supplier_id=7, customer_id=1),
            models.Vehicle(id="ZFAFIATEGEACROSS2",  chassis_no="ZFAFIATEGEACROSS2",  plate="34 XYZ 987", brand="Fiat",       model="Egea Cross",     year=2023, fuel="Hibrit",   status="Serviste",            mileage=45200, license_serial_no="BB654321", inspection_date="2025-09-18", vehicle_segment="C", vehicle_type="SUV",          tire_change_date="2026-04-15", last_service_date="2026-06-05", last_service_mileage=40000, is_active=True, supplier_id=None, customer_id=1),
            models.Vehicle(id="WVWZZZPASSATVAR3",   chassis_no="WVWZZZPASSATVAR3",   plate="06 FLT 99",  brand="Volkswagen", model="Passat Variant", year=2022, fuel="Dizel",    status="Lastik Değişiminde",  mileage=78900, license_serial_no="CC987654", inspection_date="2025-03-24", vehicle_segment="D", vehicle_type="Sedan",        tire_change_date="2025-12-05", last_service_date="2026-02-14", last_service_mileage=75000, is_active=True, supplier_id=7, customer_id=1),
            models.Vehicle(id="5YJTESLAMODELYYY4",  chassis_no="5YJTESLAMODELYYY4",  plate="35 CAR 456", brand="Tesla",      model="Model Y",        year=2024, fuel="Elektrik", status="Aktif",               mileage=8200,  license_serial_no="DD112233", inspection_date="2026-07-01", vehicle_segment="D", vehicle_type="SUV",          tire_change_date="2026-05-10", last_service_date="2026-05-10", last_service_mileage=5000,  is_active=True, supplier_id=8, customer_id=1),
            models.Vehicle(id="KMHTUCSONHYUNDAI5",  chassis_no="KMHTUCSONHYUNDAI5",  plate="34 FLE 222", brand="Hyundai",    model="Tucson",         year=2023, fuel="Benzin",   status="Yol Yardımında",      mileage=31000, license_serial_no="EE445566", inspection_date="2025-11-30", vehicle_segment="C", vehicle_type="SUV",          tire_change_date="2025-10-18", last_service_date="2026-01-20", last_service_mileage=30000, is_active=True, supplier_id=8, customer_id=1),
        ]
        db.add_all(vehicles)
        db.flush()

        # ── Quotes ─────────────────────────────────────────────
        quotes = [
            models.Quote(
                id=1,
                company_name="Tekno Holding",
                email="info@teknoholding.com",
                phone="+90 212 999 8877",
                vehicle_count=15,
                duration_months=24,
                vehicle_segment="D",
                vehicle_type="Sedan",
                estimated_annual_mileage=20000,
                monthly_price_try=425000,
                status="Sözleşme İmzalandı",
                contract_amount=425000.0,
                created_at="2026-07-10 14:30"
            )
        ]
        db.add_all(quotes)
        db.flush()

        # ── Requests ───────────────────────────────────────────
        requests = [
            models.Request(id=1, vehicle_id="ZFAFIATEGEACROSS2", supplier_id=1, type="servis",     status="İşlemde",  description="15.000 km periyodik bakımı ve fren balata değişimi.",           created_at="2026-07-17 10:00", details={"appointment_date": "2026-07-18 09:00"}),
            models.Request(id=2, vehicle_id="WVWZZZPASSATVAR3",   supplier_id=3, type="lastik",     status="Onaylandı", description="Yaz lastiklerinden kış lastiklerine geçiş ve rot-balans ayarı.", created_at="2026-07-18 11:30", details={"tire_type": "Kış Lastiği", "appointment_date": "2026-07-19 14:00"}),
            models.Request(id=3, vehicle_id="KMHTUCSONHYUNDAI5",  supplier_id=5, type="yol_yardim", status="Beklemede", description="Motor arıza lambası yandı ve araç çekici bekliyor.",             created_at="2026-07-18 13:00", details={"location": "Maslak İTÜ Önü", "issue_severity": "Yüksek"}),
        ]
        db.add_all(requests)
        db.flush()

        # ── Supplier Bids ──────────────────────────────────────
        bids = [
            models.SupplierBid(id=1, quote_id=1, supplier_id=7, supplier_name="Enterprise Filo Kiralama", monthly_price_try=410000, notes="Sıfır kilometre araçlar ile 2 hafta içinde teslimat garantisi.", created_at="2026-07-11 09:30", status="Beklemede"),
            models.SupplierBid(id=2, quote_id=1, supplier_id=8, supplier_name="Sixt Rent a Car",           monthly_price_try=415000, notes="Havalimanı teslimat seçenekleri ve kasko dahil fiyattır.",      created_at="2026-07-11 11:15", status="Beklemede"),
        ]
        db.add_all(bids)

        db.commit()
        print("✅ FleetCar veritabanı seed edildi.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed hatası: {e}")
        raise
    finally:
        db.close()
