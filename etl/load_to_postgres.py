import pandas as pd
from sqlalchemy import create_engine, text
import time




# create the engine
engine = create_engine("postgresql://josep:Medulla2026@localhost/glp1_analytics")

# Drop tables in dependency order before reloading
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS households CASCADE"))
    conn.commit()
    print("Tables dropped cleanly")

# Load households
households = pd.read_csv("data/processed/households.csv")
households.to_sql("households", engine, if_exists="replace", index=False)
print(f"Loaded {len(households):,} households")

# Load category dimension
categories_data = [
    ("chips_savory_snacks", "declining"),  ("sweet_bakery", "declining"),
    ("cookies", "declining"),              ("candy_confectionery", "declining"),
    ("crackers", "declining"),             ("popcorn_pretzels", "declining"),
    ("meat_snacks", "growing"),            ("protein_bars", "growing"),
    ("yogurt", "growing"),                 ("fresh_fruit_snacks", "growing"),
]
cats_df = pd.DataFrame(categories_data, columns=["category_name", "category_type"])
cats_df.to_sql("categories", engine, if_exists="replace", index=False)

# Load transactions (chunked for performance practice)
transactions = pd.read_csv("data/processed/transactions.csv")
# Add category_id lookup
cat_map = cats_df.reset_index().rename(columns={"index": "category_id"})
cat_map["category_id"] += 1
transactions = transactions.merge(cat_map[["category_name","category_id"]],
                                  left_on="category", right_on="category_name")

start = time.time()
transactions[["household_id","month","category_id","spend","months_on_drug"]]\
    .to_sql("transactions", engine, if_exists="replace",
            index=False, chunksize=5000, method="multi")
print(f"Loaded {len(transactions):,} transactions in {time.time()-start:.1f}s")