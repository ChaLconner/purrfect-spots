from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from app import main as main_module
from app.repositories.base_repository import BaseRepository
from app.routes import upload as upload_route
from app.routes.admin import (
    reports as reports_route,
    settings as settings_route,
    stats as stats_route,
)
from app.routes.upload import PreparedUploadData, UploadFormData
from app.schemas.settings_schemas import ConfigUpdate
from app.services.notification_service import NotificationService
from app.services.quota_service import QuotaService, QuotaServiceUnavailable
from app.services.search_service import SearchService
from app.services.subscription_service import (
    SubscriptionService,
    _subscription_id,
    _subscription_status,
    cancel_customer_subscriptions,
)
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.utils import cache as cache_utils
from app.utils.exceptions import ExternalServiceError


def _chain_builder() -> MagicMock:
    builder = MagicMock()
    for method in (
        "select",
        "eq",
        "lte",
        "lt",
        "gte",
        "gt",
        "is_",
        "order",
        "limit",
        "offset",
        "range",
        "in_",
        "or_",
        "contains",
        "text_search",
        "update",
        "insert",
        "delete",
        "maybe_single",
        "single",
        "match",
    ):
        getattr(builder, method).return_value = builder
    builder.not_ = MagicMock()
    builder.not_.is_.return_value = builder
    builder.execute = AsyncMock(return_value=MagicMock(data=[]))
    return builder


def _admin_client(builder: MagicMock) -> MagicMock:
    admin = MagicMock()
    admin.table.return_value = builder
    admin.auth.admin.delete_user = AsyncMock()
    return admin


@pytest.mark.asyncio
async def test_user_deletion_supabase_helpers_cover_claim_completion_and_rollback() -> None:
    builder = _chain_builder()
    admin = _admin_client(builder)
    service = UserService(MagicMock(), supabase_admin=admin)
    service._log_audit_event = AsyncMock()  # type: ignore[method-assign]

    request = {"id": "request-1", "user_id": "user-1"}
    builder.execute.return_value = MagicMock(data=[request])
    expired, now = await service._load_expired_deletion_requests()
    assert expired == [request]
    assert now.endswith("+00:00")

    claimed = await service._claim_deletion_request(admin, request, now)
    assert claimed == request

    await service._mark_hard_delete_completed(admin, "request-1", "user-1")
    await service._rollback_hard_delete_claim("request-1", admin)
    service._log_audit_event.assert_awaited_once_with("ACCOUNT_HARD_DELETED", "user-1")
    assert builder.execute.await_count >= 3


@pytest.mark.asyncio
async def test_user_deletion_db_helpers_cover_claim_and_rollback() -> None:
    db = AsyncMock()
    service = UserService(MagicMock(), db=db)
    service._log_audit_event = AsyncMock()  # type: ignore[method-assign]

    row = SimpleNamespace(_mapping={"id": "request-1", "user_id": "user-1"})
    load_result = MagicMock()
    load_result.__iter__.return_value = iter([row])
    claim_result = MagicMock()
    claim_result.fetchone.return_value = row
    db.execute.side_effect = [load_result, claim_result, MagicMock(), MagicMock()]

    expired, now = await service._load_expired_deletion_requests()
    claimed = await service._claim_deletion_request(MagicMock(), expired[0], now)
    await service._mark_hard_delete_completed(MagicMock(), "request-1", "user-1")
    await service._rollback_hard_delete_claim("request-1", MagicMock())

    assert expired == [{"id": "request-1", "user_id": "user-1"}]
    assert claimed == {"id": "request-1", "user_id": "user-1"}
    assert db.commit.await_count == 3
    assert db.rollback.await_count == 1


@pytest.mark.asyncio
async def test_user_deletion_hard_delete_success_and_failure_paths() -> None:
    builder = _chain_builder()
    admin = _admin_client(builder)
    service = UserService(MagicMock(), supabase_admin=admin)
    service._mark_hard_delete_completed = AsyncMock()  # type: ignore[method-assign]
    service._rollback_hard_delete_claim = AsyncMock()  # type: ignore[method-assign]

    builder.execute.return_value = MagicMock(data={"stripe_customer_id": "cus-1"})
    with patch("app.services.user.deletion_mixin.cancel_customer_subscriptions", new=AsyncMock(return_value=1)):
        assert await service._process_hard_delete_request(admin, {"id": "r-1", "user_id": "u-1"}) is True
    admin.auth.admin.delete_user.assert_awaited_once_with("u-1")

    admin.auth.admin.delete_user.reset_mock()
    admin.auth.admin.delete_user.side_effect = RuntimeError("auth unavailable")
    assert await service._process_hard_delete_request(admin, {"id": "r-2", "user_id": "u-2"}) is False
    service._rollback_hard_delete_claim.assert_awaited_once_with("r-2", admin)


