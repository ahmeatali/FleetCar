import sys
import unittest
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import init_db, main, models  # noqa: E402
from app.database import Base  # noqa: E402
from app.schemas import AdminLoginRequest, CustomerRegisterRequest, SupplierRegisterRequest  # noqa: E402


class EmailVerificationFlowTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.sent_emails = []
        self.original_sender = main.send_email_verification_email
        main.send_email_verification_email = self.fake_sender
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        main.send_email_verification_email = self.original_sender

    def fake_sender(self, email, name, token):
        self.sent_emails.append((email, name, token))
        return {"email_sent": True, "smtp_configured": True}

    def login(self, email, password):
        return main.customer_login(AdminLoginRequest(email=email, password=password), self.db)

    def assert_login_blocked_until_verified(self, email, password):
        with self.assertRaises(HTTPException) as error:
            self.login(email, password)
        self.assertEqual(error.exception.status_code, 403)

    def test_customer_registration_requires_email_verification(self):
        response = main.customer_register(
            CustomerRegisterRequest(email="customer@example.com", password="Pass12345", company_name="Customer Co"),
            self.db,
        )
        self.assertNotIn("token", response)
        self.assertTrue(response["email_sent"])
        self.assert_login_blocked_until_verified("customer@example.com", "Pass12345")

        result = main.verify_email_token(self.sent_emails[-1][2], self.db)
        self.assertEqual(result["account_type"], "customer")
        self.assertEqual(self.login("customer@example.com", "Pass12345")["status"], "success")

    def test_service_and_supplier_accounts_are_separate_and_verified(self):
        main.supplier_register(
            SupplierRegisterRequest(
                account_type="service", service_type="lastik", name="Service Co",
                email="service@example.com", password="Pass12345",
            ),
            self.db,
        )
        service_creds = AdminLoginRequest(email="service@example.com", password="Pass12345")
        with self.assertRaises(HTTPException) as error:
            main._supplier_login(service_creds, self.db, "service")
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(main.verify_email_token(self.sent_emails[-1][2], self.db)["account_type"], "service")
        self.assertEqual(main._supplier_login(service_creds, self.db, "service")["status"], "success")
        with self.assertRaises(HTTPException) as error:
            main._supplier_login(service_creds, self.db, "supplier")
        self.assertEqual(error.exception.status_code, 403)

        main.supplier_register(
            SupplierRegisterRequest(
                account_type="supplier", name="Fleet Supplier",
                email="supplier@example.com", password="Pass12345",
            ),
            self.db,
        )
        supplier_creds = AdminLoginRequest(email="supplier@example.com", password="Pass12345")
        with self.assertRaises(HTTPException) as error:
            main._supplier_login(supplier_creds, self.db, "supplier")
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(main.verify_email_token(self.sent_emails[-1][2], self.db)["account_type"], "supplier")
        self.assertEqual(main._supplier_login(supplier_creds, self.db, "supplier")["status"], "success")

    def test_customer_portal_user_must_verify_their_own_address(self):
        customer = models.Customer(company_name="Parent Co", email="parent@example.com", is_email_verified=True)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        created = main.create_customer_user(
            {"customer_id": customer.id, "name": "Driver", "email": "driver@example.com", "password": "Pass12345"},
            self.db,
        )
        self.assertTrue(created["email_sent"])
        self.assert_login_blocked_until_verified("driver@example.com", "Pass12345")
        main.verify_email_token(self.sent_emails[-1][2], self.db)
        self.assertEqual(self.login("driver@example.com", "Pass12345")["status"], "success")

    def test_startup_migration_does_not_mark_pending_accounts_verified(self):
        customer = models.Customer(company_name="Pending Customer", email="pending@example.com", is_email_verified=False)
        supplier = models.Supplier(name="Pending Supplier", type="servis", email="pending-service@example.com", is_email_verified=False)
        self.db.add_all([customer, supplier])
        self.db.commit()
        self.db.refresh(customer)
        user = models.CustomerPortalUser(
            customer_id=customer.id, name="Pending Driver", email="pending-driver@example.com",
            is_active=True, is_email_verified=False, created_at="2026-01-01",
        )
        self.db.add(user)
        self.db.commit()

        original_engine = init_db.engine
        init_db.engine = self.db.get_bind()
        try:
            init_db.create_tables()
        finally:
            init_db.engine = original_engine

        self.db.expire_all()
        self.assertFalse(self.db.get(models.Customer, customer.id).is_email_verified)
        self.assertFalse(self.db.get(models.Supplier, supplier.id).is_email_verified)
        self.assertFalse(self.db.get(models.CustomerPortalUser, user.id).is_email_verified)


if __name__ == "__main__":
    unittest.main()
