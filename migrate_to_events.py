import sqlite3

def run_migration():
    conn = sqlite3.connect('family.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Create life_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_person_id TEXT NOT NULL,
            life_stage TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            event_year TEXT,
            photo_links TEXT,
            video_link TEXT,
            audio_link TEXT,
            author_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(target_person_id) REFERENCES relatives(id),
            FOREIGN KEY(author_id) REFERENCES relatives(id)
        )
    ''')
    print("Table 'life_events' created or already exists.")
    
    # 2. Create event_contributions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            author_id TEXT NOT NULL,
            content TEXT NOT NULL,
            photo_links TEXT,
            video_link TEXT,
            audio_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES life_events(id),
            FOREIGN KEY(author_id) REFERENCES relatives(id)
        )
    ''')
    print("Table 'event_contributions' created or already exists.")
    
    # 3. Migrate memories
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
    memories_exists = cursor.fetchone()
    
    if memories_exists:
        cursor.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Found {count} memories to migrate...")
            cursor.execute("SELECT * FROM memories")
            columns = [col[0] for col in cursor.description]
            memories = cursor.fetchall()
            
            for m in memories:
                m_dict = dict(zip(columns, m))
                
                target_person_id = m_dict.get('target_person_id')
                author_id = m_dict.get('author_id')
                life_stage = m_dict.get('life_stage')
                description = m_dict.get('content', '')
                created_at = m_dict.get('created_at')
                photo_links = m_dict.get('photo_links')
                video_link = m_dict.get('video_link')
                audio_link = m_dict.get('audio_link')
                category = m_dict.get('category')
                title = m_dict.get('title')
                
                if not title:
                    title = f"Memory ({category or 'Uncategorized'})"
                
                cursor.execute('''
                    INSERT INTO life_events (
                        target_person_id, author_id, life_stage, title, description, 
                        category, event_year, photo_links, video_link, audio_link, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    target_person_id, author_id, life_stage, title, description,
                    category, None, photo_links, video_link, audio_link, created_at
                ))
            
            print("Successfully migrated all memories to 'life_events'.")
            cursor.execute("ALTER TABLE memories RENAME TO memories_backup;")
            print("Renamed table 'memories' to 'memories_backup'.")
        else:
            print("Table 'memories' is empty. Deleting table 'memories'.")
            cursor.execute("DROP TABLE memories;")
    else:
        print("Table 'memories' not found, migration might be done already.")
        
    conn.commit()
    conn.close()
    print("Database migration finished successfully.")

if __name__ == '__main__':
    run_migration()
