from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.schemas import AuditLogCreate, ContactCreate, RefreshTokenCreate


def test_refresh_token_create_schema_has_no_raw_token_field() -> None:
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    schema = RefreshTokenCreate(
        user_id=user_id,
        token_hash="hashed-token",
        issued_at=now,
        expires_at=now,
        created_ip="127.0.0.1",
        user_agent="pytest",
        last_used_at=now,
    )

    assert schema.token_hash == "hashed-token"
    assert not hasattr(schema, "token")


def test_contact_priority_score_is_bounded() -> None:
    now = datetime.now(timezone.utc)

    with pytest.raises(ValueError):
        ContactCreate(
            business_id=uuid4(),
            source_id=uuid4(),
            full_name="Test Contact",
            source_url="https://example.com",
            collection_timestamp=now,
            priority_score=101,
        )


def test_audit_log_metadata_schema_accepts_json_object() -> None:
    schema = AuditLogCreate(
        event_type="login success",
        request_id="request-1",
        metadata={"ip": "127.0.0.1"},
    )

    assert schema.metadata == {"ip": "127.0.0.1"}
