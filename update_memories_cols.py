import sqlite3

def run_migration():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    new_columns = [
        ("photo_links", "TEXT"),
        ("video_link", "TEXT"),
        ("audio_link", "TEXT")
    ]
    
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE memories ADD COLUMN {col_name} {col_type};")
            print(f"Added column '{col_name}' successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column '{col_name}' already exists.")
            else:
                raise e
                
    conn.commit()
    conn.close()
    print("Database migration finished.")

if __name__ == '__main__':
    run_migration()
