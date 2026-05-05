-- Households dimension
CREATE TABLE IF NOT EXISTS households (
    household_id      INTEGER PRIMARY KEY,
    income_bracket    VARCHAR(20),
    household_size    SMALLINT,
    has_children      BOOLEAN,
    is_glp1_user      BOOLEAN,
    glp1_start_month  SMALLINT,
    discontinued      BOOLEAN
);

-- Category dimension
CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE,
    category_type VARCHAR(20)  -- 'declining', 'growing', 'neutral'
);

-- Transactions fact table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  BIGSERIAL PRIMARY KEY,
    household_id    INTEGER REFERENCES households(household_id),
    month           SMALLINT,
    category_id     INTEGER REFERENCES categories(category_id),
    spend           NUMERIC(8,2),
    months_on_drug  SMALLINT DEFAULT 0
);

-- Indexes (you will benchmark these in Phase 4)
CREATE INDEX idx_transactions_household ON transactions(household_id);
CREATE INDEX idx_transactions_category  ON transactions(category_id);
CREATE INDEX idx_transactions_month     ON transactions(month);
-- Composite covering index — benchmark this vs individual indexes
CREATE INDEX idx_transactions_hh_cat_month ON transactions(household_id, category_id, month);