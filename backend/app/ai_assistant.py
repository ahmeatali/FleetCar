"""Claude-powered fleet insights and document reading for rental suppliers.

The platform computes the numbers; Claude only interprets them and writes
recommendations, so every suggestion can be traced back to a metric shown
next to it. Users never chat with the model: insights are generated on demand
and stored, documents are read into a preview the user confirms.
"""

import base64
import hashlib
import json
import os
from datetime import date, datetime, timedelta

from fastapi import HTTPException

from app import models as m
from app.common.time import business_today, stamp

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
CACHE_HOURS = 12
MAX_VEHICLES = 150
DOC_MAX_BYTES = 15 * 1024 * 1024
DOC_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}

_client = None


def client():
    """Lazily build the SDK client; the key comes from backend/.env via email_utils."""
    global _client
    if _client is None:
        import anthropic

        from app import email_utils  # noqa: F401  (loads backend/.env into os.environ)

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise HTTPException(503, "AI servisi yapılandırılmamış (ANTHROPIC_API_KEY yok).")
        _client = anthropic.Anthropic(max_retries=2, timeout=180.0)
    return _client


def ask(system, content, schema, effort="medium", max_tokens=64000):
    """One structured-output call. Returns (parsed JSON, usage dict).

    Streams so a long thinking + output turn does not hit the HTTP timeout; thinking
    tokens count toward max_tokens, hence the generous ceiling.
    """
    import anthropic

    try:
        with client().beta.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        ) as stream:
            response = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise HTTPException(
            503, "AI anahtarı geçersiz. backend/.env içindeki anahtarı kontrol edin."
        )
    except anthropic.PermissionDeniedError:
        raise HTTPException(503, "AI anahtarının bu işleme yetkisi yok.")
    except anthropic.RateLimitError:
        raise HTTPException(429, "AI servisi şu an yoğun. Birkaç dakika sonra tekrar deneyin.")
    except anthropic.BadRequestError as e:
        raise HTTPException(400, f"AI isteği reddedildi: {e.message}")
    except anthropic.APIStatusError as e:
        raise HTTPException(502, f"AI servisi hata verdi ({e.status_code}). Tekrar deneyin.")
    except anthropic.APIConnectionError:
        raise HTTPException(502, "AI servisine bağlanılamadı.")
    if response.stop_reason == "refusal":
        raise HTTPException(422, "AI bu içeriği işlemeyi reddetti.")
    if response.stop_reason == "max_tokens":
        raise HTTPException(502, "AI yanıtı çok uzun olduğu için yarıda kesildi. Tekrar deneyin.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(502, "AI yanıtı okunamadı. Tekrar deneyin.")
    usage = {
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return parsed, usage


# --------------------------------------------------------------------------- fleet metrics


def _day(value):
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _months(a, b):
    return max(0.0, (b - a).days / 30.44)


def fleet_metrics(db, sid=None, customer_id=None):
    """Deterministic per-vehicle usage metrics and the rule flags that select vehicles.

    Scoped to a supplier's own fleet (sid) or to the vehicles a customer rents (customer_id).
    """
    today = business_today()
    owner = (
        m.Vehicle.customer_id == customer_id
        if customer_id is not None
        else m.Vehicle.supplier_id == sid
    )
    cars = (
        db.query(m.Vehicle)
        .filter(owner, m.Vehicle.is_active.is_(True))
        .filter((m.Vehicle.status.is_(None)) | (m.Vehicle.status != "Satıldı"))
        .all()
    )
    ids = [c.id for c in cars]
    records = {}
    for r in db.query(m.VehicleMileageRecord).filter(m.VehicleMileageRecord.vehicle_id.in_(ids)):
        records.setdefault(r.vehicle_id, []).append((_day(r.recorded_at), int(r.mileage or 0)))
    last_return = {}
    rentals = db.query(m.Rental).filter(m.Rental.vehicle_id.in_(ids))
    if customer_id is None:
        rentals = rentals.filter(m.Rental.supplier_id == sid)
    for r in rentals:
        end = _day(r.returned_at) or (_day(r.ends_at) if r.status == "Tamamlandı" else None)
        if end and (r.vehicle_id not in last_return or end > last_return[r.vehicle_id]):
            last_return[r.vehicle_id] = end
    customers = {
        c.id: c.company_name
        for c in db.query(m.Customer).filter(
            m.Customer.id.in_({c.customer_id for c in cars if c.customer_id})
        )
    }
    suppliers = (
        {
            s.id: s.name
            for s in db.query(m.Supplier).filter(
                m.Supplier.id.in_({c.supplier_id for c in cars if c.supplier_id})
            )
        }
        if customer_id is not None
        else {}
    )
    rows = []
    for c in cars:
        history = sorted((d, km) for d, km in records.get(c.id, []) if d)
        start, end = _day(c.contract_start_date), _day(c.contract_end_date)
        row = {
            "plate": c.plate,
            "vehicle": " ".join(x for x in [c.brand, c.model] if x),
            "segment": c.vehicle_segment,
            "status": (
                "Bayide"
                if c.status == "Bayide"
                else "Serviste"
                if c.status in {"Servis", "Serviste", "Lastik Değişiminde"}
                else "Hasarlı"
                if c.status in {"Hasar", "Kaza"}
                else "Kirada"
                if c.customer_id
                else "Havuzda"
            ),
            "customer": customers.get(c.customer_id),
            "km": int(c.mileage or 0),
            "this_month_km": c.current_month_km,
            "monthly_km_limit": c.monthly_km_limit,
            "monthly_rent_try": c.monthly_rent,
            "contract_start": c.contract_start_date,
            "contract_end": c.contract_end_date,
            "contract_months": c.contract_duration_months,
            "committed_km": c.contract_committed_km,
            "inspection_date": c.inspection_date,
            "flags": [],
        }
        if customer_id is not None:  # the customer's own view: who supplies it, who uses it
            del row["customer"]
            row["supplier"] = suppliers.get(c.supplier_id)
            row["assigned_to"] = c.assignment_user
        recent = [(d, km) for d, km in history if d >= today - timedelta(days=90)]
        if len(recent) >= 2 and (recent[-1][0] - recent[0][0]).days >= 14:
            span = _months(recent[0][0], recent[-1][0])
            row["avg_monthly_km_90d"] = round((recent[-1][1] - recent[0][1]) / span)
        if start and start <= today and c.customer_id:
            elapsed = _months(start, today)
            before = [km for d, km in history if d <= start]
            after = [km for d, km in history if d > start]
            start_km = before[-1] if before else (after[0] if after else None)
            committed = c.contract_committed_km or (
                (c.monthly_km_limit or 0) * (c.contract_duration_months or 0) or None
            )
            duration = c.contract_duration_months or (
                round(_months(start, end)) if end and end > start else None
            )
            if start_km is not None and elapsed >= 1 and committed and duration:
                driven = row["km"] - start_km
                expected = committed * min(elapsed, duration) / duration
                projected = driven / elapsed * duration
                row.update(
                    {
                        "months_elapsed": round(elapsed, 1),
                        "km_driven_in_contract": driven,
                        "km_expected_to_date": round(expected),
                        "usage_ratio": round(driven / expected, 2) if expected else None,
                        "projected_contract_km": round(projected),
                        "projected_overage_km": round(projected - committed),
                    }
                )
                ratio = row["usage_ratio"] or 0
                if ratio > 1.1:
                    row["flags"].append("km_overage_risk")
                elif ratio < 0.5 and elapsed >= 2:
                    row["flags"].append("low_usage")
        limit, month = c.monthly_km_limit, c.current_month_km
        if limit and month is not None and c.customer_id:
            if month > limit:
                row["flags"].append("monthly_limit_exceeded")
            elif month < 0.4 * limit and today.day >= 20:
                row["flags"].append("low_monthly_usage")
        if row["status"] == "Havuzda":
            since = last_return.get(c.id) or (history[-1][0] if history else None)
            if since:
                row["idle_days"] = (today - since).days
                if row["idle_days"] >= 30:
                    row["flags"].append("idle_in_pool")
        inspection = _day(c.inspection_date)
        if inspection and (inspection - today).days <= 30:
            row["flags"].append("inspection_due")
        if end and c.customer_id and 0 <= (end - today).days <= 60:
            row["flags"].append("contract_ending")
        rows.append(row)
    return rows


KEYS = ("customer", "supplier", "assigned_to")


def fleet_overview(rows):
    def count(key):
        totals = {}
        for r in rows:
            label = r.get(key) or "Belirtilmemiş"
            totals[label] = totals.get(label, 0) + 1
        return totals

    return {
        "vehicle_count": len(rows),
        "by_status": count("status"),
        "by_segment": count("segment"),
        # supplier rows carry "customer"; customer rows carry "supplier" and "assigned_to"
        **{f"by_{key}": count(key) for key in KEYS if any(key in r for r in rows)},
        "flag_counts": {
            flag: sum(1 for r in rows if flag in r["flags"])
            for flag in sorted({f for r in rows for f in r["flags"]})
        },
    }


INSIGHT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "km_asimi",
                            "dusuk_kullanim",
                            "transfer",
                            "iade",
                            "havuzda_bekleyen",
                            "muayene_bakim",
                            "sozlesme",
                            "diger",
                        ],
                    },
                    "severity": {"type": "string", "enum": ["yuksek", "orta", "dusuk"]},
                    "plates": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "rationale": {"type": "string"},
                    "estimated_monthly_impact_try": {"type": "number"},
                },
                "required": [
                    "type",
                    "severity",
                    "plates",
                    "title",
                    "recommendation",
                    "rationale",
                    "estimated_monthly_impact_try",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "insights"],
    "additionalProperties": False,
}

