"""
Apply migration 006: Stage Tracking System
"""
import sys
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

def apply_migration():
    """Apply migration 006"""

    # Get database connection
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'grantservice'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '1256')
    )

    try:
        print("🔄 Applying migration 006: Stage Tracking System...")

        # Read migration file
        migration_path = os.path.join(
            os.path.dirname(__file__),
            'database', 'migrations', '006_add_stage_tracking.sql'
        )

        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        cur = conn.cursor()
        cur.execute(migration_sql)
        conn.commit()

        print("✅ Migration 006 applied successfully!")

        # Verify results
        print("\n📊 Verification:")

        # Check sessions table
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(current_stage) as with_stage,
                COUNT(CASE WHEN array_length(agents_passed, 1) > 0 THEN 1 END) as with_agents_passed
            FROM sessions
        """)
        total, with_stage, with_agents = cur.fetchone()
        print(f"   Sessions: {total} total, {with_stage} with stage, {with_agents} with agents_passed")

        # Check recent sessions with stage info
        cur.execute("""
            SELECT anketa_id, current_stage, agents_passed, stage_updated_at
            FROM sessions
            WHERE anketa_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 5
        """)

        print("\n📋 Recent sessions with stage tracking:")
        for row in cur.fetchall():
            anketa_id, stage, agents, updated = row
            print(f"   {anketa_id}: stage={stage}, passed={agents}")

        # Test helper function
        print("\n🧪 Testing get_stage_progress() function:")
        cur.execute("""
            SELECT * FROM get_stage_progress(
                (SELECT anketa_id FROM sessions WHERE anketa_id IS NOT NULL LIMIT 1)
            )
        """)
        result = cur.fetchone()
        if result:
            anketa_id, stage, agents, progress, emoji = result
            print(f"   {emoji} {anketa_id}: {stage} ({progress}% complete)")
            print(f"   Agents passed: {agents}")

        cur.close()

    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        conn.close()

    return True

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
