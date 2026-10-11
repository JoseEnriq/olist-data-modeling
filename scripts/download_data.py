"""Download the Olist Brazilian E-Commerce dataset into data/raw/.

Kaggle serves this public dataset through a direct link that does not
require an account. If that ever changes, download the ZIP manually from
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce and extract
the CSVs into data/raw/.

Usage:
    python scripts/download_data.py [--force]
"""

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

EXPECTED_FILES = {
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="overwrite files already in data/raw/")
    args = parser.parse_args()

    existing = {p.name for p in RAW_DIR.glob("*.csv")}
    if EXPECTED_FILES <= existing and not args.force:
        print(f"All {len(EXPECTED_FILES)} files already in {RAW_DIR}. Use --force to download again.")
        return 0

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "olist.zip"
        print(f"Downloading {URL} ...")
        with urllib.request.urlopen(URL) as response, open(zip_path, "wb") as out:
            shutil.copyfileobj(response, out)

        with zipfile.ZipFile(zip_path) as archive:
            names = set(archive.namelist())
            # Refuse anything that is not exactly the dataset we expect.
            if names != EXPECTED_FILES:
                print(f"Unexpected archive contents: {sorted(names ^ EXPECTED_FILES)}", file=sys.stderr)
                return 1
            for name in sorted(names):
                target = RAW_DIR / name
                if target.exists() and not args.force:
                    print(f"skip   {name} (already exists)")
                    continue
                with archive.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                print(f"saved  {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