INSIGHT_SYSTEM = """Sen bir araç kiralama şirketinin filo analistisin. Şirketin yöneticisine,
kendi filosundaki araçlar için uygulanabilir öneriler yazıyorsun. Yönetici soru sormayacak;
öneriler kendi başına anlaşılır olmalı.

Sana platformun hesapladığı metrikler JSON olarak verilecek. Kurallar:
- Yalnızca verilen veriye dayan. Veride olmayan bir rakamı, müşteriyi veya plakayı uydurma.
- Her öneride ilgili plakaları "plates" alanına, verideki yazımıyla aynen yaz.
- "rationale" alanında öneriyi hangi metriğe dayandırdığını rakamla göster
  (ör. "Sözleşmenin 7. ayında 41.200 km; beklenen 29.000 km, oran 1,42").
- Somut aksiyon öner: km paketi revizyonu veya aşım faturası, aracın daha çok km yapan bir
  müşteriye / birime aktarılması, düşük kullanılan aracın iadesi ya da kısa dönem kiralamaya
  alınması, havuzda bekleyen aracın pazarlanması, muayene/bakım planlaması, sözleşme yenileme.
- Benzer durumdaki araçları tek öneride grupla; aynı aracı birden çok öneride tekrarlama,
  ancak bir aracı aşım riski olan bir müşteriden düşük kullanan bir müşteriye aktarma gibi
  eşleştirme önerileri değerlidir.
- "estimated_monthly_impact_try": yalnızca verideki kira/km değerlerinden makul bir aylık etki
  hesaplayabiliyorsan TL olarak yaz; hesaplayamıyorsan 0 yaz.
- En önemli en fazla 12 öneriyi önem sırasına göre ver. Türkçe, kısa ve net yaz.
- "summary": filonun genel durumunu 2-3 cümleyle özetle."""


