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

    def ai_row(self, insights, day, trigger="daily"):
        row = m.SupplierAiInsight(
            supplier_id=1,
            kind="fleet",
            input_hash=day,
            model="test",
            payload={"summary": "", "insights": insights},
            usage={"trigger": trigger},
            created_at=f"{day}T04:00:00+00:00",
        )
        self.db.add(row)
        self.db.commit()
        return row

    def finding(self, kind, plates, title, severity="orta", impact=0):
        return {
            "type": kind,
            "plates": plates,
            "title": title,
            "severity": severity,
            "recommendation": "",
            "rationale": "",
            "estimated_monthly_impact_try": impact,
        }

    def test_morning_digest_lists_only_new_findings(self):
        today = date.today()
        yesterday = (today - timedelta(days=1)).isoformat()
        self.ai_row([self.finding("km_asimi", ["34 ABC 123"], "Km aşımı")], yesterday)
        # Same issue reworded today, plus two new ones.
        self.ai_row(
            [
                self.finding("km_asimi", ["34 ABC 123"], "Kilometre limiti aşılıyor"),
                self.finding("dusuk_kullanim", ["34 XYZ 456"], "Düşük kullanım", "dusuk"),
                self.finding("muayene_bakim", ["34 ABC 123"], "Muayene yaklaşıyor", "yuksek", 1500),
            ],
            today.isoformat(),
        )
        bind = self.db.get_bind()
        self.assertEqual(n.run_ai_digest(bind, today), 1)
        notice = self.notices("supplier", 1, "ai_daily")[0]
        self.assertEqual(notice.title, "AI 2 yeni bulgu tespit etti")
        lines = notice.body.splitlines()
        self.assertTrue(lines[1].startswith("• Muayene yaklaşıyor"))  # highest severity first
        self.assertIn("aylık ~₺1.500", lines[1])
        self.assertNotIn("Kilometre", notice.body)
        self.assertEqual(n.run_ai_digest(bind, today), 0)  # once a day
        page = n._email_html("supplier", notice.title, notice.body, notice.link)
        self.assertEqual(page.count("<li"), 2)

    def test_morning_digest_is_silent_without_new_findings(self):
        today = date.today()
        same = [self.finding("km_asimi", ["34 ABC 123"], "Km aşımı")]
        self.ai_row(same, (today - timedelta(days=1)).isoformat())
        self.ai_row(same, today.isoformat())
        self.assertEqual(n.run_ai_digest(self.db.get_bind(), today), 0)
        # A manual analysis this morning is not the daily summary.
        self.ai_row([self.finding("iade", ["34 XYZ 456"], "İade")], today.isoformat(), "manual")
        self.assertEqual(n.run_ai_digest(self.db.get_bind(), today), 0)

    def test_email_html_escapes_and_links_settings(self):
        page = n._email_html("customer", "Başlık <b>", "Gövde & metin", "/dashboard/quotes")
        self.assertIn("Başlık &lt;b&gt;", page)
        self.assertIn("/dashboard/notifications?tab=settings", page)
        self.assertFalse(n._deliverable("owner@example.test"))
        self.assertTrue(n._deliverable("filo@sirket.com.tr"))


if __name__ == "__main__":
    unittest.main()
