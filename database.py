import sqlite3
import os
import secrets
import json
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import neon_db
import supabase_db

DB_DIR = '/tmp' if (os.environ.get('VERCEL') or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK)) else os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'excuse_ai.db')

def get_active_engine_name():
    if neon_db.is_neon_enabled():
        return "Neon PostgreSQL"
    if supabase_db.is_supabase_enabled():
        return "Supabase PostgreSQL"
    return "SQLite"

def is_using_neon():
    return neon_db.is_neon_enabled()

def is_using_supabase():
    return not is_using_neon() and supabase_db.is_supabase_enabled()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if is_using_neon():
        print("[DB] Initializing Neon PostgreSQL Database Engine...")
        neon_db.init_neon_db()
        return
    
    if is_using_supabase():
        print("[DB] Using Supabase Database Engine")
        return
    
    print("[DB] Using Local SQLite Database Engine")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        auth_provider TEXT DEFAULT 'email',
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Sessions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Password Reset Tokens Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_resets (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Excuses Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS excuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scenario TEXT NOT NULL,
        urgency TEXT NOT NULL,
        recipient TEXT NOT NULL,
        tone TEXT NOT NULL,
        details TEXT,
        primary_text TEXT NOT NULL,
        variations_json TEXT,
        believability_score INTEGER DEFAULT 95,
        risk_level TEXT DEFAULT 'Low',
        tips_json TEXT,
        is_favorite INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Supporting Documents Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        doc_type TEXT NOT NULL,
        title TEXT NOT NULL,
        recipient TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        organization TEXT NOT NULL,
        content_json TEXT NOT NULL,
        is_favorite INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # User Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        default_tone TEXT DEFAULT 'Professional',
        default_recipient TEXT DEFAULT 'Manager',
        custom_api_key TEXT,
        api_provider TEXT DEFAULT 'built_in',
        theme_preference TEXT DEFAULT 'light',
        email_notifications INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    try:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN api_provider TEXT DEFAULT 'built_in'")
    except Exception:
        pass

    # OTP Codes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        purpose TEXT NOT NULL,
        user_id INTEGER,
        expires_at TIMESTAMP NOT NULL,
        verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# --- Unified Auth & User Helpers ---

def create_user(name, email, password=None, auth_provider='email', avatar_url=None):
    if is_using_neon():
        return neon_db.create_user(name, email, password, auth_provider, avatar_url)
    if is_using_supabase():
        return supabase_db.create_user(name, email, password, auth_provider, avatar_url)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password) if password else None
    
    try:
        cursor.execute(
            '''INSERT INTO users (name, email, password_hash, auth_provider, avatar_url)
               VALUES (?, ?, ?, ?, ?)''',
            (name.strip(), email.lower().strip(), password_hash, auth_provider, avatar_url)
        )
        user_id = cursor.lastrowid
        cursor.execute(
            '''INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)''',
            (user_id,)
        )
        conn.commit()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    if is_using_neon():
        return neon_db.get_user_by_email(email)
    if is_using_supabase():
        return supabase_db.get_user_by_email(email)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower().strip(),))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    if is_using_neon():
        return neon_db.get_user_by_id(user_id)
    if is_using_supabase():
        return supabase_db.get_user_by_id(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_profile(user_id, name, avatar_url=None):
    if is_using_neon():
        return neon_db.update_user_profile(user_id, name, avatar_url)
    if is_using_supabase():
        return supabase_db.update_user_profile(user_id, name, avatar_url)
    conn = get_db_connection()
    cursor = conn.cursor()
    if avatar_url:
        cursor.execute('UPDATE users SET name = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (name.strip(), avatar_url, user_id))
    else:
        cursor.execute('UPDATE users SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (name.strip(), user_id))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def change_user_password(user_id, old_password, new_password):
    if is_using_neon():
        return neon_db.change_user_password(user_id, old_password, new_password)
    if is_using_supabase():
        return supabase_db.change_user_password(user_id, old_password, new_password)
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    if user['password_hash'] and not check_password_hash(user['password_hash'], old_password):
        return False, "Current password does not match"
    
    new_hash = generate_password_hash(new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Password updated successfully"

def verify_user_credentials(email, password):
    if is_using_neon():
        return neon_db.verify_user_credentials(email, password)
    if is_using_supabase():
        return supabase_db.verify_user_credentials(email, password)
    user = get_user_by_email(email)
    if not user or not user['password_hash']:
        return None
    if check_password_hash(user['password_hash'], password):
        return user
    return None

# --- Unified Session Management ---

def create_session(user_id, remember_me=False):
    if is_using_neon():
        return neon_db.create_session(user_id, remember_me)
    if is_using_supabase():
        return supabase_db.create_session(user_id, remember_me)
    conn = get_db_connection()
    cursor = conn.cursor()
    token = secrets.token_hex(32)
    duration_days = 30 if remember_me else 2
    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    
    cursor.execute(
        'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
        (token, user_id, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return token

def get_session_user(token):
    if not token:
        return None
    if is_using_neon():
        return neon_db.get_session_user(token)
    if is_using_supabase():
        return supabase_db.get_session_user(token)
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''SELECT u.id, u.name, u.email, u.auth_provider, u.avatar_url, u.created_at
           FROM users u
           JOIN sessions s ON u.id = s.user_id
           WHERE s.token = ? AND s.expires_at > ?''',
        (token, now_str)
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def delete_session(token):
    if is_using_neon():
        return neon_db.delete_session(token)
    if is_using_supabase():
        return supabase_db.delete_session(token)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()

# --- Unified Password Resets ---

def create_password_reset_token(user_id):
    if is_using_neon():
        return neon_db.create_password_reset_token(user_id)
    if is_using_supabase():
        return supabase_db.create_password_reset_token(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    cursor.execute(
        'INSERT INTO password_resets (token, user_id, expires_at) VALUES (?, ?, ?)',
        (token, user_id, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()
    return token

def verify_and_consume_reset_token(token, new_password):
    if is_using_neon():
        return neon_db.verify_and_consume_reset_token(token, new_password)
    if is_using_supabase():
        return supabase_db.verify_and_consume_reset_token(token, new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''SELECT * FROM password_resets
           WHERE token = ? AND used = 0 AND expires_at > ?''',
        (token, now_str)
    )
    record = cursor.fetchone()
    if not record:
        conn.close()
        return False
    
    user_id = record['user_id']
    new_hash = generate_password_hash(new_password)
    
    cursor.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_hash, user_id))
    cursor.execute('UPDATE password_resets SET used = 1 WHERE token = ?', (token,))
    cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

# --- Unified OTP Verification Helpers ---

def create_otp_code(email, purpose='account_verification', user_id=None):
    if is_using_neon():
        return neon_db.create_otp_code(email, purpose, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    import random
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    email_clean = email.lower().strip()
    cursor.execute(
        'UPDATE otp_codes SET verified = -1 WHERE email = ? AND purpose = ? AND verified = 0',
        (email_clean, purpose)
    )
    cursor.execute(
        'INSERT INTO otp_codes (email, otp_code, purpose, user_id, expires_at) VALUES (?, ?, ?, ?, ?)',
        (email_clean, otp_code, purpose, user_id, expires_at)
    )
    conn.commit()
    conn.close()
    return otp_code

def verify_otp_code(email, otp_code, purpose='account_verification'):
    if is_using_neon():
        return neon_db.verify_otp_code(email, otp_code, purpose)
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    email_clean = email.lower().strip()
    code_clean = str(otp_code).strip()
    cursor.execute(
        '''SELECT * FROM otp_codes 
           WHERE email = ? AND otp_code = ? AND purpose = ? AND verified = 0 AND expires_at > ?
           ORDER BY id DESC LIMIT 1''',
        (email_clean, code_clean, purpose, now_str)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Invalid or expired verification code.", None
    cursor.execute('UPDATE otp_codes SET verified = 1 WHERE id = ?', (row['id'],))
    conn.commit()
    user_id = row['user_id']
    conn.close()
    return True, "Verification successful.", user_id

def reset_password_with_otp(email, otp_code, new_password):
    if is_using_neon():
        return neon_db.reset_password_with_otp(email, otp_code, new_password)
    verified, msg, user_id = verify_otp_code(email, otp_code, purpose='password_reset')
    if not verified:
        return False, msg
    conn = get_db_connection()
    cursor = conn.cursor()
    new_hash = generate_password_hash(new_password)
    cursor.execute(
        'UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?',
        (new_hash, email.lower().strip())
    )
    cursor.execute(
        '''DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email = ?)''',
        (email.lower().strip(),)
    )
    conn.commit()
    conn.close()
    return True, "Password reset successfully. You may now log in."

# --- Unified Excuses CRUD ---

def save_excuse(user_id, scenario, urgency, recipient, tone, details, primary_text, variations=None, score=95, risk='Low', tips=None):
    if is_using_neon():
        return neon_db.save_excuse(user_id, scenario, urgency, recipient, tone, details, primary_text, variations, score, risk, tips)
    if is_using_supabase():
        return supabase_db.save_excuse(user_id, scenario, urgency, recipient, tone, details, primary_text, variations, score, risk, tips)
    conn = get_db_connection()
    cursor = conn.cursor()
    vars_json = json.dumps(variations) if variations else '[]'
    tips_json = json.dumps(tips) if tips else '[]'
    
    cursor.execute('''
        INSERT INTO excuses (user_id, scenario, urgency, recipient, tone, details, primary_text, variations_json, believability_score, risk_level, tips_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, scenario, urgency, recipient, tone, details, primary_text, vars_json, score, risk, tips_json))
    
    excuse_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_excuse_by_id(excuse_id, user_id)

def get_excuse_by_id(excuse_id, user_id):
    if is_using_neon():
        return neon_db.get_excuse_by_id(excuse_id, user_id)
    if is_using_supabase():
        return supabase_db.get_excuse_by_id(excuse_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM excuses WHERE id = ? AND user_id = ?', (excuse_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    res['variations'] = json.loads(res['variations_json'] or '[]')
    res['tips'] = json.loads(res['tips_json'] or '[]')
    return res

def get_user_excuses(user_id, limit=50, favorites_only=False, search=''):
    if is_using_neon():
        return neon_db.get_user_excuses(user_id, limit, favorites_only, search)
    if is_using_supabase():
        return supabase_db.get_user_excuses(user_id, limit, favorites_only, search)
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM excuses WHERE user_id = ?'
    params = [user_id]
    
    if favorites_only:
        query += ' AND is_favorite = 1'
    if search:
        query += ' AND (scenario LIKE ? OR primary_text LIKE ? OR recipient LIKE ?)'
        pattern = f'%{search}%'
        params.extend([pattern, pattern, pattern])
        
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item['variations'] = json.loads(item['variations_json'] or '[]')
        item['tips'] = json.loads(item['tips_json'] or '[]')
        results.append(item)
    return results

def toggle_excuse_favorite(excuse_id, user_id):
    if is_using_neon():
        return neon_db.toggle_excuse_favorite(excuse_id, user_id)
    if is_using_supabase():
        return supabase_db.toggle_excuse_favorite(excuse_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE excuses SET is_favorite = (1 - is_favorite) WHERE id = ? AND user_id = ?', (excuse_id, user_id))
    conn.commit()
    cursor.execute('SELECT is_favorite FROM excuses WHERE id = ? AND user_id = ?', (excuse_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return row['is_favorite'] == 1 if row else False

def update_excuse_text(excuse_id, user_id, primary_text):
    if is_using_neon():
        return neon_db.update_excuse_text(excuse_id, user_id, primary_text)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE excuses SET primary_text = ? WHERE id = ? AND user_id = ?', (primary_text, excuse_id, user_id))
    conn.commit()
    conn.close()
    return get_excuse_by_id(excuse_id, user_id)

def delete_excuse(excuse_id, user_id):
    if is_using_neon():
        return neon_db.delete_excuse(excuse_id, user_id)
    if is_using_supabase():
        return supabase_db.delete_excuse(excuse_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM excuses WHERE id = ? AND user_id = ?', (excuse_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def update_document_content(doc_id, user_id, title, content_dict):
    if is_using_neon():
        return neon_db.update_document_content(doc_id, user_id, title, content_dict)
    conn = get_db_connection()
    cursor = conn.cursor()
    content_json = json.dumps(content_dict)
    cursor.execute('UPDATE documents SET title = ?, content_json = ? WHERE id = ? AND user_id = ?', (title, content_json, doc_id, user_id))
    conn.commit()
    conn.close()
    return get_document_by_id(doc_id, user_id)

# --- Unified Documents CRUD ---

def save_document(user_id, doc_type, title, recipient, issue_date, organization, content_dict):
    if is_using_neon():
        return neon_db.save_document(user_id, doc_type, title, recipient, issue_date, organization, content_dict)
    if is_using_supabase():
        return supabase_db.save_document(user_id, doc_type, title, recipient, issue_date, organization, content_dict)
    conn = get_db_connection()
    cursor = conn.cursor()
    content_json = json.dumps(content_dict)
    
    cursor.execute('''
        INSERT INTO documents (user_id, doc_type, title, recipient, issue_date, organization, content_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, doc_type, title, recipient, issue_date, organization, content_json))
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_document_by_id(doc_id, user_id)

def get_document_by_id(doc_id, user_id):
    if is_using_neon():
        return neon_db.get_document_by_id(doc_id, user_id)
    if is_using_supabase():
        return supabase_db.get_document_by_id(doc_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', (doc_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    res['content'] = json.loads(res['content_json'] or '{}')
    return res

def get_user_documents(user_id, limit=50, favorites_only=False):
    if is_using_neon():
        return neon_db.get_user_documents(user_id, limit, favorites_only)
    if is_using_supabase():
        return supabase_db.get_user_documents(user_id, limit, favorites_only)
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM documents WHERE user_id = ?'
    params = [user_id]
    if favorites_only:
        query += ' AND is_favorite = 1'
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item['content'] = json.loads(item['content_json'] or '{}')
        results.append(item)
    return results

def toggle_document_favorite(doc_id, user_id):
    if is_using_neon():
        return neon_db.toggle_document_favorite(doc_id, user_id)
    if is_using_supabase():
        return supabase_db.toggle_document_favorite(doc_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE documents SET is_favorite = (1 - is_favorite) WHERE id = ? AND user_id = ?', (doc_id, user_id))
    conn.commit()
    cursor.execute('SELECT is_favorite FROM documents WHERE id = ? AND user_id = ?', (doc_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return row['is_favorite'] == 1 if row else False

def delete_document(doc_id, user_id):
    if is_using_neon():
        return neon_db.delete_document(doc_id, user_id)
    if is_using_supabase():
        return supabase_db.delete_document(doc_id, user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM documents WHERE id = ? AND user_id = ?', (doc_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# --- Unified Settings & Dashboard ---

def get_user_settings(user_id):
    if is_using_neon():
        return neon_db.get_user_settings(user_id)
    if is_using_supabase():
        return supabase_db.get_user_settings(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)', (user_id,))
        conn.commit()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_user_settings(user_id, default_tone, default_recipient, theme_preference, custom_api_key=None, api_provider='built_in'):
    if is_using_neon():
        return neon_db.update_user_settings(user_id, default_tone, default_recipient, theme_preference, custom_api_key, api_provider)
    if is_using_supabase():
        return supabase_db.update_user_settings(user_id, default_tone, default_recipient, theme_preference, custom_api_key, api_provider)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_settings
        SET default_tone = ?, default_recipient = ?, theme_preference = ?, custom_api_key = ?, api_provider = ?
        WHERE user_id = ?
    ''', (default_tone, default_recipient, theme_preference, custom_api_key, api_provider, user_id))
    conn.commit()
    conn.close()
    return get_user_settings(user_id)

def delete_all_user_history(user_id):
    if is_using_neon():
        return neon_db.delete_all_user_history(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM excuses WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM documents WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

def delete_user_account(user_id):
    if is_using_neon():
        return neon_db.delete_user_account(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

def update_user_profile(user_id, name, avatar_url=None):
    if is_using_neon():
        return neon_db.update_user_profile(user_id, name, avatar_url)
    conn = get_db_connection()
    cursor = conn.cursor()
    if avatar_url:
        cursor.execute('UPDATE users SET name = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (name, avatar_url, user_id))
    else:
        cursor.execute('UPDATE users SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (name, user_id))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)

def update_user_password(user_id, password_hash):
    if is_using_neon():
        return neon_db.update_user_password(user_id, password_hash)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (password_hash, user_id))
    conn.commit()
    conn.close()
    return True

def get_user_dashboard_stats(user_id):
    if is_using_neon():
        return neon_db.get_user_dashboard_stats(user_id)
    if is_using_supabase():
        return supabase_db.get_user_dashboard_stats(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total_excuses FROM excuses WHERE user_id = ?', (user_id,))
    total_excuses = cursor.fetchone()['total_excuses']
    
    cursor.execute('SELECT COUNT(*) as total_docs FROM documents WHERE user_id = ?', (user_id,))
    total_docs = cursor.fetchone()['total_docs']
    
    cursor.execute('SELECT COUNT(*) as fav_excuses FROM excuses WHERE user_id = ? AND is_favorite = 1', (user_id,))
    fav_excuses = cursor.fetchone()['fav_excuses']
    
    cursor.execute('SELECT COUNT(*) as fav_docs FROM documents WHERE user_id = ? AND is_favorite = 1', (user_id,))
    fav_docs = cursor.fetchone()['fav_docs']
    
    cursor.execute('SELECT AVG(believability_score) as avg_score FROM excuses WHERE user_id = ?', (user_id,))
    avg_score_row = cursor.fetchone()['avg_score']
    avg_score = round(avg_score_row or 96)
    
    conn.close()
    return {
        'total_excuses': total_excuses,
        'total_documents': total_docs,
        'total_favorites': fav_excuses + fav_docs,
        'avg_believability': avg_score
    }

try:
    init_db()
except Exception as e:
    print(f"[DB] Database initialization notice: {e}")
