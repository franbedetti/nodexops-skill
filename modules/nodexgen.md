# NodexGen — Product description PDPs

Module that writes Tiendanube product descriptions as block-based, editable layouts.

## Endpoints

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/api/v2/stores/{store_id}/nodexgen/descriptions` | `nodexgen:read` | List all PDP logs for the store (recent first) |
| GET | `/api/v2/stores/{store_id}/nodexgen/descriptions/{product_id}` | `nodexgen:read` | Get the latest saved blocks for a product (returns nested + flat) |
| POST | `/api/v2/stores/{store_id}/nodexgen/descriptions/{product_id}` | `nodexgen:write` | Create/replace PDP for a product |
| PUT | `/api/v2/stores/{store_id}/nodexgen/descriptions/{product_id}` | `nodexgen:write` | Update PDP (logs as `api_update`) |
| POST | `/api/v2/stores/{store_id}/nodexgen/descriptions/bulk` | `nodexgen:write` | Bulk upload (max 50 items) |
| POST | `/api/v2/stores/{store_id}/nodexgen/media/upload` | `nodexgen:write` | Upload local image or video to ImageKit (returns URL ready for `block.media`) |
| GET | `/api/v2/stores/{store_id}/nodexgen/media/library?file_type=&name=&limit=` | `nodexgen:read` | List ALL files in the store's ImageKit library (with or without metadata) |
| DELETE | `/api/v2/stores/{store_id}/nodexgen/media/{file_id}` | `nodexgen:write` | Delete a file from ImageKit (verifies filePath belongs to this store) |
| GET | `/api/v2/stores/{store_id}/nodexgen/tags` | `nodexgen:read` | List tags with image counts |
| POST | `/api/v2/stores/{store_id}/nodexgen/tags` | `nodexgen:write` | Create new tag |
| PUT | `/api/v2/stores/{store_id}/nodexgen/tags/{tag_id}` | `nodexgen:write` | Rename tag (bulk-updates images) |
| DELETE | `/api/v2/stores/{store_id}/nodexgen/tags/{tag_id}?merge_into={id}` | `nodexgen:write` | Delete or merge into another tag |
| GET | `/api/v2/stores/{store_id}/nodexgen/media?tags=&match=` | `nodexgen:read` | Search image_metadata rows by tags (only files with metadata) |

Block-groups (cross-module template store) are documented under `modules/block-groups.md` and exposed via `/api/v2/stores/{store_id}/nodexgen/block-groups`.

## Body shape (POST/PUT)

```json
{
  "product_name": "Coche Lite",
  "template_id": "default",
  "descripcion_corta": "optional short text",
  "blocks": [
    {"block_type": "text-image", "titulo": "...", "texto": "...", "media": "...", "content_layout": "img-right"},
    {"block_type": "text-image", "titulo": "Hero!", "subtitulo": "Subtitle", "media": "...", "cta_text": "Buy", "cta_url": "...", "content_layout": "hero-classic"}
  ],
  "as_draft": false
}
```

`as_draft=true` writes to `NodexgenDraft` only (no TN push). See `workflows/draft-and-approve-flow.md`.

## `content_layout` — the 12-position layout matrix (v0.20.0+)

The `text-image` block (the unified "Contenido" block) accepts a `content_layout` field with 12 possible values that drive how text and media are arranged. This **replaces** the legacy `block_type` sub-types (`text-only`, `media-only`, `highlight`) and the legacy `layout` field (`auto`, `img-left`, `img-right`).

Legacy data (drafts saved before v0.20.0 with old `block_type`/`layout`) keeps rendering correctly via backwards-compat translator. New API uploads should use `content_layout`.

| `content_layout` | Renders | Use case |
|---|---|---|
| `auto` | text + image side by side, alternating left/right by index | default — long product PDPs |
| `img-right` | text-left · image-right | classic content block |
| `img-left` | image-left · text-right | reversed |
| `img-top` | image stacked above text | vertical |
| `img-bottom` | text stacked above image | vertical |
| `text-only` | text full-width, no media | replaces legacy `block_type='text-only'` |
| `media-only` | image full-width, no text | replaces legacy `block_type='media-only'` |
| `highlight` | card with title + body + CTA on accent background | replaces legacy `block_type='highlight'` |
| `text-on-image` | image as bg, text overlay (in-block width) | subtle overlay |
| `hero-classic` | full-bleed banner, ~55vh, centered text + dark overlay + CTA | landing-page hero |
| `hero-compact` | full-bleed, ~40vh, left-aligned text + horizontal gradient | shorter hero |
| `hero-bottom` | full-bleed, ~65vh, text/CTA at bottom + bottom gradient | cinematic hero |

The 3 HEROs are always full-bleed (rompen el ancho del contenedor del producto). Title renders as `<h1>` (vs `<h3>` for the other layouts).

Fields used per layout:

| Field | Used by |
|---|---|
| `titulo` | all except `text-only`, `media-only` |
| `texto` | all except `media-only` |
| `subtitulo` | all except `text-only`, `media-only` (forced below in HEROs) |
| `media` | all except `text-only` |
| `cta_text` / `cta_url` / `cta_target` | `highlight`, `hero-classic`, `hero-compact`, `hero-bottom` |

Switching `content_layout` does NOT delete fields — data persists, just hidden from the layout that doesn't render it.

## GET response — draft fallback + `source`

`GET /descriptions/{product_id}` reads with this priority (matches the panel editor's load order):

1. **Draft** in `NodexgenDraft` (if it exists) → returned with `"source": "draft"`
2. **Latest log** in `NodexgenLog` (most recent published version) → returned with `"source": "log"`
3. Neither → `{"ok": true, "found": false}`

Response when found:
```json
{
  "ok": true,
  "found": true,
  "source": "draft",            // or "log"
  "product_id": 999,
  "template_id": "default",
  "blocks": [/* skill-shape, snake_case + texto JSON children */],
  "input_data": {/* raw flat — kept for backward compat */}
}
```

Use the `source` field to know whether you're editing a draft or replacing a published version. The Python client returns the dict as-is.

## Block types

See `shared/blocks-catalog.md` (autogenerated from the codebase).

## Text formatting in `texto` / `titulo` / `subtitulo` / `descripcion_corta`

Aplica a TODOS los block_types con un campo de texto. Los markers se resuelven en server-side render — no inyectes HTML directo, no funciona y/o queda escapeado.

### Tamaño global del bloque (style)

```json
{"style": {"title_size": "1.5em", "text_size": "0.9em"}}
```

Cualquier unidad CSS (`px`, `em`, `%`, `calc(...)`). Sin estos campos, hereda del tema.

### Tamaño inline puntual (markers de pseudo-markdown)

| Marker | Tamaño |
|---|---|
| `{+texto+}` | 1.2em |
| `{++texto++}` | 1.4em |
| `{+++texto+++}` | 1.6em |
| `{-texto-}` | 0.85em |
| `{--texto--}` | 0.7em |
| `{---texto---}` | 0.55em |

Combinables: `**{+OFERTA+}**` → negrita + 1.2em.

### Modo párrafo vs lista (`textMode`)

Campo top-level del block (camelCase — flatten interno lo convierte a `text_mode`):

| `textMode` | Render |
|---|---|
| `"paragraph"` | `<p>{texto con \n→<br>}</p>` |
| `"list"` | `<ul><li>línea1</li><li>línea2</li>...</ul>` (split por `\n`) |
| omitido / `null` | Auto-detect: 1 línea = `<p>`, varias = `<ul>`. **Legacy — sé explícito en clientes nuevos.** |

### Inline format (markdown-like)

| Marker | HTML |
|---|---|
| `**texto**` | `<strong>` |
| `__texto__` | `<u>` |
| `_texto_` | `<em>` |

### Multi-párrafo en `descripcion_corta` (v0.22.3+)

```json
{"descripcion_corta": "Párrafo 1.\n\nPárrafo 2 separado por línea en blanco."}
```

- `\n\n` → párrafo nuevo (`<p class="pd-intro">` separado).
- `\n` solo → salto suave (`<br>`).
- Si la tienda tiene `short_desc_enabled=true`, todos los `<p class="pd-intro">` suben al área del subtítulo del producto via `short-desc-pdp.js` (v0.22.5+ itera todos, no solo el primero).

**Backwards compat**: payloads sin `\n\n` rinden idéntico al pre-v0.22.3 (un solo `<p>`).

### Sanitización

Pipeline: `esc(input)` → `_convert_markdown(escaped)` → emit. No hay forma de inyectar HTML arbitrario. Los markers procesan caracteres que `esc()` no toca (`*`, `_`, `{`, `+`, `-`, `}`).

## Limits

- Per-PDP block cap: enforced ONLY in the panel UI (10 for Starter, 20 for Pro). The public API does NOT validate block count — consumers are responsible for sane limits. Future versions may enforce server-side.
- Bulk: max 50 items per request
- Rate limit: 120 req/min per API key (default)

## Media uploads

`POST /media/upload` accepts a base64 data URI or any pre-encoded source. Auto-detects image vs video from MIME, mirrors the panel upload behavior:

- **Image**: stored at `/store-{store_id}/imagenes/img_{uid}.webp` (or `.png` if `keep_png=true`), WebP-converted at q-80 w-1400.
- **Video**: stored at `/store-{store_id}/videos/vid_{uid}.{ext}`, max 10MB enforced server-side.

Optional `tags` (list[str]), `note` (str), and `original_name` (str) are persisted to the `image_metadata` table and returned in the response. The returned `url` is ready to drop into `block.media` for any subsequent description/group upload.

The Python client wraps this:

```python
result = client.media.upload(file_path="hero.jpg", tags=["chochecitos"])
print(result["url"])  # → use this in block.media
```

## Tag curation

Tags are a curated vocabulary per store. The `image_tags` table holds the canonical list; `image_metadata.tags` references them by name.

- **Upload validation**: `POST /media/upload` accepts any `tags` list, but only persists tags that already exist in `image_tags`. Unknown tags come back in `warnings.unknown_tags`. To avoid the warning, create the tag first with `POST /tags` then re-upload (or update metadata separately).
- **Rename / delete propagate**: a `PUT /tags/{id}` updates every image's `image_metadata.tags` JSONB array. A `DELETE /tags/{id}` removes it from every image. `DELETE ?merge_into={other_id}` replaces with another tag (deduped).
- **Search**: `GET /media?tags=t1,t2&match=all` returns images that have BOTH t1 and t2. `match=any` returns images with EITHER. Limit max 500.

Python client:
```python
client.tags.list()                              # → [{id, name, image_count}]
client.tags.create(name="chochecitos")
client.tags.rename(tag_id=5, new_name="cuerpo-paseo")
client.tags.delete(tag_id=5)                    # plain delete
client.tags.delete(tag_id=5, merge_into=12)     # absorb into tag 12
client.media.search(tags=["chochecitos", "hero"], match="all")
```

## Behavior

- POST and PUT always push to Tiendanube unless `as_draft=true`
- External image URLs in `media` fields are auto-uploaded to ImageKit
- Template `default` always exists; other templates require admin setup
- The latest entry per product (in `NodexgenLog`) is what GET returns and what the panel editor loads
