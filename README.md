# Micro-Business Pricing Simulator

Micro-Business Pricing Simulator is a Python and Streamlit app that helps small businesses test pricing strategies before making real-world decisions. It simulates how different price points affect demand, revenue, profit, margin, and break-even volume, then turns the results into actionable pricing recommendations.

## Why this project matters

Many small businesses price products based on guesswork, competitor copying, or fear of losing customers. This project provides a lightweight decision-support tool that helps business owners explore trade-offs between **profitability**, **competitiveness**, and **sales volume**.

## Features

- Simulate multiple price points for a product or service
- Estimate demand using a simple price sensitivity model
- Compare monthly revenue, gross profit, net profit, and margin
- Visualize demand and profit across a pricing range
- Compare prices against a competitor price band
- Generate business-oriented pricing recommendations
- Save scenario runs to a local SQLite database
- Upload your own product catalog from CSV or Excel
- Export scenario results as CSV

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- SQLite

## Project Structure

```text
micro_business_pricing_simulator/
├── app.py
├── pricing_logic.py
├── database.py
├── seed_data.py
├── requirements.txt
├── README.md
├── .gitignore
└── sample_products.csv
```

## How to Run

### 1. Create and activate a virtual environment

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Generate demo data

```powershell
python seed_data.py
```

### 4. Start the app

```powershell
streamlit run app.py
```

## CSV Template

Your upload file should include these columns:

- `product_name`
- `unit_cost`
- `fixed_cost`
- `base_price`
- `base_demand`
- `elasticity`
- `competitor_min`
- `competitor_max`


## Future Improvements

- Add non-linear demand modeling
- Support discount campaigns and bundle pricing
- Add customer segments with different willingness to pay
- Add charts for contribution margin and profit heatmaps
- Deploy the app publicly with Streamlit Community Cloud
