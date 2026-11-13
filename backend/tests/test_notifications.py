"""Notifications: captured from data changes, routed to the right account, respecting preferences."""

import unittest
from datetime import date, timedelta

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app import notifications as n
from app.portal_access import mint


class NotificationTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def notices(self, portal, tenant_id, topic=None):
        q = self.db.query(m.Notification).filter_by(portal=portal, tenant_id=tenant_id)
        if topic:
            q = q.filter_by(topic=topic)
        return q.all()

    def test_catalog_lists_every_portal_and_unique_topics(self):
        rows = n.catalog_rows()
        self.assertEqual({r[0] for r in rows}, {"customer", "supplier", "service"})
        pairs = [(r[0], r[2]) for r in rows]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_offer_sent_reaches_customer_not_the_sender(self):
        offer = self.create("offer", title="Corolla / 24 Ay", vehicle_id="car2")
        self.status(offer, "Beklemede")
        got = self.notices("customer", 1, "offer_received")
        self.assertEqual(len(got), 1)
        self.assertIn("Corolla", got[0].body)
        self.assertEqual(got[0].link, "/dashboard/quotes")
        # The supplier made the change, so its own account hears nothing about it.
        self.assertEqual(self.notices("supplier", 1), [])
        # Fixture addresses are never mailed.
        self.assertEqual(got[0].email_status, "off")

    def test_record_numbers_are_final_in_notices(self):
        car = self.db.get(m.Vehicle, "car")
        car.customer_id = 1
        self.db.commit()
        self.create("damage", title="Kaporta Hasarı", details={"description": "Çizik"})
        notice = self.notices("customer", 1, "damage_update")[0]
        self.assertNotIn("pending-", notice.body)
        self.assertIn("HS", notice.body)

    def test_bulk_status_update_is_captured(self):
        req = m.Request(
            vehicle_id="car", supplier_id=3, type="servis", status="Beklemede", description="Fren"
        )
        car = self.db.get(m.Vehicle, "car")
        car.customer_id = 1
        self.db.add(req)
        self.db.commit()
        self.assertEqual(len(self.notices("service", 3, "job_new")), 1)
        self.assertEqual(len(self.notices("supplier", 1, "service_update")), 1)
        self.assertEqual(len(self.notices("customer", 1, "vehicle_assigned")), 1)
        self.db.query(m.Request).filter_by(id=req.id).update(
            {"status": "İşlemde"}, synchronize_session=False
        )
        self.db.commit()
        update = self.notices("customer", 1, "request_update")
        self.assertEqual(len(update), 1)
        self.assertIn("İşlemde", update[0].title)
        self.assertEqual(update[0].plate, "34 ABC 123")

    def test_rollback_leaves_no_notice(self):
        offer = self.create("offer", title="Geri alınan")
        self.db.query(m.SupplierOperation).filter_by(id=offer["id"]).update(
            {"status": "Beklemede"}, synchronize_session=False
        )
        self.db.rollback()
        self.db.commit()
        self.assertEqual(self.notices("customer", 1, "offer_received"), [])

    def test_approval_request_notifies_own_account(self):
        offer = self.create("offer", amount=999999)
        response = self.client.post(
            f"/api/supplier-workspace/records/{offer['id']}/request-approval"
        )
        # Large offers open an approval on their own; either way the colleagues are told.
        self.assertIn(response.status_code, (200, 409), response.text)
        self.assertEqual(len(self.notices("supplier", 1, "approval_requested")), 1)

    def test_preferences_mute_a_group_and_only_managers_change_them(self):
        ops = self.client.put(
            "/api/notifications/preferences",
            {"groups": [{"key": "sales", "in_app": False, "email": False}]},
            self.ops_token,
        )
        self.assertEqual(ops.status_code, 403)
        saved = self.client.put(
            "/api/notifications/preferences",
            {"groups": [{"key": "sales", "in_app": False, "email": False}]},
        )
        self.assertEqual(saved.status_code, 200, saved.text)
        sales = next(g for g in saved.json()["groups"] if g["key"] == "sales")
        self.assertEqual((sales["in_app"], sales["email"]), (False, False))
        self.db.add(
            m.Quote(
                company_name="Yeni",
                email="x@example.test",
                vehicle_count=3,
                status="Teklif Bekleniyor",
            )
        )
        self.db.commit()
        self.assertEqual(self.notices("supplier", 1, "quote_new"), [])
        self.assertEqual(len(self.notices("supplier", 2, "quote_new")), 1)
        self.assertEqual(
            self.notices("service", 3), []
        )  # service accounts don't get rental requests

    def test_list_read_and_driver_scope(self):
        token = mint(self.db, "customer", 1)
        car = self.db.get(m.Vehicle, "car")
        car.customer_id = 1
        car2 = self.db.get(m.Vehicle, "car2")
        car2.customer_id = 1
        self.db.commit()
        listed = self.client.get("/api/notifications", token).json()
        self.assertEqual(listed["unread"], 2)
        first = listed["items"][0]
        self.assertEqual(first["group"], "deliveries")
        self.assertEqual(
            self.client.post(f"/api/notifications/{first['id']}/read", None, token).status_code, 200
        )
        self.assertEqual(self.client.get("/api/notifications", token).json()["unread"], 1)
        # A driver sees only notices about the vehicle assigned to them.
        driver = m.CustomerPortalUser(
            customer_id=1,
            name="Sürücü",
            email="driver@example.test",
            password_hash="x",
            role="Sürücü",
            assigned_plate="34 XYZ 456",
            is_active=True,
            created_at="2026-01-01",
        )
        self.db.add(driver)
        self.db.commit()
        driver_token = mint(self.db, "customer", 1, driver.id)
        plates = {
            i["plate"] for i in self.client.get("/api/notifications", driver_token).json()["items"]
        }
        self.assertEqual(plates, {"34 XYZ 456"})
        self.assertEqual(
            self.client.post("/api/notifications/read-all", None, token).json()["count"], 1
        )
        # Another account cannot read these notices.
        other = self.notices("customer", 1)[0].id
        self.assertEqual(
            self.client.post(
                f"/api/notifications/{other}/read", None, self.other_token
            ).status_code,
            404,
        )

    def test_daily_reminders_fire_once_per_threshold(self):
        car = self.db.get(m.Vehicle, "car")
        car.customer_id = 1
        car.inspection_date = (date.today() + timedelta(days=5)).isoformat()
        self.db.commit()
        bind = self.db.get_bind()
        self.assertEqual(n.run_reminders(bind, date.today()), 2)  # customer and supplier
        self.assertEqual(n.run_reminders(bind, date.today()), 0)  # same threshold: no repeat
        notice = self.notices("customer", 1, "inspection_due")[0]
        self.assertIn("5 gün kaldı", notice.title)
        self.assertEqual(n.run_reminders(bind, date.today() + timedelta(days=5)), 2)  # due day

    def test_email_html_escapes_and_links_settings(self):
        page = n._email_html("customer", "Başlık <b>", "Gövde & metin", "/dashboard/quotes")
        self.assertIn("Başlık &lt;b&gt;", page)
        self.assertIn("/dashboard/notifications?tab=settings", page)
        self.assertFalse(n._deliverable("owner@example.test"))
        self.assertTrue(n._deliverable("filo@sirket.com.tr"))


if __name__ == "__main__":
    unittest.main()
