import sqlite3

def clear_database():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    try:
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
        print(f"Found tables: {tables}")
        
        # Clear memories table first due to foreign key references if any (optional but good practice)
        if 'memories' in tables:
            cursor.execute("DELETE FROM memories;")
            print("Cleared table 'memories'.")
            
        # Clear relatives table
        if 'relatives' in tables:
            cursor.execute("DELETE FROM relatives;")
            print("Cleared table 'relatives'.")
            
        # Reset autoincrement counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('memories', 'relatives');")
        conn.commit()
        print("Database family.db cleared successfully. All tables are empty, schemas preserved.")
    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    clear_database()
