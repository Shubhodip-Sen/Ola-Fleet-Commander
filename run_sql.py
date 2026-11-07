"""Executes sql/ola_analysis.sql statement by statement and dumps each result (used for QA + report numbers)."""
import sqlite3, re, json, sys, pandas as pd
con = sqlite3.connect("data/ola.db")
text = open("sql/ola_analysis.sql").read()
blocks = re.split(r"\n(?=-- Q\d+\.\d+ )", text)
res = {}
for b in blocks[1:]:
    name = b.split("\n")[0].strip("- ").split(" ")[0]
    stmt = "\n".join(l for l in b.split("\n") if not l.strip().startswith("--")).split(";")[0].strip()
    if not stmt: continue
    try:
        res[name] = pd.read_sql(stmt, con)
    except Exception as e:
        print("FAIL", name, e); continue
# the view
try:
    con.executescript(text[text.index("DROP VIEW"):])
except Exception as e: print("VIEW FAIL", e)
for k, v in res.items():
    print("\n##", k, v.shape); print(v.head(12).to_string(index=False))
