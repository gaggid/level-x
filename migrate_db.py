# migrate_db.py
from sqlalchemy import text
from db.connection import engine

def run_migration():
    """Add peer insights columns"""
    
    with engine.connect() as conn:
        try:
            # Add peer_insights column
            conn.execute(text("""
                ALTER TABLE peer_matches 
                ADD COLUMN IF NOT EXISTS peer_insights JSON
            """))
            
            # Add example_tweets column
            conn.execute(text("""
                ALTER TABLE peer_matches 
                ADD COLUMN IF NOT EXISTS example_tweets JSON
            """))
            
            conn.commit()
            print("✅ Migration successful!")
            print("   - Added peer_insights column")
            print("   - Added example_tweets column")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()

if __name__ == "__main__":
    run_migration()