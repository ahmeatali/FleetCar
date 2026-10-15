"""Supplier inventory stays unassigned until an explicit customer assignment."""

import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_fuel_flow import ASGIClient

from app import main, models
from app.database import Base, get_db


class SupplierFleetTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.db.add_all(
            [
                models.Supplier(id=1, name="Rental", type="kiralama"),
                models.Supplier(id=2, name="Other rental", type="kiralama"),
                models.Supplier(id=3, name="Service", type="servis"),
                models.Customer(id=1, company_name="Customer A"),
                models.Customer(id=2, company_name="Customer B"),
                models.Vehicle(
                    id="other", chassis_no="other", plate="06 OTHER", supplier_id=2, is_active=True
                ),
            ]
        )
        self.db.commit()

        def override():
            yield self.db

        main.app.dependency_overrides[get_db] = override
        self.client = ASGIClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def create_vehicle(self):
        response = self.client.post(
            "/api/vehicles",
            json={
                "plate": "34 new 01",
                "brand": "Renault",
                "model": "Clio",
                "version": "Icon",
                "engine_no": "ENG-1",
                "color": "Beyaz",
                "year": 2024,
                "fuel": "Benzin",
                "mileage": 12000,
                "chassis_no": "VIN-NEW",
                "license_serial_no": "AA123",
                "inspection_date": "2027-01-01",
                "vehicle_segment": "B",
                "vehicle_type": "Hatchback",
                "tire_change_date": "2026-01-01",
                "last_service_date": "2026-01-01",
                "last_service_mileage": 10000,
                "supplier_id": 1,
                "customer_id": None,
                "contract_start_date": "2026-10-01",
                "contract_end_date": "2027-10-01",
                "monthly_rent": 24000,
                "monthly_km_limit": 2000,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def assign(self, customer_id, expected=None, supplier_id=1, vehicle_id="VIN-NEW"):
        return self.client.request(
            "PUT",
            f"/api/suppliers/{supplier_id}/vehicles/{vehicle_id}/assignment",
            json_body={"customer_id": customer_id, "expected_customer_id": expected},
        )

    def test_inventory_reads_do_not_assign_stock_to_customer(self):
        vehicle = self.create_vehicle()
        self.assertIsNone(vehicle["customer_id"])
        for customer in (1, 2):
            self.assertEqual(
                self.client.get("/api/vehicles", params={"customer_id": customer}).json(), []
            )
        inventory = self.client.get("/api/vehicles", params={"supplier_id": 1}).json()
        self.assertEqual([v["id"] for v in inventory], ["VIN-NEW"])
        self.assertIsNone(inventory[0]["customer_id"])

    def test_assignment_reassignment_and_release_share_same_vehicle_fields(self):
        original = self.create_vehicle()
        self.assertEqual(self.assign(1).status_code, 200)
        customer_fleet = self.client.get("/api/vehicles", params={"customer_id": 1}).json()
        self.assertEqual(len(customer_fleet), 1)
        for field in (
            "id",
            "version",
            "engine_no",
            "color",
            "monthly_rent",
            "monthly_km_limit",
            "contract_end_date",
        ):
            self.assertEqual(customer_fleet[0][field], original[field])
        self.assertEqual(customer_fleet[0]["customer_name"], "Customer A")
        self.assertEqual(self.assign(2, expected=1).status_code, 200)
        self.assertEqual(self.client.get("/api/vehicles", params={"customer_id": 1}).json(), [])
        self.assertEqual(len(self.client.get("/api/vehicles", params={"customer_id": 2}).json()), 1)
        self.assertEqual(self.assign(None, expected=2).status_code, 200)
        self.assertEqual(self.client.get("/api/vehicles", params={"customer_id": 2}).json(), [])
        self.assertEqual(len(self.client.get("/api/vehicles", params={"supplier_id": 1}).json()), 1)

    def test_wrong_owner_missing_customer_and_inactive_vehicle_are_rejected(self):
        self.create_vehicle()
        self.assertEqual(self.assign(1, supplier_id=2).status_code, 404)
        self.assertEqual(self.assign(1, supplier_id=3).status_code, 404)
        self.assertEqual(self.assign(999).status_code, 404)
        self.db.get(models.Vehicle, "VIN-NEW").is_active = False
        self.db.commit()
        self.assertEqual(self.assign(1).status_code, 400)

    def test_stale_assignment_cannot_overwrite_new_customer(self):
        self.create_vehicle()
        self.assertEqual(self.assign(1).status_code, 200)
        self.assertEqual(self.assign(2).status_code, 409)
        self.assertEqual(self.db.get(models.Vehicle, "VIN-NEW").customer_id, 1)

    def test_supplier_details_and_shared_records_are_scoped(self):
        self.create_vehicle()
        self.db.add_all(
            [
                models.VehicleExpense(
                    vehicle_id="VIN-NEW", kind="Yakıt", mileage=12000, amount=100, date="2026-10-01"
                ),
                models.VehicleExpense(
                    vehicle_id="other", kind="Yakıt", mileage=20000, amount=500, date="2026-10-01"
                ),
                models.Request(
                    vehicle_id="VIN-NEW", supplier_id=3, type="servis", description="Bakım"
                ),
                models.Request(
                    vehicle_id="other",
                    supplier_id=3,
                    type="servis",
                    description="Other maintenance",
                ),
            ]
        )
        self.db.commit()
        for suffix in ("", "/files", "/hgs", "/locations"):
            self.assertEqual(
                self.client.get(
                    "/api/vehicles/VIN-NEW" + suffix, params={"supplier_id": 1}
                ).status_code,
                200,
            )
            self.assertEqual(
                self.client.get(
                    "/api/vehicles/VIN-NEW" + suffix, params={"supplier_id": 2}
                ).status_code,
                404,
            )
        expenses = self.client.get("/api/vehicle-expenses", params={"supplier_id": 1}).json()
        self.assertEqual([e["vehicle_id"] for e in expenses], ["VIN-NEW"])
        requests = self.client.get("/api/requests", params={"fleet_supplier_id": 1}).json()
        self.assertEqual([r["vehicle_id"] for r in requests], ["VIN-NEW"])
        self.assertEqual(
            self.client.get("/api/suppliers/1/customers").json(),
            [{"id": 1, "company_name": "Customer A"}, {"id": 2, "company_name": "Customer B"}],
        )

    def test_supplier_edit_updates_customer_information_without_changing_assignment(self):
        self.create_vehicle()
        self.assign(1)
        payload = {"color": "Mavi", "monthly_rent": 27000, "customer_id": 2, "supplier_id": 2}
        response = self.client.request(
            "PUT", "/api/vehicles/VIN-NEW?supplier_id=1", json_body=payload
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_id"], 1)
        self.assertEqual(response.json()["supplier_id"], 1)
        customer_vehicle = self.client.get(
            "/api/vehicles/VIN-NEW", params={"customer_id": 1}
        ).json()
        self.assertEqual(customer_vehicle["color"], "Mavi")
        self.assertEqual(customer_vehicle["monthly_rent"], 27000)
        self.assertEqual(
            self.client.request(
                "PUT", "/api/vehicles/VIN-NEW?supplier_id=2", json_body=payload
            ).status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
