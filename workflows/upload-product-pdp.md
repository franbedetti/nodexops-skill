# Workflow: Upload a single product PDP

Use this when you have ONE product whose description you want to write or update.

## Prerequisites

- API key with `nodexgen:write` scope
- The product already exists in Tiendanube (NodeXOps does not create products)
- `client.py` copied to your project

## Recipe

```python
from nodex_client import NodexClient

client = NodexClient(
    base_url="https://v2.nodexops.com",
    api_key=os.environ["NODEXOPS_API_KEY"],
    store_id=YOUR_STORE_ID,
)

result = client.products.upload(
    product_id=12345,
    product_name="Coche de paseo Avanti Lite",
    blocks=[
        {
            "block_type": "text-image",
            "titulo": "Diseñado para tu día a día",
            "texto": "Plegado en un click. **Liviano** y resistente.",
            "media": "https://imagekit.io/nodexops/avanti/lite-hero.jpg",
            "layout": "img-left",
        },
        {
            "block_type": "icon-grid",
            "titulo": "Características",
            "texto": '[{"name":"Plegable","image_url":"..."}, {"name":"Liviano","image_url":"..."}]',
            "icon_grid_cols": 4,
        },
        {
            "block_type": "accordion",
            "titulo": "Preguntas frecuentes",
            "texto": '[{"q":"Cómo se pliega?","a":"Pulsando el botón..."}]',
        },
    ],
)
print("Pushed to TN. Log:", result["log_id"])
```

## Notes

- Block schemas live in `shared/blocks-catalog.md` (autogen).
- For accordion / icon-grid / gallery / columns / button blocks, `texto` is a JSON string (not an object).
- Markdown supported in plain text fields: `**bold**`, `__underline__`, `_italic_`, `{+ size +}`.
- External image URLs (non-ImageKit) are auto-uploaded to ImageKit and the URL replaced — no extra step.
- The PDP becomes editable in the panel immediately after upload.
