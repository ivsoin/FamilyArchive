import os
import json
import random
import string
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from collections import deque
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['SECURITY_PASSWORD_SALT'] = 'my_precious_two'
serializer = URLSafeTimedSerializer(app.secret_key)

# --- НАСТРОЙКА ORM (БАЗЫ ДАННЫХ) ---
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'family.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- НАСТРОЙКА ЗАГРУЗКИ ФАЙЛОВ ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def save_uploaded_file(file_obj):
    if not file_obj or file_obj.filename == '':
        return None
    ext = os.path.splitext(file_obj.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file_obj.save(file_path)
    return f"uploads/{unique_filename}"

def send_verification_email(user_email):
    token = serializer.dumps(user_email, salt=app.config['SECURITY_PASSWORD_SALT'])
    verify_url = url_for('verify_email', token=token, _external=True)
    print("\n" + "="*50)
    print(f"📧 ЭМУЛЯЦИЯ ОТПРАВКИ ПИСЬМА")
    print(f"Кому: {user_email}")
    print(f"Тема: Подтверждение Email")
    print(f"Текст:\nЗдравствуйте!\nПожалуйста, перейдите по ссылке для подтверждения вашего адреса электронной почты:\n{verify_url}")
    print("="*50 + "\n")

# --- МОДЕЛИ БАЗЫ ДАННЫХ (ORM) ---

class Tree(db.Model):
    __tablename__ = 'trees'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Relative(db.Model):
    __tablename__ = 'relatives'
    id = db.Column(db.String(50), primary_key=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    years = db.Column(db.String(50)) # Legacy, can keep for backup
    birth_date = db.Column(db.String(20))
    death_date = db.Column(db.String(20))
    is_alive = db.Column(db.Integer, default=1)
    bio = db.Column(db.Text)
    photo = db.Column(db.String(200))
    connections = db.Column(db.Text, default='{}')
    is_deleted = db.Column(db.Integer, default=0)
    password_hash = db.Column(db.String(200))
    email = db.Column(db.String(120), unique=True)
    is_email_verified = db.Column(db.Integer, default=0)
    invite_code = db.Column(db.String(20))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    patronymic = db.Column(db.String(50))
    maiden_name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LifeEvent(db.Model):
    __tablename__ = 'life_events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    author_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    life_stage = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    event_year = db.Column(db.String(50))
    photo_links = db.Column(db.Text)
    video_link = db.Column(db.Text)
    audio_link = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventContribution(db.Model):
    __tablename__ = 'event_contributions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey('life_events.id'), nullable=False)
    author_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    photo_links = db.Column(db.Text)
    video_link = db.Column(db.Text)
    audio_link = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LifeEra(db.Model):
    __tablename__ = 'life_eras'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_year = db.Column(db.String(20))
    end_year = db.Column(db.String(20))
    cover_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    author_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    memory_year = db.Column(db.String(50))
    photo_links = db.Column(db.Text)
    video_link = db.Column(db.Text)
    audio_link = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Reflection(db.Model):
    __tablename__ = 'reflections'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    author_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Place(db.Model):
    __tablename__ = 'places'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_range = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ImportantPerson(db.Model):
    __tablename__ = 'important_people'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    target_person_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role_label = db.Column(db.String(100))
    description = db.Column(db.Text)
    period = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

family_story_participants = db.Table('family_story_participants',
    db.Column('family_story_id', db.Integer, db.ForeignKey('family_stories.id'), primary_key=True),
    db.Column('relative_id', db.String(50), db.ForeignKey('relatives.id'), primary_key=True)
)

class FamilyStory(db.Model):
    __tablename__ = 'family_stories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tree_id = db.Column(db.String(36), db.ForeignKey('trees.id'), nullable=False)
    author_id = db.Column(db.String(50), db.ForeignKey('relatives.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_range = db.Column(db.String(100))
    photo_links = db.Column(db.Text)
    video_link = db.Column(db.Text)
    audio_link = db.Column(db.Text)
    participants = db.relationship('Relative', secondary=family_story_participants, lazy='subquery',
        backref=db.backref('family_stories', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- ФУНКЦИИ-ПОМОЩНИКИ ---

def get_reverse_role(role):
    if role == 'parent':
        return 'child'
    elif role == 'child':
        return 'parent'
    elif role == 'spouse':
        return 'spouse'
    elif role == 'sibling':
        return 'sibling'
    return role

def get_all_active_family(tree_id):
    rows = Relative.query.filter_by(tree_id=tree_id, is_deleted=0).all()
    family = {}
    for row in rows:
        family[row.id] = {
            'id': row.id,
            'tree_id': row.tree_id,
            'name': row.name,
            'role': row.role,
            'years': row.years,
            'birth_date': row.birth_date,
            'death_date': row.death_date,
            'is_alive': row.is_alive,
            'bio': row.bio,
            'photo': row.photo,
            'connections': json.loads(row.connections) if row.connections else {},
            'password_hash': row.password_hash,
            'email': row.email,
            'is_email_verified': row.is_email_verified,
            'invite_code': row.invite_code,
            'first_name': row.first_name,
            'last_name': row.last_name,
            'patronymic': row.patronymic,
            'maiden_name': row.maiden_name,
            'gender': row.gender
        }
    return family

def calculate_relationships(tree_id, start_user_id):
    all_family = get_all_active_family(tree_id)
    if start_user_id not in all_family:
        return all_family

    graph = {}
    for pid, person in all_family.items():
        graph[pid] = person['connections']

    relation_mapping = {
        (): {'male': 'Я', 'female': 'Я', 'neutral': 'Я', 'tier': 0},
        ('spouse',): {'male': 'Муж', 'female': 'Жена', 'neutral': 'Супруг(а)', 'tier': 0},
        ('parent',): {'male': 'Отец', 'female': 'Мать', 'neutral': 'Родитель', 'tier': -1},
        ('child',): {'male': 'Сын', 'female': 'Дочь', 'neutral': 'Ребенок', 'tier': 1},
        ('sibling',): {'male': 'Брат', 'female': 'Сестра', 'neutral': 'Брат / Сестра', 'tier': 0},
        ('parent', 'parent'): {'male': 'Дедушка', 'female': 'Бабушка', 'neutral': 'Бабушка / Дедушка', 'tier': -2},
        ('child', 'child'): {'male': 'Внук', 'female': 'Внучка', 'neutral': 'Внук / Внучка', 'tier': 2},
        ('parent', 'sibling'): {'male': 'Дядя', 'female': 'Тетя', 'neutral': 'Дядя / Тетя', 'tier': -1},
        ('sibling', 'child'): {'male': 'Племянник', 'female': 'Племянница', 'neutral': 'Племянник / Племянница', 'tier': 1},
        ('parent', 'sibling', 'child'): {'male': 'Двоюродный брат', 'female': 'Двоюродная сестра', 'neutral': 'Двоюродный брат / сестра', 'tier': 0},
        ('parent', 'parent', 'parent'): {'male': 'Прадедушка', 'female': 'Прабабушка', 'neutral': 'Прабабушка / Прадедушка', 'tier': -3},
        ('child', 'child', 'child'): {'male': 'Правнук', 'female': 'Правнучка', 'neutral': 'Правнук / Правнучка', 'tier': 3},
        ('spouse', 'parent'): {'male': 'Свекр / Тесть', 'female': 'Свекровь / Теща', 'neutral': 'Свекр / Теща', 'tier': -1},
        ('child', 'spouse'): {'male': 'Зять', 'female': 'Невестка', 'neutral': 'Зять / Невестка', 'tier': 1},
        ('spouse', 'sibling'): {'male': 'Деверь / Шурин', 'female': 'Золовка / Свояченица', 'neutral': 'Шурин / Золовка', 'tier': 0},
        ('sibling', 'spouse'): {'male': 'Муж', 'female': 'Жена', 'neutral': 'Супруг(а) брата/сестры', 'tier': 0}
    }

    queue = deque([(start_user_id, tuple(), None)])
    visited = set([start_user_id])
    
    result = {}
    person = all_family[start_user_id]
    result[start_user_id] = {**person, 'calc_role': 'Я', 'tier': 0, 'branch': None}
    
    while queue:
        current_id, path, branch = queue.popleft()
        
        for neighbor_id, role in graph.get(current_id, {}).items():
            if neighbor_id not in visited and neighbor_id in all_family:
                if role in ('parent', 'sibling') and 'spouse' in path:
                    continue
                
                visited.add(neighbor_id)
                new_path = path + (role,)
                
                if new_path in relation_mapping:
                    mapping = relation_mapping[new_path]
                    tier = mapping['tier']
                    gender = all_family[neighbor_id].get('gender')
                    if gender == 'male':
                        role_name = mapping['male']
                    elif gender == 'female':
                        role_name = mapping['female']
                    else:
                        role_name = mapping['neutral']
                else:
                    role_name = 'Дальний родственник'
                    tier = new_path.count('child') - new_path.count('parent')
                    if tier > 3: tier = 3
                    if tier < -3: tier = -3

                new_branch = branch
                if current_id == start_user_id and role == 'parent':
                    gender = all_family[neighbor_id].get('gender')
                    if gender == 'male':
                        new_branch = 'paternal'
                    elif gender == 'female':
                        new_branch = 'maternal'

                result[neighbor_id] = {**all_family[neighbor_id], 'calc_role': role_name, 'tier': tier, 'branch': new_branch}
                queue.append((neighbor_id, new_path, new_branch))
                
    for pid, person in all_family.items():
        if pid not in result:
            result[pid] = {**person, 'calc_role': 'Родственник (без связи)', 'tier': 100}
            
    return result

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        row = Relative.query.filter_by(id=user_id, is_deleted=0).first()
        if row:
            g.user = {
                'id': row.id,
                'tree_id': row.tree_id,
                'name': row.name,
                'role': row.role,
                'years': row.years,
                'birth_date': row.birth_date,
                'death_date': row.death_date,
                'is_alive': row.is_alive,
                'bio': row.bio,
                'photo': row.photo,
                'connections': json.loads(row.connections) if row.connections else {},
                'password_hash': row.password_hash,
                'email': row.email,
                'is_email_verified': row.is_email_verified,
                'invite_code': row.invite_code,
                'first_name': row.first_name,
                'last_name': row.last_name,
                'patronymic': row.patronymic,
                'maiden_name': row.maiden_name,
                'gender': row.gender
            }
        else:
            g.user = None

# --- МАРШРУТЫ СЕРВЕРА ---

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'en')
    
    def gettext(text):
        if lang == 'ru':
            return TRANSLATIONS.get('ru', {}).get(text, text)
        return text
        
    def format_date(date_str):
        if not date_str:
            return gettext('Unknown')
        try:
            parts = date_str.split('-')
            if len(parts) == 3:
                y, m, d = parts
                d = str(int(d))
                months_ru = ['', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                months_en = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                month = months_ru[int(m)] if lang == 'ru' else months_en[int(m)]
                if lang == 'ru':
                    return f"{d} {month} {y} года"
                else:
                    return f"{d} {month} {y}"
            elif len(parts) == 1:
                return date_str
        except:
            return date_str
        return date_str
        
    def calculate_age(birth_date, death_date, is_alive):
        if not birth_date:
            return ""
        try:
            b_date = datetime.strptime(birth_date, "%Y-%m-%d")
            if is_alive == 1 or not death_date:
                end_date = datetime.now()
            else:
                end_date = datetime.strptime(death_date, "%Y-%m-%d")
            
            age = end_date.year - b_date.year - ((end_date.month, end_date.day) < (b_date.month, b_date.day))
            
            if lang == 'ru':
                if age % 10 == 1 and age % 100 != 11:
                    suffix = "год"
                elif 2 <= age % 10 <= 4 and (age % 100 < 10 or age % 100 >= 20):
                    suffix = "года"
                else:
                    suffix = "лет"
                return f"({age} {suffix})"
            else:
                suffix = "years" if age != 1 else "year"
                return f"({age} {suffix})"
        except:
            return ""
            
    return dict(_=gettext, current_lang=lang, format_date=format_date, calculate_age=calculate_age)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'ru']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    if g.user:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/people')
def people():
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    root_id = request.args.get('root_id', g.user['id'])
    
    family_dict = calculate_relationships(tree_id, root_id)
    # Filter out deleted just in case, and convert to list
    family_list = [p for p in family_dict.values() if not p.get('is_deleted', 0)]
    
    # Sort by tier, then by birth year (if available), then by name
    def sort_key(p):
        tier = p.get('tier', 100)
        birth_year = p.get('birth_date', '9999')[-4:] if p.get('birth_date') else '9999'
        return (tier, birth_year, p.get('name', ''))
        
    family_list.sort(key=sort_key)
    
    return render_template('people.html', people=family_list)

@app.route('/family_tree')
def family_tree():
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    root_id = request.args.get('root_id', g.user['id'])
    
    root_person = Relative.query.filter_by(id=root_id, tree_id=tree_id, is_deleted=0).first()
    if not root_person:
        root_id = g.user['id']
        root_person = Relative.query.get(root_id)
    
    family = calculate_relationships(tree_id, root_id)
    
    parents_of = {pid: set() for pid in family}
    siblings_of = {pid: set() for pid in family}
    spouses_of = {pid: set() for pid in family}
    
    for pid, person in family.items():
        for target_id, role in person['connections'].items():
            if target_id in family:
                if role == 'child':
                    parents_of[target_id].add(pid)
                elif role == 'parent':
                    parents_of[pid].add(target_id)
                elif role == 'sibling':
                    siblings_of[pid].add(target_id)
                    siblings_of[target_id].add(pid)
                elif role == 'spouse':
                    spouses_of[pid].add(target_id)
                    spouses_of[target_id].add(pid)

    # Propagate parents across siblings
    for pid in family:
        for sib_id in siblings_of[pid]:
            all_parents = parents_of[pid].union(parents_of[sib_id])
            parents_of[pid] = all_parents
            parents_of[sib_id] = all_parents
            
    # Infer spouses from shared children
    for pid in family:
        p_parents = list(parents_of[pid])
        for i in range(len(p_parents)):
            for j in range(i + 1, len(p_parents)):
                spouses_of[p_parents[i]].add(p_parents[j])
                spouses_of[p_parents[j]].add(p_parents[i])

    edges = []
    for child_id, parent_ids in parents_of.items():
        for parent_id in parent_ids:
            parent_node = family.get(parent_id, {})
            edges.append({
                'from': parent_id, 
                'to': child_id, 
                'type': 'parent-child',
                'branch': parent_node.get('branch')
            })

    tiers = {}
    for pid, person in family.items():
        t = person['tier']
        if t not in tiers:
            tiers[t] = []
        tiers[t].append(person)

    tier_groups = {}
    for t, people in tiers.items():
        if t == 100:
            continue
            
        groups = []
        processed = set()
        for p in people:
            if p['id'] in processed:
                continue
                
            spouse = None
            for sid in spouses_of[p['id']]:
                if sid in family and family[sid]['tier'] == t and sid not in processed:
                    spouse = family[sid]
                    break
                    
            if spouse:
                groups.append({'type': 'couple', 'p1': p, 'p2': spouse})
                processed.add(p['id'])
                processed.add(spouse['id'])
            else:
                groups.append({'type': 'single', 'person': p})
                processed.add(p['id'])
        
        tier_groups[t] = groups
        
    return render_template('tree.html', tier_groups=tier_groups, edges_json=json.dumps(edges), root_person=root_person, current_root_id=root_id)

@app.route('/profile/<person_id>')
def profile(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    row = Relative.query.filter_by(id=person_id, tree_id=tree_id, is_deleted=0).first()
    
    if not row:
        return "Родственник не найден в архиве (или был удален)", 404
        
    person = {
        'id': row.id,
        'tree_id': row.tree_id,
        'name': row.name,
        'role': row.role,
        'years': row.years,
        'birth_date': row.birth_date,
        'death_date': row.death_date,
        'is_alive': row.is_alive,
        'bio': row.bio,
        'photo': row.photo,
        'connections': json.loads(row.connections) if row.connections else {},
        'password_hash': row.password_hash,
        'email': row.email,
        'invite_code': row.invite_code
    }
    
    family = calculate_relationships(tree_id, g.user['id'])
    person['calc_role'] = family.get(person_id, {}).get('calc_role', 'Родственник')
    
    # Predefined eras if none exist
    predefined_eras = [
        ('Первые воспоминания', 'Ранние образы, семейные рассказы о рождении и первых годах', '1900', '1920'),
        ('Детство', 'Игры, школа, семейные праздники и детские приключения', '1920', '1930'),
        ('Ранняя юность', 'Первые увлечения, дружба, старшая школа и взросление', '1930', '1940'),
        ('Поздняя юность', 'Студенчество, начало карьеры, любовь и первые шаги во взрослой жизни', '1940', '1950'),
        ('Зрелость', 'Создание семьи, главные достижения, путешествия и профессиональный путь', '1950', '1980'),
        ('Поздняя зрелость', 'Мудрость лет, внуки, семейные традиции и воспоминания', '1980', '2000')
    ]
    
    existing_eras = LifeEra.query.filter_by(tree_id=tree_id, target_person_id=person_id).all()
    if not existing_eras:
        for title, desc, sy, ey in predefined_eras:
            era = LifeEra(tree_id=tree_id, target_person_id=person_id, title=title, description=desc, start_year=sy, end_year=ey)
            db.session.add(era)
        db.session.commit()
        existing_eras = LifeEra.query.filter_by(tree_id=tree_id, target_person_id=person_id).all()
        
    eras_data = []
    for era in existing_eras:
        # Count events for this era
        events_count = LifeEvent.query.filter_by(target_person_id=person_id, life_stage=era.title).count()
        eras_data.append({
            'id': era.id,
            'title': era.title,
            'description': era.description,
            'start_year': era.start_year,
            'end_year': era.end_year,
            'cover_image': era.cover_image,
            'events_count': events_count
        })

    # Timeline events (all events ordered by year)
    all_events = LifeEvent.query.filter_by(target_person_id=person_id, tree_id=tree_id).all()
    timeline_events = []
    for ev in all_events:
        timeline_events.append({
            'id': ev.id,
            'title': ev.title,
            'description': ev.description,
            'category': ev.category,
            'event_year': ev.event_year,
            'life_stage': ev.life_stage
        })
    timeline_events.sort(key=lambda x: (1 if not x['event_year'] else 0, x['event_year'] or '', x['id']))

    # Memories
    memories_query = db.session.query(Memory, Relative.name.label('author_name'))\
        .join(Relative, Memory.author_id == Relative.id)\
        .filter(Memory.target_person_id == person_id, Memory.tree_id == tree_id).all()
        
    memories = []
    for mem, author_name in memories_query:
        memories.append({
            'id': mem.id,
            'content': mem.content,
            'memory_year': mem.memory_year,
            'photo_links': mem.photo_links,
            'video_link': mem.video_link,
            'audio_link': mem.audio_link,
            'author_name': author_name,
            'date': mem.created_at.strftime('%d.%m.%Y')
        })

    # Reflections
    reflections_query = db.session.query(Reflection, Relative.name.label('author_name'))\
        .join(Relative, Reflection.author_id == Relative.id)\
        .filter(Reflection.target_person_id == person_id, Reflection.tree_id == tree_id).all()
        
    reflections = []
    for ref, author_name in reflections_query:
        reflections.append({
            'id': ref.id,
            'question': ref.question,
            'answer': ref.answer,
            'year': ref.year,
            'author_name': author_name,
            'date': ref.created_at.strftime('%d.%m.%Y')
        })

    # Places
    places_query = Place.query.filter_by(target_person_id=person_id, tree_id=tree_id).all()
    places = [{'name': p.name, 'date_range': p.date_range, 'description': p.description} for p in places_query]

    # Important People
    important_people_query = ImportantPerson.query.filter_by(target_person_id=person_id, tree_id=tree_id).all()
    important_people = [{'name': ip.name, 'role_label': ip.role_label, 'period': ip.period, 'description': ip.description} for ip in important_people_query]

    # Immediate family for the sidebar
    immediate_family = []
    for conn_id, conn_role in person['connections'].items():
        if conn_id in family:
            rel = family[conn_id]
            gender = rel.get('gender')
            
            if conn_role == 'parent':
                display_role = 'Father' if gender == 'male' else 'Mother' if gender == 'female' else 'Parent'
            elif conn_role == 'child':
                display_role = 'Son' if gender == 'male' else 'Daughter' if gender == 'female' else 'Child'
            elif conn_role == 'spouse':
                display_role = 'Husband' if gender == 'male' else 'Wife' if gender == 'female' else 'Spouse'
            elif conn_role == 'sibling':
                display_role = 'Brother' if gender == 'male' else 'Sister' if gender == 'female' else 'Sibling'
            else:
                display_role = conn_role.capitalize()
                
            immediate_family.append({
                'id': rel['id'],
                'name': rel['name'],
                'photo': rel['photo'],
                'role': display_role,
            })

    return render_template('profile.html', data=person, person_id=person_id, family=family, 
                           eras=eras_data, timeline=timeline_events, 
                           memories=memories, reflections=reflections,
                           places=places, important_people=important_people, immediate_family=immediate_family)

@app.route('/era/<person_id>/<stage>')
def era(person_id, stage):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    row = Relative.query.filter_by(id=person_id, tree_id=tree_id, is_deleted=0).first()
    
    if not row:
        return "Родственник не найден в архиве (или был удален)", 404
        
    person = {
        'id': row.id,
        'name': row.name
    }
    
    # Получаем события через JOIN LifeEvent + Author Relative
    events_query = db.session.query(LifeEvent, Relative.name.label('author_name'))\
        .join(Relative, LifeEvent.author_id == Relative.id)\
        .filter(LifeEvent.target_person_id == person_id, LifeEvent.tree_id == tree_id)\
        .all()
        
    events = []
    for ev, author_name in events_query:
        contrib_count = EventContribution.query.filter_by(event_id=ev.id).count()
        events.append({
            'id': ev.id,
            'title': ev.title,
            'description': ev.description,
            'category': ev.category,
            'event_year': ev.event_year,
            'photo_links': ev.photo_links,
            'video_link': ev.video_link,
            'audio_link': ev.audio_link,
            'author_name': author_name,
            'formatted_date': ev.created_at.strftime('%d.%m.%Y'),
            'contributions_count': contrib_count
        })
        
    events.sort(key=lambda x: (1 if not x['event_year'] else 0, x['event_year'] or '', x['id']))
    
    era_obj = LifeEra.query.filter_by(tree_id=tree_id, target_person_id=person_id, title=stage).first()
    era_data = {
        'id': era_obj.id if era_obj else None,
        'title': era_obj.title if era_obj else stage,
        'description': era_obj.description if era_obj else '',
        'cover_image': era_obj.cover_image if era_obj else '',
        'start_year': era_obj.start_year if era_obj else '',
        'end_year': era_obj.end_year if era_obj else ''
    }
    
    return render_template('era.html', person=person, person_id=person_id, stage=stage, events=events, era_data=era_data)

@app.route('/edit_era/<era_id>', methods=['POST'])
def edit_era(era_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    era = LifeEra.query.filter_by(id=era_id, tree_id=tree_id).first()
    
    if not era:
        return "Эпоха не найдена", 404
        
    description = request.form.get('description')
    
    photo_file = request.files.get('cover_image')
    if photo_file and photo_file.filename != '':
        path = save_uploaded_file(photo_file)
        if path:
            era.cover_image = path
            
    if request.form.get('delete_cover'):
        era.cover_image = None
        
    if description is not None:
        era.description = description
        
    db.session.commit()
    flash('Эпоха успешно обновлена!', 'success')
    return redirect(url_for('era', person_id=era.target_person_id, stage=era.title))

@app.route('/add_memory/<person_id>', methods=['POST'])
def add_memory(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    content = request.form.get('content')
    memory_year = request.form.get('memory_year')
    if not content:
        flash('Текст воспоминания обязателен', 'error')
        return redirect(url_for('profile', person_id=person_id))
        
    photo_list = []
    uploaded_photos = request.files.getlist('photos')
    for file in uploaded_photos:
        path = save_uploaded_file(file)
        if path:
            photo_list.append(path)
            
    ext_photo_links = request.form.get('photo_links', '')
    if ext_photo_links:
        for link in ext_photo_links.split(','):
            clean = link.strip()
            if clean:
                photo_list.append(clean)
                
    photo_links_str = ','.join(photo_list) if photo_list else None
    
    video_path = save_uploaded_file(request.files.get('video_file'))
    if not video_path:
        video_path = request.form.get('video_link')
        
    audio_path = save_uploaded_file(request.files.get('audio_file'))
    if not audio_path:
        audio_path = request.form.get('audio_link')
        
    mem = Memory(
        tree_id=g.user['tree_id'],
        target_person_id=person_id,
        author_id=g.user['id'],
        content=content,
        memory_year=memory_year,
        photo_links=photo_links_str,
        video_link=video_path,
        audio_link=audio_path
    )
    db.session.add(mem)
    db.session.commit()
    flash('Воспоминание добавлено!', 'success')
    return redirect(url_for('profile', person_id=person_id))

@app.route('/add_reflection/<person_id>', methods=['POST'])
def add_reflection(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    question = request.form.get('question')
    answer = request.form.get('answer')
    year = request.form.get('year', str(datetime.utcnow().year))
    
    if not answer:
        flash('Ответ не может быть пустым', 'error')
        return redirect(url_for('profile', person_id=person_id))
        
    ref = Reflection(
        tree_id=g.user['tree_id'],
        target_person_id=person_id,
        author_id=g.user['id'],
        question=question or "О чем я думаю сейчас",
        answer=answer,
        year=year
    )
    db.session.add(ref)
    db.session.commit()
    flash('Запись добавлена!', 'success')
    return redirect(url_for('profile', person_id=person_id))

@app.route('/add_place/<person_id>', methods=['POST'])
def add_place(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    date_range = request.form.get('date_range')
    description = request.form.get('description')
    
    if not name:
        flash('Название места обязательно', 'error')
        return redirect(url_for('profile', person_id=person_id))
        
    place = Place(
        tree_id=g.user['tree_id'],
        target_person_id=person_id,
        name=name,
        date_range=date_range,
        description=description
    )
    db.session.add(place)
    db.session.commit()
    flash('Место добавлено!', 'success')
    return redirect(url_for('profile', person_id=person_id))

@app.route('/add_important_person/<person_id>', methods=['POST'])
def add_important_person(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    role_label = request.form.get('role_label')
    period = request.form.get('period')
    description = request.form.get('description')
    
    if not name or not role_label:
        flash('Имя и роль обязательны', 'error')
        return redirect(url_for('profile', person_id=person_id))
        
    ip = ImportantPerson(
        tree_id=g.user['tree_id'],
        target_person_id=person_id,
        name=name,
        role_label=role_label,
        period=period,
        description=description
    )
    db.session.add(ip)
    db.session.commit()
    flash('Важный человек добавлен!', 'success')
    return redirect(url_for('profile', person_id=person_id))

@app.route('/add_event_form/<person_id>')
def add_event_form(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    row = Relative.query.filter_by(id=person_id, tree_id=tree_id).first()
    if not row:
        return "Не найдено", 404
        
    # We will just redirect to the era page with the first predefined era to add an event for now
    # as creating a standalone add_event.html is redundant to the era form.
    # Alternatively, we can just render the era form by passing a default life_stage.
    first_era = LifeEra.query.filter_by(tree_id=tree_id, target_person_id=person_id).first()
    if first_era:
        return redirect(url_for('era', person_id=person_id, stage=first_era.title) + "#event-edit-block")
    else:
        return redirect(url_for('profile', person_id=person_id))

@app.route('/story/<person_id>')
def story(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    row = Relative.query.filter_by(id=person_id, tree_id=tree_id).first()
    if not row:
        return "Не найдено", 404
        
    person = {
        'id': row.id,
        'name': row.name,
        'birth_date': row.birth_date,
        'death_date': row.death_date,
        'photo': row.photo,
        'bio': row.bio
    }
    
    events = LifeEvent.query.filter_by(target_person_id=person_id, tree_id=tree_id).all()
    # Sort events chronologically
    events.sort(key=lambda x: (1 if not x.event_year else 0, x.event_year or '', x.id))
    
    return render_template('story.html', person=person, events=events)

@app.route('/add_event/<person_id>', methods=['POST'])
def add_event(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    title = request.form.get('title')
    life_stage = request.form.get('life_stage')
    category = request.form.get('category')
    description = request.form.get('description')
    event_year = request.form.get('event_year')
    author_id = g.user['id']
    
    if not title or not description or not life_stage:
        flash('Заполните все обязательные поля события', 'error')
        return redirect(url_for('era', person_id=person_id, stage=life_stage))
        
    photo_list = []
    uploaded_photos = request.files.getlist('photos')
    for file in uploaded_photos:
        path = save_uploaded_file(file)
        if path:
            photo_list.append(path)
            
    ext_photo_links = request.form.get('photo_links', '')
    if ext_photo_links:
        for link in ext_photo_links.split(','):
            clean = link.strip()
            if clean:
                photo_list.append(clean)
                
    photo_links_str = ','.join(photo_list) if photo_list else None
    
    video_path = save_uploaded_file(request.files.get('video_file'))
    if not video_path:
        video_path = request.form.get('video_link')
        
    audio_path = save_uploaded_file(request.files.get('audio_file'))
    if not audio_path:
        audio_path = request.form.get('audio_link')
        
    new_event = LifeEvent(
        tree_id=tree_id,
        target_person_id=person_id,
        author_id=author_id,
        life_stage=life_stage,
        title=title,
        description=description,
        category=category,
        event_year=event_year,
        photo_links=photo_links_str,
        video_link=video_path,
        audio_link=audio_path
    )
    db.session.add(new_event)
    db.session.commit()
    
    flash('Событие успешно создано!', 'success')
    return redirect(url_for('era', person_id=person_id, stage=life_stage))

@app.route('/event/<event_id>')
def event_detail(event_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    ev = LifeEvent.query.filter_by(id=event_id, tree_id=tree_id).first()
    if not ev:
        return "Событие не найдено", 404
        
    author = Relative.query.get(ev.author_id)
    event = {
        'id': ev.id,
        'target_person_id': ev.target_person_id,
        'author_id': ev.author_id,
        'life_stage': ev.life_stage,
        'title': ev.title,
        'description': ev.description,
        'category': ev.category,
        'event_year': ev.event_year,
        'photo_links': ev.photo_links,
        'video_link': ev.video_link,
        'audio_link': ev.audio_link,
        'author_name': author.name if author else "Неизвестно",
        'author_photo': author.photo if author else "avatar.jpg",
        'formatted_date': ev.created_at.strftime('%d.%m.%Y')
    }
    
    target = Relative.query.get(ev.target_person_id)
    target_person = {
        'id': target.id,
        'name': target.name
    } if target else None
    
    contrib_rows = db.session.query(EventContribution, Relative.name.label('author_name'), Relative.photo.label('author_photo'))\
        .join(Relative, EventContribution.author_id == Relative.id)\
        .filter(EventContribution.event_id == event_id)\
        .order_by(EventContribution.created_at.asc())\
        .all()
        
    contributions = []
    for c, author_name, author_photo in contrib_rows:
        contributions.append({
            'id': c.id,
            'author_id': c.author_id,
            'content': c.content,
            'photo_links': c.photo_links,
            'video_link': c.video_link,
            'audio_link': c.audio_link,
            'author_name': author_name,
            'author_photo': author_photo,
            'formatted_date': c.created_at.strftime('%d.%m.%Y')
        })
        
    return render_template('event.html', event=event, target_person=target_person, contributions=contributions)

@app.route('/add_contribution/<event_id>', methods=['POST'])
def add_contribution(event_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    ev = LifeEvent.query.filter_by(id=event_id, tree_id=tree_id).first()
    if not ev:
        return "Событие не найдено", 404
        
    content = request.form.get('content')
    author_id = g.user['id']
    
    if not content:
        flash('Текст воспоминания не может быть пустым', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
        
    photo_list = []
    uploaded_photos = request.files.getlist('photos')
    for file in uploaded_photos:
        path = save_uploaded_file(file)
        if path:
            photo_list.append(path)
            
    ext_photo_links = request.form.get('photo_links', '')
    if ext_photo_links:
        for link in ext_photo_links.split(','):
            clean = link.strip()
            if clean:
                photo_list.append(clean)
                
    photo_links_str = ','.join(photo_list) if photo_list else None
    
    video_path = save_uploaded_file(request.files.get('video_file'))
    if not video_path:
        video_path = request.form.get('video_link')
        
    audio_path = save_uploaded_file(request.files.get('audio_file'))
    if not audio_path:
        audio_path = request.form.get('audio_link')
        
    new_contrib = EventContribution(
        event_id=event_id,
        author_id=author_id,
        content=content,
        photo_links=photo_links_str,
        video_link=video_path,
        audio_link=audio_path
    )
    db.session.add(new_contrib)
    db.session.commit()
    
    flash('Воспоминание успешно добавлено к событию!', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/edit_event/<event_id>', methods=['POST'])
def edit_event(event_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    ev = LifeEvent.query.filter_by(id=event_id, tree_id=tree_id).first()
    if not ev:
        return "Событие не найдено", 404
        
    if ev.author_id != g.user['id']:
        return "У вас нет прав на редактирование этого события", 403
        
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    event_year = request.form.get('event_year')
    
    if not title or not description:
        flash('Название и описание не могут быть пустыми', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
        
    photo_list = []
    uploaded_photos = request.files.getlist('photos')
    has_new_uploads = False
    for file in uploaded_photos:
        path = save_uploaded_file(file)
        if path:
            photo_list.append(path)
            has_new_uploads = True
            
    ext_photo_links = request.form.get('photo_links', '')
    if ext_photo_links:
        for link in ext_photo_links.split(','):
            clean = link.strip()
            if clean:
                photo_list.append(clean)
    elif not has_new_uploads:
        photo_list = ev.photo_links.split(',') if ev.photo_links else []
        
    photo_links_str = ','.join(photo_list) if photo_list else None
    
    video_path = save_uploaded_file(request.files.get('video_file'))
    if not video_path:
        video_path = request.form.get('video_link')
        if not video_path and not request.form.get('delete_video'):
            video_path = ev.video_link
            
    audio_path = save_uploaded_file(request.files.get('audio_file'))
    if not audio_path:
        audio_path = request.form.get('audio_link')
        if not audio_path and not request.form.get('delete_audio'):
            audio_path = ev.audio_link
            
    ev.title = title
    ev.description = description
    ev.category = category
    ev.event_year = event_year
    ev.photo_links = photo_links_str
    ev.video_link = video_path
    ev.audio_link = audio_path
    
    db.session.commit()
    flash('Событие успешно обновлено!', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    ev = LifeEvent.query.filter_by(id=event_id, tree_id=tree_id).first()
    if not ev:
        return "Событие не найдено", 404
        
    if ev.author_id != g.user['id']:
        return "У вас нет прав на удаление этого события", 403
        
    stage = ev.life_stage
    person_id = ev.target_person_id
    
    EventContribution.query.filter_by(event_id=event_id).delete()
    db.session.delete(ev)
    db.session.commit()
    
    flash('Событие успешно удалено', 'success')
    return redirect(url_for('era', person_id=person_id, stage=stage))

@app.route('/edit_contribution/<contribution_id>', methods=['POST'])
def edit_contribution(contribution_id):
    if not g.user:
        return redirect(url_for('login'))
        
    c = EventContribution.query.get(contribution_id)
    if not c:
        return "Дополнение не найдено", 404
        
    if c.author_id != g.user['id']:
        return "У вас нет прав на редактирование этого воспоминания", 403
        
    content = request.form.get('content')
    event_id = c.event_id
    
    if not content:
        flash('Текст не может быть пустым', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
        
    photo_list = []
    uploaded_photos = request.files.getlist('photos')
    has_new_uploads = False
    for file in uploaded_photos:
        path = save_uploaded_file(file)
        if path:
            photo_list.append(path)
            has_new_uploads = True
            
    ext_photo_links = request.form.get('photo_links', '')
    if ext_photo_links:
        for link in ext_photo_links.split(','):
            clean = link.strip()
            if clean:
                photo_list.append(clean)
    elif not has_new_uploads:
        photo_list = c.photo_links.split(',') if c.photo_links else []
        
    photo_links_str = ','.join(photo_list) if photo_list else None
    
    video_path = save_uploaded_file(request.files.get('video_file'))
    if not video_path:
        video_path = request.form.get('video_link')
        if not video_path and not request.form.get('delete_video'):
            video_path = c.video_link
            
    audio_path = save_uploaded_file(request.files.get('audio_file'))
    if not audio_path:
        audio_path = request.form.get('audio_link')
        if not audio_path and not request.form.get('delete_audio'):
            audio_path = c.audio_link
            
    c.content = content
    c.photo_links = photo_links_str
    c.video_link = video_path
    c.audio_link = audio_path
    
    db.session.commit()
    flash('Воспоминание успешно обновлено!', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/delete_contribution/<contribution_id>', methods=['POST'])
def delete_contribution(contribution_id):
    if not g.user:
        return redirect(url_for('login'))
        
    c = EventContribution.query.get(contribution_id)
    if not c:
        return "Дополнение не найдено", 404
        
    if c.author_id != g.user['id']:
        return "У вас нет прав на удаление этого воспоминания", 403
        
    event_id = c.event_id
    db.session.delete(c)
    db.session.commit()
    
    flash('Воспоминание удалено', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/add', methods=['GET', 'POST'])
def add_relative():
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    target_id = request.args.get('target_id', g.user['id'])
    
    if request.method == 'POST':
        person_id = request.form.get('person_id', '').strip()
        photo_file = request.files.get('photo')
        photo_filename = "avatar.jpg"
        
        if photo_file and photo_file.filename != '':
            photo_filename = photo_file.filename
            photo_file.save(os.path.join('static', photo_filename))
            
        role = request.form.get('role')
        
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip()
        maiden_name = request.form.get('maiden_name', '').strip()
        gender = request.form.get('gender', 'male').strip()
        full_name = f"{last_name} {first_name} {patronymic}".strip()
        
        b_date = request.form.get('birth_date')
        d_date = request.form.get('death_date')
        is_alive = 1 if request.form.get('is_alive') else 0
        
        years_str = ""
        if b_date:
            b_year = b_date[:4]
            if is_alive:
                years_str = f"{b_year} - н.в."
            else:
                d_year = d_date[:4] if d_date else "?"
                years_str = f"{b_year} - {d_year}"
                
        new_rel = Relative(
            id=person_id,
            tree_id=tree_id,
            name=full_name,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            maiden_name=maiden_name,
            gender=gender,
            role=role,
            birth_date=b_date,
            death_date=d_date if not is_alive else None,
            is_alive=is_alive,
            years=years_str,
            bio=request.form.get('bio'),
            photo=photo_filename,
            connections=json.dumps({target_id: get_reverse_role(role)}, ensure_ascii=False)
        )
        db.session.add(new_rel)
        
        target_db = Relative.query.get(target_id)
        if target_db:
            target_connections = json.loads(target_db.connections) if target_db.connections else {}
            target_connections[person_id] = role
            target_db.connections = json.dumps(target_connections, ensure_ascii=False)
            if target_id == g.user['id']:
                g.user['connections'] = target_connections
        
        db.session.commit()
        
        return redirect(url_for('dashboard'))
        
    target_person = Relative.query.get(target_id) if target_id != g.user['id'] else None
    return render_template('add.html', target_person=target_person)

@app.route('/edit/<person_id>', methods=['GET', 'POST'])
def edit_relative(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    person_db = Relative.query.filter_by(id=person_id, tree_id=tree_id, is_deleted=0).first()
    
    if not person_db:
        return "Родственник не найден", 404
        
    # Разрешаем редактировать только свой профиль или профили тех, кто еще не зарегистрировался
    if g.user['id'] != person_id and person_db.password_hash:
        flash('У вас нет прав для редактирования профиля зарегистрированного пользователя', 'error')
        return redirect(url_for('profile', person_id=person_id))
    
    if not person_db:
        return "Родственник не найден", 404
        
    person = {
        'id': person_db.id,
        'name': person_db.name,
        'first_name': person_db.first_name,
        'last_name': person_db.last_name,
        'patronymic': person_db.patronymic,
        'maiden_name': person_db.maiden_name,
        'gender': person_db.gender,
        'role': person_db.role,
        'birth_date': person_db.birth_date,
        'death_date': person_db.death_date,
        'is_alive': person_db.is_alive,
        'years': person_db.years,
        'bio': person_db.bio,
        'photo': person_db.photo,
        'connections': json.loads(person_db.connections) if person_db.connections else {},
        'email': person_db.email
    }
        
    if request.method == 'POST':
        if g.user['id'] == person_id:
            new_email = request.form.get('email', '').strip()
            
            if new_email != person_db.email:
                email_row = Relative.query.filter(Relative.email == new_email, Relative.id != person_id).first()
                if email_row:
                    flash('Этот Email уже зарегистрирован другим пользователем', 'error')
                    return redirect(url_for('edit_relative', person_id=person_id))
                
                person_db.email = new_email
                person_db.is_email_verified = 0
                if new_email:
                    send_verification_email(new_email)
                    flash('На ваш новый email отправлено письмо с ссылкой для подтверждения.', 'info')

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            photo_filename = photo_file.filename
            photo_file.save(os.path.join('static', photo_filename))
            person_db.photo = photo_filename
            
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip()
        maiden_name = request.form.get('maiden_name', '').strip()
        gender = request.form.get('gender', 'male').strip()
        full_name = f"{last_name} {first_name} {patronymic}".strip()
        
        person_db.first_name = first_name
        person_db.last_name = last_name
        person_db.patronymic = patronymic
        person_db.maiden_name = maiden_name
        person_db.gender = gender
        person_db.name = full_name
        
        b_date = request.form.get('birth_date')
        d_date = request.form.get('death_date')
        is_alive = 1 if request.form.get('is_alive') else 0
        
        years_str = ""
        if b_date:
            b_year = b_date[:4]
            if is_alive:
                years_str = f"{b_year} - н.в."
            else:
                d_year = d_date[:4] if d_date else "?"
                years_str = f"{b_year} - {d_year}"
                
        person_db.birth_date = b_date
        person_db.death_date = d_date if not is_alive else None
        person_db.is_alive = is_alive
        person_db.years = years_str
        
        person_db.bio = request.form.get('bio')
        person_db.role = request.form.get('role')
            
        connections = json.loads(person_db.connections) if person_db.connections else {}
        for conn_id in list(connections.keys()):
            field_name = f'edit_conn_{conn_id}'
            if field_name in request.form:
                new_val = request.form.get(field_name).strip()
                if new_val:
                    connections[conn_id] = new_val
                else:
                    del connections[conn_id]

        new_conn_ids = request.form.getlist('new_connection_id[]')
        new_conn_roles = request.form.getlist('new_connection_role[]')
        
        for conn_id, conn_role in zip(new_conn_ids, new_conn_roles):
            conn_id = conn_id.strip() if conn_id else ""
            conn_role = conn_role.strip() if conn_role else ""
            if conn_id and conn_role:
                connections[conn_id] = conn_role
                
                b_rel = Relative.query.filter_by(id=conn_id, tree_id=tree_id).first()
                if b_rel:
                    b_connections = json.loads(b_rel.connections) if b_rel.connections else {}
                    b_connections[person_id] = get_reverse_role(conn_role)
                    b_rel.connections = json.dumps(b_connections, ensure_ascii=False)
            
        person_db.connections = json.dumps(connections, ensure_ascii=False)
        
        db.session.commit()
        return redirect(url_for('profile', person_id=person_id))
        
    all_family = get_all_active_family(tree_id)
    if person_id in all_family:
        del all_family[person_id]
        
    return render_template('edit.html', person_id=person_id, person=person, all_family=all_family)

@app.route('/delete/<person_id>', methods=['POST'])
def delete_relative(person_id):
    if not g.user or g.user['id'] != person_id:
        flash('У вас нет прав для удаления этого профиля', 'error')
        return redirect(url_for('profile', person_id=person_id))
        
    tree_id = g.user['tree_id']
    person_db = Relative.query.filter_by(id=person_id, tree_id=tree_id).first()
    if person_db:
        person_db.is_deleted = 1
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        person_id = request.form.get('person_id', '').strip()
        password = request.form.get('password')
        
        row = Relative.query.filter(
            (Relative.id == person_id) | (Relative.email == person_id)
        ).filter(Relative.is_deleted == 0).first()
        
        if row:
            if row.password_hash:
                if check_password_hash(row.password_hash, password):
                    session.clear()
                    session['user_id'] = row.id
                    return redirect(url_for('dashboard'))
                else:
                    flash('Неверный пароль', 'error')
            else:
                flash('Для этого профиля пароль еще не задан. Пожалуйста, зарегистрируйтесь.', 'error')
        else:
            flash('Пользователь с таким ID или Email не найден', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        person_id = request.form.get('person_id', '').strip()
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip()
        maiden_name = request.form.get('maiden_name', '').strip()
        gender = request.form.get('gender', 'male').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        full_name = f"{last_name} {first_name} {patronymic}".strip()
        
        if not person_id or not last_name or not first_name or not email or not password:
            flash('Пожалуйста, заполните все обязательные поля', 'error')
        elif password != confirm_password:
            flash('Пароли не совпадают', 'error')
        else:
            row = Relative.query.get(person_id)
            email_row = Relative.query.filter_by(email=email).first()
            
            if row:
                flash('Пользователь с таким ID уже существует', 'error')
            elif email_row:
                flash('Пользователь с таким Email уже зарегистрирован', 'error')
            else:
                # Создаем новое семейное дерево
                new_tree_id = str(uuid.uuid4())
                new_tree = Tree(id=new_tree_id, name=f"Древо {full_name}")
                db.session.add(new_tree)
                
                password_hash = generate_password_hash(password)
                new_rel = Relative(
                    id=person_id,
                    tree_id=new_tree_id,
                    name=full_name,
                    first_name=first_name,
                    last_name=last_name,
                    patronymic=patronymic,
                    maiden_name=maiden_name,
                    gender=gender,
                    role='Я',
                    years='',
                    bio='',
                    photo='avatar.jpg',
                    connections='{}',
                    password_hash=password_hash,
                    email=email,
                    is_email_verified=0
                )
                db.session.add(new_rel)
                db.session.commit()
                
                send_verification_email(email)
                flash('Регистрация успешна! На ваш email отправлено письмо с ссылкой для подтверждения.', 'info')
                
                session.clear()
                session['user_id'] = person_id
                return redirect(url_for('dashboard'))
                
    return render_template('register.html')

@app.route('/generate_invite/<person_id>')
def generate_invite(person_id):
    if not g.user:
        return redirect(url_for('login'))
        
    tree_id = g.user['tree_id']
    person_db = Relative.query.filter_by(id=person_id, tree_id=tree_id).first()
    
    if not person_db:
        return "Родственник не найден", 404
        
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    person_db.invite_code = code
    db.session.commit()
    
    flash('Код приглашения успешно создан!', 'success')
    return redirect(url_for('profile', person_id=person_id))

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        invite_code = request.form.get('invite_code', '').strip().upper()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not invite_code or not email or not password:
            flash('Заполните все обязательные поля', 'error')
        elif password != confirm_password:
            flash('Пароли не совпадают', 'error')
        else:
            email_row = Relative.query.filter_by(email=email).first()
            if email_row:
                flash('Пользователь с таким Email уже зарегистрирован в архиве', 'error')
            else:
                person_db = Relative.query.filter(
                    db.func.upper(Relative.invite_code) == invite_code,
                    Relative.is_deleted == 0
                ).first()
                
                if person_db:
                    password_hash = generate_password_hash(password)
                    person_db.password_hash = password_hash
                    person_db.invite_code = None
                    person_db.email = email
                    person_db.is_email_verified = 0
                    
                    db.session.commit()
                    
                    send_verification_email(email)
                    
                    session.clear()
                    session['user_id'] = person_db.id
                    flash('Профиль успешно активирован! На вашу почту отправлено письмо для подтверждения.', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Неверный код приглашения или профиль уже активирован', 'error')
                
    return render_template('join.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=86400  # 24 часа
        )
    except SignatureExpired:
        flash('Срок действия ссылки для подтверждения истек. Отправьте письмо заново.', 'error')
        return redirect(url_for('dashboard'))
    except BadSignature:
        flash('Недействительная ссылка для подтверждения.', 'error')
        return redirect(url_for('dashboard'))
        
    user = Relative.query.filter_by(email=email).first()
    if not user:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('home'))
        
    if user.is_email_verified:
        flash('Ваш email уже подтвержден!', 'info')
    else:
        user.is_email_verified = 1
        db.session.commit()
        flash('Ваш email успешно подтвержден!', 'success')
        
    return redirect(url_for('dashboard'))

@app.route('/resend_verification')
def resend_verification():
    if not g.user:
        return redirect(url_for('login'))
        
    if g.user['is_email_verified']:
        flash('Ваш email уже подтвержден.', 'info')
        return redirect(url_for('dashboard'))
        
    if g.user['email']:
        send_verification_email(g.user['email'])
        flash('Письмо с ссылкой для подтверждения отправлено повторно.', 'success')
    else:
        flash('В вашем профиле не указан email.', 'error')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)