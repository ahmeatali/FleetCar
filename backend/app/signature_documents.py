"""Immutable manual signed-document evidence. No external e-sign provider is simulated."""

import hashlib
import json
import secrets
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import business_today, stamp
from app.database import get_db
from app.portal_access import access_audit, principal
from app.supplier_context import context, operation
from app.supplier_service import audit

router = APIRouter(tags=["Signature documents"])
DOCUMENTS = Path(__file__).resolve().parent.parent / "uploads" / "signed-documents"
DOCUMENTS.mkdir(parents=True, exist_ok=True)


def current_envelope(db, rid):
    return (
        db.query(m.SignatureEnvelope)
        .filter_by(operation_id=rid)
        .filter(m.SignatureEnvelope.status != "İptal")
        .order_by(m.SignatureEnvelope.id.desc())
        .first()
    )


def locked(db, row):
    envelope = current_envelope(db, row.id)
    if envelope:
        raise HTTPException(
            409,
            "İmzalı belge süreci açık. Değişiklik için önce bekleyen süreci iptal edin; teyidi tamamlanan kayıt yeni sözleşmeyle düzeltilir.",
        )


def ensure_signed(db, row):
    envelope = current_envelope(db, row.id)
    if (
        not envelope
        or envelope.status != "Teyit Edildi"
        or envelope.operation_version != row.version
    ):
        raise HTTPException(
            400, "Güncel sürüme ait imzalı belge ve gerekli tarafların belge teyidi tamamlanmalı."
        )
    document = db.get(m.SignedDocument, envelope.document_id)
    path = DOCUMENTS / document.stored_name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != document.sha256:
        raise HTTPException(409, "İmzalı belge bütünlüğü doğrulanamadı.")
    return envelope


