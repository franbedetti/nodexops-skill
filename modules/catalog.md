# Catalog — Tiendanube passthrough

Read-only proxies into the Tiendanube API for **product / category / store discovery**. Use these to figure out *which* products to edit; use `modules/nodexgen.md` to actually write descriptions.

All endpoints require the `products:read` scope.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v2/stores/{store_id}/products` | List TN products. Filters: `q`, `category_id`, `published`, `created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`, `page`, `per_page`, `fields` |
| GET | `/api/v2/stores/{store_id}/products/{product_id}` | Full product payload (incl. variants, images, attributes) |
| GET | `/api/v2/stores/{store_id}/categories` | Flat list of categories: `[{id, name, parent_id, permalink}, ...]` |
| GET | `/api/v2/stores/{store_id}/store-info` | TN store info: name, domain, currency, language, etc. |

These mirror the Tiendanube API 1:1 (no transformation) except `/categories`, which is flattened from TN's nested name/handle dicts into the simpler shape above.

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
```

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
