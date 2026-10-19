"""Create an isolated database, run all tests, and drop it afterward.
Usage: PG_TEST_ADMIN_URL=postgresql://postgres@localhost/postgres python -m scripts.test_local
"""
import os
import subprocess
import sys
import uuid
from pathlib import Path
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

name='kasparro_test_'+uuid.uuid4().hex
url=os.environ['PG_TEST_ADMIN_URL']
params=conninfo_to_dict(url)
params['dbname']=name
output=Path('reports/tests.txt')
output.parent.mkdir(exist_ok=True)
with psycopg.connect(url,autocommit=True) as conn:
    conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
try:
    env={**os.environ,'TEST_DATABASE_URL':make_conninfo(**params)}
    result=subprocess.run([sys.executable,'-m','pytest','-q','--tb=short'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output.write_text(result.stdout)
    print(result.stdout,end='')
finally:
    with psycopg.connect(url,autocommit=True) as conn:
        conn.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
sys.exit(result.returncode)
