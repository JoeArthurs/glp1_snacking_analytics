import pandas as pd
import numpy as np
from faker import Faker
import random

# Build the synthetic households panel

fake = Faker()
np.random.seed(42)
random.seed(42)

N_HOUSEHOLDS = 15000  # scaled-down but representative

# --- Household demographics ---
income_brackets = ["<50K", "50-75K", "75-100K", "100-125K", "125K+"]
income_weights  = [0.22, 0.25, 0.20, 0.15, 0.18]

households = pd.DataFrame({
    "household_id": range(1, N_HOUSEHOLDS + 1),
    "income_bracket": np.random.choice(income_brackets, N_HOUSEHOLDS, p=income_weights),
    "household_size": np.random.choice([1, 2, 3, 4, 5], N_HOUSEHOLDS, p=[0.28, 0.35, 0.16, 0.14, 0.07]),
    "has_children": np.random.choice([True, False], N_HOUSEHOLDS, p=[0.30, 0.70]),
})

# --- GLP-1 adoption (11% late 2023 → 16% mid-2024, weight-loss skews younger/wealthier) ---
def assign_glp1(row):
    base_prob = 0.14  # average across period
    if row["income_bracket"] in ["100-125K", "125K+"]:
        base_prob += 0.04
    return np.random.random() < base_prob

households["is_glp1_user"] = households.apply(assign_glp1, axis=1)
households["glp1_start_month"] = households["is_glp1_user"].apply(
    lambda x: np.random.randint(1, 13) if x else None
)
households["discontinued"] = households["is_glp1_user"].apply(
    lambda x: np.random.random() < 0.34 if x else False  # 34% discontinuation rate from paper
)

households.to_csv("data/processed/households.csv", index=False)
print(f"Households: {len(households)} | GLP-1 users: {households['is_glp1_user'].sum()}")
# --- Snack category definitions with baseline monthly spend ---
categories = {
    "chips_savory_snacks":  {"base_spend": 18.50, "glp1_effect": -0.101},
    "sweet_bakery":         {"base_spend": 14.20, "glp1_effect": -0.088},
    "cookies":              {"base_spend": 12.80, "glp1_effect": -0.065},
    "candy_confectionery":  {"base_spend": 11.00, "glp1_effect": -0.055},
    "crackers":             {"base_spend": 9.40,  "glp1_effect": -0.040},
    "popcorn_pretzels":     {"base_spend":  7.80, "glp1_effect": -0.035},
    "meat_snacks":          {"base_spend": 10.20, "glp1_effect": +0.042},  # KEY CATEGORY
    "protein_bars":         {"base_spend":  8.60, "glp1_effect": +0.031},
    "yogurt":               {"base_spend": 11.50, "glp1_effect": +0.058},  # largest gainer
    "fresh_fruit_snacks":   {"base_spend":  9.80, "glp1_effect": +0.022},
}

MONTHS = list(range(1, 13))  # 12-month period
records = []

for _, hh in households.iterrows():
    for month in MONTHS:
        for cat, params in categories.items():
            base = params["base_spend"]
            effect = 0.0

            if hh["is_glp1_user"] and hh["glp1_start_month"] is not None:
                months_on_drug = month - hh["glp1_start_month"]
                if months_on_drug >= 0:
                    # Effect builds over 6 months, then partially fades if discontinued
                    ramp = min(months_on_drug / 6.0, 1.0)
                    fade = 0.5 if hh["discontinued"] and months_on_drug > 6 else 1.0
                    effect = params["glp1_effect"] * ramp * fade

            # Income modifier: higher income = higher baseline
            income_mult = {"<50K": 0.75, "50-75K": 0.90, "75-100K": 1.0,
                           "100-125K": 1.20, "125K+": 1.45}[hh["income_bracket"]]

            spend = base * income_mult * (1 + effect)
            spend = max(0, spend + np.random.normal(0, spend * 0.15))  # noise

            records.append({
                "household_id": hh["household_id"],
                "month": month,
                "category": cat,
                "spend": round(spend, 2),
                "is_glp1_user": hh["is_glp1_user"],
                "months_on_drug": max(0, month - (hh["glp1_start_month"] or 99)),
            })

transactions = pd.DataFrame(records)
transactions.to_csv("data/processed/transactions.csv", index=False)
print(f"Transactions: {len(transactions):,} rows")

