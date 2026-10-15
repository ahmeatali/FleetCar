import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m


class RentalLifecycleTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def contract(self):
        offer = self.create(
            "offer",
            vehicle_id=None,
            details={"months": 12, "quantity": 2, "annual_km": 12000, "excess_km_fee": 2},
        )
        offer = self.status(self.status(offer, "Beklemede"), "Onaylandı")
        result = self.client.post(
            f'/api/supplier-workspace/records/{offer["id"]}/convert',
            {"kind": "contract", "version": offer["version"], "vehicle_ids": ["car", "car2"]},
        )
        self.assertEqual(result.status_code, 200, result.text)
        return self.status(result.json(), "Aktif")

    def deliver(self, contract, vid, km):
        delivery = self.create(
            "delivery",
            vehicle_id=vid,
            parent_id=contract["id"],
            amount=0,
            details={
                "mileage": km,
                "receiver": "Customer",
                "issuer": "Staff",
                "checks": {k: True for k in ["exterior", "interior", "documents", "equipment"]},
                "existing_damage": "Teslimde hasar yok",
                "fuel_level": 80,
            },
        )
        return self.status(delivery, "Tamamlandı")

    def test_two_cars_one_contract_independent_delivery_return_and_invoice(self):
        contract = self.contract()
        snapshot = self.client.get("/api/supplier-workspace/snapshot").json()
        self.assertEqual({r["status"] for r in snapshot["rentals"]}, {"Teslim Bekliyor"})
        self.assertEqual({v["monthly_rent"] for v in snapshot["vehicles"]}, {30000})
        first = self.deliver(contract, "car", 10000)
        second = self.deliver(contract, "car2", 12000)
        self.assertNotEqual(first["id"], second["id"])
        repeated = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/convert',
            {"kind": "delivery", "version": contract["version"], "vehicle_id": "car2"},
        )
        self.assertEqual(repeated.status_code, 409)
        invoice = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/convert',
            {"kind": "invoice", "version": contract["version"]},
        )
        self.assertEqual(invoice.status_code, 200, invoice.text)
        self.assertEqual(invoice.json()["amount"], 60000)
        self.assertIsNone(invoice.json()["vehicle_id"])
        self.assertEqual(len(invoice.json()["details"]["vehicle_allocations"]), 2)
        returned = self.create(
            "return",
            parent_id=contract["id"],
            amount=0,
            details={
                "mileage": 23000,
                "fuel_level": 40,
                "receiver": "Return Staff",
                "location": "Depot",
                "damage_charge": 500,
                "fuel_charge": 100,
                "destination": "Serviste",
                "settlement_note": "Araç incelendi, ücretlerde mutabık kalındı.",
                "checks": {k: True for k in ["exterior", "interior", "documents", "equipment"]},
            },
        )
        returned = self.status(returned, "İnceleniyor")
        returned = self.status(returned, "Mutabakat Bekliyor")
        self.assertEqual(returned["amount"], 2600)
        self.assertEqual(returned["details"]["excess_km"], 1000)
        self.assertEqual(
            returned["details"]["delivery_reference"]["existing_damage"], "Teslimde hasar yok"
        )
        self.status(returned, "Tamamlandı", expected=403, token=self.ops_token)
        returned = self.status(returned, "Tamamlandı")
        self.assertIsNone(self.db.get(m.Vehicle, "car").customer_id)
        self.assertEqual(self.db.get(m.Vehicle, "car").status, "Serviste")
        self.assertEqual(self.db.get(m.Vehicle, "car2").customer_id, 1)
        self.assertEqual(
            self.db.query(m.Rental).filter_by(vehicle_id="car").one().status, "Tamamlandı"
        )
        self.assertEqual(self.db.query(m.Rental).filter_by(vehicle_id="car2").one().status, "Aktif")
        assignment = (
            self.db.query(m.VehicleAssignment)
            .filter(
                m.VehicleAssignment.vehicle_id == "car", m.VehicleAssignment.rental_id.isnot(None)
            )
            .one()
        )
        self.assertIsNotNone(assignment.ends_at)
        self.status(contract, "Sona Erdi", expected=400)
        self.assertEqual(
            self.client.put(
                f'/api/supplier-workspace/records/{returned["id"]}',
                self.payload(version=returned["version"], parent_id=contract["id"]),
            ).status_code,
            400,
        )

    def test_contract_terms_and_car_membership_cannot_be_forged(self):
        contract = self.contract()
        fake = self.client.post(
            "/api/supplier-workspace/records/delivery",
            self.payload(parent_id=contract["id"], vehicle_id="other", amount=0),
        )
        self.assertEqual(fake.status_code, 404)
        rental = self.db.query(m.Rental).filter_by(vehicle_id="car").one()
        self.assertEqual(rental.status, "Teslim Bekliyor")
        response = self.client.post(
            "/api/supplier-workspace/records/return",
            self.payload(parent_id=contract["id"], amount=0, details={"mileage": 10000}),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.db.query(m.SupplierOperation).filter_by(kind="return").count(), 0)


del SupplierWorkspaceTests
