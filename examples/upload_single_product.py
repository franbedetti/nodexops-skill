"""Single-product PDP upload. Usage:
    NODEXOPS_API_KEY=nx_xxx STORE_ID=12345 PRODUCT_ID=999 python upload_single_product.py
"""
import os
import sys

# Adjust this import to wherever you copied client.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import NodexClient


def main():
    client = NodexClient(
        base_url=os.environ.get("NODEXOPS_BASE_URL", "https://v2.nodexops.com"),
        api_key=os.environ["NODEXOPS_API_KEY"],
        store_id=int(os.environ["STORE_ID"]),
    )

    blocks = [
        {
            "block_type": "text-image",
            "titulo": "Diseñado para vos",
            "texto": "**Calidad** premium en cada detalle.",
            "media": "https://ik.imagekit.io/nodexops/example/hero.jpg",
            "layout": "img-left",
        },
        {
            "block_type": "highlight",
            "titulo": "Envío gratis",
            "texto": "En todo el país, sin mínimo de compra.",
        },
    ]

    result = client.products.upload(
        product_id=int(os.environ["PRODUCT_ID"]),
        product_name="Demo Product",
        blocks=blocks,
        as_draft=os.environ.get("AS_DRAFT", "false").lower() == "true",
    )
    print(result)


if __name__ == "__main__":
    main()
