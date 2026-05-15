"""NodexClient — embedded Python SDK for NodeXOps public API.

Copy this file into your consumer project (rename freely, e.g. nodex_client.py).
Only dependency: requests (>=2.28).

Usage:
    from nodex_client import NodexClient

    client = NodexClient(
        base_url="https://v2.nodexops.com",
        api_key=os.environ["NODEXOPS_API_KEY"],
        store_id=12345,
    )

    client.products.get(product_id=999)
    client.products.upload(product_id=999, blocks=[...], as_draft=False)
"""

from __future__ import annotations

import time
from typing import Any
import requests


class NodexAPIError(Exception):
    """Raised on non-2xx responses (after retry budget exhausted)."""

    def __init__(self, status_code: int, message: str, body: Any = None):
        self.status_code = status_code
        self.body = body
        super().__init__(f"[{status_code}] {message}")


class _Session:
    """Internal: handles HTTP, retries, error normalization."""

    def __init__(self, base_url: str, api_key: str, store_id: int, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.store_id = store_id
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "nodex-client/0.1",
        })

    def request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries):
            response = self._session.request(method, url, timeout=30, **kwargs)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", "1"))
                time.sleep(max(wait, 1))
                continue
            if response.status_code >= 500 and attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            if not response.ok:
                try:
                    body = response.json()
                except Exception:
                    body = response.text
                raise NodexAPIError(response.status_code, response.reason, body)
            return response.json()
        raise NodexAPIError(429, "Rate limit exhausted after retries")


class _ProductsAPI:
    """NodexGen — product description PDPs."""

    def __init__(self, session: _Session):
        self._s = session

    def list(self, limit: int = 50) -> list[dict]:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/descriptions"
        resp = self._s.request("GET", path, params={"limit": limit})
        return resp["logs"]

    def get(self, product_id: int) -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/descriptions/{product_id}"
        return self._s.request("GET", path)

    def upload(
        self,
        product_id: int,
        blocks: list[dict],
        product_name: str | None = None,
        template_id: str = "default",
        descripcion_corta: str | None = None,
        as_draft: bool = False,
    ) -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/descriptions/{product_id}"
        body = {
            "blocks": blocks,
            "template_id": template_id,
            "as_draft": as_draft,
        }
        if product_name is not None:
            body["product_name"] = product_name
        if descripcion_corta is not None:
            body["descripcion_corta"] = descripcion_corta
        return self._s.request("POST", path, json=body)

    def update(
        self,
        product_id: int,
        blocks: list[dict],
        product_name: str | None = None,
        template_id: str = "default",
        descripcion_corta: str | None = None,
        as_draft: bool = False,
    ) -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/descriptions/{product_id}"
        body = {
            "blocks": blocks,
            "template_id": template_id,
            "as_draft": as_draft,
        }
        if product_name is not None:
            body["product_name"] = product_name
        if descripcion_corta is not None:
            body["descripcion_corta"] = descripcion_corta
        return self._s.request("PUT", path, json=body)

    def bulk_upload(
        self,
        items: list[dict],
        as_draft: bool = False,
        stop_on_error: bool = False,
    ) -> dict:
        """Upload N product descriptions in one request. Max 50 items.

        Each item dict should have: product_id (int, required),
        product_name (str), template_id (str, default 'default'),
        descripcion_corta (str), blocks (list[dict]).
        """
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/descriptions/bulk"
        body = {
            "items": items,
            "as_draft": as_draft,
            "stop_on_error": stop_on_error,
        }
        return self._s.request("POST", path, json=body)


class _BlockGroupsAPI:
    """Block-groups — saved arrays of blocks usable as per-brand templates."""

    def __init__(self, session: _Session):
        self._s = session

    def list(self) -> list[dict]:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/block-groups"
        return self._s.request("GET", path)

    def get(self, group_id: int) -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/block-groups/{group_id}"
        return self._s.request("GET", path)

    def create(self, name: str, blocks: list[dict], tag: str = "") -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/block-groups"
        return self._s.request("POST", path, json={
            "name": name, "blocks": blocks, "tag": tag,
        })

    def update(self, group_id: int, name: str, blocks: list[dict], tag: str = "") -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/block-groups/{group_id}"
        return self._s.request("PUT", path, json={
            "name": name, "blocks": blocks, "tag": tag,
        })

    def delete(self, group_id: int) -> dict:
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/block-groups/{group_id}"
        return self._s.request("DELETE", path)


