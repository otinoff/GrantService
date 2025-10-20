import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.database import GrantServiceDatabase

db = GrantServiceDatabase()
with db.connect() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT agent_name, prompt_type, is_default FROM agent_prompts ORDER BY agent_name, prompt_type")
    for row in cursor.fetchall():
        default = " [DEFAULT]" if row[2] else ""
        print(f"{row[0]:12} | {row[1]:20}{default}")
    cursor.close()
