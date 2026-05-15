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
| `nodexpage:read` | (Phase 2) Read content pages |
| `nodexpage:write` | (Phase 2) Create/update content pages |
| `nodexblog:read` | (Phase 3) Read blog posts |
| `nodexblog:write` | (Phase 3) Create/update blog posts |

Default scopes on a freshly-issued key cover NodexGen + block-groups for the typical "product migration" use case.

## Per-store enforcement

Each API key is bound to **exactly one store**. URL paths embed the `store_id`. If the URL's store_id ≠ key's store_id, the request is rejected with `403 Insufficient permissions`.

## Errors

| HTTP | Meaning |
|---|---|
| 401 | Bearer header missing/invalid, or key revoked/expired |
| 403 | Key lacks required scope OR key is for a different store |
| 404 | Resource (product, group, page) not found in this store |
| 429 | Rate limit (default 120 req/min, configurable per key) |
| 500 | Internal error or Tiendanube API failure (retry with backoff) |

Error messages are intentionally generic. Detailed reasons go to the server-side audit log only.

## Rate limiting

- **Default**: 120 requests/minute per API key (sliding window)
- Configurable per-key (admin can raise)
- 429 response includes a `Retry-After` header (seconds)

## Audit

Every `/api/v2/*` request is logged with: API key id, store, HTTP method + path, status code, IP, user-agent, timestamp. Visible to admins via `GET /api/v2/admin/api-keys/{key_id}/usage`.
