import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "legacy_cleanup", Path(__file__).resolve().parents[1] / "maintenance/clean_legacy_test_data.py"
)
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class LegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "application.db"
        self.backups = Path(self.folder.name) / "backups"
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript(
                """CREATE TABLE customers(id INTEGER PRIMARY KEY, company_name TEXT,email TEXT);
                CREATE TABLE quotes(id INTEGER PRIMARY KEY,company_name TEXT,email TEXT,customer_id INTEGER);
                CREATE TABLE admin_users(id INTEGER PRIMARY KEY,email TEXT);
                CREATE TABLE vehicles(id TEXT,customer_id INTEGER REFERENCES customers(id));"""
            )
            db.executemany(
                "INSERT INTO customers VALUES(?,?,?)",
                [
                    (1, "Test A.Ş.", "test_auto@fleet.com"),
                    (2, "test", "test@test.com"),
                    (3, "Real Company", "real@company.invalid"),
                ],
            )
            db.executemany(
                "INSERT INTO quotes VALUES(?,?,?,?)",
                [
                    (1, "Tekno Holding", "info@teknoholding.com", None),
                    (2, "test", "test@test.com", 2),
                    (10, "Real Company", "real@company.invalid", 3),
                ],
            )
            db.execute("INSERT INTO admin_users VALUES(1,'owner@company.invalid')")

    def tearDown(self):
        self.folder.cleanup()

    def counts(self, path=None):
        with closing(sqlite3.connect(path or self.path)) as db:
            return [
                db.execute("SELECT count(*) FROM " + table).fetchone()[0]
                for table in ["customers", "quotes", "admin_users"]
            ]

    def test_backup_exact_cleanup_preserves_real_data_and_is_idempotent(self):
        self.assertEqual(
            cleanup.clean(self.path)["selected_ids"], {"customers": [1, 2], "quotes": [2, 1]}
        )
        self.assertEqual(self.counts(), [3, 3, 1])
        result = cleanup.clean(self.path, self.backups, True)
        self.assertEqual(self.counts(result["backup"]), [3, 3, 1])
        self.assertEqual(self.counts(), [1, 1, 1])
        self.assertEqual(Path(result["backup"]).stat().st_mode & 0o777, 0o600)
        self.assertEqual(cleanup.clean(self.path, self.backups, True)["deleted"], {})
        self.assertEqual(len(list(self.backups.iterdir())), 1)

    def test_changed_identity_aborts(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE customers SET company_name='Real person' WHERE id=1")
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.path, self.backups, True)
        self.assertEqual(self.counts(), [3, 3, 1])
        self.assertFalse(self.backups.exists())

    def test_dependent_business_data_aborts(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO vehicles VALUES('actual-car',1)")
        with self.assertRaises(RuntimeError):
            cleanup.clean(self.path, self.backups, True)
        self.assertEqual(self.counts(), [3, 3, 1])

    def test_write_failure_rolls_back_deleted_quotes(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "CREATE TRIGGER prevent_delete BEFORE DELETE ON customers BEGIN SELECT RAISE(ABORT,'failure'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            cleanup.clean(self.path, self.backups, True)
        self.assertEqual(self.counts(), [3, 3, 1])
        self.assertEqual(len(list(self.backups.iterdir())), 1)