@pytest.mark.asyncio
async def test_user_execute_hard_delete_counts_completed_failed_and_skipped() -> None:
    service = UserService(MagicMock(), supabase_admin=MagicMock())
    requests = [
        {"id": "r-1", "user_id": "u-1"},
        {"id": "r-2", "user_id": "u-2"},
        {"id": "r-3", "user_id": "u-3"},
    ]
    service._load_expired_deletion_requests = AsyncMock(return_value=(requests, "now"))  # type: ignore[method-assign]
    service._claim_deletion_request = AsyncMock(side_effect=[requests[0], None, requests[2]])  # type: ignore[method-assign]
    service._process_hard_delete_request = AsyncMock(side_effect=[True, False])  # type: ignore[method-assign]

    result = await service.execute_hard_delete()

    assert result == {"completed": 1, "failed": 1, "skipped": 1}


@pytest.mark.asyncio
async def test_token_service_sql_persistence_and_user_revocation_paths() -> None:
    db = AsyncMock()
    db_result = MagicMock()
    db_result.fetchone.return_value = (datetime.now(UTC) + timedelta(hours=1),)
    db_result.fetchall.return_value = [(datetime.now(UTC) + timedelta(hours=1),)]
    db.execute.return_value = db_result
    service = TokenService(None, db=db)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    assert await service._persist_blacklist_sql("jti-1", "user-1", expires_at) is True
    assert await service._check_db_blacklist_sql("jti-1") is True
    assert await service._get_db_user_revocation("user-1") is not None
    assert db.commit.await_count == 1

    db.execute.side_effect = RuntimeError("database unavailable")
    assert await service._persist_blacklist_sql("jti-2", "user-2", expires_at) is False
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_token_service_supabase_revocation_and_blacklist_fallback_paths() -> None:
    builder = _chain_builder()
    admin = _admin_client(builder)
    service = TokenService(None, supabase_client=admin)
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    builder.execute.return_value = MagicMock(data={"last_token_revocation_at": future})

    assert await service._get_db_user_revocation("user-1") is not None
    assert await service.is_user_invalidated("user-1", datetime.now(UTC) - timedelta(minutes=1)) is True

    builder.execute.return_value = MagicMock(data=[])
    with patch("app.services.token_service.has_supabase_service_role_key", return_value=False):
        assert await service._persist_blacklist("jti-1", "user-1", datetime.fromisoformat(future), "hash-1") is False

    assert await service._persist_blacklist(None, None, None, "hash-1") is True


@pytest.mark.asyncio
async def test_token_service_global_revocation_db_and_failure_paths() -> None:
    db = AsyncMock()
    service = TokenService(None, db=db)
    assert await service.blacklist_all_user_tokens("user-1") == 1
    db.commit.assert_awaited_once()

    db.execute.side_effect = RuntimeError("database unavailable")
    assert await service.blacklist_all_user_tokens("user-2") == 0


@pytest.mark.asyncio
async def test_quota_service_rpc_normalization_and_reservation_lifecycle() -> None:
    supabase = MagicMock()
    rpc_builder = MagicMock()
    rpc_builder.execute = AsyncMock()
    supabase.rpc.return_value = rpc_builder
    service = QuotaService(supabase)

    for response_data, expected in ((True, True), (0, False), ("true", True), ([{"ok": 1}], True), ({"ok": 0}, False)):
        assert service._rpc_bool(MagicMock(data=response_data)) is expected

    rpc_builder.execute.return_value = MagicMock(data=True)
    assert await service.complete_upload_quota("reservation-1") is True
    assert await service.release_upload_quota("reservation-1") is True

    rpc_builder.execute.side_effect = RuntimeError("rpc unavailable")
    with pytest.raises(QuotaServiceUnavailable):
        await service.complete_upload_quota("reservation-2")
    with pytest.raises(QuotaServiceUnavailable):
        await service.release_upload_quota("reservation-2")


