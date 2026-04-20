import pandas as pd
import streamlit as st

from database import (
    get_catalog_df,
    get_run_history_df,
    init_db,
    load_catalog_from_csv,
    save_simulation_run,
    seed_default_catalog_if_empty,
)
from pricing_logic import choose_recommended_price, generate_recommendations, simulate_pricing_table

st.set_page_config(page_title="Micro-Business Pricing Simulator", page_icon="💸", layout="wide")

DB_PATH = "pricing_simulator.db"
init_db(DB_PATH)
seed_default_catalog_if_empty(DB_PATH)

st.title("💸 Micro-Business Pricing Simulator")
st.caption(
    "Test pricing strategies for products or services and compare revenue, profit, margin, demand, "
    "and break-even outcomes across multiple scenarios."
)

with st.sidebar:
    st.header("Data Source")
    source_mode = st.radio("Choose a starting point", ["Use product catalog", "Manual input", "Upload CSV"], index=0)

catalog_df = get_catalog_df(DB_PATH)
selected_product = None
uploaded_df = None

if source_mode == "Use product catalog":
    if catalog_df.empty:
        st.warning("The product catalog is empty. Use the upload option or run seed_data.py.")
    else:
        selected_name = st.sidebar.selectbox("Select a product", catalog_df["product_name"].tolist())
        selected_product = catalog_df[catalog_df["product_name"] == selected_name].iloc[0].to_dict()
elif source_mode == "Upload CSV":
    upload = st.sidebar.file_uploader(
        "Upload a product CSV",
        type=["csv", "xlsx"],
        help="Expected columns: product_name, unit_cost, fixed_cost, base_price, base_demand, elasticity, competitor_min, competitor_max",
    )
    if upload:
        if upload.name.lower().endswith(".csv"):
            uploaded_df = pd.read_csv(upload)
        else:
            uploaded_df = pd.read_excel(upload)
        st.sidebar.success(f"Loaded {len(uploaded_df)} rows from {upload.name}")
        if "product_name" not in uploaded_df.columns:
            st.sidebar.error("Your file needs a product_name column.")
        else:
            picked = st.sidebar.selectbox("Choose uploaded product", uploaded_df["product_name"].tolist())
            selected_product = uploaded_df[uploaded_df["product_name"] == picked].iloc[0].to_dict()
            if st.sidebar.button("Save uploaded catalog to database"):
                load_catalog_from_csv(DB_PATH, uploaded_df)
                st.sidebar.success("Uploaded catalog saved.")
    else:
        st.info("Upload a CSV or Excel file to simulate multiple products at once.")

defaults = {
    "product_name": "Cold Brew Coffee Pack",
    "unit_cost": 4.25,
    "fixed_cost": 700.0,
    "base_price": 9.50,
    "base_demand": 230.0,
    "elasticity": 1.2,
    "competitor_min": 8.50,
    "competitor_max": 11.00,
}

if selected_product:
    for key in defaults:
        defaults[key] = selected_product.get(key, defaults[key])

st.subheader("Pricing Inputs")
col1, col2, col3 = st.columns(3)

with col1:
    product_name = st.text_input("Product / Service name", value=str(defaults["product_name"]))
    unit_cost = st.number_input("Unit cost ($)", min_value=0.0, value=float(defaults["unit_cost"]), step=0.25)
    fixed_cost = st.number_input("Monthly fixed cost ($)", min_value=0.0, value=float(defaults["fixed_cost"]), step=50.0)
    base_price = st.number_input("Reference price ($)", min_value=0.01, value=float(defaults["base_price"]), step=0.25)

with col2:
    base_demand = st.number_input("Expected monthly demand at reference price", min_value=1, value=int(defaults["base_demand"]), step=5)
    elasticity = st.slider(
        "Price sensitivity (elasticity)",
        min_value=0.1,
        max_value=3.0,
        value=float(defaults["elasticity"]),
        step=0.1,
        help="Higher values mean demand drops faster when price increases.",
    )
    competitor_min = st.number_input("Competitor price floor ($)", min_value=0.0, value=float(defaults["competitor_min"]), step=0.25)
    competitor_max = st.number_input("Competitor price ceiling ($)", min_value=0.0, value=float(defaults["competitor_max"]), step=0.25)