CUSTOMER_INSIGHT_SYSTEM = """Sen uzun dönem araç kiralayan bir şirketin filo danışmanısın.
Şirketin filo yöneticisine, kiraladığı araçlar için maliyet ve verimlilik önerileri
yazıyorsun. Yönetici soru sormayacak; öneriler kendi başına anlaşılır olmalı.

Sana platformun hesapladığı metrikler JSON olarak verilecek. "supplier" aracı kiralayan
tedarikçi, "assigned_to" aracı kullanan kişi veya birimdir. Kurallar:
- Yalnızca verilen veriye dayan. Veride olmayan bir rakamı, tedarikçiyi, kişiyi veya plakayı
  uydurma.
- Her öneride ilgili plakaları "plates" alanına, verideki yazımıyla aynen yaz.
- "rationale" alanında öneriyi hangi metriğe dayandırdığını rakamla göster
  (ör. "Sözleşmenin 7. ayında 41.200 km; beklenen 29.000 km, oran 1,42").
- Kiracının çıkarına somut aksiyon öner: sözleşme sonunda aşım ücreti doğmadan km paketini
  tedarikçiyle revize etmek, çok km yapan ve az km yapan araçları kullanıcılar/birimler arasında
  değiştirerek limitleri dengelemek, sürekli az kullanılan aracı iade etmek veya daha küçük
  segmente geçmek, muayene/bakım tarihini kaçırmamak, bitmek üzere olan sözleşmeyi zamanında
  yenilemek veya teklif toplamak.
- Benzer durumdaki araçları tek öneride grupla. Aşım riski olan bir aracı düşük kullanılan bir
  araçla eşleştiren değişim önerileri değerlidir.
- "estimated_monthly_impact_try": yalnızca verideki kira/km değerlerinden makul bir aylık etki
  hesaplayabiliyorsan TL olarak yaz; hesaplayamıyorsan 0 yaz.
- En önemli en fazla 12 öneriyi önem sırasına göre ver. Türkçe, kısa ve net yaz.
- "summary": filonun genel durumunu 2-3 cümleyle özetle."""


