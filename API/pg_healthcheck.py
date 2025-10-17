# pg_healthcheck.py
import psycopg2
import traceback

cfg = dict(
    host="localhost",
    port=5432,
    database="kkokkaot_closet",
    user="postgres",
    password="000000",
)

try:
    conn = psycopg2.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print("✅ connected:", cur.fetchone()[0])
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' ORDER BY 1"
    )
    print("public tables:", [r[0] for r in cur.fetchall()])
    cur.close()
    conn.close()
except Exception:
    traceback.print_exc()
