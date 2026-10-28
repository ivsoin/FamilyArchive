import sqlite3

def guess_gender(first, last, pat):
    if pat:
        if pat.endswith('вна') or pat.endswith('чна'): return 'female'
        if pat.endswith('вич') or pat.endswith('лич'): return 'male'
    if last:
        if last.endswith('ва') or last.endswith('ая') or last.endswith('ина'): return 'female'
        if last.endswith('ов') or last.endswith('ий') or last.endswith('ин') or last.endswith('ев'): return 'male'
    if first:
        if first.endswith('а') or first.endswith('я'): return 'female'
    return 'male'

conn = sqlite3.connect('c:/Users/HUAWEI/Desktop/FamilyArchive/family.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE relatives ADD COLUMN first_name VARCHAR(50)")
    c.execute("ALTER TABLE relatives ADD COLUMN last_name VARCHAR(50)")
    c.execute("ALTER TABLE relatives ADD COLUMN patronymic VARCHAR(50)")
    c.execute("ALTER TABLE relatives ADD COLUMN maiden_name VARCHAR(50)")
    c.execute("ALTER TABLE relatives ADD COLUMN gender VARCHAR(10)")
except sqlite3.OperationalError as e:
    print("Columns may already exist:", e)

c.execute("SELECT id, name FROM relatives")
rows = c.fetchall()

for row in rows:
    pid = row[0]
    name = row[1] or ""
    parts = name.strip().split()
    last = parts[0] if len(parts) > 0 else ""
    first = parts[1] if len(parts) > 1 else ""
    pat = " ".join(parts[2:]) if len(parts) > 2 else ""
    
    gender = guess_gender(first, last, pat)
    
    c.execute("""
        UPDATE relatives 
        SET first_name=?, last_name=?, patronymic=?, gender=?, maiden_name=''
        WHERE id=?
    """, (first, last, pat, gender, pid))

conn.commit()
print("Migration completed.")
