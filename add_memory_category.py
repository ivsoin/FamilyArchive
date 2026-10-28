import sqlite3

def run_migration():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE memories ADD COLUMN category TEXT;")
        print("Added column 'category' successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'category' already exists.")
        else:
            raise e
            
    conn.commit()
    conn.close()
    print("Database migration finished.")

if __name__ == '__main__':
    run_migration()
