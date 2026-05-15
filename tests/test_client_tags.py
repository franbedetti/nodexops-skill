"""Tests for NodexClient.tags and NodexClient.media.search."""

import pytest
import requests_mock as rm

from skills.nodexops.client import NodexClient


BASE = "https://test.local"
STORE = 42
API_KEY = "nx_test"


@pytest.fixture
def client():
    return NodexClient(base_url=BASE, api_key=API_KEY, store_id=STORE)


def test_tags_list(client):
    """tags.list() calls GET /stores/{store_id}/nodexgen/tags."""
    payload = [
        {"id": 1, "name": "alpha", "image_count": 5, "created_at": "2025-01-01T00:00:00+00:00"},
        {"id": 2, "name": "beta", "image_count": 0, "created_at": "2025-01-01T00:00:00+00:00"},
    ]
    with rm.Mocker() as m:
        m.get(f"{BASE}/api/v2/stores/{STORE}/nodexgen/tags", json=payload)
        result = client.tags.list()
    assert len(result) == 2
    assert result[0]["name"] == "alpha"
    assert result[1]["image_count"] == 0


def test_tags_create(client):
    """tags.create('new-tag') calls POST with correct body."""
    payload = {"id": 7, "name": "new-tag", "image_count": 0, "created_at": "2025-01-01T00:00:00+00:00"}
    with rm.Mocker() as m:
        m.post(f"{BASE}/api/v2/stores/{STORE}/nodexgen/tags", json=payload)
        result = client.tags.create("new-tag")
    assert result["id"] == 7
    assert result["name"] == "new-tag"
    body = m.last_request.json()
    assert body == {"name": "new-tag"}


def test_tags_rename(client):
    """tags.rename(tag_id, new_name) calls PUT /{tag_id}."""
    payload = {"id": 3, "name": "renamed", "image_count": 2, "created_at": "2025-01-01T00:00:00+00:00"}
    with rm.Mocker() as m:
        m.put(f"{BASE}/api/v2/stores/{STORE}/nodexgen/tags/3", json=payload)
        result = client.tags.rename(3, "renamed")
    assert result["name"] == "renamed"
    body = m.last_request.json()
    assert body == {"name": "renamed"}


def test_tags_delete(client):
    """tags.delete(tag_id) calls DELETE /{tag_id} without merge_into."""
    payload = {"ok": True, "deleted_tag": "old", "affected_images": 4, "merged_into": None}
    with rm.Mocker() as m:
        m.delete(f"{BASE}/api/v2/stores/{STORE}/nodexgen/tags/10", json=payload)
        result = client.tags.delete(10)
    assert result["ok"] is True
    assert result["deleted_tag"] == "old"
    assert result["merged_into"] is None
    # No merge_into param
    assert "merge_into" not in (m.last_request.url or "")


def test_tags_delete_with_merge_into(client):
    """tags.delete(tag_id, merge_into=X) passes merge_into query param."""
    payload = {"ok": True, "deleted_tag": "old", "affected_images": 2, "merged_into": "new"}
    with rm.Mocker() as m:
        m.delete(f"{BASE}/api/v2/stores/{STORE}/nodexgen/tags/10", json=payload)
        result = client.tags.delete(10, merge_into=20)
    assert result["merged_into"] == "new"
    # Verify the request included merge_into param
    assert "merge_into=20" in m.last_request.url


def test_media_search_with_tags(client):
    """media.search(tags=['a','b']) calls GET /media?tags=a,b&match=all."""
    payload = {
        "ok": True, "total": 1,
        "items": [{"file_id": "f1", "original_name": "img.jpg", "note": "",
                   "tags": ["a", "b"], "created_at": "2025-01-01T00:00:00+00:00"}],
    }
    with rm.Mocker() as m:
        m.get(f"{BASE}/api/v2/stores/{STORE}/nodexgen/media", json=payload)
        result = client.media.search(tags=["a", "b"], match="all")
    assert result["ok"] is True
    assert result["total"] == 1
    assert "tags=a%2Cb" in m.last_request.url or "tags=a,b" in m.last_request.url
    assert "match=all" in m.last_request.url


def test_media_search_no_tags(client):
    """media.search() without tags calls GET /media without tags param."""
    payload = {"ok": True, "total": 0, "items": []}
    with rm.Mocker() as m:
        m.get(f"{BASE}/api/v2/stores/{STORE}/nodexgen/media", json=payload)
        result = client.media.search()
    assert result["ok"] is True
    assert "tags=" not in m.last_request.url
