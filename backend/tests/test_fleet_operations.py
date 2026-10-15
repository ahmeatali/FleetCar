import unittest
from datetime import timedelta

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.common.time import business_today, stamp


class FleetOperationsTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    root = "/api/supplier-workspace/fleet"

    def branch(self, name="Merkez", token=None):
        response = self.client.post(
            self.root + "/branches", {"name": name, "city": "İstanbul"}, token
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def setup_location(self, vid="car2"):
        b = self.branch()
        response = self.client.put(
            self.root + "/locations/" + vid,
            {
                "home_branch_id": b["id"],
                "current_branch_id": b["id"],
                "version": 0,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return b

    def reservation(self, b, **changes):
        start = business_today() + timedelta(days=3)
        return {
            "customer_id": 1,
            "vehicle_id": "car2",
            "pickup_branch_id": b["id"],
            "return_branch_id": b["id"],
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=5)).isoformat(),
            "monthly_rent": 25000,
            **changes,
        }

    def test_branch_scope_roles_location_versions_and_deactivation(self):
        b = self.setup_location()
        body = {
            "home_branch_id": b["id"],
            "current_branch_id": b["id"],
            "location_note": "Park B",
            "version": 1,
        }
        self.assertEqual(self.client.put(self.root + "/locations/car2", body).status_code, 200)
        self.assertEqual(self.client.put(self.root + "/locations/car2", body).status_code, 409)
        self.assertEqual(self.client.put(self.root + "/locations/other", body).status_code, 404)
        self.assertEqual(
            self.client.put(self.root + "/locations/car", body, self.viewer_token).status_code, 403
        )
        self.assertEqual(
            self.client.post(
                self.root + "/branches", {"name": "X", "city": "Y"}, self.ops_token
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(self.root + "/overview", self.other_token).json()["branches"], []
        )
        other = self.branch("Other", self.other_token)
        body.update(current_branch_id=other["id"], version=2)
        self.assertEqual(self.client.put(self.root + "/locations/car2", body).status_code, 404)
        change = {**b, "is_active": False}
        change.pop("id")
        self.assertEqual(
            self.client.put(self.root + f'/branches/{b["id"]}', change).status_code, 409
        )
        self.db.rollback()
        empty = self.branch("Boş")
        change = {**empty, "is_active": False}
        change.pop("id")
        self.assertEqual(
            self.client.put(self.root + f'/branches/{empty["id"]}', change).status_code, 200
        )
        self.assertEqual(
            self.client.put(self.root + f'/branches/{empty["id"]}', change).status_code, 409
        )

    def test_reservation_overlap_boundaries_cancel_and_availability(self):
        b = self.setup_location()
        body = self.reservation(b)
        response = self.client.post(self.root + "/reservations", body)
        self.assertEqual(response.status_code, 200, response.text)
        row = response.json()
        same_day = self.reservation(b, start_date=body["end_date"], end_date=body["end_date"])
        self.assertEqual(self.client.post(self.root + "/reservations", same_day).status_code, 409)
        end = (business_today() + timedelta(days=20)).isoformat()
        result = self.client.get(
            self.root + f'/availability?start_date={body["start_date"]}&end_date={end}'
        ).json()
        car = next(r for r in result if r["vehicle_id"] == "car2")
        self.assertFalse(car["available"])
        self.assertEqual(car["blocks"][0]["id"], row["id"])
        self.assertEqual(self.client.get(self.root + "/reservations", self.other_token).json(), [])
        self.assertEqual(
            self.client.post(
                self.root + f'/reservations/{row["id"]}/cancel', {"version": 1}, self.other_token
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                self.root + f'/reservations/{row["id"]}/cancel', {"version": 1}
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                self.root + f'/reservations/{row["id"]}/cancel', {"version": 1}
            ).status_code,
            409,
        )
        self.assertEqual(self.client.post(self.root + "/reservations", same_day).status_code, 200)

    def test_conversion_creates_one_draft_preserving_signature_flow(self):
        b = self.setup_location()
        r = self.client.post(self.root + "/reservations", self.reservation(b)).json()
        response = self.client.post(self.root + f'/reservations/{r["id"]}/convert', {"version": 1})
        self.assertEqual(response.status_code, 200, response.text)
        converted = response.json()
        contract = self.db.get(m.SupplierOperation, converted["contract_id"])
        self.assertEqual(contract.status, "Taslak")
        self.assertEqual(contract.details["reservation_id"], r["id"])
        self.assertEqual(contract.amount, 25000)
        self.assertEqual(self.db.query(m.Rental).count(), 0)
        self.assertEqual(
            self.client.post(
                self.root + f'/reservations/{r["id"]}/convert', {"version": 1}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(self.root + "/reservations", self.reservation(b)).status_code, 409
        )
        # Existing activation still requires a signed document.
        result = self.client.post(
            f"/api/supplier-workspace/records/{contract.id}/status",
            {"status": "Aktif", "version": contract.version},
        )
        self.assertEqual(result.status_code, 400, result.text)

    def test_contract_creation_cannot_bypass_reservation(self):
        b = self.setup_location()
        data = self.reservation(b)
        self.assertEqual(self.client.post(self.root + "/reservations", data).status_code, 200)
        response = self.client.post(
            "/api/supplier-workspace/records/contract",
            {
                "title": "Çakışma",
                "customer_id": 1,
                "vehicle_id": "car2",
                "date": data["start_date"],
                "end_date": data["end_date"],
                "amount": 10000,
                "details": {"months": 1},
            },
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.db.rollback()

    def test_contracts_multicar_and_service_block_reservations(self):
        b = self.setup_location()
        data = self.reservation(b)
        contract = self.client.post(
            "/api/supplier-workspace/records/contract",
            {
                "title": "Çoklu",
                "customer_id": 1,
                "vehicle_id": "car",
                "date": data["start_date"],
                "end_date": data["end_date"],
                "amount": 50000,
                "details": {"months": 1, "quantity": 2, "vehicle_ids": ["car", "car2"]},
            },
        )
        self.assertEqual(contract.status_code, 200, contract.text)
        self.assertEqual(self.client.post(self.root + "/reservations", data).status_code, 409)
        self.db.get(m.SupplierOperation, contract.json()["id"]).status = "İptal"
        self.db.get(m.Vehicle, "car2").status = "Serviste"
        self.db.commit()
        self.assertEqual(self.client.post(self.root + "/reservations", data).status_code, 409)
        self.db.get(m.Vehicle, "car2").status = "Aktif"
        self.db.commit()
        self.assertEqual(self.client.post(self.root + "/reservations", data).status_code, 200)

    def test_invalid_dates_customers_branches_roles_and_vehicle_scope(self):
        b = self.setup_location()
        body = self.reservation(b)
        self.assertEqual(
            self.client.post(self.root + "/reservations", body, self.viewer_token).status_code, 403
        )
        for change, status in [
            ({"customer_id": 2}, 404),
            ({"vehicle_id": "other"}, 404),
            ({"pickup_branch_id": 9999}, 404),
            ({"monthly_rent": 0}, 422),
            ({"start_date": "2020-01-01"}, 422),
            ({"end_date": business_today().isoformat()}, 422),
        ]:
            response = self.client.post(self.root + "/reservations", {**body, **change})
            self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(
            self.client.get(
                self.root + "/availability?start_date=2026-01-01&end_date=2027-01-01"
            ).status_code,
            422,
        )

    def test_task_assignment_scope_manual_completion_and_live_sources(self):
        task = {
            "title": "Araç hazırlığı",
            "due_date": business_today().isoformat(),
            "vehicle_id": "car2",
            "assignee_id": 1,
        }
        self.assertEqual(
            self.client.post(self.root + "/tasks", task, self.viewer_token).status_code, 403
        )
        self.assertEqual(
            self.client.post(self.root + "/tasks", {**task, "vehicle_id": "other"}).status_code, 404
        )
        self.assertEqual(
            self.client.post(self.root + "/tasks", {**task, "assignee_id": 999}).status_code, 404
        )
        response = self.client.post(self.root + "/tasks", task)
        self.assertEqual(response.status_code, 200, response.text)
        row = next(r for r in response.json() if not r["derived"])
        update = {
            "version": row["version"],
            "status": "Tamamlandı",
            "assignee_id": 1,
            "note": "Hazır",
        }
        self.assertEqual(
            self.client.put(self.root + f'/tasks/{row["key"]}', update).status_code, 200
        )
        self.assertEqual(
            self.client.put(self.root + f'/tasks/{row["key"]}', update).status_code, 409
        )
        self.assertEqual(self.client.get(self.root + "/tasks", self.other_token).json(), [])
        service = m.Request(
            vehicle_id="car2",
            supplier_id=3,
            type="servis",
            status="Beklemede",
            created_at=stamp(),
            details={},
        )
        self.db.add(service)
        self.db.commit()
        key = f"service-{service.id}"
        sources = self.client.get(self.root + "/tasks").json()
        self.assertTrue(any(r["key"] == key for r in sources))
        self.assertEqual(
            self.client.put(
                self.root + f"/tasks/{key}",
                {"version": 0, "assignee_id": 1, "status": "Tamamlandı"},
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.put(
                self.root + f"/tasks/{key}", {"version": 0, "assignee_id": 1, "note": "Takipte"}
            ).status_code,
            200,
        )
        service.status = "Tamamlandı"
        self.db.commit()
        self.assertFalse(any(r["key"] == key for r in self.client.get(self.root + "/tasks").json()))
        self.assertEqual(
            self.client.put(
                self.root + f"/tasks/{key}", {"version": 1, "assignee_id": 1}
            ).status_code,
            409,
        )

    def test_overdue_rental_blocks_future_days_and_live_return_task(self):
        from app.fleet_schedule import blocks

        contract = m.SupplierOperation(
            supplier_id=1,
            kind="contract",
            number="SZ-OVERDUE",
            title="Geciken",
            customer_id=1,
            vehicle_id="car2",
            date=(business_today() - timedelta(days=10)).isoformat(),
            end_date=(business_today() - timedelta(days=1)).isoformat(),
            amount=10000,
            status="Aktif",
            details={},
            created_at=stamp(),
            updated_at=stamp(),
        )
        self.db.add(contract)
        self.db.flush()
        rental = m.Rental(
            supplier_id=1,
            customer_id=1,
            vehicle_id="car2",
            contract_id=contract.id,
            status="Aktif",
            starts_at=contract.date,
            ends_at=contract.end_date,
        )
        self.db.add(rental)
        self.db.commit()
        end = (business_today() + timedelta(days=7)).isoformat()
        result = blocks(self.db, 1, "car2", contract.date, end)
        self.assertEqual(result[0]["end"], end)
        self.assertIn("geciken", result[0]["label"])
        rows = self.client.get(self.root + "/tasks").json()
        self.assertTrue(any(r["key"] == f"rental-return-{rental.id}" for r in rows))
        rental.status = "Tamamlandı"
        self.db.commit()
        self.assertEqual(blocks(self.db, 1, "car2", contract.date, end), [])

    def test_two_concurrent_reservations_cannot_double_book_sqlite(self):
        import tempfile
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        from threading import Barrier

        from fastapi import HTTPException
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.database import Base
        from app.fleet_operations import ReservationInput, create_reservation

        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(
                f"sqlite:///{Path(directory)/'schedule.db'}",
                connect_args={"check_same_thread": False, "timeout": 10},
            )
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine, autoflush=False)
            with Session() as db:
                db.add(m.Supplier(id=1, name="Filo", type="ikame_arac"))
                db.add(m.Customer(id=1, company_name="Müşteri"))
                db.add(
                    m.Vehicle(
                        id="car",
                        chassis_no="V-LOCK",
                        plate="34TEST1",
                        supplier_id=1,
                        is_active=True,
                        status="Aktif",
                    )
                )
                db.add(
                    m.SupplierCustomerLink(
                        supplier_id=1, customer_id=1, details={}, created_at=stamp()
                    )
                )
                db.add(m.FleetBranch(id=1, supplier_id=1, name="Merkez", city="İstanbul"))
                db.add(
                    m.FleetVehicleLocation(
                        vehicle_id="car",
                        supplier_id=1,
                        home_branch_id=1,
                        current_branch_id=1,
                        updated_at=stamp(),
                        updated_by="Test",
                    )
                )
                db.commit()
            data = ReservationInput(
                customer_id=1,
                vehicle_id="car",
                pickup_branch_id=1,
                return_branch_id=1,
                start_date=business_today() + timedelta(days=1),
                end_date=business_today() + timedelta(days=3),
                monthly_rent=10000,
            )
            barrier = Barrier(2)

            def reserve():
                with Session() as db:
                    barrier.wait(timeout=5)
                    try:
                        create_reservation(data, {"id": 1, "role": "owner", "actor": "Test"}, db)
                        return 200
                    except HTTPException as exc:
                        db.rollback()
                        return exc.status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: reserve(), range(2)))
            self.assertEqual(sorted(results), [200, 409])
            with Session() as db:
                self.assertEqual(db.query(m.FleetReservation).count(), 1)
            engine.dispose()

    def test_failed_conversion_rolls_back_reservation_and_draft(self):
        from unittest.mock import patch

        from fastapi import HTTPException

        b = self.setup_location()
        r = self.client.post(self.root + "/reservations", self.reservation(b)).json()
        with patch(
            "app.supplier_service.append_record", side_effect=HTTPException(409, "Yeni durum")
        ):
            response = self.client.post(
                self.root + f'/reservations/{r["id"]}/convert', {"version": 1}
            )
        self.assertEqual(response.status_code, 409)
        row = self.db.get(m.FleetReservation, r["id"])
        self.assertEqual(row.status, "Onaylandı")
        self.assertIsNone(row.contract_id)
        self.assertEqual(self.db.query(m.SupplierOperation).filter_by(kind="contract").count(), 0)

    def test_manual_task_deadline_edit_does_not_override_source_deadlines(self):
        body = {"title": "Eski başlık", "due_date": business_today().isoformat()}
        row = self.client.post(self.root + "/tasks", body).json()[0]
        due = (business_today() + timedelta(days=2)).isoformat()
        response = self.client.put(
            self.root + f'/tasks/{row["key"]}',
            {"version": row["version"], "title": "Yeni başlık", "due_date": due},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()[0]["title"], "Yeni başlık")
        self.assertEqual(response.json()[0]["due_date"], due)
        b = self.setup_location()
        r = self.client.post(self.root + "/reservations", self.reservation(b)).json()
        response = self.client.put(
            self.root + f'/tasks/reservation-{r["id"]}', {"version": 0, "due_date": due}
        )
        self.assertEqual(response.status_code, 409)

    def test_early_return_releases_converted_contract_for_new_reservation(self):
        b = self.setup_location()
        body = self.reservation(b)
        first = self.client.post(self.root + "/reservations", body).json()
        converted = self.client.post(
            self.root + f'/reservations/{first["id"]}/convert', {"version": 1}
        ).json()
        contract = self.db.get(m.SupplierOperation, converted["contract_id"])
        contract.status = "Aktif"
        self.db.add(
            m.Rental(
                supplier_id=1,
                customer_id=1,
                contract_id=contract.id,
                vehicle_id="car2",
                status="Tamamlandı",
                starts_at=contract.date,
                ends_at=contract.end_date,
                returned_at=stamp(),
            )
        )
        self.db.commit()
        second = self.client.post(self.root + "/reservations", body)
        self.assertEqual(second.status_code, 200, second.text)
        result = self.client.post(
            self.root + f'/reservations/{second.json()["id"]}/convert', {"version": 1}
        )
        self.assertEqual(result.status_code, 200, result.text)


del SupplierWorkspaceTests
