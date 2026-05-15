# Workflow: Bulk migration (hundreds/thousands of products)

When migrating an entire catalog, prefer `bulk_upload` over a Python `for` loop of single calls.

## Why bulk

- Fewer HTTP round-trips → lower total latency
- Per-item error tracking in one structured response
- Avoids tripping per-key rate limits (one bulk = one request, even with 50 items)

## Recipe

```python
from nodex_client import NodexClient, NodexAPIError

client = NodexClient(...)

BATCH_SIZE = 50  # API max per request

def to_item(product):
    return {
        "product_id": product["tn_id"],
        "product_name": product["name"],
        "template_id": "default",
        "blocks": designed_blocks_for(product),
    }

all_products = load_your_catalog()
failed = []

for i in range(0, len(all_products), BATCH_SIZE):
    batch = all_products[i:i + BATCH_SIZE]
    items = [to_item(p) for p in batch]

    try:
        result = client.products.bulk_upload(items=items, as_draft=True)
    except NodexAPIError as e:
        # Whole batch failed (auth/rate limit/etc) — record and continue
        failed.append({"batch_start": i, "error": str(e)})
        continue

    # Per-item failures are inside the response
    for r in result["results"]:
        if not r["ok"]:
            failed.append({"product_id": r["product_id"], "error": r["error"], "code": r["code"]})

    print(f"Batch {i}: {result['succeeded']}/{result['total']} succeeded")

print(f"\nDone. {len(failed)} items failed:")
for f in failed:
    print(" ", f)
```

## Best practices

- **Always start with `as_draft=True`** for the first batch — sample in panel, sanity-check rendering, then re-run with `as_draft=False` for production.
- **Cap your concurrent migrations**: even with bulk, the underlying TN API has its own rate limits. Sequential bulks of 50 is usually safer than parallel.
- **Use `stop_on_error=True`** if you want to halt on the first failure (e.g., wrong template_id) and inspect; default is to continue past failures.
- **Idempotent**: re-running a bulk with the same product_ids OVERWRITES — safe to retry on partial failures.
- **Save the response**: each `result["log_id"]` (or `draft_id`) is your audit trail in NodexOps.
