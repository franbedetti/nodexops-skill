# Catalog — Tiendanube passthrough

Proxies into the Tiendanube product API. Two uses:

- **Discovery** (read): find *which* products to work on — by category, date, text.
- **Catalog writes**: create, edit and delete the Tiendanube product itself — name, price, stock, variants, images, categories, published state.

For the block-based **description** of a product use `modules/nodexgen.md` (`client.products`), not these endpoints: a `description` written here bypasses NodeXOps and gets overwritten the next time the PDP is published from NodeXOps.

## Endpoints

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/api/v2/stores/{store_id}/products` | `products:read` | List TN products. Filters: `q`, `category_id`, `published`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `page`, `per_page`, `fields` |
| GET | `/api/v2/stores/{store_id}/products/{product_id}` | `products:read` | Full product payload (incl. variants, images, attributes) |
| GET | `/api/v2/stores/{store_id}/categories` | `products:read` | Flat list of categories: `[{id, name, parent_id, permalink}, ...]` |
| GET | `/api/v2/stores/{store_id}/store-info` | `products:read` | TN store info: name, domain, currency, language, etc. |
| POST | `/api/v2/stores/{store_id}/products` | `products:write` | Create a product. Returns TN's product payload (with the new `id`) |
| PUT | `/api/v2/stores/{store_id}/products/{product_id}` | `products:write` | Partial update: only the fields you send change. Returns the updated product |
| DELETE | `/api/v2/stores/{store_id}/products/{product_id}` | `products:write` | Delete the product. Returns `{"ok": true}` |

These mirror the Tiendanube API 1:1 (no transformation) except `/categories`, which is flattened from TN's nested name/handle dicts into the simpler shape above.

## ⚠️ Before you write

- **Writes hit the live store immediately.** There is no draft, no preview and no undo. A new price or stock value is what shoppers see (and buy at) the moment the call returns.
- **Delete is irreversible.** Tiendanube has no trash: the product, its variants, images and URL are gone. It cannot be restored — only re-created, with a new `id` (and whatever links pointed to the old one stop working).
- **NodeXOps does not validate the body.** It is forwarded to Tiendanube as-is; Tiendanube decides what is valid (see Errors). Test on one product and re-read it with `product()` before a bulk run.
- Keys that only need to read should not carry `products:write` — see `shared/auth.md` → "Read-only keys".

## Python client

```python
from nodex_client import NodexClient

client = NodexClient(...)

# Discover
cats = client.catalog.categories()
store = client.catalog.store_info()
products = client.catalog.products(category_id=42, published=True, per_page=200)

# Drill into one product
p = client.catalog.product(341034061)
print(p["name"], p["variants"][0]["price"])

# Create (published=False: it stays hidden until you check it)
new = client.catalog.create_product({
    "name": {"es": "Remera básica"},
    "published": False,
    "categories": [123],                       # create: plain ints
    "images": [{"src": "https://cdn.example.com/remera.jpg"}],
    "variants": [{"price": "15000.00", "stock": 10, "sku": "REM-001"}],
})

# Edit (partial)
client.catalog.update_product(new["id"], {"published": True})