def serialize(db, envelope):
    if not envelope:
        return None
    document = db.get(m.SignedDocument, envelope.document_id)
    record = db.get(m.SupplierOperation, envelope.operation_id)
    return {
        "id": envelope.id,
        "operation_id": envelope.operation_id,
        "number": record.number,
        "kind": record.kind,
        "title": record.title,
        "source": envelope.source,
        "status": envelope.status,
        "operation_version": envelope.operation_version,
        "version": envelope.version,
        "signed_date": envelope.signed_date,
        "required_parties": envelope.required_parties,
        "attestations": envelope.attestations,
        "snapshot": document.snapshot,
        "snapshot_sha256": hashlib.sha256(
            json.dumps(document.snapshot, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "sha256": document.sha256,
        "document_id": document.id,
        "original_name": document.original_name,
        "created_at": envelope.created_at,
        "completed_at": envelope.completed_at,
    }


@router.get("/api/supplier-workspace/records/{rid}/signature")
def supplier_envelope(rid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    operation(db, ctx, rid)
    return serialize(db, current_envelope(db, rid))


@router.post("/api/supplier-workspace/records/{rid}/signed-document")
async def upload(
    rid: int,
    request: Request,
    version: int = Query(gt=0),
    signed_date: date = Query(),
    filename: str = Query(max_length=250),
    ctx=Depends(context),
    db: Session = Depends(get_db),
):
    row = operation(db, ctx, rid)
    if ctx["role"] != "owner":
        raise HTTPException(403, "İmzalı belgeyi şirket sahibi kaydeder.")
    if row.kind not in {"contract", "delivery"} or row.status not in {"Taslak", "Planlandı"}:
        raise HTTPException(400, "Taslak sözleşme veya planlanan teslim kaydı gerekli.")
    if row.version != version:
        raise HTTPException(409, "Kayıt sürümü değişti.")
    locked(db, row)
    if signed_date > business_today():
        raise HTTPException(400, "İmza tarihi gelecekte olamaz.")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 15 * 1024 * 1024:
            raise HTTPException(413, "İmzalı PDF en fazla 15 MB olmalı.")
    if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-2048:]:
        raise HTTPException(415, "İmzalı PDF dosyası gerekli.")
    snapshot = {
        key: getattr(row, key)
        for key in [
            "id",
            "kind",
            "number",
            "title",
            "customer_id",
            "vehicle_id",
            "parent_id",
            "date",
            "end_date",
            "amount",
            "details",
            "version",
        ]
    }
    links = (
        db.query(m.ContractVehicle).filter_by(contract_id=row.id).all()
        if row.kind == "contract"
        else []
    )
    ids = [link.vehicle_id for link in links] or [row.vehicle_id]
    snapshot["vehicles"] = [
        {
            key: getattr(db.get(m.Vehicle, vid), key, None)
            for key in ["id", "plate", "chassis_no", "brand", "model", "year", "mileage"]
        }
        for vid in ids
    ]
    customer = db.get(m.Customer, row.customer_id)
    from app.tenant_visibility import file_visible

    attachments = []
    for file in db.query(m.VehicleFile).filter(m.VehicleFile.vehicle_id.in_(ids)).all():
        file_scope = db.get(m.VehicleFileScope, file.id)
        if (
            file_visible(db, row.customer_id, file)
            or file_scope
            and file_scope.visibility == "asset"
        ):
            attachments.append(
                {"id": file.id, "name": file.original_name, "category": file.category}
            )
    snapshot["files"] = attachments
    snapshot["customer"] = {
        key: getattr(customer, key, None)
        for key in ["id", "company_name", "legal_title", "email", "phone", "address"]
    }
    document = m.SignedDocument(
        supplier_id=ctx["id"],
        customer_id=row.customer_id,
        operation_id=row.id,
        stored_name=secrets.token_hex(24) + ".pdf",
        original_name=Path(filename).name,
        sha256=hashlib.sha256(raw).hexdigest(),
        snapshot=json.loads(json.dumps(snapshot)),
        created_at=stamp(),
    )
    path = DOCUMENTS / document.stored_name
    try:
        path.write_bytes(raw)
        db.add(document)
        db.flush()
        envelope = m.SignatureEnvelope(
            operation_id=row.id,
            supplier_id=ctx["id"],
            customer_id=row.customer_id,
            document_id=document.id,
            operation_version=row.version,
            source="manual_signed_pdf",
            status="Teyit Bekliyor",
            required_parties=(
                ["supplier", "customer", "platform"]
                if row.kind == "contract"
                else ["supplier", "customer"]
            ),
            attestations={},
            signed_date=signed_date.isoformat(),
            created_at=stamp(),
        )
        db.add(envelope)
        db.flush()
        audit(
            db,
            ctx,
            row,
            "Islak imzalı PDF kaydedildi",
            {"envelope_id": envelope.id, "sha256": document.sha256, "source": envelope.source},
        )
        db.commit()
        return serialize(db, envelope)
    except IntegrityError:
        db.rollback()
        path.unlink(missing_ok=True)
        raise HTTPException(409, "Bu sürüm için belge süreci zaten açıldı.")
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


class Attestation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(gt=0)
    confirm: bool


def party_context(request: Request, db: Session = Depends(get_db)):
    p = principal(request, db)
    if p["kind"] == "service" or p["role"] != "owner":
        raise HTTPException(
            403, "Belge teyidi firma sahibi veya platform yöneticisi tarafından yapılmalı."
        )
    return p


def allowed(p, envelope):
    return (
        p["kind"] == "admin"
        or p["kind"] == "supplier"
        and p["id"] == envelope.supplier_id
        or p["kind"] == "customer"
        and p["id"] == envelope.customer_id
    )


@router.post("/api/signature-envelopes/{eid}/attest")
def attest(
    eid: int,
    data: Attestation,
    request: Request,
    p=Depends(party_context),
    db: Session = Depends(get_db),
):
    envelope = db.get(m.SignatureEnvelope, eid)
    if not envelope or not allowed(p, envelope):
        raise HTTPException(404, "Belge süreci bulunamadı.")
    if envelope.version != data.version or envelope.status != "Teyit Bekliyor":
        raise HTTPException(409, "Belge süreci değişti. Yenileyin.")
    if not data.confirm:
        raise HTTPException(400, "Belgeyi ve ilgili sürümün şartlarını doğruladığınızı teyit edin.")
    party = {"supplier": "supplier", "customer": "customer", "admin": "platform"}[p["kind"]]
    if party not in envelope.required_parties or party in envelope.attestations:
        raise HTTPException(409, "Bu tarafın teyidi gerekmiyor veya zaten alındı.")
    row = db.get(m.SupplierOperation, envelope.operation_id)
    if row.version != envelope.operation_version:
        raise HTTPException(409, "Operasyon sürümü değişti.")
    document = db.get(m.SignedDocument, envelope.document_id)
    path = DOCUMENTS / document.stored_name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != document.sha256:
        raise HTTPException(409, "Belge bütünlüğü doğrulanamadı.")
    name = (
        db.get(m.AdminUser, p["id"]).email
        if p["kind"] == "admin"
        else (
            db.get(m.Supplier, p["id"]).name
            if p["kind"] == "supplier"
            else db.get(m.Customer, p["id"]).company_name
        )
    )
    proofs = {
        **envelope.attestations,
        party: {
            "actor": name,
            "subject_id": p["id"],
            "confirmed_at": stamp(),
            "document_sha256": document.sha256,
        },
    }
    complete = all(role in proofs for role in envelope.required_parties)
    updated = (
        db.query(m.SignatureEnvelope)
        .filter_by(id=eid, version=data.version, status="Teyit Bekliyor")
        .update(
            {
                "attestations": proofs,
                "status": "Teyit Edildi" if complete else "Teyit Bekliyor",
                "completed_at": stamp() if complete else None,
                "version": data.version + 1,
            },
            synchronize_session=False,
        )
    )
    if updated != 1:
        db.rollback()
        raise HTTPException(409, "Belge süreci başka işlemle değişti.")
    audit(
        db,
        {"id": envelope.supplier_id, "actor": name},
        row,
        "İmzalı belge teyidi: " + party,
        {"envelope_id": eid, "sha256": document.sha256},
    )
    db.commit()
    db.refresh(envelope)
    return serialize(db, envelope)


@router.post("/api/supplier-workspace/signature-envelopes/{eid}/cancel")
def cancel(eid: int, data: Attestation, ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Firma sahibi yetkisi gerekli.")
    envelope = db.query(m.SignatureEnvelope).filter_by(id=eid, supplier_id=ctx["id"]).first()
    if not envelope:
        raise HTTPException(404, "Belge süreci bulunamadı.")
    changed = (
        db.query(m.SignatureEnvelope)
        .filter_by(id=eid, version=data.version, status="Teyit Bekliyor")
        .update({"status": "İptal", "version": data.version + 1}, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Tamamlanmış veya değişmiş süreç iptal edilemez.")
    row = operation(db, ctx, envelope.operation_id)
    row.version += 1
    row.updated_at = stamp()
    audit(db, ctx, row, "Bekleyen belge süreci iptal edildi", {"envelope_id": eid})
    db.commit()
    return {"ok": True}


@router.get("/api/customer-workspace/signatures")
@router.get("/api/admin/signatures")
def inbox(request: Request, p=Depends(party_context), db: Session = Depends(get_db)):
    if (
        request.url.path.startswith("/api/admin")
        and p["kind"] != "admin"
        or request.url.path.startswith("/api/customer")
        and p["kind"] != "customer"
    ):
        raise HTTPException(403, "Hesap türü eşleşmiyor.")
    query = db.query(m.SignatureEnvelope).filter(m.SignatureEnvelope.status != "İptal")
    if p["kind"] == "customer":
        query = query.filter_by(customer_id=p["id"])
    else:
        query = query.filter(m.SignatureEnvelope.required_parties.contains("platform"))
    access_audit(db, p, request)
    return [
        serialize(db, envelope) for envelope in query.order_by(m.SignatureEnvelope.id.desc()).all()
    ]


@router.get("/api/signed-documents/{docid}")
def download(docid: int, request: Request, db: Session = Depends(get_db)):
    p = principal(request, db)
    document = db.get(m.SignedDocument, docid)
    if not document:
        raise HTTPException(404, "Belge bulunamadı.")
    if p["kind"] == "customer" and p["role"] != "owner":
        raise HTTPException(403, "Firma belgesi için firma sahibi yetkisi gerekli.")
    if not (
        p["kind"] == "admin"
        or p["kind"] == "supplier"
        and p["id"] == document.supplier_id
        or p["kind"] == "customer"
        and p["id"] == document.customer_id
    ):
        raise HTTPException(404, "Belge bulunamadı.")
    path = DOCUMENTS / document.stored_name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != document.sha256:
        raise HTTPException(409, "Belge bütünlüğü doğrulanamadı.")
    access_audit(db, p, request)
    return FileResponse(
        path,
        filename=document.original_name,
        media_type="application/pdf",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
