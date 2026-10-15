import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.portal_access import mint


class MarketplaceBridgeTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_customer_request_bid_offer_decision_contract_share_identity(self):
        self.db.get(m.Customer, 2).email = "other@example.test"
        self.db.commit()
        customer_token = mint(self.db, "customer", 1)
        response = self.client.post(
            "/api/quotes",
            {
                "company_name": "Forged Other",
                "email": "other@example.test",
                "phone": "fake",
                "vehicle_count": 1,
                "duration_months": 12,
                "vehicle_segment": "D",
                "vehicle_type": "Sedan",
                "estimated_annual_mileage": 30000,
            },
            customer_token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        quote = response.json()
        self.assertEqual(quote["customer_id"], 1)
        self.assertEqual(quote["company_name"], "ABC Lojistik")
        response = self.client.post(
            f'/api/quotes/{quote["id"]}/bids?supplier_id=1',
            {"monthly_price_try": 30000, "notes": "Servis ve lastik dahil."},
        )
        self.assertEqual(response.status_code, 200, response.text)
        bid = response.json()
        offers = self.client.get("/api/supplier-workspace/records/offer").json()
        self.assertEqual(len(offers), 1)
        offer = offers[0]
        self.assertEqual(offer["details"]["quote_id"], quote["id"])
        self.assertEqual(offer["details"]["bid_id"], bid["id"])
        response = self.client.put(
            f'/api/bids/{bid["id"]}/status', {"status": "Onaylandı"}, customer_token
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.db.get(m.Quote, quote["id"]).status, "Teklif Onaylandı")
        self.assertIsNone(self.db.get(m.Customer, 1).signed_at)
        self.assertEqual(self.db.get(m.SupplierOperation, offer["id"]).status, "Onaylandı")
        self.assertEqual(self.db.query(m.CustomerOfferDecision).count(), 1)
        self.assertEqual(
            self.client.put(
                f'/api/bids/{bid["id"]}/status', {"status": "Onaylandı"}, customer_token
            ).status_code,
            200,
        )
        self.assertEqual(self.db.query(m.CustomerOfferDecision).count(), 1)
        offer = self.client.get("/api/supplier-workspace/records/offer").json()[0]
        response = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"kind": "contract", "version": offer["version"], "vehicle_id": "car"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        contract = response.json()
        self.status(contract, "Aktif")
        self.assertEqual(self.db.get(m.Quote, quote["id"]).status, "Sözleşme İmzalandı")
        self.assertIsNotNone(self.db.get(m.Customer, 1).signed_at)
        self.assertEqual(
            self.client.post(
                f'/api/quotes/{quote["id"]}/bids?supplier_id=1',
                {"monthly_price_try": 10000, "notes": "Overwrite"},
            ).status_code,
            409,
        )


del SupplierWorkspaceTests
