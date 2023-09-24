import duckdb
import pandas as pd

# open connection
conn = duckdb.connect(database=':memory:', read_only=False)

# automatically read and register csv as a virtual table
conn.execute("CREATE TABLE georef AS SELECT * FROM read_csv_auto('data/georef-germany-kreis.csv')")

result = conn.execute("""
             SELECT 
                "Land name" AS 'federal_state',
                "Kreis name (short)" AS 'district',
                "Type" AS type,
                "Geo Shape" AS 'geoshape'
             FROM georef
             ORDER BY district
             """)
rows = result.df()

conn.close()

rows.to_csv("data/georef_districts.csv")