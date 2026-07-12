#!/bin/bash
source /home/abulrahmansalah/miniconda3/etc/profile.d/conda.sh
conda activate mini-rag-app

DB_NAME="minirag"
DB_USER="postgres"
DB_HOST="localhost"

echo "=== Step 1: Dropping all vector collection tables ==="
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE tablename LIKE 'collection_%' LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', r.tablename;
    END LOOP;
END;
\$\$;"

echo "=== Step 2: Alembic downgrade (drop all schema tables) ==="
cd /mnt/e/kolya/mini_rag_course/project/mini_rag/src/models/db_schemes/minirag
alembic downgrade base

echo "=== Step 3: Alembic upgrade (recreate all schema tables) ==="
alembic upgrade head

echo "=== Done! Fresh database ready. ==="
