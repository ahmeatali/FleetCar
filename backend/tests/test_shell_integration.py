import os
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from test_supplier_workspace import SupplierWorkspaceTests

from app import models as m
from app.shell_integration import SalesQuery, parse_sales, request_body

LOCAL = ZoneInfo("Europe/Istanbul")


def fixture(rid="123", plate="34 ABC 123", amount="1500.25", count=1, success="true"):
    """Synthetic SOAP fixture using names/types from Shell's public WSDL."""
    when = (datetime.now(LOCAL) - timedelta(days=2)).replace(microsecond=0).isoformat()
    return f"""<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body><GetCustomerSalesTransaction_with_ridResponse xmlns="https://tts.turkiyeshell.com">
    <GetCustomerSalesTransaction_with_ridResult><PROCESSRESULT><Success>{success}</Success>
    <Message>Provider message should never reach browser</Message></PROCESSRESULT>
    <COUNTOFSALESTRANSACTIONLIST>{count}</COUNTOFSALESTRANSACTIONLIST>
    <LISTOFSALESTRANSACTION><SALESTRANSACTIONINFO_WITH_RID>
    <RID>{rid}</RID><Plate_cd>{plate}</Plate_cd><Transaction_date>{when}</Transaction_date>
    <Vehicle_km>10500</Vehicle_km><Volume>30.5</Volume>
    <Sales_total_amount>{amount}</Sales_total_amount><Fuel_name>Motorin</Fuel_name>
    <Retail_outlet_name>Shell Test</Retail_outlet_name><Invoice_no>INV-1</Invoice_no>
    <Utts_Isutts>UTTS-1</Utts_Isutts></SALESTRANSACTIONINFO_WITH_RID></LISTOFSALESTRANSACTION>
    </GetCustomerSalesTransaction_with_ridResult></GetCustomerSalesTransaction_with_ridResponse>
    </soap:Body></soap:Envelope>""".encode()


class ShellIntegrationTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    root = "/api/supplier-workspace/integrations/shell"

    def configure(self):
        response = self.client.put(self.root + "/config", {"branch_code": "001"})
        self.assertEqual(response.status_code, 200, response.text)

    def mapping(self, vid="car", plate="34 ABC 123", token=None):
        return self.client.put(
            self.root + "/mappings",
            {
                "external_id": plate,
                "vehicle_id": vid,
            },
            token=token,
        )

    def sync(self, raw=None):
        day = (datetime.now(LOCAL) - timedelta(days=2)).date().isoformat()
        with patch("app.shell_integration.fetch_sales", return_value=raw or fixture()):
            return self.client.post(self.root + "/sync", {"start_date": day, "end_date": day})

    def test_soap_contract_validation_and_secrets(self):
        day = (datetime.now(LOCAL) - timedelta(days=2)).date()
        query = SalesQuery(start_date=day, end_date=day)
        with patch.dict(
            os.environ,
            {
                "SHELL_1_CUST_CODE": "001",
                "SHELL_1_USER_ID": "user",
                "SHELL_1_PASSWORD": "<&secret",
            },
        ):
            body = request_body(1, {"branch_code": "002"}, query)
            self.assertIn(b"GetCustomerSalesTransaction_with_rid", body)
            tree = ET.fromstring(body)
            fields = {e.tag.split("}")[-1]: e.text for e in tree.iter()}
            self.assertEqual(fields["password"], "<&secret")
            self.assertEqual(fields["report_end_dt"], day.isoformat() + "T23:59:59")
            overview = self.client.get(self.root).json()
            self.assertTrue(overview["credentials_configured"])
            self.assertNotIn("secret", str(overview))
        rows = parse_sales(fixture())
        self.assertEqual(rows[0]["plate"], "34ABC123")
        self.assertEqual(rows[0]["amount"], 1500.25)
        fractional = fixture().replace(
            b"<Vehicle_km>10500</Vehicle_km>", b"<Vehicle_km>10500.75</Vehicle_km>"
        )
        self.assertEqual(parse_sales(fractional)[0]["mileage"], 10500)
        empty = fixture(count=0)
        start = empty.index(b"<LISTOFSALESTRANSACTION>")
        end = empty.index(b"</LISTOFSALESTRANSACTION>") + len(b"</LISTOFSALESTRANSACTION>")
        self.assertEqual(parse_sales(empty[:start] + empty[end:]), [])
        for raw in [
            fixture(success="false"),
            fixture(count=2),
            fixture(rid=""),
            fixture(amount="NaN"),
            fixture(amount="-1"),
            b"<Envelope/>",
            b'<!DOCTYPE x [<!ENTITY p "x">]><x>&p;</x>',
            "<x/>".encode("utf-16"),
        ]:
            with self.assertRaises((ValueError, KeyError)):
                parse_sales(raw)
        with self.assertRaises(ValueError):
            SalesQuery(start_date=day, end_date=day + timedelta(days=32))
        with self.assertRaises(ValueError):
            SalesQuery(start_date=day, end_date=datetime.now(LOCAL).date())
        with self.assertRaises(ValueError):
            SalesQuery(start_date=day - timedelta(days=500), end_date=day)

    def test_sync_expense_replay_and_batch_rollback(self):
        self.configure()
        self.assertEqual(self.mapping().status_code, 200)
        response = self.sync()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["processed"], 1)
        expense = self.db.query(m.VehicleExpense).one()
        self.assertEqual((expense.kind, expense.amount, expense.liters), ("Yakıt", 1500.25, 30.5))
        self.assertEqual(expense.receipt_no, "SHELL-123")
        self.assertFalse(expense.full_tank)
        self.assertEqual(self.db.get(m.Vehicle, "car").mileage, 10000)
        self.assertEqual(self.sync().json()["duplicate"], 1)
        self.assertEqual(self.db.query(m.VehicleExpense).count(), 1)
        # A new sale before a conflicting existing RID must also roll back.
        first = parse_sales(fixture(rid="456"))[0]
        conflicting = parse_sales(fixture(amount="999"))[0]
        with patch("app.shell_integration.parse_sales", return_value=[first, conflicting]):
            response = self.sync()
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.db.query(m.VehicleExpense).count(), 1)
        self.assertEqual(self.db.query(m.IntegrationEvent).count(), 1)

    def test_pending_mapping_retry_and_company_scope(self):
        self.configure()
        self.assertEqual(self.sync().json()["pending"], 1)
        self.assertEqual(self.db.query(m.VehicleExpense).count(), 0)
        eid = self.db.query(m.IntegrationEvent).one().id
        response = self.client.post(self.root + f"/events/{eid}/retry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events"][0]["status"], "Eşleştirme Bekliyor")
        self.assertEqual(self.mapping("other").status_code, 404)
        self.assertEqual(self.mapping().status_code, 200)
        self.assertEqual(self.mapping("car2").status_code, 409)
        self.assertEqual(self.mapping("car", "34 OTHER 1").status_code, 409)
        self.assertEqual(self.client.get(self.root, self.other_token).json()["events"], [])
        self.assertEqual(
            self.client.post(
                self.root + f"/events/{eid}/retry", token=self.other_token
            ).status_code,
            404,
        )
        self.assertEqual(self.client.post(self.root + f"/events/{eid}/retry").status_code, 200)
        self.assertEqual(self.client.post(self.root + f"/events/{eid}/retry").status_code, 409)
        self.assertEqual(self.db.query(m.VehicleExpense).count(), 1)

    def test_roles_configuration_and_settings_preservation(self):
        self.assertEqual(
            self.client.put(self.root + "/config", {}, self.viewer_token).status_code, 403
        )
        self.assertEqual(self.mapping(token=self.viewer_token).status_code, 403)
        day = (datetime.now(LOCAL) - timedelta(days=2)).date().isoformat()
        query = {"start_date": day, "end_date": day}
        self.assertEqual(
            self.client.post(self.root + "/sync", query, self.viewer_token).status_code, 403
        )
        self.assertEqual(self.client.post(self.root + "/sync", query).status_code, 400)
        self.configure()
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.client.post(self.root + "/sync", query).status_code, 503)
        settings = self.client.get("/api/supplier-workspace/settings").json()
        self.assertEqual(
            self.client.put("/api/supplier-workspace/settings", settings).status_code, 200
        )
        self.assertEqual(self.client.get(self.root).json()["config"]["branch_code"], "001")
        response = self.sync(fixture(success="false"))
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("Provider message", response.text)
        self.assertEqual(self.db.query(m.IntegrationEvent).count(), 0)


del SupplierWorkspaceTests
