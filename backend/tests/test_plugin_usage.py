"""插件使用统计的去重边界测试。"""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Request

from app.services.plugin_usage import _visitor_key, record_plugin_usage


def make_request(
    ip: str = "203.0.113.8",
    user_agent: str = "plugin-test",
    *,
    forwarded_ip: str | None = None,
) -> Request:
    """构造带反向代理来源信息的最小请求。"""

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (b"x-real-ip", ip.encode()),
                (b"x-forwarded-for", (forwarded_ip or ip).encode()),
                (b"user-agent", user_agent.encode()),
            ],
            "client": ("127.0.0.1", 12345),
        }
    )


def test_anonymous_visitor_key_is_stable_without_exposing_source_data() -> None:
    event_date = date(2026, 9, 12)
    first = _visitor_key(make_request(), None, event_date)
    second = _visitor_key(make_request(), None, event_date)

    assert first == second
    assert len(first) == 64
    assert "203.0.113.8" not in first
    assert "plugin-test" not in first


def test_visitor_key_changes_with_identity_or_date() -> None:
    request = make_request()
    assert _visitor_key(request, None, date(2026, 9, 12)) != _visitor_key(
        request,
        None,
        date(2026, 9, 13),
    )
    assert _visitor_key(request, None, date(2026, 9, 12)) != _visitor_key(
        make_request(ip="203.0.113.9"),
        None,
        date(2026, 9, 12),
    )


def test_spoofed_forwarded_address_does_not_change_visitor_key() -> None:
    event_date = date(2026, 9, 12)
    assert _visitor_key(make_request(), None, event_date) == _visitor_key(
        make_request(forwarded_ip="198.51.100.99"),
        None,
        event_date,
    )


@pytest.mark.asyncio
async def test_first_usage_increments_version_and_plugin_counters() -> None:
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(rowcount=1),
                SimpleNamespace(rowcount=1),
                SimpleNamespace(rowcount=1),
            ]
        )
    )

    counted = await record_plugin_usage(
        db,
        make_request(),
        SimpleNamespace(id=7),
        SimpleNamespace(id=11),
        "copy",
        user=None,
    )

    assert counted is True
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_duplicate_usage_does_not_increment_any_counter() -> None:
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(rowcount=0)))

    counted = await record_plugin_usage(
        db,
        make_request(),
        SimpleNamespace(id=7),
        SimpleNamespace(id=11),
        "download",
        user=None,
    )

    assert counted is False
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_unknown_usage_action_is_rejected() -> None:
    db = SimpleNamespace(execute=AsyncMock())

    with pytest.raises(ValueError, match="未知的插件使用事件"):
        await record_plugin_usage(
            db,
            make_request(),
            SimpleNamespace(id=7),
            SimpleNamespace(id=11),
            "preview",
            user=None,
        )

    assert db.execute.await_count == 0