@pytest.mark.asyncio
async def test_quota_service_database_reads_and_status_fallback() -> None:
    db = AsyncMock()
    supabase = MagicMock()
    service = QuotaService(supabase, db=db)
    now = datetime.now(UTC)
    result = MagicMock()
    result.fetchall.return_value = [(now - timedelta(hours=1),)]
    db.execute.return_value = result

    usage, window = await service.get_quota_usage("user-1", max_rows=5)
    assert usage == 1
    assert window is not None

    user_status = await service.get_user_quota_status("user-1", False)
    assert user_status.used == 1
    assert user_status.remaining == service.FREE_LIMIT - 1

    service.get_quota_usage = AsyncMock(side_effect=RuntimeError("database unavailable"))  # type: ignore[method-assign]
    failed_status = await service.get_user_quota_status("user-1", True)
    assert failed_status.used == 0
    assert failed_status.remaining == 0


@pytest.mark.asyncio
async def test_upload_helpers_cover_detection_storage_persistence_and_cleanup() -> None:
    upload_file = MagicMock()
    form = UploadFormData(
        file=upload_file,
        lat="7.8",
        lng="98.3",
        location_name="Park",
        description="Nice",
        tags='["safe"]',
        cat_detection_data='{"has_cats": true}',
        verification_token=None,
        location_blurred="yes",
    )
    prepared = upload_route._prepare_upload_data(form)
    assert isinstance(prepared, PreparedUploadData)
    assert prepared.location_blurred is True
    assert prepared.tags == ["safe"]

    assert upload_route._parse_client_detection_data(None) is None
    assert upload_route._parse_client_detection_data("not-json") is None
    assert upload_route._parse_client_detection_data('{"has_cats": true}') == {"has_cats": True}
    assert upload_route._get_upload_status({"confidence": 0.6}) == "approved"
    assert upload_route._get_upload_status({"confidence": 59}) == "pending_review"

    detection_service = MagicMock()
    detection_service.detect_cats = AsyncMock(return_value={"has_cats": True, "confidence": 0.9})
    with patch("app.routes.upload.verify_upload_verification_token", new=AsyncMock(return_value={"has_cats": True})):
        verified = await upload_route._resolve_upload_detection("token", b"image", "user-1", detection_service, None)
    assert verified["detection_source"] == "verified_token"

    storage = MagicMock()
    storage.upload_file = AsyncMock(return_value="https://cdn.example/image.jpg")
    assert await upload_route._upload_to_storage(storage, b"image", "image/jpeg", ".jpg", "user-1") == (
        "https://cdn.example/image.jpg"
    )

    quota = MagicMock()
    quota.renew_upload_quota = AsyncMock(return_value=True)
    quota.complete_upload_quota = AsyncMock(return_value=False)
    await upload_route._renew_upload_reservation(quota, "reservation-1", True)
    await upload_route._complete_upload_reservation(quota, "reservation-1", True)
    quota.complete_upload_quota.assert_awaited_once_with("reservation-1")

    storage.delete_file = AsyncMock(side_effect=RuntimeError("cleanup failed"))
    await upload_route._delete_uploaded_file(storage, "https://cdn.example/image.jpg", "test cleanup")


@pytest.mark.asyncio
async def test_upload_helpers_cover_quota_and_storage_failure_branches() -> None:
    quota = MagicMock()
    quota.renew_upload_quota = AsyncMock(side_effect=QuotaServiceUnavailable("unavailable"))
    with pytest.raises(HTTPException) as renew_error:
        await upload_route._renew_upload_reservation(quota, "reservation-1", True)
    assert getattr(renew_error.value, "status_code", None) == 503

    quota.renew_upload_quota.side_effect = None
    quota.renew_upload_quota.return_value = False
    with pytest.raises(HTTPException) as expired_error:
        await upload_route._renew_upload_reservation(quota, "reservation-1", True)
    assert getattr(expired_error.value, "status_code", None) == 503

    storage = MagicMock()
    storage.upload_file = AsyncMock(side_effect=ExternalServiceError("storage unavailable"))
    with pytest.raises(HTTPException) as upload_error:
        await upload_route._upload_to_storage(storage, b"image", "image/jpeg", ".jpg", "user-1")
    assert getattr(upload_error.value, "status_code", None) == 500

    quota.complete_upload_quota = AsyncMock(side_effect=QuotaServiceUnavailable("unavailable"))
    await upload_route._complete_upload_reservation(quota, "reservation-2", True)