# Delete — irreversible
client.catalog.delete_product(new["id"])
```

## Writable fields (passthrough)

Whatever Tiendanube's `POST /products` / `PUT /products/{id}` accepts. The most used:

| Field | Shape | Notes |
|---|---|---|
| `name` | `{"es": "..."}` | **Required on create.** Multi-language dict |
| `handle` | `{"es": "slug"}` | URL slug. Auto-generated from `name` if omitted |
| `published` | bool | Create with `false` to review before going live |
| `free_shipping` | bool | |
| `requires_shipping` | bool | If `false`, TN silently ignores writes to `weight`/`width`/`height`/`depth` |
| `categories` | create: `[123, 456]` · update: `[{"id": 123}]` | Different shape on each verb; mixing them → 422 `"All elements of categories must be integers."` |
| `images` | `[{"src": url, "position", "alt"}]` | Create only, max 9 per request. TN downloads and re-hosts the image |
| `variants` | `[{price, promotional_price, stock, sku, weight, width, height, depth, values}]` | Create: sets the product's variants. Without variants TN creates one "virtual" variant holding price/stock |
| `tags`, `seo_title`, `seo_description`, `brand`, `video_url`, `attributes` | | See TN's product docs |

Units and values that trip people up:

- `price` / `promotional_price` are strings (`"1500.00"`), in the store currency.
- `stock: ""` (empty string) = unlimited stock. `null` is not the same; reading back an unlimited variant gives `stock: null`.
- To clear `promotional_price` send `""`. Sending `null` returns 200 and changes nothing.
- `weight` is in **kg** (`"0.250"`); `width` / `height` / `depth` in **cm**.
- `seo_title` is cut at 70 **bytes** by TN (accents count double), even mid-word, and the PUT still returns 200.

Things this passthrough does **not** do: edit one variant's price/stock (TN's `/products/{id}/variants/{vid}`), per-location stock, or adding images to an existing product. Those TN endpoints are not exposed by NodeXOps.

### Changing `name` changes the URL

On `PUT`, changing `name` makes Tiendanube **regenerate the `handle`** — the product's public URL — and it may append a random suffix. The response is still 200. If the URL must stay, send the current `handle` in the same body:

```python
p = client.catalog.product(pid)
client.catalog.update_product(pid, {"name": {"es": "Nuevo nombre"}, "handle": p["handle"]})
```

## Errors

Tiendanube's errors are translated; you never get a bare 500 for a TN rejection. The body is FastAPI's `{"detail": ...}`, surfaced by the client as `NodexAPIError.body`.

| HTTP | When | `detail` | What to do |
|---|---|---|---|
| 404 | The product does not exist in this store | `"Not found in Tiendanube"` | Don't retry. For a delete retried after a 502, 404 means it was already deleted |
| 422 | Tiendanube rejected the data (wrong type, invalid value…) | `{"tiendanube_status": 400\|422, "message": <TN's body>}` | Fix the payload; retrying the same body fails again |
| 422 | NodeXOps' own body validation (e.g. `name` missing on create) | FastAPI's list of field errors | Fix the payload |
| 429 | NodeXOps' per-key limit or Tiendanube's own limit | `"Rate limit exceeded"` / `"Tiendanube rate limit"`; `Retry-After` header | Wait `Retry-After` seconds. Nothing was written, so retrying is safe |
| 502 | Tiendanube failed (5xx), did not respond, or rejected the store's token | `{"tiendanube_status": N}` or `"Tiendanube did not respond"` | See Idempotency |
| 403 | Missing scope, key for another store, or store inactive | | Check the key |

Example — categories sent as `[{"id": 123}]` on create (TN wants plain ints there). `message` is Tiendanube's own body, passed through untouched:

```json
HTTP/1.1 422
{"detail": {"tiendanube_status": 422,
            "message": {"code": 422, "message": "Unprocessable Entity",
                        "description": "All elements of categories must be integers."}}}
```

```python
from nodex_client import NodexAPIError

try:
    client.catalog.create_product({"name": {"es": "Remera"}, "categories": [{"id": 123}]})
except NodexAPIError as e:
    if e.status_code == 422:
        print("TN says:", e.body["detail"]["message"])
    else:
        raise
```

Example — Tiendanube down:

```json
HTTP/1.1 502
{"detail": {"tiendanube_status": 503}}
```

The reason of every TN error (status, category and TN's message for a 422) is also stored in the API audit log, so the store owner can trace a failed write.

## Rate limits

- Every call (read or write) counts against the key's limit: **120 requests/minute** by default, sliding window. A 429 carries `Retry-After` (seconds).
- Tiendanube has its own per-store limit; if TN answers 429 you get a 429 with TN's `Retry-After` (60 if TN sends none).
- The Python client retries 429s automatically (up to `max_retries`, sleeping `Retry-After`). For bulk runs, pace yourself below the limit instead of relying on retries.

## Idempotency — what happens if you retry

| Call | Safe to retry blindly? | Why |
|---|---|---|
| any call answered **429** | Yes | Nothing was written |
| any call answered **4xx** (404/422/403) | No point | Same body, same answer |
| `PUT` answered **502** / timeout | Yes | Same body, same end state. The client retries 5xx on PUT |
| `POST` answered **502** / timeout | **No** | TN may have created the product and the answer got lost. A second POST creates a **duplicate** (TN just adds a suffix to the handle). The client does **not** auto-retry it |
| `DELETE` answered **502** / timeout | Check first | It may already be gone. The client does not auto-retry; call `product(id)` — 404 means done |

There is no idempotency key. To make creates safe to re-run, give every product a unique SKU and check before creating:

```python
def create_once(client, payload, sku):
    hits = client.catalog.products(q=sku, fields="id,variants")
    for p in hits:
        if any(v.get("sku") == sku for v in p.get("variants", [])):
            return p                        # already created by a previous attempt
    return client.catalog.create_product(payload)
```

(`q` is TN's fuzzy text search, so the exact-SKU check on the variants is what decides. Before relying on this in a bulk run, confirm on your store that `products(q=<an existing sku>)` does find that product. Don't count on TN rejecting a repeated SKU for you.)

## Pagination

TN paginates server-side. Iterate `page=1,2,3,...` until you get an empty list:

```python
all_products = []
page = 1
while True:
    batch = client.catalog.products(category_id=42, page=page, per_page=200)
    if not batch:
        break
    all_products.extend(batch)
    page += 1
```

Per-page max is 200 (TN limit). Going higher silently caps.

## Common filters

- **By category**: `category_id=42` — find which `id` to use via `client.catalog.categories()`.
- **Published only**: `published=True` (skip drafts).
- **Modified since a date**: `updated_at_min="2026-01-01T00:00:00-03:00"` — ISO 8601 with timezone.
- **Slim payload**: `fields="id,name,handle"` — TN supports comma-separated field lists, reducing response size on big catalogs.

## Caveats

- These endpoints proxy live TN data — not cached. Don't loop calling them in tight loops; respect rate limits.
- The `q` text search hits TN's product name search — fuzzy, not exact.
- `categories()` returns ALL categories (auto-paginated server-side); fine for stores with hundreds of categories, slow for tens of thousands.
- A write can return 200 and still not change a field (TN ignores some values silently — see the field notes above). Re-read with `product()` when it matters.
