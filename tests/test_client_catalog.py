"""Tests for NodexClient.catalog — TN passthrough, incl. writes (API-03)."""

from unittest.mock import patch

import pytest
import requests_mock

from skills.nodexops.client import NodexAPIError, NodexClient

BASE = "https://test.local/api/v2/stores/42/products"


@pytest.fixture
def client():
    return NodexClient(base_url="https://test.local", api_key="nx_test", store_id=42)


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("skills.nodexops.client.time.sleep"):
        yield


def test_create_product_sends_payload_as_is(client):
    data = {
        "name": {"es": "Remera"},
        "variants": [{"price": "1500.00", "stock": 10, "sku": "REM-1"}],
        "published": False,
    }
    with requests_mock.Mocker() as m:
        m.post(BASE, json={"id": 555, "name": {"es": "Remera"}})
        result = client.catalog.create_product(data)
        assert m.last_request.method == "POST"
        assert m.last_request.json() == data
    assert result["id"] == 555


def test_update_product_uses_put(client):
    with requests_mock.Mocker() as m:
        m.put(f"{BASE}/555", json={"id": 555, "published": True})
        result = client.catalog.update_product(555, {"published": True})
        assert m.last_request.json() == {"published": True}
    assert result["published"] is True


def test_delete_product(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE}/555", json={"ok": True})
        assert client.catalog.delete_product(555) == {"ok": True}
        assert m.last_request.method == "DELETE"


def test_create_does_not_retry_on_502(client):
    """A 502 may mean TN created the product: retrying blindly would duplicate it."""
    with requests_mock.Mocker() as m:
        m.post(BASE, [
            {"status_code": 502, "json": {"detail": {"tiendanube_status": 503}}},
            {"status_code": 200, "json": {"id": 1}},
        ])
        with pytest.raises(NodexAPIError) as e:
            client.catalog.create_product({"name": {"es": "x"}})
        assert m.call_count == 1
    assert e.value.status_code == 502


def test_delete_does_not_retry_on_502(client):
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE}/9", [{"status_code": 502}, {"status_code": 200, "json": {"ok": True}}])
        with pytest.raises(NodexAPIError):
            client.catalog.delete_product(9)
        assert m.call_count == 1


def test_update_retries_on_502(client):
    """PUT with the same body is safe to repeat."""
    with requests_mock.Mocker() as m:
        m.put(f"{BASE}/9", [{"status_code": 502}, {"status_code": 200, "json": {"id": 9}}])
        assert client.catalog.update_product(9, {"published": True})["id"] == 9
        assert m.call_count == 2


def test_create_retries_on_429_honoring_retry_after(client):
    """A 429 means the request was not processed: always safe to retry."""
    with requests_mock.Mocker() as m, patch("skills.nodexops.client.time.sleep") as sleep:
        m.post(BASE, [
            {"status_code": 429, "headers": {"Retry-After": "60"}},
            {"status_code": 200, "json": {"id": 7}},
        ])
        assert client.catalog.create_product({"name": {"es": "x"}})["id"] == 7
    sleep.assert_called_once_with(60)


def test_422_exposes_tiendanube_reason(client):
    detail = {"tiendanube_status": 422, "message": {"description": {"sku": ["has already been taken"]}}}
    with requests_mock.Mocker() as m:
        m.post(BASE, status_code=422, json={"detail": detail})
        with pytest.raises(NodexAPIError) as e:
            client.catalog.create_product({"name": {"es": "x"}})
    assert e.value.status_code == 422
    assert e.value.body["detail"]["message"]["description"]["sku"] == ["has already been taken"]