with col3:
    sim_min_price = st.number_input("Simulation min price ($)", min_value=0.01, value=max(0.5, round(base_price * 0.70, 2)), step=0.25)
    sim_max_price = st.number_input("Simulation max price ($)", min_value=0.01, value=round(base_price * 1.40, 2), step=0.25)
    price_step = st.number_input("Price step ($)", min_value=0.05, value=0.25, step=0.05)
    marketing_boost = st.slider(
        "Expected demand lift from marketing (%)",
        min_value=0,
        max_value=40,
        value=0,
        step=5,
        help="Use this to test how stronger promotion might offset price sensitivity.",
    )

if sim_max_price <= sim_min_price:
    st.error("Simulation max price must be greater than simulation min price.")
    st.stop()

simulation_df = simulate_pricing_table(
    product_name=product_name,
    unit_cost=unit_cost,
    fixed_cost=fixed_cost,
    base_price=base_price,
    base_demand=base_demand,
    elasticity=elasticity,
    competitor_min=competitor_min,
    competitor_max=competitor_max,
    sim_min_price=sim_min_price,
    sim_max_price=sim_max_price,
    price_step=price_step,
    marketing_boost_pct=marketing_boost,
)

recommended_row = choose_recommended_price(simulation_df)
recommendations = generate_recommendations(
    simulation_df=simulation_df,
    product_name=product_name,
    unit_cost=unit_cost,
    fixed_cost=fixed_cost,
    base_price=base_price,
    competitor_min=competitor_min,
    competitor_max=competitor_max,
)

best_profit_row = simulation_df.loc[simulation_df["net_profit"].idxmax()]
best_revenue_row = simulation_df.loc[simulation_df["revenue"].idxmax()]
best_demand_row = simulation_df.loc[simulation_df["estimated_demand"].idxmax()]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Recommended price", f"${recommended_row['price']:.2f}")
m2.metric("Best monthly profit", f"${best_profit_row['net_profit']:.2f}")
m3.metric("Best revenue price", f"${best_revenue_row['price']:.2f}")
m4.metric("Highest demand price", f"${best_demand_row['price']:.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Scenario Table", "Recommendations", "Saved Runs"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Price vs Revenue and Net Profit")
        st.line_chart(simulation_df.set_index("price")[["revenue", "net_profit"]])
        st.markdown("#### Price vs Estimated Demand")
        st.line_chart(simulation_df.set_index("price")[["estimated_demand"]])
    with c2:
        st.markdown("#### Recommended Scenario")
        st.dataframe(recommended_row.to_frame().rename(columns={recommended_row.name: "value"}), use_container_width=True)
        st.markdown("#### Competitor Position Mix")
        comp_counts = simulation_df["competitor_position"].value_counts().rename_axis("position").reset_index(name="count")
        st.bar_chart(comp_counts.set_index("position"))
        st.info(
            f"At the recommended price of ${recommended_row['price']:.2f}, the estimated break-even volume is {recommended_row['breakeven_units']:.0f} units/month."
        )

with tab2:
    st.markdown("#### Full Simulation Table")
    st.dataframe(simulation_df, use_container_width=True)
    st.download_button(
        "Download simulation results as CSV",
        data=simulation_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{product_name.lower().replace(' ', '_')}_pricing_scenarios.csv",
        mime="text/csv",
    )

with tab3:
    st.markdown("#### Strategic Recommendations")
    for rec in recommendations:
        st.markdown(f"- {rec}")

    save_name = st.text_input("Scenario label", value=f"{product_name} - Base Scenario")
    if st.button("Save run to history"):
        summary = {
            "recommended_price": float(recommended_row["price"]),
            "recommended_profit": float(recommended_row["net_profit"]),
            "best_revenue_price": float(best_revenue_row["price"]),
            "best_demand_price": float(best_demand_row["price"]),
            "marketing_boost_pct": int(marketing_boost),
            "competitor_position": str(recommended_row["competitor_position"]),
        }
        save_simulation_run(DB_PATH, save_name, product_name, summary)
        st.success("Scenario saved to history.")

    st.markdown("#### Scenario Snapshot")
    st.write(
        {
            "product_name": product_name,
            "unit_cost": unit_cost,
            "fixed_cost": fixed_cost,
            "reference_price": base_price,
            "reference_demand": base_demand,
            "elasticity": elasticity,
            "competitor_band": [competitor_min, competitor_max],
            "marketing_boost_pct": marketing_boost,
        }
    )

with tab4:
    history_df = get_run_history_df(DB_PATH)
    if history_df.empty:
        st.info("No saved runs yet. Save one from the Recommendations tab.")
    else:
        st.dataframe(history_df, use_container_width=True)

st.markdown("---")
st.markdown(
    "Built for business scenario planning: compare pricing options, understand demand trade-offs, and turn data into a pricing recommendation you can pitch."
)
