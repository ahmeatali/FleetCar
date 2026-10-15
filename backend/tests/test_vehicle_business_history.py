import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app.portal_access import mint


class VehicleBusinessHistoryTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status
    active_contract = SupplierWorkspaceTests.active_contract
    payload = SupplierWorkspaceTests.payload

    def test_shared_history_is_scoped_and_excludes_customer_drafts(self):
        contract = self.active_contract()
        draft = self.create(
            "invoice",
            title="Internal draft",
            amount=100,
            details={"direction": "gelir", "invoice_no": "HIST-001"},
        )
        supplier = self.client.get("/api/supplier-workspace/vehicles/car/business-history")
        self.assertEqual(supplier.status_code, 200, supplier.text)
        self.assertIn(contract["id"], {r["id"] for r in supplier.json()})
        self.assertIn(draft["id"], {r["id"] for r in supplier.json()})
        customer = self.client.get(
            "/api/customer-workspace/vehicles/car/business-history",
            token=mint(self.db, "customer", 1),
        )
        self.assertEqual(customer.status_code, 200, customer.text)
        self.assertIn(contract["id"], {r["id"] for r in customer.json()})
        self.assertNotIn(draft["id"], {r["id"] for r in customer.json()})
        self.assertNotIn("details", customer.json()[0])
        self.assertEqual(
            self.client.get(
                "/api/customer-workspace/vehicles/car/business-history",
                token=mint(self.db, "customer", 2),
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get("/api/supplier-workspace/vehicles/other/business-history").status_code,
            404,
        )


del SupplierWorkspaceTests
