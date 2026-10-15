import unittest

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.portal_access import mint
from app.supplier_operations import session_token


class IdentityReuseTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown

    def test_deleted_company_and_user_identifiers_never_revive_old_sessions(self):
        company = m.Supplier(name="Disposable", type="ikame_arac")
        self.db.add(company)
        self.db.commit()
        old_id = company.id
        token = session_token(self.db, old_id)
        self.db.delete(company)
        self.db.commit()
        new_company = m.Supplier(name="New Company", type="ikame_arac")
        self.db.add(new_company)
        self.db.commit()
        self.assertGreater(new_company.id, old_id)
        self.assertEqual(
            self.client.get("/api/supplier-workspace/snapshot", token).status_code, 403
        )
        customer = m.Customer(company_name="Disposable Customer")
        self.db.add(customer)
        self.db.commit()
        old_customer = customer.id
        token = mint(self.db, "customer", old_customer)
        self.db.delete(customer)
        self.db.commit()
        new_customer = m.Customer(company_name="New Customer")
        self.db.add(new_customer)
        self.db.commit()
        self.assertGreater(new_customer.id, old_customer)
        self.assertEqual(self.client.get("/api/vehicles", token).status_code, 401)


del SupplierWorkspaceTests
