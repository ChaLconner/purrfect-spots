from __future__ import annotations

import importlib
import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import config
from scripts import (
    check_api_breaking_changes as api_contract,
    inspect_dead_letters,
)


def test_api_contract_schema_edges_and_compositions() -> None:
    baseline_document = {"components": {"schemas": {"User": {"type": "object"}}}}
    current_document = baseline_document

    relaxed = api_contract._check_single_parameter_change(
        "/users",
        "get",
        "limit",
        "query",
        {"required": True, "schema": {"type": "integer"}},
        {"required": False, "schema": {"type": "integer"}},
        baseline_document,
        current_document,
    )
    assert relaxed[0]["type"] == "required_param_relaxed"

    removed_body = api_contract._check_request_body_changes(
        "/users", "post", {"content": {}}, None, baseline_document, current_document
    )
    assert removed_body[0]["type"] == "request_body_removed"

    removed_content = api_contract._check_request_body_changes(
        "/users",
        "post",
        {"content": {"application/json": {"schema": {"type": "object"}}}},
        {"content": {"text/plain": {"schema": {"type": "string"}}}},
        baseline_document,
        current_document,
    )
    assert removed_content[0]["type"] == "request_content_type_removed"

    response_changes = api_contract._check_response_changes(
        "/users",
        "get",
        {
            "responses": {
                "x-note": {},
                "404": {},
                "200": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "201": {},
            }
        },
        {"responses": {"404": {}, "200": {"content": {}}}},
        baseline_document,
        current_document,
    )
    assert any(change["type"] == "response_removed" for change in response_changes)
    assert any(change["type"] == "response_content_type_removed" for change in response_changes)

    assert api_contract._resolve_schema({"$ref": "#/components/schemas/User"}, baseline_document) == {"type": "object"}
    assert api_contract._resolve_schema({"$ref": "#/components/schemas/Missing"}, baseline_document) == {}
    assert api_contract._same_schema_reference(
        {"$ref": "#/components/schemas/User"}, {"$ref": "#/components/schemas/User"}
    )
    assert not api_contract._same_schema_reference({"type": "string"}, {"type": "string"})

    composition = api_contract._compare_schema(
        {"$ref": "#/components/schemas/User"},
        {"anyOf": [{"$ref": "#/components/schemas/User"}]},
        "GET /users response",
        "response_schema_changed",
        baseline_document,
        current_document,
    )
    assert composition == []


def test_api_contract_schema_constraints_and_nested_shapes() -> None:
    type_change, compatible = api_contract._compare_basic_schema(
        {"type": "string"}, {"type": "integer"}, "field", "parameter_schema_changed"
    )
    assert type_change
    assert compatible is False

    comparisons = (
        ({"format": "email"}, {"format": "uuid"}),
        ({"nullable": True}, {"nullable": False}),
        ({"enum": ["a", "b"]}, {"enum": ["a"]}),
        ({"minLength": 2}, {"minLength": 3}),
        ({"minItems": 2}, {"minItems": 3}),
        ({"minimum": 2}, {"minimum": 3}),
        ({"exclusiveMinimum": 2}, {"exclusiveMinimum": 3}),
        ({"maxLength": 3}, {"maxLength": 2}),
        ({"maxItems": 3}, {"maxItems": 2}),
        ({"maximum": 3}, {"maximum": 2}),
        ({"exclusiveMaximum": 3}, {"exclusiveMaximum": 2}),
    )
    for baseline, current in comparisons:
        changes, compatible = api_contract._compare_basic_schema(baseline, current, "field", "schema_changed")
        assert changes
        assert compatible

    baseline_document: dict[str, Any] = {
        "type": "object",
        "required": ["id", "name"],
        "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
        "additionalProperties": True,
    }
    current_document: dict[str, Any] = {
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "integer"}},
        "additionalProperties": False,
    }
    object_changes = api_contract._compare_schema(
        baseline_document, current_document, "payload", "response_schema_changed", {}, {}
    )
    assert len(object_changes) >= 3

    required_request = api_contract._compare_schema(
        {"type": "object", "required": [], "properties": {}},
        {"type": "object", "required": ["name"], "properties": {}},
        "payload",
        "request_schema_changed",
        {},
        {},
    )
    assert any("Required request fields" in change["message"] for change in required_request)

    array_changes = api_contract._compare_schema(
        {"type": "array", "items": {"type": "string"}},
        {"type": "array", "items": {"type": "integer"}},
        "payload",
        "response_schema_changed",
        {},
        {},
    )
    assert array_changes
    assert api_contract._compare_schema({}, {"type": "string"}, "missing", "schema_changed", {}, {}) == []
    assert api_contract._compare_schema({"type": "string"}, {}, "removed", "schema_changed", {}, {})


