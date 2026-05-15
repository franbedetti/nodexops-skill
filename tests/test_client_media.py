"""Tests for NodexClient.media."""

import base64
import tempfile
from pathlib import Path

import pytest
import requests_mock

from skills.nodexops.client import NodexClient


@pytest.fixture
def client():
    return NodexClient(base_url="https://test.local", api_key="nx_test", store_id=42)


def test_upload_with_data_uri(client):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/media/upload",
            json={"ok": True, "url": "https://ik.imagekit.io/x/img.webp", "kind": "image",
                  "file_id": "abc", "folder": "/store-42/imagenes", "tags": [], "note": ""},
        )
        result = client.media.upload(
            data="data:image/jpeg;base64,xyz",
            filename="hero.jpg",
            tags=["chochecitos"],
        )
    assert result["url"] == "https://ik.imagekit.io/x/img.webp"
    body = m.last_request.json()
    assert body["data"] == "data:image/jpeg;base64,xyz"
    assert body["filename"] == "hero.jpg"
    assert body["tags"] == ["chochecitos"]


def test_upload_with_file_path_auto_encodes(client, tmp_path):
    img_bytes = b"fake-jpeg-content"
    img_file = tmp_path / "test.jpg"
    img_file.write_bytes(img_bytes)

    with requests_mock.Mocker() as m:
        m.post(
            "https://test.local/api/v2/stores/42/nodexgen/media/upload",
            json={"ok": True, "url": "https://ik.imagekit.io/x/img.webp", "kind": "image",
                  "file_id": "abc", "folder": "/store-42/imagenes", "tags": [], "note": ""},
        )
        client.media.upload(file_path=str(img_file))
        body = m.last_request.json()
    expected_b64 = base64.b64encode(img_bytes).decode()
    assert body["data"] == f"data:image/jpeg;base64,{expected_b64}"
    assert body["filename"] == "test.jpg"


def test_upload_raises_when_neither_path_nor_data(client):
    with pytest.raises(ValueError, match="file_path"):
        client.media.upload()