@pytest.mark.asyncio
async def test_upload_save_photo_record_covers_reservation_and_legacy_paths() -> None:
    gallery = MagicMock()
    quota = MagicMock()
    gallery.save_photo = AsyncMock(return_value={"id": "photo-1"})
    quota.check_quota = AsyncMock(return_value=True)
    quota.increment_usage = AsyncMock()

    photo = {"id": "photo-1"}
    saved, used_reservation, error = await upload_route._save_photo_record(gallery, quota, photo, "user-1", False, True)
    assert saved == photo
    assert used_reservation is True
    assert error is None

    with patch("app.routes.upload.redis_service.lock") as lock:
        lock.return_value.__aenter__ = AsyncMock()
        lock.return_value.__aexit__ = AsyncMock(return_value=None)
        saved, allowed, error = await upload_route._save_photo_record(gallery, quota, photo, "user-1", False, False)
    assert saved == photo
    assert allowed is True
    assert error is None
    quota.increment_usage.assert_awaited_once_with("user-1")


@pytest.mark.asyncio
async def test_subscription_helpers_cover_customer_status_and_reconciliation_paths() -> None:
    service = SubscriptionService(MagicMock())
    assert _subscription_status({"status": "active"}) == "active"
    assert _subscription_status(SimpleNamespace(status="trialing")) == "trialing"
    assert _subscription_id({"id": "sub-1"}) == "sub-1"
    assert _subscription_id(SimpleNamespace(id=None)) is None
    assert service._extract_subscription_price_ids({"items": {"data": [{"price": {"id": "price-1"}}]}}) == {"price-1"}

    with patch("app.services.subscription_service.stripe.Subscription.list") as list_subscriptions:
        collection = MagicMock(data=[SimpleNamespace(status="active", id="sub-1")])
        collection.auto_paging_iter.return_value = iter([])
        list_subscriptions.return_value = collection
        with patch("app.services.subscription_service.stripe.Subscription.modify") as modify:
            assert await cancel_customer_subscriptions("customer-1") == 1
            modify.assert_called_once_with("sub-1", cancel_at_period_end=True)

    assert await cancel_customer_subscriptions("") == 0

    run_at = datetime.now(UTC)
    with patch.object(service, "_subscription_matches_pro_plan", return_value=True):
        assert (
            service._has_live_pro_subscription(
                {"status": "active", "current_period_end": run_at.timestamp() + 3600}, run_at
            )
            is True
        )
        assert (
            service._has_live_pro_subscription(
                {"status": "past_due", "current_period_end": run_at.timestamp() - 1}, run_at
            )
            is False
        )

    assert service._reconciliation_subscription_id({"id": "sub-1", "customer": "customer-1"}, "customer-1") == "sub-1"
    assert service._reconciliation_subscription_id({"id": "sub-1", "customer": "other"}, "customer-1") is None


@pytest.mark.asyncio
async def test_subscription_reconcile_customer_revokes_when_no_live_pro_subscription() -> None:
    service = SubscriptionService(MagicMock())
    service._revoke_pro_status_by_customer_id = AsyncMock()  # type: ignore[method-assign]
    service._apply_subscription_snapshot = AsyncMock(return_value=True)  # type: ignore[method-assign]
    run_at = datetime.now(UTC)

    with patch("app.services.subscription_service._list_all_customer_subscriptions", return_value=[]):
        result = await service._reconcile_customer("user-1", "customer-1", run_at)

    assert result == 0
    service._revoke_pro_status_by_customer_id.assert_awaited_once_with("customer-1")


