# Block Groups — Reusable templates

Saved arrays of blocks per store. Use as parameterizable templates across many products of the same brand or category. Cross-module: usable from NodexGen (PDPs), and in the future from NodexPage and Blog when those modules ship.

## Endpoints

All under `/api/v2/stores/{store_id}/nodexgen/block-groups` for now (will be aliased under a cross-module path in a future release).

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/block-groups` | `block-groups:read` | List groups (lightweight: no full blocks payload, just `blocks_count`) |
| GET | `/block-groups/{group_id}` | `block-groups:read` | Get one group with full blocks (skill-shape) |
| POST | `/block-groups` | `block-groups:write` | Create new group |
| PUT | `/block-groups/{group_id}` | `block-groups:write` | Update name/tag/blocks |
| DELETE | `/block-groups/{group_id}` | `block-groups:write` | Delete |

## Body shape

POST/PUT accept the same skill-shape as `/descriptions` blocks (snake_case fields, `texto` as JSON-string for `columns` / `group` children):

```json
{
  "name": "Avanti Chochecitos",
  "tag": "brand:avanti,category:chochecitos",
  "blocks": [
    {"block_type": "text-image", "titulo": "...", "texto": "...", "media": "...", "img_size": "large"},
    {
      "block_type": "columns",
      "titulo": "...",
      "texto": "[{\"block_type\":\"text-image\",\"titulo\":\"Left\"},{\"block_type\":\"text-image\",\"titulo\":\"Right\"}]",
      "columns_cols": 2,
      "columns_layout": "img-top"
    }
  ]
}
```

## Response shape

GET returns the **same skill-shape** that POST/PUT accept — round-trip friendly. Internally NodeXOps stores the panel-shape (camelCase + native `columnsChildren`/`groupChildren` arrays) so the panel UI can read what was written via API; the converter at the public boundary translates between shapes in both directions.

POST/PUT/GET all return:
```json
{
  "id": 42,
  "name": "Avanti Chochecitos",
  "tag": "brand:avanti,category:chochecitos",
  "blocks": [/* skill-shape blocks */],
  "created_at": "2026-04-25T19:31:14.895096Z"
}
```

GET `/block-groups` (the list) returns the lightweight variant (no `blocks` field, just `blocks_count`):
```json
[{"id": 42, "name": "Avanti Chochecitos", "tag": "...", "blocks_count": 6, "created_at": "..."}]
```

## Workflow

See `workflows/use-block-group-as-template.md` for the canonical pattern: list groups → fetch one → deepcopy → customize per product → POST `/descriptions/{product_id}`.

## Python client

```python
client.block_groups.list()                         # → [{id, name, tag, blocks_count, created_at}]
client.block_groups.get(group_id=42)               # → full skill-shape
client.block_groups.create(name="...", blocks=[...], tag="...")
client.block_groups.update(group_id=42, name="...", blocks=[...], tag="...")
client.block_groups.delete(group_id=42)
```

## Notes

- The skill-shape ↔ panel-shape converter handles columns and group blocks transparently. You always work in skill-shape via the public API.
- Block-groups created in the panel UI are also readable via the public API GET (the same converter normalizes both directions).
- Editing a group does NOT update products that previously used it as a template — the template is a starting point, not a live binding.
