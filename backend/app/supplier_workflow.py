"""Workflow vocabulary and default settings, shared by validation and projections."""

INITIAL = {
    "offer": "Taslak",
    "contract": "Taslak",
    "delivery": "Planlandı",
    "policy": "Aktif",
    "damage": "Bildirildi",
    "fine": "Açık",
    "invoice": "Taslak",
    "payment": "Tamamlandı",
    "approval": "Beklemede",
    "scenario": "Kaydedildi",
    "return": "Planlandı",
    "sale": "Hazırlık",
    "maintenance": "Önerildi",
}


PREFIXES = {
    "offer": "TKF",
    "contract": "SZ",
    "delivery": "TES",
    "policy": "PLC",
    "damage": "HS",
    "maintenance": "BKM",
    "sale": "SAT",
    "return": "IAD",
    "fine": "TPC",
    "invoice": "FAT",
    "payment": "ODM",
    "approval": "ONY",
    "scenario": "PLN",
}


TRANSITIONS = {
    "offer": {
        "Revizyon Bekliyor": ["Taslak", "İptal"],
        "Taslak": ["Beklemede", "İptal"],
        "Beklemede": ["Onaylandı", "Reddedildi", "İptal"],
        "Onaylandı": ["İptal"],
    },
    "contract": {"Taslak": ["Aktif", "İptal"], "Aktif": ["Sona Erdi", "İptal"]},
    "delivery": {"Planlandı": ["Tamamlandı", "İptal"]},
    "policy": {"Taslak": ["Aktif", "İptal"], "Aktif": ["İptal"]},
    "damage": {
        "Bildirildi": ["İnceleniyor", "İptal"],
        "İnceleniyor": ["Onarımda", "İptal"],
        "Onarımda": ["Tamamlandı", "İptal"],
    },
    "fine": {"Açık": ["İtiraz Edildi", "Ödendi", "İptal"], "İtiraz Edildi": ["Ödendi", "İptal"]},
    "invoice": {"Taslak": ["Kesildi", "İptal"], "Kesildi": ["İptal"]},
    "maintenance": {
        "Önerildi": ["Onaylandı", "Reddedildi"],
        "Onaylandı": ["Planlandı", "Önerildi"],
    },
    "sale": {
        "Hazırlık": ["Ekspertizde", "İptal"],
        "Ekspertizde": ["İlanda", "İptal"],
        "İlanda": ["Teklif Alındı", "İptal"],
        "Teklif Alındı": ["Satıldı", "İptal"],
    },
    "return": {
        "Planlandı": ["İnceleniyor", "İptal"],
        "İnceleniyor": ["Mutabakat Bekliyor", "İptal"],
        "Mutabakat Bekliyor": ["Tamamlandı", "İptal"],
    },
    "payment": {},
    "approval": {"Beklemede": ["Onaylandı", "Reddedildi"]},
    "scenario": {},
}


DEFAULT_SETTINGS = {
    "approval_threshold": 100000,
    "low_balance": 200,
    "renewal_days": 30,
    "low_usage_km": 500,
    "fuel_l100_threshold": 12,
    "company_name": "",
    "currency": "TRY",
    "company_mode": "FLEETRENT_PANEL",
}
