"""Tests for NodexClient.block_groups and NodexClient.products.bulk_upload."""

import pytest
import requests_mock

from skills.nodexops.client import NodexClient


@pytest.fixture
def client():
    return NodexClient(base_url="https://test.local", api_key="nx_test", store_id=42)


def test_list_block_groups(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.local/api/v2/stores/42/nodexgen/block-groups",
            json=[{"id": 1, "name": "Chochecitos", "blocks_count": 3}],
        )
        result = client.block_groups.list()
    assert result[0]["name"] == "Chochecitos"


def test_get_block_group(client):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.local/api/v2/stores/42/nodexgen/block-groups/7",
            json={"id": 7, "name": "X", "blocks": [{"block_type": "text-only"}]},
        )
        result = client.block_groups.get(7)
    assert result["id"] == 7
    assert len(result["blocks"]) == 1


def test_create_block_group(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/block-groups",
            json={"id": 9, "name": "New"},
        )
        result = client.block_groups.create(
            name="New", blocks=[{"block_type": "text-only"}], tag="brand-x",
        )
    assert result["id"] == 9
    assert m.last_request.json()["tag"] == "brand-x"


def test_update_block_group(client):
    with requests_mock.Mocker() as m:
        m.put(
            "https://test.local/api/v2/stores/42/nodexgen/block-groups/9",
            json={"id": 9, "name": "Renamed"},
        )
        client.block_groups.update(9, name="Renamed", blocks=[])
    assert m.last_request.json()["name"] == "Renamed"


def test_delete_block_group(client):
    with requests_mock.Mocker() as m:
        m.delete(
            "https://test.local/api/v2/stores/42/nodexgen/block-groups/9",
            json={"ok": True},
        )
        client.block_groups.delete(9)
    assert m.called


def test_bulk_upload(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/descriptions/bulk",
            json={
                "ok": True, "total": 2, "succeeded": 2, "failed": 0,
                "results": [
                    {"product_id": 1, "ok": True, "log_id": 100},
                    {"product_id": 2, "ok": True, "log_id": 101},
                ],
            },
        )
        result = client.products.bulk_upload(
            items=[
                {"product_id": 1, "blocks": []},
                {"product_id": 2, "blocks": []},
            ],
            as_draft=False,
        )
    assert result["succeeded"] == 2
    assert m.last_request.json()["items"][0]["product_id"] == 1