def _analyse(db, rows, model, owner, system, force, trigger):
    """Shared generation: cache by input hash/age, ask Claude, keep only known plates, store."""
    if not rows:
        raise HTTPException(400, "Analiz için aktif araç bulunmuyor.")
    flagged = sorted(
        [r for r in rows if r["flags"]],
        key=lambda r: (-len(r["flags"]), -(r.get("usage_ratio") or 0)),
    )[:MAX_VEHICLES]
    data = {"today": business_today().isoformat(), "overview": fleet_overview(rows)}
    data["vehicles_needing_attention"] = flagged
    if len(flagged) < 30:  # small fleets: give full context so transfer pairs can be found
        data["other_vehicles"] = [r for r in rows if not r["flags"]][: 60 - len(flagged)]
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    cached = (
        db.query(model).filter_by(kind="fleet", **owner).order_by(model.id.desc()).first()
    )
    if cached and not force:
        age = datetime.fromisoformat(stamp()) - datetime.fromisoformat(cached.created_at)
        if cached.input_hash == digest or age < timedelta(hours=CACHE_HOURS):
            return insight_view(cached, rows)
    if not flagged:
        payload = {
            "summary": "Kayıtlı verilerde km aşımı, düşük kullanım veya yaklaşan bir tarih "
            "görünmüyor.",
            "insights": [],
        }
        usage = {}
    else:
        payload, usage = ask(system, blob, INSIGHT_SCHEMA, effort="medium")
        usage = dict(usage)
        known = {r["plate"] for r in rows}
        for item in payload.get("insights", []):
            item["plates"] = [p for p in item.get("plates", []) if p in known]
    usage["trigger"] = trigger
    row = model(
        **owner,
        kind="fleet",
        input_hash=digest,
        model=usage.get("model", MODEL),
        payload=payload,
        usage=usage,
        created_at=stamp(),
    )
    db.add(row)
    db.commit()
    return insight_view(row, rows)


