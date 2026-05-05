## Environment Setup

### Prerequisites
- Python 3.11 (via conda)
- PostgreSQL 16
- Tableau Desktop (Phase 5)

### 1. Clone the repo and create the conda environment
```bash
git clone https://github.com/JoeArthurs/glp1_snacking_analytics.git
cd glp1_snacking_analytics
conda create -n glp1-analytics python=3.11
conda activate glp1-analytics
pip install -r requirements.txt
python -m ipykernel install --user --name glp1-analytics --display-name "GLP-1 Analytics"
```

### 2. Set up PostgreSQL
```bash
psql -U postgres
```
```sql
CREATE DATABASE glp1_analytics;
CREATE USER your_os_username WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE glp1_analytics TO your_os_username;
GRANT ALL ON SCHEMA public TO your_os_username;
ALTER DATABASE glp1_analytics OWNER TO your_os_username;
\q
```

### 3. Run the pipeline in order
```bash
# Step 1 — generate synthetic household panel and transactions
python etl/build_synthetic_panel.py

# Step 2 — create tables and indexes in Postgres
psql -d glp1_analytics -f sql/01_schema.sql

# Step 3 — load CSVs into Postgres
python etl/load_to_postgres.py
```

### 4. Verify the load
```bash
psql -d glp1_analytics -c "SELECT COUNT(*) FROM transactions;"
# Expected: 1,800,000
```