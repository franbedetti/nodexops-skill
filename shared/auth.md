# Authentication

All NodeXOps public API endpoints use **Bearer token** auth with API keys.

## Header format

```
Authorization: Bearer nx_<your-key>
```

## Scopes

Each API key has a list of scopes. You receive a 403 if the key is missing the required scope OR if the key was issued for a different store than the one in the URL.

| Scope | Permits |
|---|---|
| `nodexgen:read` | Read product descriptions and logs |
| `nodexgen:write` | Create/update product descriptions (and bulk) |
| `block-groups:read` | List and read block-groups |
| `block-groups:write` | Create/update/delete block-groups |
| `products:read` | Catalog discovery: list/read Tiendanube products, categories, store info |
| `products:write` | Catalog writes: create/update/delete Tiendanube products (price, stock and variants included — goes live immediately) |
| `nodexpage:read` | (Phase 2) Read content pages |
| `nodexpage:write` | (Phase 2) Create/update content pages |
| `nodexblog:read` | (Phase 3) Read blog posts |
| `nodexblog:write` | (Phase 3) Create/update blog posts |

Default scopes on a freshly-issued key: `nodexgen:read`, `nodexgen:write`, `block-groups:read`, `block-groups:write`, `products:read`, `products:write` — the typical "product migration" use case. **The default includes catalog writes.**

### Read-only keys

If your integration only needs to read (or only writes descriptions), don't carry `products:write` around. Ask the NodeXOps admin for a key with only the scopes you need, or mint one yourself from the key you already have — a key can create another key for its own store with a **subset** of its scopes (and a rate limit no higher than its own):

```bash
curl -X POST https://v2.nodexops.com/api/v2/api-keys/ \
  -H "Authorization: Bearer $NODEXOPS_API_KEY" -H "Content-Type: application/json" \
  -d '{"store_id": 12345, "name": "read-only reporting",
       "scopes": ["nodexgen:read", "block-groups:read", "products:read"]}'
```

The response carries the new key in `raw_key` (shown only once). Revoke a key with `DELETE /api/v2/api-keys/{key_id}`.

## Per-store enforcement

Each API key is bound to **exactly one store**. URL paths embed the `store_id`. If the URL's store_id ≠ key's store_id, the request is rejected with `403 Insufficient permissions`.

## Errors

| HTTP | Meaning |
|---|---|
| 401 | Bearer header missing/invalid, or key revoked/expired |
| 403 | Key lacks required scope OR key is for a different store |
| 404 | Resource (product, group, page) not found in this store |
| 422 | Tiendanube rejected the data (catalog endpoints): `detail` = `{tiendanube_status, message}` with Tiendanube's own reason |
| 429 | Rate limit (default 120 req/min, configurable per key), or Tiendanube's own limit on catalog endpoints. Always with `Retry-After` |
| 500 | Internal error (retry with backoff) |
| 502 | Tiendanube failed or did not respond (retry with backoff) |

Error messages are intentionally generic, except Tiendanube's own rejection reason on catalog endpoints (the 422 above) — see `modules/catalog.md` → Errors.

## Rate limiting

- **Default**: 120 requests/minute per API key (sliding window)
- Configurable per-key (admin can raise)
- 429 response includes a `Retry-After` header (seconds), plus `X-RateLimit-Limit` and `X-RateLimit-Remaining`

## Audit

Every `/api/v2/*` request is logged with: API key id, store, HTTP method + path, status code, IP, user-agent, timestamp — and, when Tiendanube failed a catalog call, its reason (status, category and, for a 422, TN's message; never request bodies or tokens). The log is server-side: ask the NodeXOps admin to trace a request (give them the time, method and path).
