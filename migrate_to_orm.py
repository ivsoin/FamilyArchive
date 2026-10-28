import sqlite3
import uuid

def run_migration():
    conn = sqlite3.connect('family.db')
    cursor = conn.cursor()
    
    # 1. Создаем таблицу trees
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Table 'trees' created.")
    
    # 2. Проверяем, есть ли уже дефолтное дерево
    cursor.execute("SELECT COUNT(*) FROM trees")
    tree_count = cursor.fetchone()[0]
    
    default_tree_id = "default-tree"
    if tree_count == 0:
        cursor.execute("INSERT INTO trees (id, name) VALUES (?, ?)", (default_tree_id, "Архив семьи"))
        print(f"Created default tree with ID: {default_tree_id}")
    
    # 3. Добавляем колонку tree_id в relatives
    try:
        cursor.execute("ALTER TABLE relatives ADD COLUMN tree_id TEXT REFERENCES trees(id);")
        print("Added column 'tree_id' to 'relatives'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'tree_id' already exists in 'relatives'.")
        else:
            raise e
            
    # 4. Добавляем колонку tree_id в life_events
    try:
        cursor.execute("ALTER TABLE life_events ADD COLUMN tree_id TEXT REFERENCES trees(id);")
        print("Added column 'tree_id' to 'life_events'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'tree_id' already exists in 'life_events'.")
        else:
            raise e
            
    # 5. Проставляем дефолтный tree_id для всех записей без дерева
    cursor.execute("UPDATE relatives SET tree_id = ? WHERE tree_id IS NULL", (default_tree_id,))
    cursor.execute("UPDATE life_events SET tree_id = ? WHERE tree_id IS NULL", (default_tree_id,))
    print("Set default tree_id for existing relatives and life_events.")
    
    conn.commit()
    conn.close()
    print("ORM database migration finished successfully.")

if __name__ == '__main__':
    run_migration()
