"""Remove only the inspected local legacy test identities; dry-run by default.

No age-based deletion, fuzzy matching, administrator deletion or cascading cleanup.
Unexpected identities/dependencies abort the transaction. Backups include private data.
"""

import argparse
import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

CUSTOMERS = {1: ("Test A.Ş.", "test_auto@fleet.com"), 2: ("test", "test@test.com")}
QUOTES = {i: ("test", "test@test.com") for i in (2, 3, 4, 5, 7, 8, 9)}
QUOTES[6] = ("Test Firma A.Ş.", "info@teknoholding.com")
# Explicitly confirmed as test data by the user after the initial inventory.
QUOTES[1] = ("Tekno Holding", "info@teknoholding.com")


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def inspect(connection):
    selected = {}
    for table, fingerprints, name in [
        ("customers", CUSTOMERS, "company_name"),
        ("quotes", QUOTES, "company_name"),
    ]:
        rows = []
        for row_id, expected in fingerprints.items():
            row = connection.execute(
                f"SELECT {quoted(name)},email FROM {table} WHERE id=?", (row_id,)
            ).fetchone()
            if row is None:
                continue
            if tuple(row) != expected:
                raise RuntimeError(f"{table}:{row_id} kimliği değişmiş; otomatik silme durduruldu.")
            rows.append(row_id)
        selected[table] = rows
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    # Protect both declared FKs and older columns that lack declared constraints.
    for table in tables:
        cols = {r[1] for r in connection.execute(f"PRAGMA table_info({quoted(table)})")}
        for parent, column in [("customers", "customer_id"), ("quotes", "quote_id")]:
            ids = selected[parent]
            if table == "quotes" and parent == "customers":
                keep = (
                    connection.execute(
                        "SELECT id FROM quotes WHERE customer_id IN ("
                        + ",".join("?" for _ in ids)
                        + ")",
                        ids,
                    ).fetchall()
                    if ids
                    else []
                )
                if any(r[0] not in selected["quotes"] for r in keep):
                    raise RuntimeError("Test müşterisine bağlı korunacak teklif var.")
                continue
            if column in cols and ids:
                count = connection.execute(
                    f"SELECT count(*) FROM {quoted(table)} WHERE {quoted(column)} IN ("
                    + ",".join("?" for _ in ids)
                    + ")",
                    ids,
                ).fetchone()[0]
                if count:
                    raise RuntimeError(
                        f"{table}: {count} bağlı kayıt var; ayrıca değerlendirilmesi gerekir."
                    )
        if table == "portal_sessions" and selected["customers"]:
            count = connection.execute(
                "SELECT count(*) FROM portal_sessions WHERE kind='customer' AND subject_id IN ("
                + ",".join("?" for _ in selected["customers"])
                + ")",
                selected["customers"],
            ).fetchone()[0]
            if count:
                raise RuntimeError("Müşteriye bağlı oturumlar var; ayrı iptal adımı gerekir.")
    for table in tables:
        for fk in connection.execute(f"PRAGMA foreign_key_list({quoted(table)})"):
            parent, child_column, parent_column = fk[2], fk[3], fk[4]
            if parent not in selected or not selected[parent] or parent_column != "id":
                continue
            ids = selected[parent]
            query = (
                f"SELECT count(*) FROM {quoted(table)} WHERE {quoted(child_column)} IN ("
                + ",".join("?" for _ in ids)
                + ")"
            )
            if connection.execute(query, ids).fetchone()[0] and not (
                table == "quotes" and parent == "customers"
            ):
                raise RuntimeError(f"{table}: bağlı kayıt bulundu; silme durduruldu.")
    return selected


def clean(database, backup_dir=None, apply=False):
    database = Path(database).resolve(strict=True)
    connection = sqlite3.connect(
        database.as_uri() + ("?mode=rw" if apply else "?mode=ro"), uri=True, timeout=5
    )
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        if apply:
            connection.execute("BEGIN IMMEDIATE")
        selected = inspect(connection)
        result = {
            "database": str(database),
            "mode": "apply" if apply else "dry-run",
            "selected_ids": selected,
            "deleted": {},
        }
        if not apply or not any(selected.values()):
            return result
        if not backup_dir:
            raise RuntimeError("Silmeden önce yedek klasörü gerekli.")
        directory = Path(backup_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = (
            directory / f"{database.stem}-before-cleanup-{stamp}-{uuid.uuid4().hex[:8]}.sqlite3"
        )
        fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        # A separate read connection can take a snapshot while the writer holds the reserved lock.
        with (
            closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(backup)) as target,
        ):
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Yedek doğrulanamadı.")
        result["backup"] = str(backup)
        before_fk = list(connection.execute("PRAGMA foreign_key_check"))
        for table in ["quotes", "customers"]:
            ids = selected[table]
            if not ids:
                continue
            connection.executemany(f"DELETE FROM {table} WHERE id=?", [(i,) for i in ids])
            result["deleted"][table] = len(ids)
        after_fk = list(connection.execute("PRAGMA foreign_key_check"))
        if after_fk != before_fk:
            raise RuntimeError("İlişki bütünlüğü değişti; işlem geri alındı.")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Veritabanı doğrulanamadı.")
        connection.commit()
        return result
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    parser.add_argument("--backup-dir")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(clean(args.database, args.backup_dir, args.apply), ensure_ascii=False, indent=2)
    )
