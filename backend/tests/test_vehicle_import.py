import io
import unittest
import zipfile
from xml.sax.saxutils import escape

from app import vehicle_import as vi


def xlsx(rows):
    """Minimal .xlsx with inline strings, like many export tools write."""

    def ref(c, r):
        letters = ""
        c += 1
        while c:
            c, rem = divmod(c - 1, 26)
            letters = chr(65 + rem) + letters
        return f"{letters}{r}"

    body = "".join(
        f'<row r="{r}">'
        + "".join(
            f'<c r="{ref(c, r)}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
            for c, v in enumerate(row)
        )
        + "</row>"
        for r, row in enumerate(rows, start=1)
    )
    sheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{body}</sheetData></worksheet>"
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("xl/workbook.xml", "<workbook/>")
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return stream.getvalue()


HEADER = ["Plaka", "Şase", "Marka", "Tip", "Model Yılı", "Yakıt", "KM", "Muayene Bitiş Tarih"]


class VehicleImportParsingTests(unittest.TestCase):
    def test_maps_export_columns_and_normalizes_values(self):
        table = vi.read_table(
            xlsx(
                [
                    HEADER + ["Hasarlı", "Lokasyon"],
                    [
                        "34PYE003 ",
                        "vr7edyhz8tj697022",
                        "CITROEN",
                        "BERLINGO PLUS 1.5 BLUEHDI 2026",
                        "2026",
                        "Motorin",
                        "7000",
                        "1970-01-01",
                        "Evet",
                        "İstanbul",
                    ],
                    ["", "", "", "", "", "", "", "", "", ""],
                ]
            ),
            "liste.xlsx",
        )
        rows, ignored = vi.build_rows(table)
        self.assertEqual(len(rows), 1)
        v = rows[0]["values"]
        self.assertEqual(v["plate"], "34 PYE 003")
        self.assertEqual(v["chassis_no"], "VR7EDYHZ8TJ697022")
        self.assertEqual(
            (v["brand"], v["model"], v["version"]), ("Citroen", "BERLINGO", "PLUS 1.5 BLUEHDI")
        )
        self.assertEqual(v["fuel"], "Dizel")
        self.assertIsNone(v["inspection_date"])
        self.assertEqual(v["status"], "Hasar")
        self.assertIn("Lokasyon", ignored)
        self.assertIn("Muayene tarihi yok.", rows[0]["warnings"])

    def test_dates_csv_and_required_columns(self):
        self.assertEqual(vi.parse_date("45000"), "2023-03-15")
        self.assertEqual(vi.parse_date("20.04.2027"), "2027-04-20")
        self.assertEqual(vi.parse_date("2027-04-20 11:35:00"), "2027-04-20")
        self.assertEqual(vi.parse_date("yarın"), "invalid")
        self.assertEqual(vi.brand_name("BMW"), "BMW")
        csv_bytes = "Plaka;Marka\n34 AB 12;Fiat\n".encode("cp1254")
        with self.assertRaises(Exception) as caught:
            vi.build_rows(vi.read_table(csv_bytes, "liste.csv"))
        self.assertIn("Şase", caught.exception.detail)
        with self.assertRaises(Exception):
            vi.read_table(b"not a zip", "liste.xlsx")
        with self.assertRaises(Exception):
            vi.read_table(b"x", "liste.xls")


if __name__ == "__main__":
    unittest.main()
