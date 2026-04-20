from pathlib import Path

import pandas as pd

from database import DEFAULT_PRODUCTS, init_db, seed_default_catalog_if_empty

DB_PATH = "pricing_simulator.db"
CSV_PATH = Path("sample_products.csv")


def main() -> None:
    init_db(DB_PATH)
    seed_default_catalog_if_empty(DB_PATH)
    pd.DataFrame(DEFAULT_PRODUCTS).to_csv(CSV_PATH, index=False)
    print(f"Seeded database: {DB_PATH}")
    print(f"Wrote sample CSV: {CSV_PATH.resolve()}")


if __name__ == "__main__":
    main()
