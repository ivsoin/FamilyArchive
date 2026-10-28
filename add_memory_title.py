import sqlite3

def run_migration():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE memories ADD COLUMN title TEXT;")
        conn.commit()
        print("Migration successful: added column 'title' to 'memories' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'title' already exists.")
        else:
            raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
