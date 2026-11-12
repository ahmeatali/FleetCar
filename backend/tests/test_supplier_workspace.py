import asyncio
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main
from app import models as m
from app.auth import hash_password, verify_password
from app.database import Base, get_db
from app.supplier_operations import session_token


class WorkspaceClient:
    def __init__(self, token):
        self.token = token

    def request(self, method, url, body=None, token=None):
        parts = urlsplit(url)
        payload = (
            body
            if isinstance(body, bytes)
            else json.dumps(body).encode() if body is not None else b""
        )
        messages = []

        async def receive():
            return {"type": "http.request", "body": payload, "more_body": False}

        async def send(message):
            messages.append(message)

        headers = [
            (
                b"content-type",
                b"application/pdf" if isinstance(body, bytes) else b"application/json",
            )
        ]
        value = self.token if token is None else token
        if value:
            headers.append((b"authorization", f"Bearer {value}".encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": parts.path,
            "raw_path": parts.path.encode(),
            "query_string": parts.query.encode(),
            "headers": headers,
            "server": ("test", 80),
            "client": ("test", 1),
            "root_path": "",
        }
        asyncio.run(main.app(scope, receive, send))
        status = next(r["status"] for r in messages if r["type"] == "http.response.start")
        text = b"".join(
            r.get("body", b"") for r in messages if r["type"] == "http.response.body"
        ).decode(errors="replace")
        return SimpleNamespace(status_code=status, text=text, json=lambda: json.loads(text))

    def get(self, path, token=None):
        return self.request("GET", path, token=token)

    def post(self, path, body=None, token=None):
        return self.request("POST", path, body, token)

    def put(self, path, body, token=None):
        return self.request("PUT", path, body, token)


def sign_fixture(test, row):
    from io import BytesIO

    from reportlab.pdfgen.canvas import Canvas

    from app.portal_access import mint

    existing = test.client.get(f'/api/supplier-workspace/records/{row["id"]}/signature').json()
    if existing and existing["status"] == "Teyit Edildi":
        return
    stream = BytesIO()
    pdf = Canvas(stream)
    pdf.drawString(30, 800, "TEST FIXTURE: manual signed-document evidence; not a real signature.")
    pdf.save()
    result = test.client.post(
        f'/api/supplier-workspace/records/{row["id"]}/signed-document?version={row["version"]}&signed_date={date.today().isoformat()}&filename=fixture.pdf',
        stream.getvalue(),
    )
    test.assertEqual(result.status_code, 200, result.text)
    envelope = result.json()
    if not test.db.get(m.AdminUser, 9000):
        test.db.add(
            m.AdminUser(id=9000, email="platform-fixture@example.test", password_hash="fixture")
        )
        test.db.commit()
    tokens = [test.token, mint(test.db, "customer", row["customer_id"])]
    if row["kind"] == "contract":
        tokens.append(mint(test.db, "admin", 9000))
    for token in tokens:
        result = test.client.post(
            f'/api/signature-envelopes/{envelope["id"]}/attest',
            {"version": envelope["version"], "confirm": True},
            token=token,
        )
        test.assertEqual(result.status_code, 200, result.text)
        envelope = result.json()


class SupplierWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self._signed_dir = tempfile.TemporaryDirectory(prefix="fleetrent-signed-tests-")
        self._signature_patch = patch(
            "app.signature_documents.DOCUMENTS", Path(self._signed_dir.name)
        )
        self._signature_patch.start()
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.db.add_all(
            [
                m.Supplier(
                    id=1,
                    name="ABC Filo Kiralama",
                    type="ikame_arac",
                    email="owner@example.test",
                    is_email_verified=True,
                    password_hash=hash_password("OwnerPassword10"),
                ),
                m.Supplier(id=2, name="Other Fleet", type="ikame_arac", is_email_verified=True),
                m.Supplier(id=3, name="Servis", type="servis", is_email_verified=True),
                m.Customer(id=1, company_name="ABC Lojistik", email="customer@example.test"),
                m.Customer(id=2, company_name="Other Customer"),
                m.Vehicle(
                    id="car",
                    chassis_no="VIN1",
                    plate="34 ABC 123",
                    brand="BMW",
                    model="520i",
                    year=2024,
                    fuel="Benzin",
                    mileage=10000,
                    supplier_id=1,
                    is_active=True,
                    license_serial_no="AA123",
                    inspection_date="2027-10-01",
                    vehicle_segment="D",
                    vehicle_type="Sedan",
                    tire_change_date="2026-01-01",
                    last_service_date="2026-01-01",
                ),
                m.Vehicle(
                    id="car2",
                    chassis_no="VIN2",
                    plate="34 XYZ 456",
                    brand="Toyota",
                    model="Corolla",
                    year=2023,
                    fuel="Hibrit",
                    mileage=12000,
                    supplier_id=1,
                    is_active=True,
                    license_serial_no="AA124",
                    inspection_date="2027-10-01",
                    vehicle_segment="C",
                    vehicle_type="Sedan",
                    tire_change_date="2026-01-01",
                    last_service_date="2026-01-01",
                ),
                m.Vehicle(
                    id="other",
                    chassis_no="VIN3",
                    plate="06 OTHER",
                    brand="Ford",
                    model="Focus",
                    year=2024,
                    fuel="Benzin",
                    supplier_id=2,
                    is_active=True,
                    license_serial_no="AA125",
                    inspection_date="2027-10-01",
                    vehicle_segment="C",
                    vehicle_type="Sedan",
                    tire_change_date="2026-01-01",
                    last_service_date="2026-01-01",
                ),
                m.SupplierCustomerLink(
                    supplier_id=1,
                    customer_id=1,
                    details={"sector": "Lojistik"},
                    created_at=datetime.now(timezone.utc).isoformat(),
                ),
            ]
        )
        self.db.commit()
        self.token = session_token(self.db, 1)
        self.other_token = session_token(self.db, 2)
        self.db.add_all(
            [
                m.SupplierPortalUser(
                    id=1,
                    supplier_id=1,
                    name="Ops",
                    email="ops@example.test",
                    role="operations",
                    is_active=True,
                    password_hash=hash_password("MemberPassword10"),
                    created_at=date.today().isoformat(),
                ),
                m.SupplierPortalUser(
                    id=2,
                    supplier_id=1,
                    name="Viewer",
                    email="view@example.test",
                    role="viewer",
                    is_active=True,
                    password_hash=hash_password("MemberPassword10"),
                    created_at=date.today().isoformat(),
                ),
                m.SupplierPortalUser(
                    id=3,
                    supplier_id=1,
                    name="Finance",
                    email="finance@example.test",
                    role="finance",
                    is_active=True,
                    password_hash=hash_password("MemberPassword10"),
                    created_at=date.today().isoformat(),
                ),
            ]
        )
        self.db.commit()
        self.ops_token = session_token(self.db, 1, 1)
        self.viewer_token = session_token(self.db, 1, 2)
        self.finance_token = session_token(self.db, 1, 3)

        def override():
            yield self.db

        main.app.dependency_overrides[get_db] = override
        self.client = WorkspaceClient(self.token)

    def tearDown(self):
        main.app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()
        self._signature_patch.stop()
        self._signed_dir.cleanup()

    def payload(self, **kwargs):
        return {
            "title": "Test kaydı",
            "customer_id": 1,
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=365)).isoformat(),
            "amount": 30000,
            "details": {"months": 12, "quantity": 1, "annual_km": 30000},
            **kwargs,
        }

    def create(self, kind, **kwargs):
        response = self.client.post(
            "/api/supplier-workspace/records/" + kind, self.payload(**kwargs)
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def status(self, row, status, expected=200, token=None):
        if expected == 200 and (
            (row["kind"] == "contract" and status == "Aktif")
            or (row["kind"] == "delivery" and status == "Tamamlandı")
        ):
            sign_fixture(self, row)
        response = self.client.post(
            f'/api/supplier-workspace/records/{row["id"]}/status',
            {"status": status, "version": row["version"]},
            token,
        )
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def active_contract(self):
        row = self.create("contract")
        active = self.status(row, "Aktif")
        self.assertEqual(self.db.get(m.Vehicle, "car").contract_signed_at, date.today().isoformat())
        return active

    def test_authentication_and_supplier_scope(self):
        self.assertEqual(
            self.client.get("/api/supplier-workspace/snapshot", token="").status_code, 401
        )
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/snapshot", token="supplier_token_1_fake"
            ).status_code,
            401,
        )
        snapshot = self.client.get("/api/supplier-workspace/snapshot").json()
        self.assertEqual({v["id"] for v in snapshot["vehicles"]}, {"car", "car2"})
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/vehicles/car", token=self.other_token
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/vehicles/car/files", token=self.other_token
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/offer", self.payload(), self.other_token
            ).status_code,
            404,
        )

    def test_offer_contract_delivery_reaches_customer_and_preserves_history(self):
        offer = self.create("offer")
        offer = self.status(offer, "Beklemede")
        offer = self.status(offer, "Onaylandı")
        response = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"kind": "contract", "version": offer["version"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        contract = self.status(response.json(), "Aktif")
        car = self.client.get("/api/vehicles/car?customer_id=1").json()
        self.assertEqual(car["contract_no"], contract["number"])
        self.assertEqual(car["monthly_rent"], 30000)
        self.assertEqual(car["monthly_km_limit"], 2500)
        response = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/convert',
            {"kind": "delivery", "version": contract["version"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        delivery = response.json()
        details = {
            "receiver": "Ahmet Demir",
            "issuer": "Mehmet Kaya",
            "location": "İstanbul",
            "mileage": 10100,
            "checks": {k: True for k in ["exterior", "interior", "documents", "equipment"]},
        }
        response = self.client.put(
            f'/api/supplier-workspace/records/{delivery["id"]}',
            self.payload(
                parent_id=contract["id"], amount=0, version=delivery["version"], details=details
            ),
        )
        self.assertEqual(response.status_code, 200, response.text)
        delivery = response.json()
        complete = self.status(delivery, "Tamamlandı")
        self.assertIn("delivery_form_id", complete["details"])
        self.assertEqual(self.db.query(m.DeliveryForm).count(), 1)
        self.assertEqual(
            self.client.get("/api/customer/delivery-forms?customer_id=1").json()[0]["km"], 10100
        )
        self.status(delivery, "Tamamlandı", expected=409)
        self.assertEqual(self.db.query(m.DeliveryForm).count(), 1)
        self.status(contract, "Sona Erdi", expected=400)
        returned = self.create(
            "return",
            parent_id=contract["id"],
            amount=0,
            details={
                "mileage": 10100,
                "fuel_level": 50,
                "receiver": "Return Staff",
                "location": "Depot",
                "destination": "Havuzda",
                "settlement_note": "Mutabık",
                "checks": {k: True for k in ["exterior", "interior", "documents", "equipment"]},
            },
        )
        returned = self.status(returned, "İnceleniyor")
        returned = self.status(returned, "Mutabakat Bekliyor")
        self.status(returned, "Tamamlandı")
        self.status(contract, "Sona Erdi")
        self.assertIsNone(self.db.get(m.Vehicle, "car").customer_id)
        self.assertEqual(self.db.query(m.DeliveryForm).count(), 1)
        self.assertGreater(self.db.query(m.SupplierOperationEvent).count(), 5)

    def test_multiple_vehicle_offer_capacity_and_contract_overlap(self):
        offer = self.create(
            "offer", vehicle_id=None, details={"months": 12, "quantity": 2, "annual_km": 30000}
        )
        offer = self.status(offer, "Beklemede")
        offer = self.status(offer, "Onaylandı")
        response = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"kind": "contract", "version": offer["version"], "vehicle_ids": ["car", "car2"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.status(response.json(), "Aktif")
        self.assertEqual(response.json()["amount"], 60000)
        self.assertEqual(self.db.query(m.ContractVehicle).count(), 2)
        self.assertEqual(self.db.query(m.Rental).count(), 2)
        response = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"kind": "contract", "version": offer["version"], "vehicle_id": "car"},
        )
        self.assertEqual(response.status_code, 409)
        duplicate = self.create("contract")
        self.status(duplicate, "Aktif", expected=409)

    def test_delivery_checks_and_monotonic_mileage(self):
        contract = self.active_contract()
        delivery = self.create(
            "delivery",
            parent_id=contract["id"],
            amount=0,
            details={"receiver": "Name", "mileage": 10001, "checks": {}},
        )
        self.status(delivery, "Tamamlandı", expected=400)
        details = {
            "receiver": "Name",
            "mileage": 9999,
            "checks": {k: True for k in ["exterior", "interior", "documents", "equipment"]},
        }
        response = self.client.put(
            f'/api/supplier-workspace/records/{delivery["id"]}',
            self.payload(parent_id=contract["id"], amount=0, version=1, details=details),
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.status(response.json(), "Tamamlandı", expected=400)
        self.assertEqual(self.db.query(m.DeliveryForm).count(), 0)

    def test_invoice_payment_balance_and_no_cancel_after_receipt(self):
        contract = self.active_contract()
        response = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/convert',
            {"kind": "invoice", "version": contract["version"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        invoice = self.status(response.json(), "Kesildi")
        self.create("payment", parent_id=invoice["id"], amount=10000, details={})
        invoice = self.client.get("/api/supplier-workspace/records/invoice").json()[0]
        self.assertEqual(invoice["balance"], 20000)
        self.assertEqual(invoice["status"], "Kısmen Ödendi")
        response = self.client.post(
            "/api/supplier-workspace/records/payment",
            self.payload(parent_id=invoice["id"], amount=20001, details={}),
        )
        self.assertEqual(response.status_code, 400)
        self.create("payment", parent_id=invoice["id"], amount=20000, details={})
        invoice = self.client.get("/api/supplier-workspace/records/invoice").json()[0]
        self.assertEqual(invoice["balance"], 0)
        self.assertEqual(invoice["status"], "Ödendi")
        self.status(invoice, "İptal", expected=400)
        self.assertEqual(self.db.query(m.SupplierOperation).filter_by(kind="payment").count(), 2)

    def test_onay_is_bound_to_amount_version_and_owner_role(self):
        contract = self.create("contract", amount=200000)
        self.status(contract, "Aktif", expected=400)
        approval = self.client.get("/api/supplier-workspace/records/approval").json()[0]
        self.status(approval, "Onaylandı", expected=403, token=self.ops_token)
        self.status(approval, "Onaylandı")
        edited = self.client.put(
            f'/api/supplier-workspace/records/{contract["id"]}',
            self.payload(amount=210000, version=1),
        ).json()
        self.status(edited, "Aktif", expected=400)
        response = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/request-approval'
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.status(response.json(), "Onaylandı")
        self.status(edited, "Aktif")

    def decide(self, row, decision, expected=200, token=None, note=""):
        response = self.client.post(
            f'/api/supplier-workspace/records/{row["id"]}/decision',
            {"decision": decision, "note": note, "version": row["version"]},
            token,
        )
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def set_matrix(self, contract_limits):
        current = self.client.get("/api/supplier-workspace/settings").json()
        current["approval_matrix"]["contract"] = contract_limits
        response = self.client.put("/api/supplier-workspace/settings", current)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_approval_walks_role_limit_chain(self):
        self.set_matrix({"fleet_manager": None, "operations": 150000, "finance": 300000})
        contract = self.create("contract", amount=200000)
        approval = self.client.get("/api/supplier-workspace/records/approval").json()[0]
        steps = approval["details"]["steps"]
        self.assertEqual([s["role"] for s in steps], ["operations", "finance"])
        self.assertEqual(approval["details"]["category"], "contract")
        self.decide(approval, "approve", expected=403, token=self.finance_token)
        self.decide(approval, "approve", expected=403, token=self.viewer_token)
        approval = self.decide(approval, "approve", token=self.ops_token)
        self.assertEqual(approval["status"], "Beklemede")
        self.assertEqual(approval["details"]["steps"][0]["actor"], "Ops")
        self.status(contract, "Aktif", expected=400)
        self.decide(approval, "approve", expected=403, token=self.ops_token)
        self.decide(approval, "reject", expected=400, token=self.finance_token)
        approval = self.decide(approval, "approve", token=self.finance_token)
        self.assertEqual(approval["status"], "Onaylandı")
        self.status(contract, "Aktif")
        self.decide(approval, "approve", expected=400, token=self.finance_token)

    def test_approval_rejection_owner_override_and_self_approval(self):
        self.set_matrix({"fleet_manager": None, "operations": 150000, "finance": 300000})
        self.create("contract", amount=250000)
        approval = self.client.get("/api/supplier-workspace/records/approval").json()[0]
        rejected = self.decide(approval, "reject", token=self.ops_token, note="Bütçe dışı")
        self.assertEqual(rejected["status"], "Reddedildi")
        self.assertEqual(rejected["details"]["steps"][0]["note"], "Bütçe dışı")
        response = self.client.post(
            "/api/supplier-workspace/records/contract",
            self.payload(amount=140000, vehicle_id="car2"),
            token=self.ops_token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        own = next(
            a
            for a in self.client.get("/api/supplier-workspace/records/approval").json()
            if a["status"] == "Beklemede"
        )
        self.assertEqual(own["details"]["requested_by"]["user_id"], 1)
        self.decide(own, "approve", expected=403, token=self.ops_token)
        approved = self.decide(own, "approve")
        self.assertEqual(approved["status"], "Onaylandı")
        self.assertTrue(all(s["status"] == "Onaylandı" for s in approved["details"]["steps"]))

    def test_approval_matrix_rejects_lower_upper_limit(self):
        current = self.client.get("/api/supplier-workspace/settings").json()
        self.assertEqual(current["approval_matrix"]["service"]["fleet_manager"], 10000)
        current["approval_matrix"]["service"] = {
            "fleet_manager": 50000,
            "operations": 10000,
            "finance": 100000,
        }
        response = self.client.put("/api/supplier-workspace/settings", current)
        self.assertEqual(response.status_code, 422)
        del current["approval_matrix"]
        current["renewal_days"] = 45
        response = self.client.put("/api/supplier-workspace/settings", current)
        self.assertEqual(response.status_code, 200, response.text)
        saved = self.client.get("/api/supplier-workspace/settings").json()
        self.assertEqual(saved["approval_matrix"]["service"]["fleet_manager"], 10000)

    def test_password_change_checks_current_and_signs_out_other_sessions(self):
        other_device = session_token(self.db, 1)
        bad = self.client.post(
            "/api/supplier-workspace/password",
            {"current_password": "WrongPassword1", "new_password": "NewOwnerPass10"},
        )
        self.assertEqual(bad.status_code, 400)
        short = self.client.post(
            "/api/supplier-workspace/password",
            {"current_password": "OwnerPassword10", "new_password": "short"},
        )
        self.assertEqual(short.status_code, 422)
        ok = self.client.post(
            "/api/supplier-workspace/password",
            {"current_password": "OwnerPassword10", "new_password": "NewOwnerPass10"},
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertTrue(verify_password("NewOwnerPass10", self.db.get(m.Supplier, 1).password_hash))
        self.assertEqual(self.client.get("/api/supplier-workspace/session").status_code, 200)
        gone = self.client.get("/api/supplier-workspace/session", token=other_device)
        self.assertEqual(gone.status_code, 401)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/session", token=self.ops_token).status_code,
            200,
        )
        member = self.client.post(
            "/api/supplier-workspace/password",
            {"current_password": "MemberPassword10", "new_password": "NewMemberPass10"},
            token=self.ops_token,
        )
        self.assertEqual(member.status_code, 200, member.text)
        self.assertTrue(
            verify_password("NewMemberPass10", self.db.get(m.SupplierPortalUser, 1).password_hash)
        )

    def test_dealer_vehicle_cannot_be_contracted_until_picked_up(self):
        path = "/api/supplier-workspace/vehicles/car2/dealer"
        response = self.client.post(path, {"at_dealer": True}, token=self.viewer_token)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(path, {"at_dealer": True})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Bayide")
        self.assertEqual(self.client.post(path, {"at_dealer": True}).status_code, 400)
        blocked = self.client.post(
            "/api/supplier-workspace/records/contract", self.payload(vehicle_id="car2")
        )
        self.assertEqual(blocked.status_code, 400, blocked.text)
        response = self.client.post(path, {"at_dealer": False})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Aktif")
        self.create("contract", vehicle_id="car2")

    def test_bulk_vehicle_import_preview_commit_and_reimport(self):
        from tests.test_vehicle_import import HEADER, xlsx

        good = [
            "34 KLM 101",
            "WVWZZZ1KZAW000001",
            "Volkswagen",
            "Golf 1.5 TSI",
            "2024",
            "Benzin",
        ]
        rows = [
            HEADER,
            good + ["12000", "2027-01-01"],
            ["34 KLM 102", "BAD", "Fiat", "Egea", "2023", "Dizel", "5000", ""],
            ["34 ABC 123", "WVWZZZ1KZAW000002", "Fiat", "Egea", "2023", "Dizel", "5000", ""],
            ["34 KLM 101", "WVWZZZ1KZAW000003", "Fiat", "Egea", "2023", "Dizel", "5000", ""],
        ]
        url = "/api/supplier-workspace/vehicle-import?filename=liste.xlsx"
        denied = self.client.post(url, xlsx(rows), token=self.viewer_token)
        self.assertEqual(denied.status_code, 403)
        preview = self.client.post(url, xlsx(rows))
        self.assertEqual(preview.status_code, 200, preview.text)
        summary = preview.json()
        self.assertEqual((summary["create"], summary["error"]), (1, 3))
        errors = {r["row"]: " ".join(r["errors"]) for r in summary["rows"]}
        self.assertIn("Şase", errors[3])
        self.assertIn("başka bir araçta", errors[4])
        self.assertIn("tekrar ediyor", errors[5])
        self.assertIsNone(self.db.get(m.Vehicle, "WVWZZZ1KZAW000001"))
        done = self.client.post(url + "&commit=true", xlsx(rows))
        self.assertEqual(done.status_code, 200, done.text)
        self.assertEqual(done.json()["result"], {"created": 1, "updated": 0})
        car = self.db.get(m.Vehicle, "WVWZZZ1KZAW000001")
        self.assertEqual((car.supplier_id, car.plate, car.mileage), (1, "34 KLM 101", 12000))
        self.assertEqual(
            (car.model, car.version, car.inspection_date), ("Golf", "1.5 TSI", "2027-01-01")
        )
        again = self.client.post(url, xlsx(rows[:2])).json()
        self.assertEqual(again["unchanged"], 1)
        lower = self.client.post(url, xlsx([HEADER, good + ["9000", "2027-01-01"]])).json()
        self.assertEqual(lower["unchanged"], 1)
        self.assertIn("düşük", " ".join(lower["rows"][0]["warnings"]))
        newer = [HEADER, good + ["15000", "2028-01-01"]]
        updated = self.client.post(url + "&commit=true", xlsx(newer)).json()
        self.assertEqual(updated["result"], {"created": 0, "updated": 1})
        self.db.refresh(car)
        self.assertEqual((car.mileage, car.inspection_date), (15000, "2028-01-01"))
        nothing = self.client.post(url + "&commit=true", xlsx(newer))
        self.assertEqual(nothing.status_code, 400)

    def test_ai_fleet_insights_metrics_cache_and_plate_filter(self):
        from app import ai_assistant

        car = self.db.get(m.Vehicle, "car")
        start = date.today() - timedelta(days=183)
        car.customer_id, car.mileage = 1, 40000
        car.contract_start_date = start.isoformat()
        car.contract_end_date = (start + timedelta(days=365)).isoformat()
        car.contract_duration_months, car.monthly_km_limit = 12, 2000
        self.db.add(
            m.VehicleMileageRecord(
                vehicle_id="car", mileage=10000, recorded_at=start.isoformat(), source="t"
            )
        )
        self.db.commit()
        rows = {r["plate"]: r for r in ai_assistant.fleet_metrics(self.db, 1)}
        self.assertIn("km_overage_risk", rows["34 ABC 123"]["flags"])
        self.assertGreater(rows["34 ABC 123"]["usage_ratio"], 2)
        self.assertEqual(rows["34 XYZ 456"]["status"], "Havuzda")
        self.assertNotIn("06 OTHER", rows)
        url = "/api/supplier-workspace/ai/fleet-insights"
        self.assertIsNone(self.client.get(url).json())
        reply = {
            "summary": "Özet",
            "insights": [
                {
                    "type": "km_asimi",
                    "severity": "yuksek",
                    "plates": ["34 ABC 123", "99 UYDURMA 1"],
                    "title": "Aşım",
                    "recommendation": "Paketi yükseltin",
                    "rationale": "Oran 2,5",
                    "estimated_monthly_impact_try": 0,
                }
            ],
        }
        with patch("app.ai_assistant.ask", return_value=(reply, {"model": "m"})) as ask:
            denied = self.client.post(url, token=self.viewer_token)
            self.assertEqual(denied.status_code, 403)
            first = self.client.post(url)
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json()["insights"][0]["plates"], ["34 ABC 123"])
            sent = json.loads(ask.call_args.args[1])
            self.assertEqual(sent["vehicles_needing_attention"][0]["plate"], "34 ABC 123")
            self.client.post(url)
            self.assertEqual(ask.call_count, 1)
            self.client.post(url + "?force=true")
            self.assertEqual(ask.call_count, 2)
        latest = self.client.get(url, token=self.viewer_token).json()
        self.assertEqual(latest["summary"], "Özet")
        self.assertIn("34 ABC 123", latest["metrics"])

    def test_ai_daily_run_once_per_day_with_claims_and_retry(self):
        from app import ai_daily

        car = self.db.get(m.Vehicle, "car")
        start = date.today() - timedelta(days=183)
        car.customer_id, car.mileage = 1, 40000
        car.contract_start_date = start.isoformat()
        car.contract_end_date = (start + timedelta(days=365)).isoformat()
        car.contract_duration_months, car.monthly_km_limit = 12, 2000
        self.db.add(
            m.VehicleMileageRecord(
                vehicle_id="car", mileage=10000, recorded_at=start.isoformat(), source="t"
            )
        )
        self.db.query(m.SupplierSession).filter(m.SupplierSession.supplier_id != 1).delete()
        self.db.commit()
        factory = sessionmaker(bind=self.engine, autoflush=False)
        reply = ({"summary": "Günlük", "insights": []}, {"model": "m"})
        today = date(2026, 11, 12)
        with patch("app.ai_assistant.ask", side_effect=RuntimeError("API down")), self.assertLogs(
            "fleetcar.ai_daily", "ERROR"
        ):
            self.assertEqual(ai_daily.run_daily(factory, today), {1: "failed"})
        self.assertEqual(self.db.query(m.AiJobClaim).count(), 0)  # released for a retry
        with patch("app.ai_assistant.ask", return_value=reply) as ask:
            self.assertEqual(ai_daily.run_daily(factory, today), {1: "done"})
            self.assertEqual(ai_daily.run_daily(factory, today), {1: "skipped"})
            self.assertEqual(ask.call_count, 1)
        latest = self.client.get("/api/supplier-workspace/ai/fleet-insights").json()
        self.assertEqual((latest["summary"], latest["trigger"]), ("Günlük", "daily"))
        # another worker already holds tomorrow's claim: this one must not call the API
        tomorrow = today + timedelta(days=1)
        self.db.add(
            m.AiJobClaim(
                job=ai_daily.JOB, supplier_id=1, run_date=tomorrow.isoformat(), started_at="x"
            )
        )
        self.db.commit()
        with patch("app.ai_assistant.ask", return_value=reply) as ask, patch(
            "app.ai_daily.analysed_today", return_value=False
        ):
            self.assertEqual(ai_daily.run_daily(factory, tomorrow), {1: "skipped"})
            ask.assert_not_called()
        self.db.query(m.SupplierSession).delete()
        self.db.commit()
        self.assertEqual(ai_daily.run_daily(factory, today + timedelta(days=2)), {})

    def test_ai_daily_schedule_targets_six_oclock(self):
        from app import ai_daily
        from app.common.time import BUSINESS_TIMEZONE

        early = datetime(2026, 11, 12, 5, 30, tzinfo=BUSINESS_TIMEZONE)
        late = datetime(2026, 11, 12, 6, 0, tzinfo=BUSINESS_TIMEZONE)
        self.assertEqual(ai_daily.seconds_until_next_run(early), 1800)
        self.assertEqual(ai_daily.seconds_until_next_run(late), 86400)
        self.assertEqual(
            ai_daily.local_date("2026-11-12T22:30:00+00:00"), date(2026, 11, 13)
        )

    def test_ai_document_reading_matches_vehicles(self):
        url = "/api/supplier-workspace/ai/read-document?doc_type="
        contract = {
            "document_kind": "Sözleşme",
            "contract_no": "SZ-1",
            "lessor": "ABC",
            "lessee": "ABC Lojistik",
            "start_date": "2026-12-01",
            "end_date": "2027-11-30",
            "duration_months": 12,
            "general_terms": [],
            "vehicles": [
                {
                    "chassis_no": "vin1",
                    "plate": "",
                    "brand_model": "BMW",
                    "monthly_rent_try": 50000,
                    "monthly_km_limit": 2500,
                    "total_km": 30000,
                    "extra_km_price_try": 4.5,
                    "duration_months": 12,
                    "source": "Ek-1",
                },
                {
                    "chassis_no": "",
                    "plate": "34XYZ456",
                    "brand_model": "Toyota",
                    "monthly_rent_try": 0,
                    "monthly_km_limit": 0,
                    "total_km": 0,
                    "extra_km_price_try": 0,
                    "duration_months": 0,
                    "source": "Ek-1",
                },
                {
                    "chassis_no": "VIN3",
                    "plate": "06 OTHER",
                    "brand_model": "Ford",
                    "monthly_rent_try": 0,
                    "monthly_km_limit": 0,
                    "total_km": 0,
                    "extra_km_price_try": 0,
                    "duration_months": 0,
                    "source": "Ek-1",
                },
            ],
            "notes": "",
        }
        with patch("app.ai_assistant.ask", return_value=(contract, {})) as ask:
            self.assertEqual(
                self.client.post(url + "contract", b"%PDF", token=self.viewer_token).status_code,
                403,
            )
            response = self.client.post(url + "contract", b"%PDF-1.4 test")
            self.assertEqual(response.status_code, 200, response.text)
            matched = [v["vehicle"] for v in response.json()["data"]["vehicles"]]
            self.assertEqual(matched[0]["plate"], "34 ABC 123")
            self.assertEqual(matched[1]["plate"], "34 XYZ 456")
            self.assertIsNone(matched[2])  # another supplier's vehicle is never matched
            block = ask.call_args.args[1][0]
            self.assertEqual(block["source"]["media_type"], "application/pdf")
            bad = self.client.post(url + "poster", b"%PDF")
            self.assertEqual(bad.status_code, 400)

    def test_policy_projection_and_expensive_policy_approval(self):
        policy = self.create(
            "policy",
            amount=200000,
            details={"policy_type": "Kasko", "policy_no": "KS001", "insurer": "Company"},
        )
        self.assertEqual(policy["status"], "Taslak")
        self.assertIsNone(self.db.get(m.Vehicle, "car").casco_policy_no)
        self.status(policy, "Aktif", expected=400)
        approval = self.client.get("/api/supplier-workspace/records/approval").json()[0]
        self.status(approval, "Onaylandı")
        policy = self.status(policy, "Aktif")
        self.assertEqual(self.db.get(m.Vehicle, "car").casco_policy_no, "KS001")
        self.status(policy, "İptal")
        self.assertIsNone(self.db.get(m.Vehicle, "car").casco_policy_no)

    def test_role_matrix_read_only_and_finance_operations(self):
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/offer", self.payload(), self.viewer_token
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/invoice",
                self.payload(details={"direction": "gelir", "invoice_no": "F1"}),
                self.ops_token,
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/invoice",
                self.payload(details={"direction": "gelir", "invoice_no": "F1"}),
                self.finance_token,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/supplier-workspace/users", self.viewer_token).status_code, 403
        )
        self.assertEqual(
            self.client.put("/api/supplier-workspace/settings", {}, self.finance_token).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                "/api/supplier-workspace/vehicles/car", {"color": "Mavi"}, self.viewer_token
            ).status_code,
            403,
        )

    def test_member_login_and_revocation(self):
        response = self.client.post(
            "/api/supplier/login",
            {"email": "ops@example.test", "password": "MemberPassword10"},
            token="",
        )
        self.assertEqual(response.status_code, 200, response.text)
        token = response.json()["token"]
        self.assertEqual(
            self.client.get("/api/supplier-workspace/session", token).json()["role"], "operations"
        )
        self.db.get(m.SupplierPortalUser, 1).is_active = False
        self.db.commit()
        self.assertEqual(self.client.get("/api/supplier-workspace/session", token).status_code, 403)
        self.assertEqual(self.client.post("/api/supplier-workspace/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/supplier-workspace/session").status_code, 401)

    def test_shared_sources_and_customer_relationship(self):
        payload = {
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "amount": 2500,
            "title": "Yakıt",
            "details": {"mileage": 10100, "liters": 50, "station": "Station"},
        }
        self.assertEqual(
            self.client.post("/api/supplier-workspace/shared/fuel", payload).status_code, 200
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/shared/hgs",
                {**payload, "amount": 500, "details": {"type": "Yükleme"}},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/shared/hgs",
                {**payload, "amount": 125, "details": {"type": "Geçiş"}},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/shared/service",
                {**payload, "amount": 0, "details": {"type": "servis", "provider_id": "3"}},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/shared/tire",
                {
                    **payload,
                    "amount": 0,
                    "details": {
                        "brand": "Michelin",
                        "size": "205/55 R16",
                        "remaining_km": 20000,
                        "tread_depth_mm": 5,
                    },
                },
            ).status_code,
            200,
        )
        snapshot = self.client.get("/api/supplier-workspace/snapshot").json()
        self.assertEqual(len(snapshot["fuel"]), 1)
        self.assertEqual(len(snapshot["hgs"]), 2)
        self.assertEqual(len(snapshot["tire"]), 1)
        self.assertEqual(len(snapshot["service"]), 1)
        self.assertEqual(self.db.get(m.Vehicle, "car").hgs_balance, 375)
        from app.portal_access import mint

        customer_token = mint(self.db, "customer", 2)
        self.assertEqual(
            self.client.post(
                "/api/customer-workspace/suppliers/1/authorize", token=customer_token
            ).status_code,
            200,
        )
        response = self.client.post(
            "/api/supplier-workspace/customers",
            {"company_name": "Other Customer", "customer_id": 2, "details": {"city": "Ankara"}},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.put(
            "/api/supplier-workspace/vehicles/car/assignment",
            {"customer_id": 2, "expected_customer_id": None},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.get(m.Vehicle, "car").customer_id, 2)
        policy = self.create(
            "policy",
            customer_id=None,
            amount=500,
            details={"policy_type": "Kasko", "policy_no": "REL-001", "insurer": "Test"},
        )
        self.assertEqual(policy["customer_id"], 2)

    def test_validation_stale_write_and_cost_link_scope(self):
        row = self.create("offer")
        self.status(row, "Beklemede")
        response = self.client.put(
            f'/api/supplier-workspace/records/{row["id"]}', self.payload(version=1)
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/contract", self.payload(end_date="2020-01-01")
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/records/offer", self.payload(amount=-1)
            ).status_code,
            422,
        )
        self.db.add(
            m.VehicleExpense(
                id=77,
                vehicle_id="other",
                kind="Yakıt",
                amount=500,
                mileage=1,
                date=date.today().isoformat(),
            )
        )
        self.db.commit()
        response = self.client.post(
            "/api/supplier-workspace/records/invoice",
            self.payload(
                details={"direction": "gider", "invoice_no": "F1", "source_reference": "fuel:77"}
            ),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            self.client.post("/api/supplier-workspace/vehicles", {"plate": "bad"}).status_code, 422
        )

    def test_expired_session_and_service_account_are_denied(self):
        expired = session_token(self.db, 1)
        row = (
            self.db.query(m.SupplierSession)
            .filter_by(token_hash=__import__("hashlib").sha256(expired.encode()).hexdigest())
            .one()
        )
        row.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.db.commit()
        self.assertEqual(
            self.client.get("/api/supplier-workspace/session", expired).status_code, 401
        )
        service_token = session_token(self.db, 3)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/session", service_token).status_code, 403
        )

    def test_invalid_shared_input_returns_validation_error(self):
        payload = {
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "amount": 100,
            "title": "HGS",
            "details": {"type": None},
        }
        self.assertEqual(
            self.client.post("/api/supplier-workspace/shared/hgs", payload).status_code, 422
        )
        payload["details"] = {"brand": None, "size": "205/55 R16"}
        self.assertEqual(
            self.client.post("/api/supplier-workspace/shared/tire", payload).status_code, 422
        )

    def test_close_contract_cancels_planned_delivery_without_auto_billing_undelivered_cost(self):
        contract = self.active_contract()
        self.create("delivery", parent_id=contract["id"], amount=0, details={})
        payload = {
            "vehicle_id": "car",
            "date": date.today().isoformat(),
            "amount": 1000,
            "title": "Yakıt",
            "details": {"mileage": 10100, "liters": 20},
        }
        self.assertEqual(
            self.client.post("/api/supplier-workspace/shared/fuel", payload).status_code, 200
        )
        self.status(contract, "Sona Erdi")
        self.assertEqual(
            self.client.get("/api/supplier-workspace/records/delivery").json()[0]["status"], "İptal"
        )
        snapshot = self.client.get("/api/supplier-workspace/snapshot").json()
        self.assertIsNone(snapshot["fuel"][0]["customer_id"])
        self.assertIsNone(self.db.get(m.Vehicle, "car").customer_id)
        final_invoice = self.create(
            "invoice",
            parent_id=contract["id"],
            details={"invoice_no": "FINAL-001", "direction": "gelir"},
        )
        self.assertEqual(self.status(final_invoice, "Kesildi")["customer_id"], 1)

    def test_invalid_scenario_and_duplicate_invoice_edit_are_rejected(self):
        response = self.client.post(
            "/api/supplier-workspace/records/scenario",
            self.payload(
                amount=0,
                details={"vehicle_count": 2, "electric_count": 3, "monthly_unit_cost": 1000},
            ),
        )
        self.assertEqual(response.status_code, 400)
        self.create("invoice", details={"invoice_no": "F1", "direction": "gelir"})
        two = self.create("invoice", details={"invoice_no": "F2", "direction": "gelir"})
        response = self.client.put(
            f'/api/supplier-workspace/records/{two["id"]}',
            self.payload(
                version=two["version"], details={"invoice_no": "F1", "direction": "gelir"}
            ),
        )
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
