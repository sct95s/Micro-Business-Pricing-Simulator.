from __future__ import annotations

import json
import sqlite3
from typing import Dict

import pandas as pd

DEFAULT_PRODUCTS = [
    {"product_name": "Cold Brew Coffee Pack", "unit_cost": 4.25, "fixed_cost": 700.0, "base_price": 9.50, "base_demand": 230.0, "elasticity": 1.2, "competitor_min": 8.50, "competitor_max": 11.00},
    {"product_name": "Handmade Candle Set", "unit_cost": 7.40, "fixed_cost": 950.0, "base_price": 18.00, "base_demand": 150.0, "elasticity": 1.0, "competitor_min": 16.00, "competitor_max": 22.00},
    {"product_name": "Student Tutoring Session", "unit_cost": 12.00, "fixed_cost": 600.0, "base_price": 30.00, "base_demand": 90.0, "elasticity": 1.5, "competitor_min": 25.00, "competitor_max": 35.00},
    {"product_name": "Campus Merch Tote Bag", "unit_cost": 6.80, "fixed_cost": 800.0, "base_price": 16.50, "base_demand": 180.0, "elasticity": 1.3, "competitor_min": 14.00, "competitor_max": 19.00},
]


def init_db(db_path: str = "pricing_simulator.db") -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT UNIQUE,
                unit_cost REAL,
                fixed_cost REAL,
                base_price REAL,
                base_demand REAL,
                elasticity REAL,
                competitor_min REAL,
                competitor_max REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS simulation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_label TEXT,
                product_name TEXT,
                summary_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def seed_default_catalog_if_empty(db_path: str = "pricing_simulator.db") -> None:
    current = get_catalog_df(db_path)
    if not current.empty:
        return
    with sqlite3.connect(db_path) as conn:
        for product in DEFAULT_PRODUCTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO product_catalog (
                    product_name, unit_cost, fixed_cost, base_price, base_demand, elasticity, competitor_min, competitor_max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product["product_name"],
                    product["unit_cost"],
                    product["fixed_cost"],
                    product["base_price"],
                    product["base_demand"],
                    product["elasticity"],
                    product["competitor_min"],
                    product["competitor_max"],
                ),
            )
        conn.commit()


def get_catalog_df(db_path: str = "pricing_simulator.db") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT product_name, unit_cost, fixed_cost, base_price, base_demand, elasticity, competitor_min, competitor_max FROM product_catalog ORDER BY product_name",
            conn,
        )


def load_catalog_from_csv(db_path: str, df: pd.DataFrame) -> None:
    required = {"product_name", "unit_cost", "fixed_cost", "base_price", "base_demand", "elasticity", "competitor_min", "competitor_max"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    with sqlite3.connect(db_path) as conn:
        for _, row in df.iterrows():
            conn.execute(
                """
                INSERT INTO product_catalog (
                    product_name, unit_cost, fixed_cost, base_price, base_demand, elasticity, competitor_min, competitor_max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_name) DO UPDATE SET
                    unit_cost=excluded.unit_cost,
                    fixed_cost=excluded.fixed_cost,
                    base_price=excluded.base_price,
                    base_demand=excluded.base_demand,
                    elasticity=excluded.elasticity,
                    competitor_min=excluded.competitor_min,
                    competitor_max=excluded.competitor_max
                """,
                (
                    row["product_name"],
                    float(row["unit_cost"]),
                    float(row["fixed_cost"]),
                    float(row["base_price"]),
                    float(row["base_demand"]),
                    float(row["elasticity"]),
                    float(row["competitor_min"]),
                    float(row["competitor_max"]),
                ),
            )
        conn.commit()


def save_simulation_run(db_path: str, scenario_label: str, product_name: str, summary: Dict) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO simulation_runs (scenario_label, product_name, summary_json) VALUES (?, ?, ?)",
            (scenario_label, product_name, json.dumps(summary)),
        )
        conn.commit()


def get_run_history_df(db_path: str = "pricing_simulator.db") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT scenario_label, product_name, summary_json, created_at FROM simulation_runs ORDER BY created_at DESC",
            conn,
        )
    if df.empty:
        return df
    parsed = df["summary_json"].apply(json.loads)
    return pd.concat([df.drop(columns=["summary_json"]), pd.json_normalize(parsed)], axis=1)
