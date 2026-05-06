import pandas as pd
from sqlalchemy import create_engine, text
import time
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
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
cats_df["category_id"] = range(1, len(cats_df) + 1)
cats_df.to_sql("categories", engine, if_exists="replace", index=False)

# Load transactions (chunked for performance practice)
transactions = pd.read_csv("data/processed/transactions.csv")

# Add category_id lookup — cats_df already has category_id, use it directly
transactions = transactions.merge(cats_df[["category_name", "category_id"]],
                                  left_on="category", right_on="category_name")

start = time.time()
transactions[["household_id", "month", "category_id", "spend", "months_on_drug"]]\
    .to_sql("transactions", engine, if_exists="replace",
            index=False, chunksize=5000, method="multi")
print(f"Loaded {len(transactions):,} transactions in {time.time()-start:.1f}s")