def test_api_contract_cli_helpers_and_main(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    baseline_path = tmp_path / "baseline.json"
    schema = {"openapi": "3.1.0", "paths": {}}

    with patch.object(api_contract.sys, "argv", ["checker", "--baseline", str(baseline_path), "--update-baseline"]):
        args = api_contract._parse_args()
    assert args.baseline == str(baseline_path)
    assert args.update_baseline is True

    assert api_contract._handle_missing_baseline(baseline_path, False) == 1
    with patch.object(api_contract, "get_current_schema", return_value=schema):
        assert api_contract._handle_missing_baseline(baseline_path, True) == 0
    assert json.loads(baseline_path.read_text(encoding="utf-8")) == schema

    api_contract._report_changes([{"message": "breaking"}], [{"message": "warning"}])
    captured = capsys.readouterr().out
    assert "breaking" in captured
    assert "warning" in captured
    api_contract._report_changes([], [])
    assert "No breaking changes" in capsys.readouterr().out

    current: dict[str, Any] = {"paths": {}}
    assert api_contract._handle_breaking_changes([], True, True, baseline_path, current) == 0
    assert api_contract._handle_breaking_changes([{"message": "breaking"}], True, True, baseline_path, current) == 0
    assert api_contract._handle_breaking_changes([{"message": "breaking"}], False, False, baseline_path, current) == 0
    assert api_contract._handle_breaking_changes([{"message": "breaking"}], True, False, baseline_path, current) == 1

    with (
        patch.object(
            api_contract,
            "_parse_args",
            return_value=Namespace(baseline=str(baseline_path), update_baseline=False, fail_on_breaking=True),
        ),
        patch.object(api_contract, "load_schema", return_value=schema),
        patch.object(api_contract, "get_current_schema", return_value=schema),
    ):
        assert api_contract.main() == 0


def _load_seed_admin_module(client: MagicMock):
    sys.modules.pop("scripts.seed_admin_data", None)
    with (
        patch.object(config, "SUPABASE_SERVICE_KEY", "test-service-key"),
        patch("app.utils.supabase_client.get_supabase_admin_client", return_value=client),
    ):
        return importlib.import_module("scripts.seed_admin_data")


def test_seed_admin_helpers_cover_success_and_failure_paths() -> None:
    client = MagicMock()
    builder = MagicMock()
    client.table.return_value = builder
    builder.upsert.return_value.execute.return_value = SimpleNamespace(data=[{"id": "row-1"}])
    module = _load_seed_admin_module(client)
    module.INITIAL_PERMISSIONS = [{"code": "photos.read"}]
    module.INITIAL_ROLES = [{"name": "admin"}]
    module.ROLE_PERMISSION_MAPPING = {"admin": ["*"]}

    assert module._seed_permissions() == {"photos.read": "row-1"}
    assert module._seed_roles() == {"admin": "row-1"}
    rows = module._build_role_permission_rows({"photos.read": "permission-1"}, {"admin": "role-1"})
    assert rows == [{"role_id": "role-1", "permission_id": "permission-1"}]
    assert module._build_role_permission_rows({}, {}) == []

    module._insert_role_permissions([])
    module._insert_role_permissions(rows)
    builder.upsert.side_effect = RuntimeError("seed failed")
    assert module._seed_permissions() == {}
    assert module._seed_roles() == {}
    module._insert_role_permissions(rows)

    with (
        patch.object(module, "_seed_permissions", return_value={}),
        patch.object(module, "_seed_roles", return_value={}),
        patch.object(module, "_build_role_permission_rows", return_value=[]),
        patch.object(module, "_insert_role_permissions") as insert,
    ):
        module.seed_data()
    insert.assert_called_once_with([])


def _load_seed_data_module(client: MagicMock):
    sys.modules.pop("scripts.seed_data", None)
    with (
        patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "test-service-key"},
            clear=False,
        ),
        patch("supabase.create_client", return_value=client),
    ):
        return importlib.import_module("scripts.seed_data")


