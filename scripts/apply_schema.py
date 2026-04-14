"""
apply_schema.py — Apply JustBuildIt schema to Neon PostgreSQL.
Usage: python3 scripts/apply_schema.py
"""
import sys
import os

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not found. Run: pip3 install psycopg2-binary")
    sys.exit(1)

NEON_DSN = (
    "postgresql://neondb_owner:npg_blWwU4x8qrBa"
    "@ep-rough-forest-a1cwj3t7-pooler.ap-southeast-1.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)

SCHEMA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "backend", "migrations", "schema.sql"
)


def apply():
    print("🔌 Connecting to Neon DB...")
    conn = psycopg2.connect(NEON_DSN)
    conn.autocommit = True
    cur = conn.cursor()

    print("📂 Reading schema file...")
    with open(os.path.abspath(SCHEMA_FILE)) as f:
        sql = f.read()

    print("⚙️  Applying schema...")
    cur.execute(sql)

    # List created tables
    cur.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    print("\n✅ Schema applied successfully!")
    print(f"   Tables in 'public' schema ({len(tables)}):")
    for table in tables:
        print(f"     • {table}")


if __name__ == "__main__":
    apply()
