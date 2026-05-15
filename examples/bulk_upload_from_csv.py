"""Bulk upload from a CSV. Each row → one product + simple PDP.

CSV columns expected: product_id, product_name, hero_image_url, short_description

Usage:
    NODEXOPS_API_KEY=nx_xxx STORE_ID=12345 python bulk_upload_from_csv.py products.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import NodexClient


BATCH_SIZE = 50


def row_to_item(row):
    return {
        "product_id": int(row["product_id"]),
        "product_name": row["product_name"],
        "blocks": [
            {
                "block_type": "text-image",
                "titulo": row["product_name"],
                "texto": row["short_description"],
                "media": row["hero_image_url"],
                "layout": "img-left",
            }
        ],
    }


def main(csv_path: str):
    client = NodexClient(
        base_url=os.environ.get("NODEXOPS_BASE_URL", "https://v2.nodexops.com"),
        api_key=os.environ["NODEXOPS_API_KEY"],
        store_id=int(os.environ["STORE_ID"]),
    )

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows. Uploading as drafts.")
    failed = []

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        items = [row_to_item(r) for r in batch]
        result = client.products.bulk_upload(items=items, as_draft=True)
        print(f"  Batch {i // BATCH_SIZE + 1}: {result['succeeded']}/{result['total']} ok")
        for r in result["results"]:
            if not r["ok"]:
                failed.append(r)

    print(f"\nDone. {len(failed)} failures:")
    for f in failed:
        print("  ", f)


if __name__ == "__main__":
    main(sys.argv[1])