def test_seed_data_helpers_cover_empty_and_populated_paths() -> None:
    client = MagicMock()
    builder = MagicMock()
    client.table.return_value = builder
    builder.select.return_value = builder
    builder.limit.return_value = builder
    builder.insert.return_value = builder
    builder.execute.return_value = SimpleNamespace(data=[{"id": "user-1"}])
    module = _load_seed_data_module(client)

    users = module._load_seed_users()
    assert len(users) == 5
    builder.execute.return_value = SimpleNamespace(data=[])
    assert module._load_seed_users() == []

    builder.execute.return_value = SimpleNamespace(data=[{"id": "photo-1"}])
    users = [{"id": "user-1"}]
    with patch.object(module.random, "choice", side_effect=lambda values: values[0]):
        photos = module._create_seed_photos(users)
    assert len(photos) == 10
    assert all(photo == {"id": "photo-1"} for photo in photos)

    module._create_seed_interactions(photos, users)
    with patch.object(module.random, "randint", side_effect=[0, 1] * len(photos)):
        module._create_seed_interactions(photos, [])

    with (
        patch.object(module, "_load_seed_users", return_value=[]),
        patch.object(module, "_create_seed_photos") as create_photos,
        patch.object(module, "_create_seed_interactions") as create_interactions,
    ):
        module.seed_data()
    create_photos.assert_not_called()
    create_interactions.assert_not_called()

    with (
        patch.object(module, "_load_seed_users", return_value=users),
        patch.object(module, "_create_seed_photos", return_value=photos) as create_photos,
        patch.object(module, "_create_seed_interactions") as create_interactions,
    ):
        module.seed_data()
    create_photos.assert_called_once_with(users)
    create_interactions.assert_called_once_with(photos, users)


@pytest.mark.asyncio
async def test_dead_letter_inspection_redacts_and_closes() -> None:
    message = SimpleNamespace(
        message_id="message-1",
        fields={
            "message": json.dumps(
                {
                    "source_stream": "vision",
                    "source_message_id": "source-1",
                    "reason": "timeout",
                    "fields": {"secret": "omitted"},  # pragma: allowlist secret
                    "fields_redacted": True,
                    "failed_at": "2026-08-17T00:00:00Z",
                }
            )
        },
    )
    with (
        patch.object(
            inspect_dead_letters,
            "_arguments",
            return_value=Namespace(stream="stripe", count=4),
        ),
        patch.object(
            inspect_dead_letters.queue_service, "read_dead_letters", new=AsyncMock(return_value=[message])
        ) as read,
        patch.object(inspect_dead_letters.queue_service, "close", new=AsyncMock()) as close,
    ):
        await inspect_dead_letters._run()
    read.assert_awaited_once_with(inspect_dead_letters.QueueService.STRIPE_STREAM, 4)
    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_dead_letter_inspection_closes_on_read_failure() -> None:
    failure = RuntimeError("queue unavailable")
    with (
        patch.object(
            inspect_dead_letters,
            "_arguments",
            return_value=Namespace(stream="vision", count=1),
        ),
        patch.object(inspect_dead_letters.queue_service, "read_dead_letters", new=AsyncMock(side_effect=failure)),
        patch.object(inspect_dead_letters.queue_service, "close", new=AsyncMock()) as close,
        pytest.raises(RuntimeError, match="queue unavailable"),
    ):
        await inspect_dead_letters._run()
    close.assert_awaited_once()
