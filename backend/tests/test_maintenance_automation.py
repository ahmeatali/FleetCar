import unittest
from datetime import date, datetime, timedelta, timezone

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.supplier_integrations import GpsPoint, ingest
from app.supplier_operations import context, session_token


class MaintenanceAutomationTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_gps_threshold_proposes_once_then_approved_service_updates_next_threshold(self):
        self.db.get(m.Vehicle, "car").next_service_due_km = 10500
        self.db.commit()
        response = self.client.put(
            "/api/supplier-workspace/integrations/arvento/mappings",
            {"external_id": "d1", "vehicle_id": "car"},
        )
        self.assertEqual(response.status_code, 200)
        ctx = context("Bearer " + self.token, self.db)
        point = GpsPoint(
            device_id="d1",
            occurred_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            latitude=41,
            longitude=29,
            mileage=11000,
        )
        ingest(self.db, ctx, [point])
        self.db.commit()
        ingest(
            self.db,
            ctx,
            [
                point.model_copy(
                    update={
                        "occurred_at": point.occurred_at + timedelta(seconds=30),
                        "mileage": 11010,
                    }
                )
            ],
        )
        self.db.commit()
        self.assertEqual(self.db.query(m.AutomationRun).count(), 1)
        proposal = self.client.get("/api/supplier-workspace/records/maintenance").json()[0]
        self.assertIn("10500", proposal["details"]["reason"])
        self.status(proposal, "Onaylandı", expected=400)
        details = {
            **proposal["details"],
            "provider_id": 3,
            "appointment_date": date.today().isoformat(),
            "next_interval_km": 10000,
        }
        response = self.client.put(
            f'/api/supplier-workspace/records/{proposal["id"]}',
            self.payload(
                customer_id=None, version=proposal["version"], amount=2000, details=details
            ),
        )
        self.assertEqual(response.status_code, 200, response.text)
        proposal = response.json()
        self.status(proposal, "Onaylandı", expected=403, token=self.ops_token)
        proposal = self.status(proposal, "Onaylandı")
        proposal = self.status(proposal, "Planlandı")
        rid = proposal["details"]["request_id"]
        self.assertEqual(self.db.query(m.Request).count(), 1)
        provider_token = session_token(self.db, 3)
        response = self.client.put(
            f"/api/requests/{rid}/status",
            {"supplier_id": 3, "status": "Tamamlandı"},
            provider_token,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.db.get(m.Request, rid).status, "Beklemede")
        response = self.client.post(
            f"/api/requests/{rid}/invoice",
            {
                "supplier_id": 3,
                "invoice_no": "SERVICE-1",
                "invoice_date": date.today().isoformat(),
                "invoice_amount": 2000,
            },
            provider_token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.put(
            f"/api/requests/{rid}/status",
            {"supplier_id": 3, "status": "Tamamlandı"},
            provider_token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.get(m.Vehicle, "car").next_service_due_km, 21010)
        self.assertEqual(self.db.get(m.Vehicle, "car").last_service_mileage, 11010)
        self.assertEqual(self.db.get(m.SupplierOperation, proposal["id"]).status, "Tamamlandı")
        ledger = self.client.get("/api/supplier-workspace/reports/costs").json()["rows"]
        self.assertEqual(sum(r["amount"] for r in ledger), 2000)

    def test_actual_cost_above_budget_requires_owner_approval(self):
        proposal = self.create(
            "maintenance",
            amount=1000,
            customer_id=None,
            details={
                "provider_id": 3,
                "appointment_date": date.today().isoformat(),
                "next_interval_km": 5000,
            },
        )
        proposal = self.status(self.status(proposal, "Onaylandı"), "Planlandı")
        rid = proposal["details"]["request_id"]
        token = session_token(self.db, 3)
        response = self.client.post(
            f"/api/requests/{rid}/invoice",
            {
                "supplier_id": 3,
                "invoice_no": "OVER-1",
                "invoice_date": date.today().isoformat(),
                "invoice_amount": 2000,
            },
            token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.put(
            f"/api/requests/{rid}/status", {"supplier_id": 3, "status": "Tamamlandı"}, token
        )
        self.assertEqual(response.status_code, 400, response.text)
        approval = self.client.get("/api/supplier-workspace/records/approval").json()[0]
        self.assertEqual(approval["amount"], 2000)
        self.status(approval, "Onaylandı")
        response = self.client.put(
            f"/api/requests/{rid}/status", {"supplier_id": 3, "status": "Tamamlandı"}, token
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.get(m.Vehicle, "car").next_service_due_km, 15000)


del SupplierWorkspaceTests
