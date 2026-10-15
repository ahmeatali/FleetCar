"""Response-result audit independent of the business transaction; never log tokens or bodies."""

import inspect
import logging
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models as m
from app.database import SessionLocal, get_db


class PortalAuditMiddleware:
    def __init__(self, app, application):
        self.app = app
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith(
            ("/api/", "/uploads/", "/admin/login")
        ):
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        result = 500

        async def observed_send(message):
            nonlocal result
            if message["type"] == "http.response.start":
                result = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, observed_send)
        finally:
            db = None
            overridden = None
            try:
                factory = self.application.dependency_overrides.get(get_db)
                if factory:
                    overridden = factory()
                    source = next(overridden) if inspect.isgenerator(overridden) else overridden
                    db = Session(bind=source.get_bind())
                else:
                    db = SessionLocal()
                state = scope.setdefault("state", {})
                if not state.get("audit_principal"):
                    from app.portal_access import principal

                    try:
                        principal(Request(scope), db)
                    except HTTPException:
                        pass
                actor = state.get("audit_principal", {"kind": "anonymous", "id": 0})
                route = scope.get("route")
                resource = getattr(route, "path", "/unmatched-route")
                target = actor["id"] if actor["kind"] in {"supplier", "service"} else None
                params = scope.get("path_params", {})
                if "vehicle_id" in params or "vid" in params:
                    car = db.get(m.Vehicle, params.get("vehicle_id") or params.get("vid"))
                    target = car.supplier_id if car else target
                if "docid" in params:
                    document = db.get(m.SignedDocument, params["docid"])
                    target = document.supplier_id if document else target
                if "rid" in params and "/records/" in resource:
                    record = db.get(m.SupplierOperation, params["rid"])
                    target = record.supplier_id if record else target
                if "eid" in params and "/signature-envelopes/" in resource:
                    envelope = db.get(m.SignatureEnvelope, params["eid"])
                    target = envelope.supplier_id if envelope else target
                db.add(
                    m.AuditEvent(
                        principal_kind=actor["kind"],
                        subject_id=actor["id"],
                        user_id=actor.get("user_id"),
                        role=actor.get("role"),
                        target_supplier_id=target,
                        method=scope["method"],
                        resource=resource,
                        status_code=result,
                        elapsed_ms=int((time.perf_counter() - started) * 1000),
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
                db.commit()
            except Exception as error:
                if db:
                    db.rollback()
                logging.getLogger("fleetcar.audit").warning(
                    "API audit could not be persisted (%s)", type(error).__name__
                )
            finally:
                if db:
                    db.close()
                if inspect.isgenerator(overridden):
                    overridden.close()
