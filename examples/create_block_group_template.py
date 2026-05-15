"""Create a block-group (template) for later reuse across products.

Usage:
    NODEXOPS_API_KEY=nx_xxx STORE_ID=12345 python create_block_group_template.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import NodexClient


def main():
    client = NodexClient(
        base_url=os.environ.get("NODEXOPS_BASE_URL", "https://v2.nodexops.com"),
        api_key=os.environ["NODEXOPS_API_KEY"],
        store_id=int(os.environ["STORE_ID"]),
    )

    template_blocks = [
        {
            "block_type": "text-image",
            "titulo": "[NOMBRE PRODUCTO]",
            "texto": "[DESCRIPCION CORTA]",
            "media": "[URL IMAGEN HERO]",
            "layout": "img-left",
        },
        {
            "block_type": "icon-grid",
            "titulo": "Características",
            "texto": '[{"name":"Caract 1","image_url":""},{"name":"Caract 2","image_url":""}]',
            "icon_grid_cols": 4,
        },
        {
            "block_type": "accordion",
            "titulo": "Preguntas frecuentes",
            "texto": '[{"q":"[PREGUNTA 1]","a":"[RESPUESTA 1]"}]',
        },
    ]

    group = client.block_groups.create(
        name="Avanti Chochecitos (proposal)",
        tag="brand:avanti,category:chochecitos",
        blocks=template_blocks,
    )
    print(f"Created group {group['id']}. Open NodeXOps panel to review and approve.")


if __name__ == "__main__":
    main()