def test_main_sentry_filter_and_redaction_helpers_cover_privacy_paths(monkeypatch) -> None:
    monkeypatch.delenv("QUALITY_HELPER_FLAG", raising=False)
    assert main_module._env_flag("QUALITY_HELPER_FLAG") is False
    assert main_module._env_flag("QUALITY_HELPER_FLAG", default=True) is True
    monkeypatch.setenv("QUALITY_HELPER_FLAG", " yes ")
    assert main_module._env_flag("QUALITY_HELPER_FLAG") is True

    assert main_module._drop_sentry_exception({}) is False
    assert main_module._drop_sentry_exception({"exc_info": (None, HTTPException(status_code=404), None)}) is True
    assert main_module._drop_sentry_exception({"exc_info": (None, HTTPException(status_code=500), None)}) is False
    assert main_module._drop_sentry_exception({"exc_info": (None, main_module.asyncio.CancelledError(), None)}) is True

    assert main_module._drop_synthetic_sentry_event("normal", {"message": "normal"}) is False
    assert main_module._drop_synthetic_sentry_event("normal", {"message": "MagicMock from test"}) is True
    assert (
        main_module._drop_synthetic_sentry_event(
            "normal", {"request": {"headers": {"User-Agent": "pytest testclient"}}}
        )
        is True
    )
    assert main_module._drop_synthetic_sentry_event({"id": "00000000-0000-4000-test"}, {"message": "normal"}) is True

    event: dict[str, Any] = {
        "request": {
            "headers": {
                "Authorization": "secret",
                "X-Trace": "trace",
            }
        },
        "user": {"email": "person@example.com", "ip_address": "127.0.0.1", "username": "person"},
        "breadcrumbs": {
            "values": [
                {"category": "query", "data": {"query": "secret query"}},
                {"category": "http", "data": {"url": "https://example.test/path?token=secret"}},
            ]
        },
    }
    main_module._redact_sentry_event(event)
    assert event["request"]["headers"]["Authorization"] == "[REDACTED]"
    assert event["request"]["headers"]["X-Trace"] == "trace"
    assert event["user"]["email"] == "[REDACTED]"
    assert event["breadcrumbs"]["values"][0]["data"]["query"] == "[REDACTED_QUERY]"
    assert event["breadcrumbs"]["values"][1]["data"]["url"].endswith("?[REDACTED_PARAMS]")


@pytest.mark.asyncio
async def test_base_repository_covers_sql_and_supabase_read_write_paths() -> None:
    db = AsyncMock()
    row = SimpleNamespace(_mapping={"id": "record-1", "name": "Record"})
    db_result = MagicMock()
    db_result.fetchone.return_value = row
    db.execute.return_value = db_result
    repository = BaseRepository(MagicMock(), db=db)

    assert await repository.fetch_one("items", {"id": "record-1"}, allowed_columns={"id", "name"}) == {
        "id": "record-1",
        "name": "Record",
    }
    assert await repository.fetch_one("items", {"unsafe": "value"}, allowed_columns={"id"}) is None
    assert (
        await repository.update_record("items", "record-1", {"name": "Updated"}, allowed_columns={"id", "name"}) is True
    )
    assert (
        await repository.update_record("items", "record-1", {"unsafe": "value"}, allowed_columns={"id", "name"})
        is False
    )

    builder = _chain_builder()
    supabase = MagicMock()
    supabase.table.return_value = builder
    builder.execute.return_value = MagicMock(data=[{"id": "record-1"}])
    supabase_repository = BaseRepository(supabase)
    assert await supabase_repository.fetch_one("items", {"id": "record-1"}) == {"id": "record-1"}
    assert await supabase_repository.update_record("items", "record-1", {"name": "Updated"}) is True

    builder.execute.return_value = MagicMock(data=[])
    assert await supabase_repository.fetch_one("items", {"id": "missing"}) is None
    assert await supabase_repository.update_record("items", "record-1", {"name": "Updated"}) is False
    assert await supabase_repository.update_record("items", "record-1", {}) is True


@pytest.mark.asyncio
async def test_notification_service_covers_db_and_supabase_listing_paths() -> None:
    user_id = "00000000-0000-4000-a000-000000000001"
    actor_id = "00000000-0000-4000-a000-000000000002"
    db = AsyncMock()
    row = SimpleNamespace(
        _mapping={"id": "notification-1", "actor_name": "Actor", "actor_picture": "https://img.example/a.jpg"}
    )
    db_result = MagicMock()
    db_result.fetchall.return_value = [row]
    db.execute.return_value = db_result
    service = NotificationService(MagicMock(), db=db)

    listed = await service._get_notifications_db(user_id, 100, -5, datetime.now(UTC), datetime.now(UTC))
    assert listed[0]["actor_name"] == "Actor"
    assert "before" in str(db.execute.call_args.args[1])

    supabase = MagicMock()
    builder = _chain_builder()
    supabase.table.return_value = builder
    builder.execute.return_value = MagicMock(
        data=[{"id": "notification-2", "actor": {"name": "Actor 2", "picture": None}}]
    )
    supabase_service = NotificationService(supabase)
    notifications = await supabase_service._get_notifications_supabase(user_id, 100, 2, None, datetime.now(UTC))
    assert notifications == [{"id": "notification-2", "actor_name": "Actor 2", "actor_picture": None}]

    create_result = MagicMock()
    create_result.fetchone.return_value = row
    db.execute.return_value = create_result
    created = await service.create_notification(user_id, "system", "Message", actor_id=actor_id)
    assert created["id"] == "notification-1"
    assert await service.get_unread_count("not-a-uuid") == 0
    create_result.scalar.return_value = 3
    assert await service.get_unread_count(user_id) == 3


