import unittest
import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

from test_supplier_workspace import SupplierWorkspaceTests

from app.supplier_reports import REPORTS, financial_ledger, pdf_bytes, xlsx_bytes


class SupplierReportTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create
    status = SupplierWorkspaceTests.status

    def test_invoice_tax_validation_profit_and_tenant_reports(self):
        invoice = self.create(
            "invoice",
            amount=36000,
            details={
                "invoice_no": "NET-1",
                "direction": "gelir",
                "net_amount": 30000,
                "tax_rate": 20,
            },
        )
        self.status(invoice, "Kesildi")
        expense = self.create(
            "invoice",
            amount=12000,
            details={
                "invoice_no": "NET-2",
                "direction": "gider",
                "net_amount": 10000,
                "tax_rate": 20,
            },
        )
        self.status(expense, "Kesildi")
        result = self.client.get("/api/supplier-workspace/reports/profit_vehicle").json()
        self.assertEqual(result["rows"][0]["net_profit"], 20000)
        self.assertEqual(result["rows"][0]["gross_margin"], 24000)
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/reports/profit_vehicle", self.other_token
            ).json()["rows"],
            [],
        )
        bad = self.client.post(
            "/api/supplier-workspace/records/invoice",
            self.payload(
                amount=120,
                details={
                    "invoice_no": "BAD",
                    "direction": "gelir",
                    "net_amount": 100,
                    "tax_rate": 10,
                },
            ),
        )
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(len(self.client.get("/api/supplier-workspace/reports/catalog").json()), 18)
        for report in REPORTS:
            response = self.client.get("/api/supplier-workspace/reports/" + report)
            self.assertEqual(response.status_code, 200, (report, response.text))
        filtered = self.client.get(
            "/api/supplier-workspace/reports/profit_vehicle?customer=2"
        ).json()
        self.assertEqual(filtered["rows"], [])
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/reports/fleet?start=2027-01-01&end=2026-01-01"
            ).status_code,
            400,
        )

    def test_real_xlsx_strings_and_pdf_turkish(self):
        report = {
            "title": "Müşteri Kârlılığı / Şirket Özeti",
            "generated_at": "2026-10-14",
            "note": "Vergi ayrımı eksik veriler tahmin edilmez.",
            "columns": ["plate", "note", "amount"],
            "labels": {"plate": "Plaka", "note": "Açıklama", "amount": "Tutar"},
            "rows": [
                {
                    "plate": "34 ABC 123",
                    "note": '=HYPERLINK("https://example.test") — Şişli / Çeşme / ıİğĞşŞ',
                    "amount": 30000,
                }
            ],
        }
        content = xlsx_bytes(report)
        with zipfile.ZipFile(BytesIO(content)) as archive:
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            self.assertEqual(sheet.findall(".//s:f", ns), [])
            self.assertIn("Şişli", archive.read("xl/worksheets/sheet1.xml").decode())
            self.assertIn("<v>30000</v>", archive.read("xl/worksheets/sheet1.xml").decode())
        content = pdf_bytes(report)
        self.assertTrue(content.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", content[-20:])
        self.assertGreater(len(content), 10000)
        self.assertEqual(
            self.client.get(
                "/api/supplier-workspace/reports/fleet?format=xlsx", self.viewer_token
            ).status_code,
            403,
        )

    def test_missing_tax_is_unknown_and_allocation_rounding_balances(self):
        invoice = {
            "kind": "invoice",
            "id": 1,
            "raw_status": "Kesildi",
            "amount": 120,
            "date": "2026-10-14",
            "customer_id": 1,
            "details": {
                "direction": "gelir",
                "net_amount": 100,
                "tax_rate": 20,
                "vehicle_allocations": [
                    {"vehicle_id": "car", "amount": 40},
                    {"vehicle_id": "car2", "amount": 40},
                    {"vehicle_id": "car3", "amount": 40},
                ],
            },
        }
        data = {"vehicles": [], "records": [invoice], "fuel": [], "hgs": [], "service": []}
        ledger = financial_ledger(data)
        self.assertEqual(round(sum(r["net_amount"] for r in ledger), 2), 100)
        self.assertEqual(round(sum(r["tax_amount"] for r in ledger), 2), 20)
        old = self.create("invoice", details={"invoice_no": "OLD", "direction": "gelir"})
        self.status(old, "Kesildi")
        result = self.client.get("/api/supplier-workspace/reports/profit_vehicle").json()
        self.assertIsNone(result["rows"][0]["net_profit"])
        self.assertIn("Vergi ayrımı eksik", result["rows"][0]["note"])


del SupplierWorkspaceTests
