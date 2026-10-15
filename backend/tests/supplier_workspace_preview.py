"""Isolated browser fixture. Never connects to the application database or providers."""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datetime import date

import uvicorn
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_supplier_workspace import SupplierWorkspaceTests

from app import main
from app import models as m
from app.auth import hash_password
from app.database import get_db
from app.portal_access import mint

f = SupplierWorkspaceTests()
f.setUp()
service_account = f.db.get(m.Supplier, 3)
service_account.email = "service-browser@example.test"
service_account.password_hash = hash_password("ServicePassword10")
service_account.is_email_verified = True
f.db.commit()
# Local test fixture, isolated from the user's database.
f.active_contract()
f.create(
    "offer",
    title="Corolla / 24 Ay",
    vehicle_id="car2",
    amount=32000,
    details={"months": 24, "quantity": 1, "annual_km": 30000},
)
f.create(
    "policy",
    title="Kasko Yenileme",
    amount=15000,
    details={"policy_type": "Kasko", "policy_no": "KSK-001", "insurer": "Test Sigorta"},
)
f.create(
    "damage",
    title="Kaporta Hasarı",
    vehicle_id="car2",
    amount=8000,
    details={"description": "Sağ arka kapı çizik", "incident_type": "Hasar"},
)
f.create(
    "fine", title="Park Cezası", amount=1500, details={"fine_no": "TPC-001", "location": "İstanbul"}
)
f.create(
    "scenario",
    title="Havuz Araç Planı",
    vehicle_id=None,
    customer_id=None,
    amount=0,
    details={
        "vehicle_count": 2,
        "monthly_unit_cost": 25000,
        "electric_count": 1,
        "assumptions": "Araç başına aylık maliyet varsayımı.",
    },
)
f.create(
    "invoice",
    title="Ekim 2026 Kira Faturası",
    amount=30000,
    details={"direction": "gelir", "invoice_no": "FAT-001"},
)
f.db.get(m.Vehicle, "car").current_month_km = 250
f.db.get(m.Vehicle, "car").gps_latitude = 41.0082
f.db.get(m.Vehicle, "car").gps_longitude = 28.9784
f.db.get(m.Vehicle, "car2").next_service_due_km = 13000
f.db.commit()
for kind, body in [
    (
        "fuel",
        {
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "amount": 2000,
            "title": "Test yakıt fişi",
            "details": {"liters": 40, "mileage": 10100, "station": "Test İstasyon"},
        },
    ),
    (
        "hgs",
        {
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "amount": 500,
            "title": "Bakiye yüklemesi",
            "details": {"type": "Yükleme"},
        },
    ),
    (
        "service",
        {
            "vehicle_id": "car2",
            "date": date.today().isoformat(),
            "amount": 0,
            "title": "Periyodik Bakım",
            "details": {"type": "servis", "provider_id": "3"},
        },
    ),
]:
    response = f.client.post("/api/supplier-workspace/shared/" + kind, body)
    if response.status_code != 200:
        raise RuntimeError(response.text)

customer_token = mint(f.db, "customer", 1)
admin_token = mint(f.db, "admin", 9000)
fixture_path = Path(
    os.environ.get(
        "FLEETRENT_E2E_FIXTURE",
        str(Path(tempfile.gettempdir()) / "supplier-workspace-fixture.json"),
    )
)

pdf_path = fixture_path.with_suffix(".pdf")
pdf = Canvas(str(pdf_path))
pdf.drawString(30, 800, "TEST FIXTURE ONLY. No real signature.")
pdf.save()
fixture_path.write_text(
    json.dumps(
        {
            "pdf_path": str(pdf_path),
            "admin_token": admin_token,
            "customer_token": customer_token,
            "token": f.token,
            "viewer_token": f.viewer_token,
            "ops_token": f.ops_token,
            "finance_token": f.finance_token,
        }
    )
)
fixture_path.chmod(0o600)
# The browser issues concurrent requests. A StaticPool memory fixture shares one
# sqlite connection across threads, so serve an isolated temporary copy instead.
preview_dir = tempfile.TemporaryDirectory(prefix="fleetrent-e2e-db-")
preview_db = Path(preview_dir.name) / "preview.sqlite3"
source = f.engine.raw_connection()
target = sqlite3.connect(preview_db)
try:
    source.driver_connection.backup(target)
finally:
    source.close()
    target.close()
preview_engine = create_engine(
    f"sqlite:///{preview_db}", connect_args={"check_same_thread": False, "timeout": 30}
)
with preview_engine.begin() as connection:
    connection.exec_driver_sql("PRAGMA journal_mode=WAL")
Session = sessionmaker(bind=preview_engine, autoflush=False)


def dependency():
    db = Session()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = dependency
try:
    uvicorn.run(
        main.app,
        host="127.0.0.1",
        port=int(os.environ.get("FLEETRENT_E2E_API_PORT", "8088")),
        lifespan="off",
        log_level="warning",
    )

finally:
    preview_engine.dispose()
    preview_dir.cleanup()
    f.tearDown()
    fixture_path.unlink(missing_ok=True)
    pdf_path.unlink(missing_ok=True)
