#!/usr/bin/env python3
"""Drop all vector collection tables so Alembic downgrade can proceed."""
import sys
sys.path.insert(0, '/mnt/e/kolya/mini_rag_course/project/mini_rag/src')

import sqlalchemy as sa

# DB credentials from .env
db_url = "postgresql+psycopg2://postgres:PASSWORD@localhost:5432/minirag"


engine = sa.create_engine(db_url)

with engine.connect() as conn:
    # Find all collection tables
    result = conn.execute(sa.text(
        "SELECT tablename FROM pg_tables WHERE tablename LIKE 'collection_%'"
    ))
    tables = [row[0] for row in result]

    if not tables:
        print("No collection tables found.")
    else:
        for table in tables:
            print(f"Dropping table: {table}")
            conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        conn.commit()
        print(f"Dropped {len(tables)} collection table(s).")

print("Done. You can now run: alembic downgrade base && alembic upgrade head")