@pytest.mark.asyncio
async def test_search_service_covers_sql_and_supabase_count_predicates() -> None:
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 4
    db.execute.return_value = result
    service = SearchService(MagicMock(), db=db)

    assert await service._count_matches_sql("cat", ["#Cute"], fulltext=True) == 4
    assert await service._count_matches_sql("cat", None, fulltext=False) == 4
    assert service._clean_tags([" #Cute ", "Outdoor"]) == ["cute", "outdoor"]

    supabase = MagicMock()
    builder = _chain_builder()
    supabase.table.return_value = builder
    builder.execute.return_value = MagicMock(count=7, data=[])
    supabase_service = SearchService(supabase)
    assert await supabase_service._count_matches_supabase("cat", ["#Cute"], fulltext=True) == 7
    assert await supabase_service._count_matches_supabase("cat", ["Cute"], fulltext=False) == 7


@pytest.mark.asyncio
async def test_admin_stats_helpers_cover_rpc_and_fallback_paths() -> None:
    admin = MagicMock()
    builder = _chain_builder()
    admin.table.return_value = builder
    admin.rpc.return_value = builder
    builder.execute.side_effect = [
        MagicMock(count=10),
        MagicMock(count=20),
        MagicMock(count=2),
        MagicMock(count=4),
        MagicMock(data={"users": []}),
        MagicMock(data=[]),
    ]
    with (
        patch.object(stats_route, "_fetch_trends_fallback", new=AsyncMock(return_value={"users": []})),
        patch.object(stats_route, "_fetch_monthly_report_fallback", new=AsyncMock(return_value=[])),
    ):
        rpc_result = await stats_route._fetch_dashboard_summary_rpc(admin)
    assert rpc_result["stats"]["total_users"] == 10

    builder.execute.side_effect = None
    builder.execute.return_value = MagicMock(count=3)
    assert await stats_route._safe_dashboard_count(admin, "users", filters={"role": "admin"}) == 3
    builder.execute.side_effect = RuntimeError("count unavailable")
    assert await stats_route._safe_dashboard_count(admin, "users") == 0

    with (
        patch.object(stats_route, "_fetch_trends_fallback", new=AsyncMock(side_effect=RuntimeError("trend"))),
        patch.object(stats_route, "_fetch_monthly_report_fallback", new=AsyncMock(side_effect=RuntimeError("month"))),
    ):
        assert await stats_route._safe_dashboard_trends(admin) == {"users": [], "photos": [], "reports": []}
        assert await stats_route._safe_dashboard_monthly(admin) == []


@pytest.mark.asyncio
async def test_admin_report_helpers_schedule_unique_notifications_and_audits() -> None:
    background_tasks = BackgroundTasks()
    gallery = MagicMock()
    notifications = MagicMock()
    reports_route._schedule_photo_deletion_and_notification(
        background_tasks, "photo-1", "https://img.example/photo.jpg", "user-1", gallery, notifications
    )
    reports_route._queue_reporter_notification(
        background_tasks, notifications, "report-1", {"reporter_id": "reporter-1", "status": "resolved"}, "Note"
    )
    reports_route._queue_bulk_reporter_notifications(
        background_tasks,
        notifications,
        [{"id": "r-1", "reporter_id": "reporter-1"}, {"id": "r-2", "reporter_id": "reporter-1"}],
        "dismissed",
    )
    assert len(background_tasks.tasks) == 4

    builder = _chain_builder()
    admin = _admin_client(builder)
    request = MagicMock(client=SimpleNamespace(host="127.0.0.1"))
    current_admin = SimpleNamespace(id="admin-1")
    builder.execute.return_value = MagicMock(
        data=[
            {
                "id": "report-1",
                "photo_id": "photo-1",
                "reporter_id": "reporter-1",
                "photo": {"id": "photo-1", "image_url": "https://img.example/photo.jpg", "user_id": "user-1"},
            },
            {"id": "report-2", "photo_id": "photo-1", "photo": {"id": "photo-1"}},
        ]
    )
    with patch.object(reports_route, "log_admin_action", new=AsyncMock()):
        await reports_route._delete_bulk_report_photos(
            admin,
            ["report-1", "report-2"],
            BackgroundTasks(),
            request,
            cast(Any, current_admin),
            gallery,
            notifications,
        )
    assert builder.execute.await_count >= 1


