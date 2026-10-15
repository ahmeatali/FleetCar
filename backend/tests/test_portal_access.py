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


del SupplierWorkspaceTests
