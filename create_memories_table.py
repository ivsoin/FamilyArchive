import sqlite3

def create_table():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_person_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            life_stage TEXT NOT NULL,
            media_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(target_person_id) REFERENCES relatives(id),
            FOREIGN KEY(author_id) REFERENCES relatives(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Table 'memories' created successfully in family.db.")

if __name__ == '__main__':
    create_table()
