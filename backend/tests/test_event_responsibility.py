import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m


class EventResponsibilityTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_cost_uses_event_history_and_unmatched_requires_manual_confirmation(self):
        self.db.add(
            m.Rental(
                id=100,
                supplier_id=1,
                customer_id=1,
                contract_id=self.create("contract")["id"],
                vehicle_id="car",
                status="Tamamlandı",
                delivered_at="2026-01-01T08:00:00+03:00",
                starts_at="2026-01-01",
                ends_at="2026-02-01",
                returned_at="2026-02-01T12:00:00+03:00",
            )
        )
        self.db.add(
            m.VehicleAssignment(
                supplier_id=1,
                customer_id=1,
                vehicle_id="car",
                rental_id=100,
                driver_name="Ahmet",
                starts_at="2026-01-01T08:00:00+03:00",
                ends_at="2026-02-01T12:00:00+03:00",
            )
        )
        self.db.add(
            m.HgsTransaction(
                vehicle_id="car",
                type="Geçiş",
                amount=125,
                date="2026-01-15T10:00:00+03:00",
                balance=0,
            )
        )
        self.db.get(m.Vehicle, "car").customer_id = 2
        self.db.commit()
        snapshot = self.client.get("/api/supplier-workspace/snapshot").json()
        self.assertEqual(snapshot["hgs"][0]["customer_id"], 1)
        self.assertEqual(snapshot["hgs"][0]["driver_name"], "Ahmet")
        self.db.add(
            m.HgsTransaction(
                vehicle_id="car",
                type="Geçiş",
                amount=50,
                date="2026-03-01T10:00:00+03:00",
                balance=0,
            )
        )
        self.db.commit()
        unknown = self.db.query(m.HgsTransaction).order_by(m.HgsTransaction.id.desc()).first()
        response = self.client.post(
            f"/api/supplier-workspace/responsibility/hgs/{unknown.id}/reflect"
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.put(
            f"/api/supplier-workspace/responsibility/hgs/{unknown.id}",
            {"customer_id": 1, "reason": "Olay belgesi ve sözleşme incelendi."},
        )
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.post(
            f"/api/supplier-workspace/responsibility/hgs/{unknown.id}/reflect"
        )
        self.assertEqual(response.status_code, 200, response.text)
        invoice = response.json()
        self.assertEqual(invoice["customer_id"], 1)
        self.assertEqual(invoice["amount"], 50)
        self.assertEqual(
            self.client.post(
                f"/api/supplier-workspace/responsibility/hgs/{unknown.id}/reflect"
            ).status_code,
            409,
        )
        self.status(invoice, "Kesildi")
        response = self.client.put(
            f"/api/supplier-workspace/responsibility/hgs/{unknown.id}",
            {"customer_id": 2, "reason": "Değişiklik talebi açıklaması."},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.client.put(
                f"/api/supplier-workspace/responsibility/hgs/{unknown.id}",
                {"customer_id": 1, "reason": "Olay belgesi doğrulandı."},
                self.viewer_token,
            ).status_code,
            403,
        )

    def test_date_only_driver_change_is_ambiguous_and_hgs_reload_never_reflects(self):
        contract = self.create("contract")
        self.db.add(
            m.Rental(
                id=100,
                supplier_id=1,
                customer_id=1,
                contract_id=contract["id"],
                vehicle_id="car",
                status="Aktif",
                delivered_at="2026-01-01T00:00:00+03:00",
                starts_at="2026-01-01",
                ends_at="2027-01-01",
            )
        )
        self.db.add_all(
            [
                m.VehicleAssignment(
                    supplier_id=1,
                    customer_id=1,
                    vehicle_id="car",
                    rental_id=100,
                    driver_name="First",
                    starts_at="2026-01-01",
                    ends_at="2026-01-15T12:00:00+03:00",
                ),
                m.VehicleAssignment(
                    supplier_id=1,
                    customer_id=1,
                    vehicle_id="car",
                    rental_id=100,
                    driver_name="Second",
                    starts_at="2026-01-15T12:00:00+03:00",
                ),
            ]
        )
        self.db.commit()
        from app.event_responsibility import resolve

        self.assertEqual(
            resolve(self.db, 1, "car", "2026-01-15")["responsibility_status"], "Belirsiz"
        )
        self.assertEqual(
            resolve(self.db, 1, "car", "2026-01-15T12:00:00+03:00")["driver_name"], "Second"
        )
        self.db.add(
            m.HgsTransaction(
                vehicle_id="car", type="Yükleme", amount=500, date="2026-01-15", balance=500
            )
        )
        self.db.commit()
        rid = self.db.query(m.HgsTransaction).one().id
        self.assertEqual(
            self.client.post(
                f"/api/supplier-workspace/responsibility/hgs/{rid}/reflect"
            ).status_code,
            400,
        )


del SupplierWorkspaceTests
