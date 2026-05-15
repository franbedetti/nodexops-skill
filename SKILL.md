---
name: nodexops
description: Use NodeXOps as a programmatic content engine for Tiendanube stores — upload product PDPs (Phase 1 ✅), content pages (Phase 2 🚧), and blog posts (Phase 3 🚧) with rich block-based layouts via API key auth. Use when an external project needs to bulk-create or update store content without manual UI work.
---

# NodeXOps Public API Skill

Use this skill when an external project (e.g., a migration tool or a content automation pipeline) needs to write to a Tiendanube store via NodeXOps — uploading product descriptions, content pages, or blog posts as rich, editable, block-based content.

## When to use

- Bulk-uploading PDPs to a TN store from a CSV / database / scraper output
- Generating PDPs from product data using AI and publishing them as drafts for client review
- Reusing a pre-approved "template" (block-group) across many products of a category
- Automating blog post or content page publication

## When NOT to use

- Creating products in Tiendanube — use the TN API directly. NodeXOps only writes the description.
- Touching stock, prices, variants, shipping. Out of scope.
- Designing layouts manually — that's the panel UI's job.

## Setup (1-time per consumer project)

1. Ask the NodeXOps admin for an API key for your target store. The key has a `nx_…` prefix and is shown only once at creation.
2. Save it as `NODEXOPS_API_KEY` in your project's `.env`. Note the store_id.
3. Copy `client.py` from this skill into your project (e.g., `nodex_client.py`).
4. `pip install requests` (only dependency).

```python
from nodex_client import NodexClient

client = NodexClient(
    base_url="https://v2.nodexops.com",
    api_key=os.environ["NODEXOPS_API_KEY"],
    store_id=12345,
)
```

## Index

- **Auth model & scopes**: `shared/auth.md`
- **Block catalog** (autogen, all available block types): `shared/blocks-catalog.md`
- **Full API reference** (autogen, all endpoints): `reference/api-reference.md`
- **NodexGen module** (product PDPs): `modules/nodexgen.md`
- **Catalog module** (TN passthrough — find products by category): `modules/catalog.md`
- **Block Groups** (cross-module reusable templates): `modules/block-groups.md`
- **NodexPage module** (content pages): `modules/nodexpage.md` 🚧 Phase 2
- **Blog module**: `modules/nodexblog.md` 🚧 Phase 3
- **Workflows** (recipes for common flows):
  - `workflows/upload-product-pdp.md`
  - `workflows/edit-pdps-by-category.md`
  - `workflows/use-block-group-as-template.md`
  - `workflows/draft-and-approve-flow.md`
  - `workflows/bulk-migration.md`
- **Examples** (working scripts in `examples/`)

## Phase status

| Module | Public API | Skill content |
|---|---|---|
| NodexGen (product PDPs) | ✅ Live | ✅ Complete |
| NodexPage (content pages) | 🚧 Building | Stub |
| Blog (posts) | 🚧 Building | Stub |

Block-groups (saved templates) are cross-module and are exposed alongside NodexGen today.
