"""Tests for NodexClient.products — uses requests-mock to avoid network."""

import pytest
import requests_mock

from skills.nodexops.client import NodexClient


@pytest.fixture
def client():
    return NodexClient(
        base_url="https://test.local",
        api_key="nx_test",
        store_id=42,
    )


def test_products_get_returns_blocks(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/100",
            json={"ok": True, "found": True, "product_id": 100, "blocks": [{"titulo": "Hi"}]},
        )
        result = client.products.get(product_id=100)
    assert result["found"] is True
    assert result["blocks"][0]["titulo"] == "Hi"


def test_products_upload_sends_correct_payload(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/100",
            json={"ok": True, "log_id": 1, "action": "api"},
        )
        client.products.upload(
            product_id=100,
            blocks=[{"block_type": "text-only", "titulo": "Hi"}],
            product_name="Widget",
        )
        body = m.last_request.json()
    assert body["product_name"] == "Widget"
    assert body["blocks"][0]["titulo"] == "Hi"
    assert body.get("as_draft") is not True


def test_products_upload_as_draft(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/100",
            json={"ok": True, "draft_id": 5, "action": "api_draft", "tn_pushed": False},
        )
        result = client.products.upload(
            product_id=100,
            blocks=[{"block_type": "text-only"}],
            as_draft=True,
        )
        body = m.last_request.json()
    assert body["as_draft"] is True
    assert result["tn_pushed"] is False


def test_authorization_header_set(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/100",
            json={"ok": True, "found": False},
        )
        client.products.get(product_id=100)
    assert m.last_request.headers["Authorization"] == "Bearer nx_test"


def test_retries_on_429(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/100",
            [
                {"status_code": 429, "headers": {"Retry-After": "0"}},
                {"json": {"ok": True, "found": False}, "status_code": 200},
            ],
        )
        result = client.products.get(product_id=100)
    assert result["ok"] is True
    assert m.call_count == 2
