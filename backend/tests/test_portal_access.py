import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.portal_access import mint


class PortalAccessTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown

    def test_legacy_authentication_and_company_scope(self):
        for path in [
            "/api/vehicles",
            "/api/dashboard/stats",
            "/api/quotes",
            "/api/admin/customers",
            "/uploads/vehicles/not-a-file.pdf",
        ]:
            self.assertEqual(self.client.get(path, token="").status_code, 401, path)
        self.assertEqual(
            self.client.get("/api/vehicles", token="supplier_token_1_fake").status_code, 401
        )
        self.assertEqual(
            {r["id"] for r in self.client.get("/api/supplier-workspace/directory").json()}, {1}
        )
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/customers",
                {"company_name": "Other Customer", "customer_id": 2},
            ).status_code,
            404,
        )
        cars = self.client.get("/api/vehicles").json()
        self.assertEqual({car["id"] for car in cars}, {"car", "car2"})
        self.assertEqual(self.client.get("/api/vehicles/other").status_code, 404)
        self.assertEqual(self.client.get("/api/vehicles/other/files").status_code, 404)
        self.assertEqual(self.client.get("/api/admin/customers").status_code, 403)
        self.assertEqual(self.client.put("/api/vehicles/car", {"customer_id": 2}).status_code, 403)
        self.assertEqual(self.client.get("/api/customer/documents?customer_id=2").status_code, 403)
        # Existing supplier rows may have unset optional contact fields.
        directory = self.client.get("/api/suppliers")
        self.assertEqual(directory.status_code, 200, directory.text)
        self.assertTrue(all(isinstance(row["city"], str) for row in directory.json()))

    def test_customer_scope_read_has_no_assignment_side_effect(self):
        token = mint(self.db, "customer", 1)
        other = mint(self.db, "customer", 2)
        self.db.get(m.Vehicle, "car").customer_id = 1
        self.db.commit()
        response = self.client.get("/api/vehicles", token=token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual({row["id"] for row in response.json()}, {"car"})
        self.assertEqual(self.client.get("/api/vehicles/car", token=other).status_code, 404)
        self.assertEqual(
            self.client.get("/api/customer/documents?customer_id=2", token=token).status_code, 404
        )
        self.assertEqual(self.client.get("/api/dashboard/stats", token=token).status_code, 200)
        self.assertIsNone(self.db.get(m.Vehicle, "car2").customer_id)
        self.assertEqual(
            self.client.get("/api/dashboard/stats", token=other).json()["total_vehicles"], 0
        )
        self.assertEqual(
            self.client.post(
                "/api/customer/documents", {"customer_id": 2, "tax_plate": "fake.pdf"}, token=token
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.put("/api/vehicles/car", {"supplier_id": 2}, token=token).status_code, 403
        )

    def test_audit_logout_and_private_files(self):
        self.client.get("/api/vehicles")
        row = self.db.query(m.AccessAudit).first()
        self.assertEqual(
            (row.principal_kind, row.subject_id, row.resource), ("supplier", 1, "/api/vehicles")
        )
        token = mint(self.db, "customer", 1)
        self.assertEqual(self.client.post("/api/auth/logout", token=token).status_code, 200)
        self.assertEqual(self.client.get("/api/vehicles", token=token).status_code, 401)
        self.db.add(
            m.VehicleFile(
                vehicle_id="other",
                category="document",
                document_type="Ruhsat",
                original_name="private.pdf",
                stored_name="private-other.pdf",
                content_type="application/pdf",
                file_size=10,
                uploaded_at="2026-01-01",
            )
        )
        self.db.commit()
        self.assertEqual(self.client.get("/uploads/vehicles/private-other.pdf").status_code, 404)

    def _admin_token(self):
        from app.auth import hash_password

        admin = m.AdminUser(
            email="root@fleetrent.test",
            password_hash=hash_password("x"),
            created_at="2026-01-01",
        )
        self.db.add(admin)
        self.db.commit()
        return admin, mint(self.db, "admin", admin.id)

    def test_impersonation_opens_portal_logs_and_stops(self):
        admin, admin_token = self._admin_token()
        imp = "/api/admin/impersonate"

        # Only an admin can impersonate.
        supplier_body = {"portal": "supplier", "subject_id": 1}
        self.assertEqual(self.client.post(imp, supplier_body).status_code, 403)
        bad_portal = {"portal": "x", "subject_id": 1}
        self.assertEqual(self.client.post(imp, bad_portal, token=admin_token).status_code, 422)
        missing = {"portal": "supplier", "subject_id": 999}
        self.assertEqual(self.client.post(imp, missing, token=admin_token).status_code, 404)

        started = self.client.post(imp, {"portal": "supplier", "subject_id": 1}, token=admin_token)
        self.assertEqual(started.status_code, 200, started.text)
        data = started.json()
        self.assertEqual(data["storage_key"], "fleetcar_supplier_token")
        self.assertEqual(data["open_path"], "/supplier-portal")
        self.assertEqual(data["subject_name"], "ABC Filo Kiralama")
        self.assertEqual(data["subject_id"], 1)

        # The minted token acts as that supplier and is marked with the admin id.
        session = self.client.get("/api/supplier-workspace/session", token=data["token"])
        self.assertEqual(session.status_code, 200, session.text)
        row = self.db.query(m.SupplierSession).filter_by(impersonated_by=admin.id).one()
        self.assertEqual(row.supplier_id, 1)
        event = self.db.query(m.ImpersonationEvent).one()
        self.assertEqual((event.portal, event.subject_id, event.ended_at), ("supplier", 1, None))

        # Customer impersonation works through the customer routes.
        customer_body = {"portal": "customer", "subject_id": 1}
        cust = self.client.post(imp, customer_body, token=admin_token).json()
        self.assertEqual(cust["storage_key"], "fleetcar_token")
        self.assertEqual(cust["subject_id"], 1)
        self.assertEqual(self.client.get("/api/vehicles", token=cust["token"]).status_code, 200)
        portal_sessions = self.db.query(m.PortalSession).filter_by(
            impersonated_by=admin.id, kind="customer"
        )
        self.assertTrue(portal_sessions.count())

        log = self.client.get("/api/admin/impersonation-log", token=admin_token).json()
        self.assertEqual({r["portal"] for r in log}, {"supplier", "customer"})
        self.assertTrue(all(r["active"] for r in log))

        # Stopping ends the session and stamps the event; the token stops working.
        stop = self.client.post(
            "/api/admin/impersonate/stop", {"event_id": event.id}, token=admin_token
        )
        self.assertEqual(stop.status_code, 200, stop.text)
        reused = self.client.get("/api/supplier-workspace/session", token=data["token"])
        self.assertEqual(reused.status_code, 401)
        self.db.refresh(event)
        self.assertIsNotNone(event.ended_at)



del SupplierWorkspaceTests
