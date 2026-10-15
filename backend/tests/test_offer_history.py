import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.portal_access import mint


class OfferHistoryTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_customer_revision_acceptance_and_immutable_snapshots(self):
        token = mint(self.db, "customer", 1)
        offer = self.status(self.create("offer"), "Beklemede")
        response = self.client.post(
            f'/api/customer-workspace/offers/{offer["id"]}/decision',
            {
                "version": offer["version"],
                "decision": "revise",
                "note": "24 ay ve yeni fiyat rica ediyoruz.",
            },
            token=token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        revised = response.json()
        self.assertEqual(revised["raw_status"], "Revizyon Bekliyor")
        edited = self.client.put(
            f'/api/supplier-workspace/records/{offer["id"]}',
            self.payload(
                version=revised["version"],
                amount=28000,
                details={"quantity": 1, "months": 24, "annual_km": 30000},
            ),
        ).json()
        self.assertEqual(edited["raw_status"], "Taslak")
        sent = self.status(edited, "Beklemede")
        response = self.client.post(
            f'/api/customer-workspace/offers/{offer["id"]}/decision',
            {"version": sent["version"], "decision": "accept"},
            token=token,
        )
        self.assertEqual(response.status_code, 200, response.text)
        accepted = response.json()
        response = self.client.post(
            f'/api/customer-workspace/offers/{offer["id"]}/decision',
            {"version": sent["version"], "decision": "reject"},
            token=token,
        )
        self.assertEqual(response.status_code, 409)
        versions = self.client.get(f'/api/supplier-workspace/records/{offer["id"]}/versions').json()
        self.assertEqual(versions[0]["snapshot"]["amount"], 30000)
        self.assertEqual(versions[-1]["snapshot"]["amount"], 28000)
        self.assertEqual(len({v["version"] for v in versions}), len(versions))
        self.assertEqual(self.db.query(m.CustomerOfferDecision).count(), 2)
        converted = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"version": accepted["version"], "kind": "contract", "vehicle_id": "car"},
        )
        self.assertEqual(converted.status_code, 200, converted.text)
        self.assertEqual(converted.json()["details"]["accepted_offer_version"], accepted["version"])
        self.assertEqual(converted.json()["amount"], 28000)
        self.assertEqual(converted.json()["details"]["months"], 24)

    def test_tenant_expiry_and_revision_validation(self):
        token = mint(self.db, "customer", 1)
        other = mint(self.db, "customer", 2)
        draft = self.create("offer")
        self.assertEqual(self.client.get("/api/customer-workspace/offers", token=token).json(), [])
        offer = self.status(draft, "Beklemede")
        self.assertEqual(self.client.get("/api/customer-workspace/offers", token=other).json(), [])
        self.assertEqual(
            self.client.get(
                f'/api/customer-workspace/offers/{offer["id"]}/versions', token=other
            ).status_code,
            404,
        )
        body = {"version": offer["version"], "decision": "accept"}
        self.assertEqual(
            self.client.post(
                f'/api/customer-workspace/offers/{offer["id"]}/decision', body, token=other
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f'/api/customer-workspace/offers/{offer["id"]}/decision',
                {**body, "decision": "revise"},
                token=token,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                f'/api/customer-workspace/offers/{offer["id"]}/decision',
                {**body, "version": 1},
                token=token,
            ).status_code,
            409,
        )
        self.db.get(m.SupplierOperation, offer["id"]).end_date = "2020-01-01"
        self.db.commit()
        self.assertEqual(
            self.client.post(
                f'/api/customer-workspace/offers/{offer["id"]}/decision', body, token=token
            ).status_code,
            400,
        )


del SupplierWorkspaceTests
