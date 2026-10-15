import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m


class AuditResultTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown

    def test_denied_requests_download_attempts_and_success_are_audited_without_token(self):
        self.assertEqual(self.client.get("/api/supplier-workspace/snapshot").status_code, 200)
        self.assertEqual(self.client.get("/api/supplier-workspace/vehicles/other").status_code, 404)
        self.assertEqual(self.client.get("/api/vehicles", token="").status_code, 401)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/audit", self.viewer_token).status_code, 403
        )
        rows = self.db.query(m.AuditEvent).all()
        self.assertEqual({r.status_code for r in rows}, {200, 401, 403, 404})
        self.assertTrue(
            any(
                r.principal_kind == "supplier" and r.subject_id == 1 and r.status_code == 404
                for r in rows
            )
        )
        self.assertTrue(all(self.token not in r.resource for r in rows))
        response = self.client.get("/api/supplier-workspace/audit")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(any(row["status_code"] == 403 for row in response.json()))
        self.assertEqual(
            self.client.get("/api/supplier-workspace/audit", self.other_token).status_code, 200
        )
        # An attempted cross-tenant read is observable by the targeted company's owner,
        # but the requesting company never receives the target company's identity in audit DTOs.
        self.assertTrue(all("target_supplier_id" not in row for row in response.json()))


del SupplierWorkspaceTests