def fleet_insights(db, ctx, force=False, trigger="manual"):
    sid = ctx["id"]
    return _analyse(
        db,
        fleet_metrics(db, sid),
        m.SupplierAiInsight,
        {"supplier_id": sid},
        INSIGHT_SYSTEM,
        force,
        trigger,
    )


def customer_fleet_insights(db, customer_id, force=False, trigger="manual"):
    return _analyse(
        db,
        fleet_metrics(db, customer_id=customer_id),
        m.CustomerAiInsight,
        {"customer_id": customer_id},
        CUSTOMER_INSIGHT_SYSTEM,
        force,
        trigger,
    )


def insight_view(row, rows):
    return {
        **row.payload,
        "generated_at": row.created_at,
        "model": row.model,
        "trigger": (row.usage or {}).get("trigger", "manual"),
        "vehicle_count": len(rows),
        "flagged_count": sum(1 for r in rows if r["flags"]),
        "metrics": {r["plate"]: r for r in rows if r["flags"]},
    }


# --------------------------------------------------------------------------- documents

_DATE = {"type": "string", "description": "YYYY-MM-DD; bilinmiyorsa boş"}
_NUM = {"type": "number", "description": "bilinmiyorsa 0"}
_STR = {"type": "string", "description": "bilinmiyorsa boş"}


def _obj(props):
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


DOC_SCHEMAS = {
    "receipt": _obj(
        {
            "document_kind": _STR,
            "plate": _STR,
            "date": _DATE,
            "station": _STR,
            "receipt_no": _STR,
            "fuel_type": {"type": "string", "enum": ["Benzin", "Dizel", "LPG", "Elektrik", ""]},
            "liters": _NUM,
            "unit_price_try": _NUM,
            "total_try": _NUM,
            "mileage": _NUM,
            "utts_code": _STR,
            "notes": _STR,
        }
    ),
    "invoice": _obj(
        {
            "document_kind": _STR,
            "seller": _STR,
            "buyer": _STR,
            "invoice_no": _STR,
            "date": _DATE,
            "due_date": _DATE,
            "category": {
                "type": "string",
                "enum": ["Servis", "Lastik", "Yakıt", "Sigorta", "HGS", "Kira", "Diğer"],
            },
            "subtotal_try": _NUM,
            "vat_try": _NUM,
            "total_try": _NUM,
            "lines": {
                "type": "array",
                "items": _obj(
                    {"description": _STR, "plate": _STR, "quantity": _NUM, "amount_try": _NUM}
                ),
            },
            "notes": _STR,
        }
    ),
    "contract": _obj(
        {
            "document_kind": _STR,
            "contract_no": _STR,
            "lessor": _STR,
            "lessee": _STR,
            "start_date": _DATE,
            "end_date": _DATE,
            "duration_months": _NUM,
            "general_terms": {"type": "array", "items": _STR},
            "vehicles": {
                "type": "array",
                "items": _obj(
                    {
                        "chassis_no": _STR,
                        "plate": _STR,
                        "brand_model": _STR,
                        "monthly_rent_try": _NUM,
                        "monthly_km_limit": _NUM,
                        "total_km": _NUM,
                        "extra_km_price_try": _NUM,
                        "duration_months": _NUM,
                        "source": {"type": "string", "description": "Ana metin, Ek-1, Ek-2..."},
                    }
                ),
            },
            "notes": _STR,
        }
    ),
}
DOC_PROMPTS = {
    "receipt": "Bu bir akaryakıt fişi veya UTTS (Ulusal Taşıt Tanıma Sistemi) dökümü. Fişteki "
    "plaka, tarih, istasyon, fiş no, yakıt tipi, litre, birim fiyat, toplam tutar ve varsa km "
    "bilgisini çıkar.",
    "invoice": "Bu bir fatura. Satıcı, alıcı, fatura no, tarih, vade, KDV hariç tutar, KDV, "
    "genel toplam ve kalemleri çıkar. Kalemlerde plaka geçiyorsa yaz. Faturanın konusuna göre "
    "kategoriyi seç (servis/bakım, lastik, yakıt, sigorta, HGS, kira, diğer).",
    "contract": "Bu bir araç kiralama sözleşmesi; Ek-1, Ek-2 gibi ekleri de içerebilir. "
    "Sözleşme no, taraflar, başlangıç/bitiş, süre ve önemli genel şartları çıkar. Eklerdeki araç "
    "listesinde her araç için şase no, plaka, marka/model, aylık kira, aylık km limiti veya "
    "toplam km, km aşım birim fiyatı ve süreyi ayrı ayrı yaz; bilginin hangi bölümden geldiğini "
    "'source' alanına yaz. Araca özel değer yoksa sözleşmenin genel değerini kullan.",
}
DOC_SYSTEM = """Belgelerden veri çıkaran bir asistansın. Yalnızca belgede yazanı aktar; tahmin
etme, eksik alanı boş metin veya 0 bırak. Tutarları TL olarak, ondalık ayırıcı nokta olacak
şekilde sayı yaz. Tarihleri YYYY-MM-DD biçiminde yaz. Plakayı "34 ABC 123" biçiminde, şase
numarasını boşluksuz büyük harfle yaz. Okunamayan kısımları "notes" alanında belirt."""


