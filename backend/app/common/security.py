"""Opaque portal session issuance and expiration, shared by every portal kind."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

SESSION_LIFETIME = timedelta(days=7)


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session_expired(expires_at):
    try:
        expiry = datetime.fromisoformat(expires_at)
        if expiry.tzinfo is None:
            return True
        return expiry <= datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return True


def issue_session(db, model, **identity):
    token = secrets.token_urlsafe(48)
    db.add(
        model(
            **identity,
            token_hash=token_digest(token),
            expires_at=(datetime.now(timezone.utc) + SESSION_LIFETIME).isoformat(),
        )
    )
    db.commit()
    return token
