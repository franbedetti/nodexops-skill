# Workflow: upload + tag images for reuse

Subir imágenes a la galería de la tienda con un tag que las identifique, para después recuperarlas al armar PDPs. Convención: **un tag por imagen** (es como organizan el admin las tiendas que usan NodeXOps).

## Cómo elegir el tag

Una sola "dimensión" por imagen. Elegí UNA de estas convenciones según cómo penses reusarla:

| Convención | Ejemplo de tag | Cuándo conviene |
|---|---|---|
| **Por producto** | `c28`, `welly-3-en-1` | Imagen específica de un producto (ficha técnica, render, foto de detalle). Granular pero hay 1 tag por producto que la usa. |
| **Por categoría** | `cocheros`, `butacas` | Imagen genérica reusable en todos los productos de esa categoría (banner promocional, lifestyle de catálogo). 1 tag sirve a N productos. |
| **Por campaña** | `cyber-week`, `dia-del-niño` | Asset de una campaña puntual que se quita después de la fecha. |

No combines — la galería del admin muestra 1 chip por imagen y las búsquedas son por tag exacto. Si necesitás una imagen para dos cosas, subila dos veces con tags distintos.

## Recipe

```python
from nodex_client import NodexClient, NodexAPIError

client = NodexClient(...)

def upload_with_tag(file_path: str, tag: str) -> dict:
    """Sube file_path a la galería con el tag indicado.

    Crea el tag si no existe (la API hace soft-validation: tags
    desconocidos se droppean silenciosamente).
    """
    # 1. Asegurar que el tag existe en el vocabulario de la tienda
    try:
        client.tags.create(name=tag)
    except NodexAPIError as e:
        # 409 = ya existe → ok seguir
        if e.status not in (409, 400):
            raise

    # 2. Upload
    return client.media.upload(file_path=file_path, tags=[tag])


# Caso 1: imagen específica de un producto
result = upload_with_tag("/local/fotos/c28-medidas.png", "c28")
url = result["url"]

# Caso 2: banner reusable para toda una categoría
result = upload_with_tag("/local/banners/cybermonday.jpg", "cyber-week")
```

## Reusar la imagen al armar un block

Ya subida + tagueada, la recuperás con `client.media.search`:

```python
hits = client.media.search(tags=["c28"], limit=10)
for img in hits["items"]:
    print(img["original_name"], img["url"] if "url" in img else img["file_id"])

# En un block: usar img["url"] como block["media"]
blocks = [
    {
        "type": "text-image",
        "titulo": "Características",
        "texto": "...",
        "media": hits["items"][0]["url"],
    }
]
```

## Encontrar el handle de una categoría

Si vas a usar la convención "tag = handle de categoría":

```python
cats = client.catalog.categories()
for c in cats:
    print(c["name"], "→", c["permalink"])  # ej: "COCHECITOS → /cochecitos"

# Usar el slug del permalink (sin "/") como tag:
cat_tag = cats[0]["permalink"].strip("/")  # "cochecitos"
```

## Limpieza del vocabulario

Listar y eliminar tags que ya no usás:

```python
for t in client.tags.list():
    print(t["name"], "→", t.get("image_count", 0), "imágenes")

# Borrar uno (las imágenes que lo usen quedan sin tag pero no se borran):
client.tags.delete(tag_id=42)

# O reabsorberlo en otro tag:
client.tags.delete(tag_id=42, merge_into=99)
```

## Related

- `modules/nodexgen.md` — usar la URL en `block.media`
- `modules/catalog.md` — listar categorías para usar como tag
- `workflows/edit-pdps-by-category.md` — combinar con bulk PDP edit
