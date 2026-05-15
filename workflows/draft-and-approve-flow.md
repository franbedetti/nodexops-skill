# Workflow: Draft + manual approval flow

Use when the client wants to **review every PDP before it goes live in TN**.

## How it works

`client.products.upload(..., as_draft=True)`:
- Writes to `NodexgenDraft` (not `NodexgenLog`)
- Does NOT push HTML to Tiendanube
- The next time the client opens that product in the NodeXOps panel, the draft loads automatically — fully editable
- The client clicks "Publicar" in the panel to push to TN

## Recipe

```python
for product in batch:
    result = client.products.upload(
        product_id=product["tn_id"],
        product_name=product["name"],
        blocks=designed_blocks_for(product),
        as_draft=True,  # ← key flag
    )
    assert result["tn_pushed"] is False
    print(f"Draft ready for {product['name']} (draft_id={result['draft_id']})")

# Notify the client
print("All drafts uploaded. Open the NodeXOps panel to review and publish.")
```

## Caveats

- Only one draft per (store, product) — uploading again overwrites the previous draft
- Drafts have no plan-based block-cap (the cap applies on publish, in the panel)
- A draft has no expiry; it lives until the client publishes or deletes it
- If a product already has a published PDP and you upload a draft, the live TN description is unchanged until the client publishes the draft
