import os
import re
from app import app, db, Relative
from sqlalchemy import text
from datetime import datetime

# Russian months for parsing dates like "15 мая 1995"
months = {
    'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04', 'мая': '05', 'май': '05',
    'июн': '06', 'июл': '07', 'авг': '08', 'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
}

def parse_date(date_str):
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    
    # E.g., 1995
    m = re.search(r'\b(18|19|20)\d{2}\b', date_str)
    year = m.group(0) if m else None
    
    if not year:
        return None
        
    # E.g., 15 мая 1995
    for month_name, month_num in months.items():
        if month_name in date_str:
            # Try to find day
            day_m = re.search(r'\b([1-9]|[12]\d|3[01])\b', date_str)
            if day_m and day_m.group(0) != year:
                day = day_m.group(0).zfill(2)
                return f"{year}-{month_num}-{day}"
            return f"{year}-{month_num}-01"
            
    # E.g., 05.10.1990
    m_dots = re.search(r'\b([1-9]|[12]\d|3[01])[\./-](0[1-9]|1[012])[\./-]((18|19|20)\d{2})\b', date_str)
    if m_dots:
        return f"{m_dots.group(3)}-{m_dots.group(2).zfill(2)}-{m_dots.group(1).zfill(2)}"
        
    return f"{year}-01-01"


with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE relatives ADD COLUMN birth_date VARCHAR(20)"))
        db.session.execute(text("ALTER TABLE relatives ADD COLUMN death_date VARCHAR(20)"))
        db.session.execute(text("ALTER TABLE relatives ADD COLUMN is_alive INTEGER DEFAULT 1"))
        db.session.commit()
        print("Columns added successfully.")
    except Exception as e:
        print(f"Columns might already exist: {e}")
        db.session.rollback()

    relatives = Relative.query.all()
    count = 0
    for r in relatives:
        if r.years:
            parts = r.years.split('-')
            
            if len(parts) == 1:
                # E.g., "1995", "Родился 15 мая 1995"
                b_date = parse_date(parts[0])
                if b_date:
                    r.birth_date = b_date
                    r.is_alive = 1
            else:
                # E.g., "1950 - 2020", "1980 - н.в."
                b_date = parse_date(parts[0])
                if b_date:
                    r.birth_date = b_date
                    
                d_str = parts[1].lower()
                if 'н' in d_str or 'v' in d_str or 'в' in d_str: # e.g., н.в.
                    r.is_alive = 1
                else:
                    d_date = parse_date(parts[1])
                    if d_date:
                        r.death_date = d_date
                        r.is_alive = 0
                    else:
                        r.is_alive = 1
                        
            count += 1
            
    db.session.commit()
    print(f"Data migration completed. Processed {count} records.")
