"""Marketplace requests/bids and supplier offers share one versioned commercial decision."""

from fastapi import HTTPException

from app import models as m
from app.common.time import business_today, stamp
from app.offer_history import capture
from app.supplier_schemas import OperationInput
from app.supplier_service import append_record, audit, link_customer


def editable(db, quote, bid=None):
    if quote.status in {
        "Teklif Onaylandı",
        "Sözleşme İmzalandı",
        "Sözleşme Yapıldı",
        "İstek Silindi",
        "Silindi",
    }:
        raise HTTPException(
            409, "Sonuçlanmış talebe teklif verilemez; yeni talep veya revizyon gerekli."
        )
    if bid:
        link = db.get(m.MarketplaceOfferLink, bid.id)
        offer = db.get(m.SupplierOperation, link.offer_id) if link else None
        if offer and offer.status == "Onaylandı":
            raise HTTPException(409, "Kabul edilmiş teklifin şartları değiştirilemez.")


def upsert(db, quote, bid):
    if not quote.customer_id:
        return None  # Historical anonymous requests require identity reconciliation first.
    supplier = db.get(m.Supplier, bid.supplier_id)
    ctx = {"id": supplier.id, "actor": supplier.name, "role": "owner"}
    link_customer(db, supplier.id, quote.customer_id)
    link = db.get(m.MarketplaceOfferLink, bid.id)
    offer = db.get(m.SupplierOperation, link.offer_id) if link else None
    details = {
        "quote_id": quote.id,
        "bid_id": bid.id,
        "source": "marketplace",
        "months": quote.duration_months or 12,
        "quantity": quote.vehicle_count or 1,
        "annual_km": quote.estimated_annual_mileage or 0,
        "terms": bid.notes,
        "request_items": quote.items or [],
        "request_details": quote.details or {},
        "requested_segment": quote.vehicle_segment,
        "requested_type": quote.vehicle_type,
    }
    if offer:
        if offer.status not in {"Taslak", "Beklemede", "Revizyon Bekliyor", "Reddedildi"}:
            raise HTTPException(409, "Teklif sürümü değiştirilemez.")
        offer.amount = bid.monthly_price_try
        offer.details = details
        offer.status = "Beklemede"
        offer.version += 1
        offer.updated_at = stamp()
        capture(db, offer)
        audit(db, ctx, offer, "İhale teklifi revize edilerek gönderildi")
    else:
        offer = append_record(
            db,
            ctx,
            "offer",
            OperationInput(
                title=f"TLP-{quote.id:06d} / {quote.company_name}",
                customer_id=quote.customer_id,
                date=business_today(),
                amount=bid.monthly_price_try,
                details=details,
            ),
        )
        offer.status = "Beklemede"
        offer.version += 1
        capture(db, offer)
        db.add(
            m.MarketplaceOfferLink(
                bid_id=bid.id, quote_id=quote.id, supplier_id=bid.supplier_id, offer_id=offer.id
            )
        )
        audit(db, ctx, offer, "İhale teklifi müşteriye gönderildi")
    return offer


def sync_decision(db, offer, decision):
    link = db.query(m.MarketplaceOfferLink).filter_by(offer_id=offer.id).first()
    if not link:
        return
    bid = db.get(m.SupplierBid, link.bid_id)
    quote = db.get(m.Quote, link.quote_id)
    bid.status = {"accept": "Onaylandı", "reject": "Reddedildi", "revise": "Revizyon Bekliyor"}[
        decision
    ]
    if decision == "accept":
        quote.status = "Teklif Onaylandı"
        quote.monthly_price_try = bid.monthly_price_try
        for other in (
            db.query(m.SupplierBid)
            .filter(m.SupplierBid.quote_id == quote.id, m.SupplierBid.id != bid.id)
            .all()
        ):
            if other.status == "Onaylandı":
                raise HTTPException(409, "Bu talep başka bir teklifle sonuçlandı.")
            other.status = "Reddedildi"
            other_link = db.get(m.MarketplaceOfferLink, other.id)
            row = db.get(m.SupplierOperation, other_link.offer_id) if other_link else None
            if row and row.status not in {"İptal", "Reddedildi"}:
                row.status = "Reddedildi"
                row.version += 1
                row.updated_at = stamp()
                capture(db, row)
                audit(
                    db,
                    {"id": row.supplier_id, "actor": "Müşteri teklif kararı"},
                    row,
                    "Müşteri başka teklifi kabul etti",
                )


def decide_legacy(db, bid, target):
    link = db.get(m.MarketplaceOfferLink, bid.id)
    quote = db.get(m.Quote, bid.quote_id)
    if not link:
        if not quote.customer_id:
            raise HTTPException(400, "Talep önce doğrulanmış müşteri hesabıyla eşleştirilmeli.")
        offer = upsert(db, quote, bid)
    else:
        offer = db.get(m.SupplierOperation, link.offer_id)
    if offer.status == "Onaylandı" and target == "Onaylandı":
        return
    if offer.status != "Beklemede":
        raise HTTPException(409, "Teklif güncellendi veya karar verildi.")
    decision = "accept" if target == "Onaylandı" else "reject"
    customer = db.get(m.Customer, offer.customer_id)
    db.add(
        m.CustomerOfferDecision(
            offer_id=offer.id,
            offer_version=offer.version,
            customer_id=offer.customer_id,
            decision=decision,
            note="Müşteri ihale ekranı kararı",
            actor=customer.company_name,
            created_at=stamp(),
        )
    )
    offer.details = {
        **offer.details,
        "customer_decision": decision,
        "customer_decision_version": offer.version,
        "customer_decision_at": stamp(),
        "acceptance_source": "customer_portal",
    }
    offer.status = target
    offer.version += 1
    offer.updated_at = stamp()
    capture(db, offer)
    sync_decision(db, offer, decision)
    audit(
        db,
        {"id": offer.supplier_id, "actor": customer.company_name},
        offer,
        "Müşteri ihale kararı: " + target,
    )