class _MediaAPI:
    """Upload local images/videos to ImageKit via NodeXOps."""

    def __init__(self, session: _Session):
        self._s = session

    def upload(
        self,
        file_path: str | None = None,
        data: str | None = None,
        filename: str | None = None,
        kind: str | None = None,
        keep_png: bool = False,
        tags: list[str] | None = None,
        note: str = "",
        original_name: str = "",
    ) -> dict:
        """Upload an image or video to ImageKit.

        Pass either `file_path` (local file, auto-encoded to data URI) OR `data` + `filename`.
        kind auto-detects from MIME if not specified.

        Returns: {ok, url, name, size, file_id, kind, folder, tags, note}
        """
        if file_path is not None:
            import base64
            import mimetypes
            from pathlib import Path
            p = Path(file_path)
            raw = p.read_bytes()
            mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            data = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
            filename = filename or p.name
        elif data is None or filename is None:
            raise ValueError("Provide either file_path OR (data + filename)")

        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/media/upload"
        body = {
            "data": data,
            "filename": filename,
            "keep_png": keep_png,
            "tags": tags or [],
            "note": note,
            "original_name": original_name,
        }
        if kind is not None:
            body["kind"] = kind
        return self._s.request("POST", path, json=body)

    def search(
        self,
        tags: list[str] | None = None,
        match: str = "all",
        limit: int = 50,
    ) -> dict:
        """Search image_metadata rows by tags (local DB metadata search).

        Args:
            tags: list of tag names to filter by (None = return all)
            match: "all" (must have ALL tags) or "any" (must have ANY tag)
            limit: max results (1-500)

        Returns: {ok, total, items: [{file_id, original_name, note, tags, created_at}]}

        Note: only returns files that have metadata (tags or note). Use `library()`
        to list ALL files in the ImageKit library (with or without metadata).
        """
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/media"
        params: dict = {"match": match, "limit": limit}
        if tags:
            params["tags"] = ",".join(tags)
        return self._s.request("GET", path, params=params)

    def library(
        self,
        file_type: str = "all",
        name: str = "",
        limit: int = 50,
    ) -> dict:
        """List ALL files in the store's ImageKit library (read scope: nodexgen:read).

        Args:
            file_type: "image" | "non-image" (videos) | "all" (default)
            name: substring filter on filename, case-insensitive (default empty = no filter)
            limit: 1-200 (default 50)

        Returns: {ok, count, files: [{file_id, name, url, file_path, thumbnail, size, created_at, file_type}]}

        Use file_id from results to call delete().
        """
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/media/library"
        params: dict = {"file_type": file_type, "limit": limit}
        if name:
            params["name"] = name
        return self._s.request("GET", path, params=params)

    def delete(self, file_id: str) -> dict:
        """Delete a single file from the store's ImageKit library (write scope: nodexgen:write).

        Args:
            file_id: ImageKit fileId (get it from library() or upload() response)

        Returns: {ok, file_id, file_path, metadata_removed}

        Raises:
            APIError 404 if file not found in ImageKit
            APIError 403 if file does not belong to this store (filePath mismatch)
        """
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/media/{file_id}"
        return self._s.request("DELETE", path)


class _TagsAPI:
    """Curated tag vocabulary for media."""

    def __init__(self, session: _Session):
        self._s = session

    def list(self) -> list[dict]:
        """List all tags for the store with image counts."""
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/tags"
        return self._s.request("GET", path)

    def create(self, name: str) -> dict:
        """Create a new tag in the store's curated vocabulary."""
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/tags"
        return self._s.request("POST", path, json={"name": name})

    def rename(self, tag_id: int, new_name: str) -> dict:
        """Rename a tag (bulk-updates all image_metadata rows that reference it)."""
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/tags/{tag_id}"
        return self._s.request("PUT", path, json={"name": new_name})

    def delete(self, tag_id: int, merge_into: int | None = None) -> dict:
        """Delete a tag. Pass merge_into to absorb it into another tag instead."""
        path = f"/api/v2/stores/{self._s.store_id}/nodexgen/tags/{tag_id}"
        params = {"merge_into": merge_into} if merge_into is not None else None
        return self._s.request("DELETE", path, params=params)


class _CatalogAPI:
    """Tiendanube passthrough — list TN products, categories, store info.

    Distinct from ``client.products`` which targets NodexGen descriptions.
    Use ``client.catalog`` to discover which products to edit; use
    ``client.products`` to read/write their descriptions.
    """

    def __init__(self, session: _Session):
        self._s = session

    def products(
        self,
        q: str | None = None,
        category_id: int | None = None,
        published: bool | None = None,
        created_at_min: str | None = None,
        created_at_max: str | None = None,
        updated_at_min: str | None = None,
        updated_at_max: str | None = None,
        page: int = 1,
        per_page: int = 50,
        fields: str | None = None,
    ) -> list[dict]:
        """List products from Tiendanube. Supports filtering by category_id,
        published state, and ISO date ranges (created_at_*, updated_at_*).

        Returns the raw TN product list (a list of product dicts).
        """
        path = f"/api/v2/stores/{self._s.store_id}/products"
        params: dict = {"page": page, "per_page": per_page}
        if q is not None:
            params["q"] = q
        if category_id is not None:
            params["category_id"] = category_id
        if published is not None:
            params["published"] = "true" if published else "false"
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        if updated_at_max:
            params["updated_at_max"] = updated_at_max
        if fields:
            params["fields"] = fields
        return self._s.request("GET", path, params=params)

    def product(self, product_id: int) -> dict:
        """Get a single product from Tiendanube (full payload including variants)."""
        path = f"/api/v2/stores/{self._s.store_id}/products/{product_id}"
        return self._s.request("GET", path)

    def categories(self) -> list[dict]:
        """Flat list of all categories: ``[{id, name, parent_id, permalink}, ...]``."""
        path = f"/api/v2/stores/{self._s.store_id}/categories"
        return self._s.request("GET", path)

    def store_info(self) -> dict:
        """Tiendanube store info: name, domain, currency, language, etc."""
        path = f"/api/v2/stores/{self._s.store_id}/store-info"
        return self._s.request("GET", path)


class NodexClient:
    """Top-level entrypoint. One instance per (store, key) pair."""

    def __init__(self, base_url: str, api_key: str, store_id: int, max_retries: int = 3):
        self._session = _Session(base_url, api_key, store_id, max_retries=max_retries)
        self.products = _ProductsAPI(self._session)
        self.catalog = _CatalogAPI(self._session)
        self.block_groups = _BlockGroupsAPI(self._session)
        self.media = _MediaAPI(self._session)
        self.tags = _TagsAPI(self._session)