@pytest.mark.asyncio
async def test_admin_settings_helpers_cover_encryption_history_and_pending_paths() -> None:
    assert settings_route._settings_cache_key(None) == "admin_settings:all"
    assert settings_route._settings_cache_key("security") == "admin_settings:security"
    assert settings_route._settings_history_cache_key("smtp_password") == "admin_settings_history:smtp_password"
    assert settings_route._mask_encrypted_value("secret", True) is None
    assert settings_route._mask_encrypted_value("visible", False) == "visible"

    plain_value = settings_route._prepare_setting_value(
        "feature_flag", {"value": False, "is_encrypted": False}, ConfigUpdate(value=True)
    )
    assert plain_value == (True, False, False)
    empty_update = ConfigUpdate(value=" ")
    with pytest.raises(HTTPException, match="cannot be empty"):
        settings_route._prepare_setting_value("smtp_password", {"value": "old", "is_encrypted": True}, empty_update)
    with patch.object(settings_route.encryption_service, "encrypt_value", return_value="encrypted"):
        encrypted = settings_route._prepare_setting_value(
            "smtp_password", {"value": "old", "type": "string", "is_encrypted": True}, ConfigUpdate(value="new")
        )
    assert encrypted == ("encrypted", "old", True)

    builder = _chain_builder()
    admin = _admin_client(builder)
    builder.execute.return_value = MagicMock(data=[{"config_key": "smtp_password", "proposed_value": "secret"}])
    current_admin = SimpleNamespace(id="admin-1", name="", email="admin@example.com")
    with (
        patch.object(settings_route.line_service, "send_notification", new=AsyncMock()),
        patch.object(settings_route, "_invalidate_settings_cache", new=AsyncMock()),
    ):
        pending = await settings_route._create_pending_setting_change(
            admin, "smtp_password", "encrypted", cast(Any, current_admin), is_encrypted=True
        )
    assert pending["proposed_value"] is None

    await settings_route._record_config_history(admin, "feature_flag", False, True, "admin-1", "test")
    with (
        patch.object(settings_route.redis_service, "delete_pattern", new=AsyncMock()),
        patch.object(settings_route.redis_service, "delete", new=AsyncMock()),
    ):
        await settings_route._invalidate_settings_cache("feature_flag")
        await settings_route._invalidate_settings_cache()


@pytest.mark.asyncio
async def test_cache_helpers_cover_memory_hits_misses_and_redis_scans(monkeypatch) -> None:
    cache_utils.memory_cache.clear()
    monkeypatch.setattr(cache_utils, "redis_client", None)
    calls = 0

    async def load_value(value: str) -> str:
        nonlocal calls
        calls += 1
        return value

    cached_loader = cache_utils.cache(expire=60, key_prefix="quality")(load_value)
    assert await cached_loader("value") == "value"
    assert await cached_loader("value") == "value"
    assert calls == 1

    cache_utils.memory_cache["cache:quality:stale"] = cache_utils.MemoryCacheEntry("stale", 0)
    cache_utils._clear_memory_cache("cache:quality:*")
    cache_utils.memory_cache["cache:quality:one"] = cache_utils.MemoryCacheEntry("one", 9999999999)
    cache_utils._clear_memory_cache("cache:quality:one")
    assert "cache:quality:one" not in cache_utils.memory_cache

    class FakeRedis:
        def __init__(self) -> None:
            self.deleted: list[str] = []

        async def scan_iter(self, **_: object):
            for key in ("cache:quality:one", "cache:other:two"):
                yield key

        async def delete(self, *keys: str) -> None:
            self.deleted.extend(keys)

    fake_redis = FakeRedis()
    monkeypatch.setattr(cache_utils, "redis_client", fake_redis)
    await cache_utils.clear_cache("cache:*")
    await cache_utils.clear_cache_patterns(("cache:quality:*",))
    assert "cache:quality:one" in fake_redis.deleted
