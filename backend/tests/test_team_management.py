import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import test_supplier_workspace as fixtures

from app import models as m
from app.portal_access import mint
from app.supplier_context import session_token
from app.team_permissions import base_permissions


class TeamManagementTests(unittest.TestCase):
    setUp = fixtures.SupplierWorkspaceTests.setUp
    tearDown = fixtures.SupplierWorkspaceTests.tearDown

    def create_member(self, portal="supplier", **changes):
        data = {
            "name": "Yeni Üye",
            "email": portal + ".team@example.test",
            "role": "fleet_manager" if portal == "supplier" else "Filo Yöneticisi",
            **changes,
        }
        token = self.client.token if portal == "supplier" else mint(self.db, "customer", 1)
        result = self.client.post(f"/api/team/{portal}/users", data, token=token)
        self.assertEqual(result.status_code, 201, result.text)
        return result.json(), token

    def test_scope_and_owner_only_admin(self):
        result, owner = self.create_member()
        uid = result["user"]["id"]
        member = session_token(self.db, 1, uid)
        self.assertEqual(
            self.client.get("/api/team/supplier/overview", token=member).status_code, 403
        )
        other = session_token(self.db, 2)
        self.assertEqual(
            self.client.post(f"/api/team/supplier/users/{uid}/invite", token=other).status_code, 404
        )
        self.assertEqual(
            self.client.get("/api/team/customer/overview", token=owner).status_code, 403
        )
        self.assertEqual(self.client.get("/api/team/supplier/overview", token="").status_code, 401)
        self.assertEqual(
            self.client.put(
                "/api/team/supplier/users/999",
                {"name": "Owner", "email": "x@test.test", "role": "owner"},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/team/supplier/users",
                {"name": "Admin", "email": "admin.team@test.test", "role": "owner"},
            ).status_code,
            422,
        )

    def test_invitation_single_use_hash_storage_and_login(self):
        with patch("app.email_utils._send_message") as send:
            result, owner = self.create_member(invite=True)
        self.assertTrue(result["email_sent"])
        send.assert_called_once()
        token = result["invitation_url"].split("#token=")[1]
        row = self.db.query(m.TeamInvitation).first()
        self.assertNotEqual(row.token_hash, token)
        self.assertNotIn(token, self.client.get("/api/team/supplier/overview").text)
        self.assertEqual(
            self.client.post(
                "/api/team/invitation/inspect", {"token": token}, token=""
            ).status_code,
            200,
        )
        accepted = self.client.post(
            "/api/team/invitation/accept",
            {"token": token, "password": "MemberPassword10"},
            token="",
        )
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(
            self.client.post(
                "/api/team/invitation/accept",
                {"token": token, "password": "MemberPassword10"},
                token="",
            ).status_code,
            410,
        )
        login = self.client.post(
            "/api/supplier/login",
            {"email": "supplier.team@example.test", "password": "MemberPassword10"},
            token="",
        )
        self.assertEqual(login.status_code, 200, login.text)

    def test_resend_expiry_revoke_and_email_failure_are_explicit(self):
        result, owner = self.create_member()
        path = f'/api/team/supplier/users/{result["user"]["id"]}'
        with patch("app.email_utils._send_message", side_effect=RuntimeError("transport down")):
            first = self.client.post(path + "/invite").json()
            second = self.client.post(path + "/invite").json()
        self.assertFalse(second["email_sent"])
        old = first["invitation_url"].split("#token=")[1]
        new = second["invitation_url"].split("#token=")[1]
        self.assertEqual(
            self.client.post("/api/team/invitation/inspect", {"token": old}, token="").status_code,
            410,
        )
        self.assertEqual(
            self.client.post("/api/team/invitation/inspect", {"token": new}, token="").status_code,
            200,
        )
        self.client.post(path + "/revoke-invitation")
        self.assertEqual(
            self.client.post("/api/team/invitation/inspect", {"token": new}, token="").status_code,
            410,
        )
        with patch("app.email_utils._send_message"):
            expired = (
                self.client.post(path + "/invite").json()["invitation_url"].split("#token=")[1]
            )
        row = self.db.query(m.TeamInvitation).order_by(m.TeamInvitation.id.desc()).first()
        row.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.db.commit()
        self.assertEqual(
            self.client.post(
                "/api/team/invitation/inspect", {"token": expired}, token=""
            ).status_code,
            410,
        )

    def test_permissions_enforced_on_routes_legacy_and_snapshot(self):
        perms = base_permissions("supplier", "fleet_manager")
        for action in perms["fuel"]:
            perms["fuel"][action] = False
        perms["vehicles"]["edit"] = False
        result, owner = self.create_member(permissions=perms)
        uid = result["user"]["id"]
        token = session_token(self.db, 1, uid)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/expenses", token=token).status_code, 403
        )
        self.assertEqual(self.client.get("/api/vehicle-expenses", token=token).status_code, 403)
        self.assertEqual(
            self.client.post(
                "/api/supplier-workspace/shared/fuel",
                {"vehicle_id": "car", "amount": 1, "date": "2026-10-15"},
                token=token,
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put("/api/supplier-workspace/vehicles/car", {}, token=token).status_code,
            403,
        )
        snapshot = self.client.get("/api/supplier-workspace/snapshot", token=token)
        self.assertEqual(snapshot.status_code, 200, snapshot.text)
        self.assertEqual(snapshot.json()["fuel"], [])
        self.assertEqual(self.client.get("/api/vehicles", token=token).status_code, 200)

    def test_role_template_inheritance_stale_updates_and_in_use_delete(self):
        perms = base_permissions("supplier", "fleet_manager")
        for action in perms["fuel"]:
            perms["fuel"][action] = False
        role = {"name": "Araç Ekibi", "base_role": "fleet_manager", "permissions": perms}
        response = self.client.post("/api/team/supplier/roles", role)
        self.assertEqual(response.status_code, 201, response.text)
        key = response.json()["key"]
        rid = key.split(":")[1]
        result, _ = self.create_member(role=key)
        uid = result["user"]["id"]
        token = session_token(self.db, 1, uid)
        self.assertEqual(self.client.get("/api/vehicle-expenses", token=token).status_code, 403)
        self.assertEqual(
            self.client.request("DELETE", f"/api/team/supplier/roles/{rid}").status_code, 409
        )
        role["version"] = 1
        role["permissions"] = base_permissions("supplier", "fleet_manager")
        updated = self.client.put(f"/api/team/supplier/roles/{rid}", role)
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(self.client.get("/api/vehicles", token=token).status_code, 401)
        token = session_token(self.db, 1, uid)
        self.assertEqual(self.client.get("/api/vehicle-expenses", token=token).status_code, 200)
        self.assertEqual(self.client.put(f"/api/team/supplier/roles/{rid}", role).status_code, 409)

    def test_user_deactivation_revokes_sessions_and_invitation(self):
        with patch("app.email_utils._send_message"):
            result, owner = self.create_member(invite=True)
        uid = result["user"]["id"]
        token = session_token(self.db, 1, uid)
        edit = {key: result["user"][key] for key in ("name", "email", "role", "version")}
        edit["is_active"] = False
        response = self.client.put(f"/api/team/supplier/users/{uid}", edit)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/api/vehicles", token=token).status_code, 401)
        invitation = result["invitation_url"].split("#token=")[1]
        self.assertEqual(
            self.client.post(
                "/api/team/invitation/accept",
                {"token": invitation, "password": "MemberPassword10"},
                token="",
            ).status_code,
            410,
        )
        self.assertEqual(self.client.put(f"/api/team/supplier/users/{uid}", edit).status_code, 409)

    def test_invalid_permissions_cannot_expand_supported_base_role(self):
        perms = base_permissions("supplier", "viewer")
        perms["vehicles"]["edit"] = True
        self.assertEqual(
            self.client.post(
                "/api/team/supplier/roles",
                {"name": "Overreach", "base_role": "viewer", "permissions": perms},
            ).status_code,
            422,
        )
        perms = base_permissions("supplier", "fleet_manager")
        perms["vehicles"]["view"] = False
        self.assertEqual(
            self.client.post(
                "/api/team/supplier/roles",
                {"name": "Invalid", "base_role": "fleet_manager", "permissions": perms},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/team/supplier/roles",
                {
                    "name": "Invalid",
                    "base_role": "fleet_manager",
                    "permissions": {"hidden": {"view": True}},
                },
            ).status_code,
            422,
        )

    def test_customer_invitation_and_scoped_permissions(self):
        with patch("app.email_utils._send_message"):
            result, owner = self.create_member("customer", invite=True)
        token = result["invitation_url"].split("#token=")[1]
        self.assertEqual(
            self.client.post(
                "/api/team/invitation/accept",
                {"token": token, "password": "CustomerPassword10"},
                token="",
            ).status_code,
            200,
        )
        login = self.client.post(
            "/api/customer/login",
            {"email": "customer.team@example.test", "password": "CustomerPassword10"},
            token="",
        )
        self.assertEqual(login.status_code, 200, login.text)
        member = login.json()["token"]
        self.assertEqual(
            self.client.get("/api/team/customer/overview", token=member).status_code, 403
        )
        self.assertEqual(
            self.client.get("/api/vehicles?customer_id=2", token=member).status_code, 404
        )
        self.assertTrue(
            self.client.get("/api/team/customer/overview", token=owner).json()["activities"]
        )

    def test_permission_check_uses_route_template_not_vehicle_identifier(self):
        perms = base_permissions("supplier", "fleet_manager")
        for action in perms["vehicles"]:
            perms["vehicles"][action] = False
        result, _ = self.create_member(permissions=perms)
        token = session_token(self.db, 1, result["user"]["id"])
        for name in ("fuel", "snapshot", "session", "logout"):
            self.db.add(
                m.Vehicle(
                    id=name,
                    chassis_no="TEST-" + name,
                    plate="TEST " + name,
                    brand="Test",
                    model="Test",
                    supplier_id=1,
                    is_active=True,
                )
            )
        self.db.commit()
        for name in ("fuel", "snapshot", "session", "logout"):
            self.assertEqual(
                self.client.get("/api/vehicles/" + name, token=token).status_code, 403, name
            )

    def test_conversion_requires_target_module_creation_permission(self):
        perms = base_permissions("supplier", "fleet_manager")
        perms["contracts"]["create"] = False
        result, _ = self.create_member(permissions=perms)
        token = session_token(self.db, 1, result["user"]["id"])
        response = self.client.post(
            "/api/supplier-workspace/fleet/reservations/999/convert", {"version": 1}, token=token
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_new_tables_can_be_added_without_changing_existing_tenant_rows(self):
        from app.init_db import create_tables

        classes = (m.TeamInvitation, m.TeamActivity, m.TeamMemberAccess, m.TeamRole)
        before = {
            cls.__tablename__: self.db.query(cls).count()
            for cls in (
                m.Supplier,
                m.Customer,
                m.Vehicle,
                m.SupplierPortalUser,
                m.CustomerPortalUser,
            )
        }
        for cls in classes:
            cls.__table__.drop(self.engine)
        with patch("app.init_db.engine", self.engine):
            create_tables()
        after = {
            cls.__tablename__: self.db.query(cls).count()
            for cls in (
                m.Supplier,
                m.Customer,
                m.Vehicle,
                m.SupplierPortalUser,
                m.CustomerPortalUser,
            )
        }
        self.assertEqual(before, after)
        self.assertEqual(self.client.get("/api/team/supplier/overview").status_code, 200)
