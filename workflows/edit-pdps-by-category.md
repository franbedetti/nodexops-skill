# Workflow: edit PDPs by category

Find all products in a TN category, then rewrite their descriptions in bulk.

## Recipe

```python
from nodex_client import NodexClient

client = NodexClient(...)

# 1. Find the category id
cats = client.catalog.categories()
target = next(c for c in cats if c["name"].lower() == "cocheros")
print(f"Editing category {target['id']} — {target['name']}")

# 2. Pull every product in that category (handle pagination)
products = []
page = 1
while True:
    batch = client.catalog.products(
        category_id=target["id"],
        published=True,
        per_page=200,
        page=page,
        fields="id,name,handle",  # slim payload
    )
    if not batch:
        break
    products.extend(batch)
    page += 1

print(f"Found {len(products)} products to edit")

# 3. Build a description for each. Use a saved template (block-group)
#    so the layout is consistent across the category.
template = client.block_groups.get(group_id=99)  # "Cocheros — layout estándar"

def blocks_for(product):
    # Customize the template per product (insert name, swap an image, etc.)
    blocks = template["blocks"]
    # ... your per-product tweaks here ...
    return blocks

# 4. Bulk upload as DRAFTS for client review before going live
BATCH = 50
for i in range(0, len(products), BATCH):
    chunk = products[i:i + BATCH]
    items = [
        {
            "product_id": p["id"],
            "product_name": p["name"],
            "blocks": blocks_for(p),
        }
        for p in chunk
    ]
    resp = client.products.bulk_upload(items=items, as_draft=True)
    print(f"  batch {i // BATCH + 1}: {resp['success_count']}/{len(chunk)} OK")
```

## Pattern notes

- **Draft first, publish later**: `as_draft=True` lets your client review in the NodeXOps admin before going to the storefront. Once approved, re-run with `as_draft=False`.
- **Use block-groups for consistency**: pulling a pre-approved template avoids drift across hundreds of products. See `modules/block-groups.md`.
- **Per-product variation**: keep the template generic, do tweaks in `blocks_for(product)` — names, prices, links, images.
- **Filter further**: combine `category_id` with `updated_at_min` to only re-edit products updated since a date, or `q="palabra"` to narrow within the category.

## Related

- `modules/catalog.md` — passthrough endpoints reference
- `modules/nodexgen.md` — PDP block schema + writing
- `modules/block-groups.md` — saved templates
- `workflows/draft-and-approve-flow.md` — how to manage the draft lifecycle
