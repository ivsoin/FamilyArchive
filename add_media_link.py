import sqlite3

def run_migration():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE memories ADD COLUMN media_link TEXT;")
        conn.commit()
        print("Migration successful: added column 'media_link' to 'memories' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'media_link' already exists.")
        else:
            raise e
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
