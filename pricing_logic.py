from __future__ import annotations

import math
from typing import List

import numpy as np
import pandas as pd


def estimate_demand(price: float, base_price: float, base_demand: float, elasticity: float, marketing_boost_pct: float = 0.0) -> float:
    pct_change = (price - base_price) / base_price
    demand_factor = 1 - (elasticity * pct_change)
    demand_factor = max(0.05, demand_factor)
    boosted_demand = base_demand * demand_factor * (1 + marketing_boost_pct / 100)
    return max(0, boosted_demand)


def classify_competitor_position(price: float, competitor_min: float, competitor_max: float) -> str:
    if price < competitor_min:
        return "Below market"
    if price > competitor_max:
        return "Above market"
    return "Within market"


def simulate_pricing_table(
    product_name: str,
    unit_cost: float,
    fixed_cost: float,
    base_price: float,
    base_demand: float,
    elasticity: float,
    competitor_min: float,
    competitor_max: float,
    sim_min_price: float,
    sim_max_price: float,
    price_step: float,
    marketing_boost_pct: float = 0.0,
) -> pd.DataFrame:
    prices = np.arange(sim_min_price, sim_max_price + price_step / 2, price_step)
    rows = []
    for price in prices:
        price = round(float(price), 2)
        demand = estimate_demand(price, base_price, base_demand, elasticity, marketing_boost_pct)
        revenue = price * demand
        gross_profit = (price - unit_cost) * demand
        net_profit = gross_profit - fixed_cost
        margin_pct = (net_profit / revenue * 100) if revenue > 0 else 0
        contribution_margin = price - unit_cost
        breakeven_units = fixed_cost / contribution_margin if contribution_margin > 0 else math.inf
        rows.append(
            {
                "product_name": product_name,
                "price": price,
                "estimated_demand": round(demand, 2),
                "revenue": round(revenue, 2),
                "gross_profit": round(gross_profit, 2),
                "net_profit": round(net_profit, 2),
                "profit_margin_pct": round(margin_pct, 2),
                "breakeven_units": round(breakeven_units, 2) if math.isfinite(breakeven_units) else math.inf,
                "competitor_position": classify_competitor_position(price, competitor_min, competitor_max),
            }
        )
    return pd.DataFrame(rows)


def choose_recommended_price(simulation_df: pd.DataFrame) -> pd.Series:
    df = simulation_df.copy()
    df["profit_norm"] = (df["net_profit"] - df["net_profit"].min()) / ((df["net_profit"].max() - df["net_profit"].min()) or 1)
    df["margin_norm"] = (df["profit_margin_pct"] - df["profit_margin_pct"].min()) / ((df["profit_margin_pct"].max() - df["profit_margin_pct"].min()) or 1)
    df["demand_norm"] = (df["estimated_demand"] - df["estimated_demand"].min()) / ((df["estimated_demand"].max() - df["estimated_demand"].min()) or 1)
    df["market_fit"] = df["competitor_position"].map({"Within market": 1.0, "Below market": 0.8, "Above market": 0.65})
    df["score"] = df["profit_norm"] * 0.45 + df["margin_norm"] * 0.25 + df["demand_norm"] * 0.15 + df["market_fit"] * 0.15
    return df.loc[df["score"].idxmax()]


def generate_recommendations(
    simulation_df: pd.DataFrame,
    product_name: str,
    unit_cost: float,
    fixed_cost: float,
    base_price: float,
    competitor_min: float,
    competitor_max: float,
) -> List[str]:
    best_profit = simulation_df.loc[simulation_df["net_profit"].idxmax()]
    best_revenue = simulation_df.loc[simulation_df["revenue"].idxmax()]
    recommended = choose_recommended_price(simulation_df)
    low_margin = simulation_df[simulation_df["profit_margin_pct"] < 10]
    premium_options = simulation_df[simulation_df["competitor_position"] == "Above market"]
    market_options = simulation_df[simulation_df["competitor_position"] == "Within market"]

    recommendations = [
        f"For {product_name}, the best balanced recommendation is ${recommended['price']:.2f}, which is expected to generate ${recommended['net_profit']:.2f} in monthly net profit with demand around {recommended['estimated_demand']:.0f} units.",
        f"If your priority is maximum monthly profit, the top scenario is ${best_profit['price']:.2f}. If your priority is maximum sales volume or market share, consider the lower-price range where demand stays stronger.",
        f"The strongest revenue scenario occurs at ${best_revenue['price']:.2f}, but revenue alone should not drive pricing decisions if margins or break-even volume become risky.",
    ]

    if not market_options.empty:
        best_market = market_options.loc[market_options["net_profit"].idxmax()]
        recommendations.append(
            f"The best option within the competitor price band is ${best_market['price']:.2f}, which can help you stay competitive without racing to the bottom."
        )

    if not premium_options.empty:
        top_premium = premium_options.loc[premium_options["net_profit"].idxmax()]
        recommendations.append(
            f"A premium pricing option above the market range exists at ${top_premium['price']:.2f}. This is worth testing if your product has brand strength, better quality, or a differentiated experience."
        )

    if len(low_margin) > 0:
        recommendations.append(
            "Several low-price scenarios produce thin margins. Avoid pricing mainly for volume unless it supports a broader strategy such as customer acquisition, bundling, or upselling."
        )

    if recommended["breakeven_units"] > recommended["estimated_demand"]:
        recommendations.append(
            "The current recommendation still sits below the monthly break-even demand threshold. Consider cutting fixed costs, increasing demand through marketing, or improving unit economics before scaling."
        )
    else:
        recommendations.append(
            "At the recommended price, estimated demand stays above break-even volume, which lowers pricing risk and improves sustainability."
        )

    if recommended["price"] < unit_cost:
        recommendations.append(
            "Any price below unit cost creates a structural loss. Use deep discounts only as short-term promotions, not as a default strategy."
        )

    return recommendations
