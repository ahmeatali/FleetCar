import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m


class VehicleSaleTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_sale_reserves_stock_and_creates_invoice_without_fake_revenue(self):
        sale = self.create(
            "sale",
            amount=80000,
            details={
                "expertise_reference": "EXP-1",
                "offer_price": 78000,
                "sale_price": 77000,
                "buyer_name": "ABC Lojistik",
                "sale_document": "SALE-PDF-1",
            },
        )
        self.assertEqual(self.db.get(m.Vehicle, "car").vehicle_group, "Satışta")
        contract = self.client.post("/api/supplier-workspace/records/contract", self.payload())
        self.assertEqual(contract.status_code, 400)
        sale = self.status(self.status(self.status(sale, "Ekspertizde"), "İlanda"), "Teklif Alındı")
        self.status(sale, "Satıldı", expected=403, token=self.ops_token)
        sale = self.status(sale, "Satıldı")
        self.assertFalse(self.db.get(m.Vehicle, "car").is_active)
        self.assertEqual(sale["amount"], 77000)
        self.assertEqual(self.db.query(m.VehicleSale).one().buyer_id, 1)
        invoice = self.client.post(
            f'/api/supplier-workspace/records/{sale["id"]}/convert',
            {"kind": "invoice", "version": sale["version"]},
        )
        self.assertEqual(invoice.status_code, 200, invoice.text)
        self.assertEqual(invoice.json()["amount"], 77000)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/reports/profit_vehicle").json()["rows"], []
        )
        self.assertEqual(
            self.client.put(
                "/api/supplier-workspace/vehicles/car", {"is_active": True, "vehicle_group": "Filo"}
            ).status_code,
            400,
        )

    def test_cancel_releases_stock_and_rented_stock_is_rejected(self):
        self.db.get(m.Vehicle, "car").customer_id = 1
        self.db.commit()
        response = self.client.post(
            "/api/supplier-workspace/records/sale", self.payload(amount=80000)
        )
        self.assertEqual(response.status_code, 409)
        self.db.get(m.Vehicle, "car").customer_id = None
        self.db.commit()
        self.db.get(m.Vehicle, "car").vehicle_group = "Operasyon"
        self.db.commit()
        sale = self.create("sale", amount=80000)
        self.status(sale, "İptal")
        self.assertEqual(self.db.get(m.Vehicle, "car").vehicle_group, "Operasyon")


del SupplierWorkspaceTests
