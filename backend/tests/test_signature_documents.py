import unittest

from test_supplier_workspace import SupplierWorkspaceTests, sign_fixture

from app import models as m
from app.portal_access import mint


class SignatureDocumentTests(unittest.TestCase):
    setUp = SupplierWorkspaceTests.setUp
    tearDown = SupplierWorkspaceTests.tearDown
    payload = SupplierWorkspaceTests.payload
    create = SupplierWorkspaceTests.create

    def test_three_parties_required_and_document_immutable(self):
        contract = self.create("contract")
        response = self.client.post(
            f'/api/supplier-workspace/records/{contract["id"]}/status',
            {"status": "Aktif", "version": contract["version"]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.db.get(m.Vehicle, "car").customer_id)
        sign_fixture(self, contract)
        envelope = self.client.get(
            f'/api/supplier-workspace/records/{contract["id"]}/signature'
        ).json()
        self.assertEqual(envelope["source"], "manual_signed_pdf")
        self.assertEqual(set(envelope["attestations"]), {"supplier", "customer", "platform"})
        self.assertEqual(envelope["status"], "Teyit Edildi")
        self.assertEqual(
            self.client.put(
                f'/api/supplier-workspace/records/{contract["id"]}',
                self.payload(version=1, amount=20000),
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(
                f'/api/supplier-workspace/signature-envelopes/{envelope["id"]}/cancel',
                {"version": envelope["version"], "confirm": True},
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.get(
                f'/api/signed-documents/{envelope["document_id"]}', self.other_token
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                f'/api/signed-documents/{envelope["document_id"]}', mint(self.db, "customer", 2)
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                f'/api/signed-documents/{envelope["document_id"]}', mint(self.db, "customer", 1)
            ).status_code,
            200,
        )
        document = self.db.get(m.SignedDocument, envelope["document_id"])
        import app.signature_documents as signatures

        (signatures.DOCUMENTS / document.stored_name).write_bytes(b"%PDF-corrupted")
        self.assertEqual(self.client.get(f"/api/signed-documents/{document.id}").status_code, 409)
        self.assertEqual(
            self.client.post(
                f'/api/supplier-workspace/records/{contract["id"]}/status',
                {"status": "Aktif", "version": contract["version"]},
            ).status_code,
            409,
        )

    def test_upload_and_attestation_scope_and_revision_binding(self):
        from io import BytesIO

        from reportlab.pdfgen.canvas import Canvas

        contract = self.create("contract")
        stream = BytesIO()
        pdf = Canvas(stream)
        pdf.drawString(30, 800, "Manual fixture.")
        pdf.save()
        path = f'/api/supplier-workspace/records/{contract["id"]}/signed-document?version=1&signed_date=2026-01-01&filename=contract.pdf'
        self.assertEqual(self.client.post(path, b"invalid pdf").status_code, 415)
        self.assertEqual(self.client.post(path, stream.getvalue(), self.ops_token).status_code, 403)
        response = self.client.post(path, stream.getvalue())
        self.assertEqual(response.status_code, 200, response.text)
        envelope = response.json()
        self.assertEqual(self.client.post(path, stream.getvalue()).status_code, 409)
        response = self.client.post(
            f'/api/signature-envelopes/{envelope["id"]}/attest',
            {"version": envelope["version"], "confirm": False},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.client.post(
                f'/api/signature-envelopes/{envelope["id"]}/attest',
                {"version": 1, "confirm": True},
                self.other_token,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f'/api/supplier-workspace/signature-envelopes/{envelope["id"]}/cancel',
                {"version": 1, "confirm": True},
            ).status_code,
            200,
        )
        revised = self.client.get("/api/supplier-workspace/records/contract").json()[0]
        self.assertEqual(revised["version"], 2)
        self.assertEqual(
            self.client.put(
                f'/api/supplier-workspace/records/{contract["id"]}',
                self.payload(version=2, amount=20000),
            ).status_code,
            200,
        )
        # The cancelled document remains preserved, with its old version/hash.
        self.assertEqual(self.db.query(m.SignedDocument).count(), 1)
        self.assertEqual(self.db.query(m.SignatureEnvelope).one().status, "İptal")


del SupplierWorkspaceTests