def _norm_plate(value):
    from app.vehicle_import import normalize_plate

    return normalize_plate(value) if value else ""


def read_document(db, ctx, doc_type, content, media_type):
    if doc_type not in DOC_SCHEMAS:
        raise HTTPException(400, "Belge türü fiş, fatura veya sözleşme olmalı.")
    if media_type not in DOC_TYPES:
        raise HTTPException(415, "PDF, JPG, PNG veya WEBP yükleyin.")
    if not content or len(content) > DOC_MAX_BYTES:
        raise HTTPException(413, "Dosya boş olamaz ve en fazla 15 MB olmalıdır.")
    data = base64.standard_b64encode(content).decode()
    block = (
        {"type": "document", "source": {"type": "base64", "media_type": media_type, "data": data}}
        if media_type == "application/pdf"
        else {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}
    )
    parsed, usage = ask(
        DOC_SYSTEM,
        [block, {"type": "text", "text": DOC_PROMPTS[doc_type]}],
        DOC_SCHEMAS[doc_type],
        effort="low",
    )
    cars = db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all()
    by_plate = {c.plate.replace(" ", ""): c for c in cars if c.plate}
    by_chassis = {c.chassis_no: c for c in cars}

    def match(plate="", chassis=""):
        chassis = (chassis or "").replace(" ", "").upper()
        car = by_chassis.get(chassis) or by_plate.get(_norm_plate(plate).replace(" ", ""))
        return (
            {
                "id": car.id,
                "plate": car.plate,
                "name": f"{car.brand or ''} {car.model or ''}".strip(),
                "mileage": car.mileage,
                "has_customer": bool(car.customer_id),
            }
            if car
            else None
        )

    if doc_type == "receipt":
        parsed["plate"] = _norm_plate(parsed.get("plate"))
        parsed["vehicle"] = match(parsed["plate"])
    elif doc_type == "invoice":
        for line in parsed.get("lines", []):
            line["plate"] = _norm_plate(line.get("plate"))
            line["vehicle"] = match(line["plate"])
    else:
        for item in parsed.get("vehicles", []):
            item["plate"] = _norm_plate(item.get("plate"))
            item["vehicle"] = match(item["plate"], item.get("chassis_no"))
    return {"doc_type": doc_type, "data": parsed, "usage": usage}
