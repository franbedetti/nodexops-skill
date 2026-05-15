# Workflow: Use a block-group as a per-brand/category template

Block-groups are saved arrays of blocks that act as starting templates. Typical use: "Avanti chochecitos" template — same structure (hero, features, FAQ), different content per product.

## Recipe

```python
from copy import deepcopy
from nodex_client import NodexClient

client = NodexClient(...)

# 1. List groups, pick the right template
groups = client.block_groups.list()
chochecitos = next(g for g in groups if g["name"] == "Avanti Chochecitos")

# 2. Fetch the full template
template = client.block_groups.get(chochecitos["id"])
template_blocks = template["blocks"]

# 3. For each product, customize and upload
for product in your_product_list:
    blocks = deepcopy(template_blocks)

    # Edit blocks in-place. Example: replace the hero title and image of the first block:
    blocks[0]["titulo"] = product["name"]
    blocks[0]["media"] = product["hero_image_url"]
    blocks[0]["texto"] = product["short_description"]

    # Replace FAQ answers if the second block is an accordion
    import json
    if blocks[1]["block_type"] == "accordion":
        faqs = [{"q": q, "a": a} for q, a in product.get("faqs", [])]
        blocks[1]["texto"] = json.dumps(faqs)

    client.products.upload(
        product_id=product["tn_id"],
        product_name=product["name"],
        blocks=blocks,
    )
```

## Creating a template programmatically

You can also CREATE a block-group via API. Useful when generating templates from AI proposals for client review:

```python
group = client.block_groups.create(
    name="Avanti Chochecitos (draft)",
    tag="proposal",
    blocks=[...],
)
print("Created group", group["id"], "— review in panel before using.")
```

The client can then open the NodeXOps panel, edit the group visually, and approve it. After approval, the group is ready to use in the loop above.
