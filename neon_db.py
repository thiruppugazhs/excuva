import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    psycopg2_available = True
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    psycopg2_available = False

def get_neon_connection_string():
    return os.environ.get('DATABASE_URL') or os.environ.get('NEON_DATABASE_URL')

def is_neon_enabled():
    conn_str = get_neon_connection_string()
    if not conn_str or not psycopg2_available:
        return False
    if '[YOUR_PASSWORD]' in conn_str or 'YOUR_PASSWORD' in conn_str or 'your_password' in conn_str:
        return False
    return True

def get_neon_connection():
    conn_str = get_neon_connection_string()
    if not conn_str or not psycopg2_available:
        return None
    try:
        # Standard Neon connection string includes sslmode=require
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"[Neon DB] Connection error: {e}")
        return None

def init_neon_db():
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT,
                    auth_provider VARCHAR(50) DEFAULT 'email',
                    avatar_url TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token VARCHAR(255) PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS password_resets (
                    token VARCHAR(255) PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS excuses (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    scenario TEXT NOT NULL,
                    urgency VARCHAR(50) NOT NULL,
                    recipient VARCHAR(100) NOT NULL,
                    tone VARCHAR(100) NOT NULL,
                    details TEXT,
                    primary_text TEXT NOT NULL,
                    variations_json TEXT DEFAULT '[]',
                    believability_score INTEGER DEFAULT 95,
                    risk_level VARCHAR(50) DEFAULT 'Low',
                    tips_json TEXT DEFAULT '[]',
                    is_favorite INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    doc_type VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    recipient VARCHAR(100) NOT NULL,
                    issue_date VARCHAR(100) NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    content_json TEXT NOT NULL,
                    is_favorite INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    default_tone VARCHAR(100) DEFAULT 'Professional',
                    default_recipient VARCHAR(100) DEFAULT 'Manager',
                    custom_api_key TEXT,
                    api_provider VARCHAR(50) DEFAULT 'built_in',
                    theme_preference VARCHAR(50) DEFAULT 'light',
                    email_notifications INTEGER DEFAULT 1
                );

                ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS api_provider VARCHAR(50) DEFAULT 'built_in';

                CREATE TABLE IF NOT EXISTS otp_codes (
                    id BIGSERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    otp_code VARCHAR(10) NOT NULL,
                    purpose VARCHAR(50) NOT NULL,
                    user_id BIGINT,
                    expires_at TIMESTAMPTZ NOT NULL,
                    verified INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                UPDATE user_settings SET theme_preference = 'light' WHERE theme_preference = 'dark' OR theme_preference = 'system' OR theme_preference IS NULL;
            ''')
            conn.commit()
            print("[Neon DB] Schema initialized successfully.")
            return True
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] Init schema failed: {e}")
        return False
    finally:
        conn.close()

# --- Neon User CRUD ---

def create_user(name, email, password=None, auth_provider='email', avatar_url=None):
    conn = get_neon_connection()
    if not conn:
        return None
    password_hash = generate_password_hash(password) if password else None
    email_clean = email.lower().strip()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''INSERT INTO users (name, email, password_hash, auth_provider, avatar_url)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING *''',
                (name.strip(), email_clean, password_hash, auth_provider, avatar_url)
            )
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    '''INSERT INTO user_settings (user_id) VALUES (%s)
                       ON CONFLICT (user_id) DO NOTHING''',
                    (user['id'],)
                )
            conn.commit()
            return dict(user) if user else None
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] create_user error: {e}")
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email.lower().strip(),))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        print(f"[Neon DB] get_user_by_email error: {e}")
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        print(f"[Neon DB] get_user_by_id error: {e}")
        return None
    finally:
        conn.close()

def update_user_profile(user_id, name, avatar_url=None):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            if avatar_url:
                cursor.execute(
                    'UPDATE users SET name = %s, avatar_url = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *',
                    (name.strip(), avatar_url, user_id)
                )
            else:
                cursor.execute(
                    'UPDATE users SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *',
                    (name.strip(), user_id)
                )
            user = cursor.fetchone()
            conn.commit()
            return dict(user) if user else None
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_user_profile error: {e}")
        return None
    finally:
        conn.close()

def change_user_password(user_id, old_password, new_password):
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    if user.get('password_hash') and not check_password_hash(user['password_hash'], old_password):
        return False, "Current password does not match"
    
    new_hash = generate_password_hash(new_password)
    conn = get_neon_connection()
    if not conn:
        return False, "Neon DB connection unavailable"
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s',
                (new_hash, user_id)
            )
            conn.commit()
            return True, "Password updated successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Update failed: {str(e)}"
    finally:
        conn.close()

def verify_user_credentials(email, password):
    user = get_user_by_email(email)
    if not user or not user.get('password_hash'):
        return None
    if check_password_hash(user['password_hash'], password):
        return user
    return None

# --- Neon Sessions ---

def create_session(user_id, remember_me=False):
    conn = get_neon_connection()
    if not conn:
        return None
    token = secrets.token_hex(32)
    duration_days = 30 if remember_me else 2
    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)',
                (token, user_id, expires_at)
            )
            conn.commit()
            return token
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] create_session error: {e}")
        return None
    finally:
        conn.close()

def get_session_user(token):
    if not token:
        return None
    conn = get_neon_connection()
    if not conn:
        return None
    now_utc = datetime.now(timezone.utc)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT u.id, u.name, u.email, u.auth_provider, u.avatar_url, u.created_at
                   FROM users u
                   JOIN sessions s ON u.id = s.user_id
                   WHERE s.token = %s AND s.expires_at > %s''',
                (token, now_utc)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        print(f"[Neon DB] get_session_user error: {e}")
        return None
    finally:
        conn.close()

def delete_session(token):
    conn = get_neon_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM sessions WHERE token = %s', (token,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] delete_session error: {e}")
    finally:
        conn.close()

# --- Neon Password Resets ---

def create_password_reset_token(user_id):
    conn = get_neon_connection()
    if not conn:
        return None
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO password_resets (token, user_id, expires_at) VALUES (%s, %s, %s)',
                (token, user_id, expires_at)
            )
            conn.commit()
            return token
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] create_password_reset_token error: {e}")
        return None
    finally:
        conn.close()

def verify_and_consume_reset_token(token, new_password):
    conn = get_neon_connection()
    if not conn:
        return False
    now_utc = datetime.now(timezone.utc)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM password_resets WHERE token = %s AND used = 0 AND expires_at > %s',
                (token, now_utc)
            )
            record = cursor.fetchone()
            if not record:
                return False
            
            user_id = record['user_id']
            new_hash = generate_password_hash(new_password)
            
            cursor.execute('UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s', (new_hash, user_id))
            cursor.execute('UPDATE password_resets SET used = 1 WHERE token = %s', (token,))
            cursor.execute('DELETE FROM sessions WHERE user_id = %s', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] verify_and_consume_reset_token error: {e}")
        return False
    finally:
        conn.close()

# --- Neon OTP Verification ---

def create_otp_code(email, purpose='account_verification', user_id=None):
    conn = get_neon_connection()
    if not conn:
        return None
    import random
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    email_clean = email.lower().strip()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE otp_codes SET verified = -1 WHERE email = %s AND purpose = %s AND verified = 0',
                (email_clean, purpose)
            )
            cursor.execute(
                'INSERT INTO otp_codes (email, otp_code, purpose, user_id, expires_at) VALUES (%s, %s, %s, %s, %s)',
                (email_clean, otp_code, purpose, user_id, expires_at)
            )
            conn.commit()
            return otp_code
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] create_otp_code error: {e}")
        return None
    finally:
        conn.close()

def verify_otp_code(email, otp_code, purpose='account_verification'):
    conn = get_neon_connection()
    if not conn:
        return False, "Database connection unavailable", None
    now_utc = datetime.now(timezone.utc)
    email_clean = email.lower().strip()
    code_clean = str(otp_code).strip()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT * FROM otp_codes 
                   WHERE email = %s AND otp_code = %s AND purpose = %s AND verified = 0 AND expires_at > %s
                   ORDER BY id DESC LIMIT 1''',
                (email_clean, code_clean, purpose, now_utc)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Invalid or expired verification code.", None
            cursor.execute('UPDATE otp_codes SET verified = 1 WHERE id = %s', (row['id'],))
            conn.commit()
            return True, "Verification successful.", row.get('user_id')
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] verify_otp_code error: {e}")
        return False, "Verification failed.", None
    finally:
        conn.close()

def reset_password_with_otp(email, otp_code, new_password):
    verified, msg, user_id = verify_otp_code(email, otp_code, purpose='password_reset')
    if not verified:
        return False, msg
    
    conn = get_neon_connection()
    if not conn:
        return False, "Database connection unavailable"
    try:
        new_hash = generate_password_hash(new_password)
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE email = %s',
                (new_hash, email.lower().strip())
            )
            cursor.execute(
                '''DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email = %s)''',
                (email.lower().strip(),)
            )
            conn.commit()
            return True, "Password reset successfully. You may now log in."
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] reset_password_with_otp error: {e}")
        return False, "Failed to update password."
    finally:
        conn.close()

# --- Neon Excuses CRUD ---

def save_excuse(user_id, scenario, urgency, recipient, tone, details, primary_text, variations=None, score=95, risk='Low', tips=None):
    conn = get_neon_connection()
    if not conn:
        return None
    vars_json = json.dumps(variations or [])
    tips_json = json.dumps(tips or [])
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO excuses (user_id, scenario, urgency, recipient, tone, details, primary_text, variations_json, believability_score, risk_level, tips_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            ''', (user_id, scenario, urgency, recipient, tone, details, primary_text, vars_json, score, risk, tips_json))
            row = cursor.fetchone()
            conn.commit()
            if not row:
                return None
            res = dict(row)
            res['variations'] = json.loads(res.get('variations_json') or '[]')
            res['tips'] = json.loads(res.get('tips_json') or '[]')
            return res
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] save_excuse error: {e}")
        return None
    finally:
        conn.close()

def get_excuse_by_id(excuse_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM excuses WHERE id = %s AND user_id = %s', (excuse_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res['variations'] = json.loads(res.get('variations_json') or '[]')
            res['tips'] = json.loads(res.get('tips_json') or '[]')
            return res
    except Exception as e:
        print(f"[Neon DB] get_excuse_by_id error: {e}")
        return None
    finally:
        conn.close()

def get_user_excuses(user_id, limit=50, favorites_only=False, search=''):
    conn = get_neon_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            query = 'SELECT * FROM excuses WHERE user_id = %s'
            params = [user_id]
            if favorites_only:
                query += ' AND is_favorite = 1'
            if search:
                query += ' AND (scenario ILIKE %s OR primary_text ILIKE %s OR recipient ILIKE %s)'
                pat = f'%{search}%'
                params.extend([pat, pat, pat])
            query += ' ORDER BY created_at DESC LIMIT %s'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item['variations'] = json.loads(item.get('variations_json') or '[]')
                item['tips'] = json.loads(item.get('tips_json') or '[]')
                results.append(item)
            return results
    except Exception as e:
        print(f"[Neon DB] get_user_excuses error: {e}")
        return []
    finally:
        conn.close()

def toggle_excuse_favorite(excuse_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE excuses SET is_favorite = (1 - is_favorite) WHERE id = %s AND user_id = %s RETURNING is_favorite',
                (excuse_id, user_id)
            )
            row = cursor.fetchone()
            conn.commit()
            return row['is_favorite'] == 1 if row else False
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] toggle_excuse_favorite error: {e}")
        return False
    finally:
        conn.close()

def update_excuse_text(excuse_id, user_id, primary_text):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE excuses SET primary_text = %s WHERE id = %s AND user_id = %s RETURNING *',
                (primary_text, excuse_id, user_id)
            )
            row = cursor.fetchone()
            conn.commit()
            if not row:
                return None
            res = dict(row)
            res['variations'] = json.loads(res.get('variations_json') or '[]')
            res['tips'] = json.loads(res.get('tips_json') or '[]')
            return res
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_excuse_text error: {e}")
        return None
    finally:
        conn.close()

def delete_excuse(excuse_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM excuses WHERE id = %s AND user_id = %s', (excuse_id, user_id))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] delete_excuse error: {e}")
        return False
    finally:
        conn.close()

def update_document_content(doc_id, user_id, title, content_dict):
    conn = get_neon_connection()
    if not conn:
        return None
    content_json = json.dumps(content_dict)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE documents SET title = %s, content_json = %s WHERE id = %s AND user_id = %s RETURNING *',
                (title, content_json, doc_id, user_id)
            )
            row = cursor.fetchone()
            conn.commit()
            if not row:
                return None
            doc = dict(row)
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            return doc
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_document_content error: {e}")
        return None
    finally:
        conn.close()

# --- Neon Documents CRUD ---

def save_document(user_id, doc_type, title, recipient, issue_date, organization, content_dict):
    conn = get_neon_connection()
    if not conn:
        return None
    content_json = json.dumps(content_dict)
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO documents (user_id, doc_type, title, recipient, issue_date, organization, content_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            ''', (user_id, doc_type, title, recipient, issue_date, organization, content_json))
            row = cursor.fetchone()
            conn.commit()
            if not row:
                return None
            doc = dict(row)
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            return doc
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] save_document error: {e}")
        return None
    finally:
        conn.close()

def get_document_by_id(doc_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM documents WHERE id = %s AND user_id = %s', (doc_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            doc = dict(row)
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            return doc
    except Exception as e:
        print(f"[Neon DB] get_document_by_id error: {e}")
        return None
    finally:
        conn.close()

def get_user_documents(user_id, limit=50, favorites_only=False):
    conn = get_neon_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            query = 'SELECT * FROM documents WHERE user_id = %s'
            params = [user_id]
            if favorites_only:
                query += ' AND is_favorite = 1'
            query += ' ORDER BY created_at DESC LIMIT %s'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                doc = dict(r)
                doc['content'] = json.loads(doc.get('content_json') or '{}')
                results.append(doc)
            return results
    except Exception as e:
        print(f"[Neon DB] get_user_documents error: {e}")
        return []
    finally:
        conn.close()

def toggle_document_favorite(doc_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE documents SET is_favorite = (1 - is_favorite) WHERE id = %s AND user_id = %s RETURNING is_favorite',
                (doc_id, user_id)
            )
            row = cursor.fetchone()
            conn.commit()
            return row['is_favorite'] == 1 if row else False
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] toggle_document_favorite error: {e}")
        return False
    finally:
        conn.close()

def delete_document(doc_id, user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM documents WHERE id = %s AND user_id = %s', (doc_id, user_id))
            affected = cursor.rowcount
            conn.commit()
            return affected > 0
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] delete_document error: {e}")
        return False
    finally:
        conn.close()

# --- Neon Settings & Dashboard ---

def get_user_settings(user_id):
    conn = get_neon_connection()
    if not conn:
        return {}
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM user_settings WHERE user_id = %s', (user_id,))
            row = cursor.fetchone()
            if not row:
                cursor.execute('INSERT INTO user_settings (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING', (user_id,))
                conn.commit()
                cursor.execute('SELECT * FROM user_settings WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
            return dict(row) if row else {}
    except Exception as e:
        print(f"[Neon DB] get_user_settings error: {e}")
        return {}
    finally:
        conn.close()

def update_user_settings(user_id, default_tone, default_recipient, theme_preference, custom_api_key=None, api_provider='built_in'):
    conn = get_neon_connection()
    if not conn:
        return {}
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO user_settings (user_id, default_tone, default_recipient, theme_preference, custom_api_key, api_provider)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    default_tone = EXCLUDED.default_tone,
                    default_recipient = EXCLUDED.default_recipient,
                    theme_preference = EXCLUDED.theme_preference,
                    custom_api_key = EXCLUDED.custom_api_key,
                    api_provider = EXCLUDED.api_provider
                RETURNING *
            ''', (user_id, default_tone, default_recipient, theme_preference, custom_api_key, api_provider))
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else {}
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_user_settings error: {e}")
        return {}
    finally:
        conn.close()

def get_user_dashboard_stats(user_id):
    conn = get_neon_connection()
    if not conn:
        return {'total_excuses': 0, 'total_documents': 0, 'total_favorites': 0, 'avg_believability': 96}
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as total_excuses FROM excuses WHERE user_id = %s', (user_id,))
            total_excuses = cursor.fetchone()['total_excuses']
            
            cursor.execute('SELECT COUNT(*) as total_docs FROM documents WHERE user_id = %s', (user_id,))
            total_docs = cursor.fetchone()['total_docs']
            
            cursor.execute('SELECT COUNT(*) as fav_excuses FROM excuses WHERE user_id = %s AND is_favorite = 1', (user_id,))
            fav_excuses = cursor.fetchone()['fav_excuses']
            
            cursor.execute('SELECT COUNT(*) as fav_docs FROM documents WHERE user_id = %s AND is_favorite = 1', (user_id,))
            fav_docs = cursor.fetchone()['fav_docs']
            
            cursor.execute('SELECT AVG(believability_score) as avg_score FROM excuses WHERE user_id = %s', (user_id,))
            avg_score_row = cursor.fetchone()['avg_score']
            avg_score = round(float(avg_score_row or 96))
            
            return {
                'total_excuses': int(total_excuses),
                'total_documents': int(total_docs),
                'total_favorites': int(fav_excuses + fav_docs),
                'avg_believability': avg_score
            }
    except Exception as e:
        print(f"[Neon DB] get_user_dashboard_stats error: {e}")
        return {'total_excuses': 0, 'total_documents': 0, 'total_favorites': 0, 'avg_believability': 96}
    finally:
        conn.close()

def delete_all_user_history(user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM excuses WHERE user_id = %s', (user_id,))
            cursor.execute('DELETE FROM documents WHERE user_id = %s', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] delete_all_user_history error: {e}")
        return False
    finally:
        conn.close()

def delete_user_account(user_id):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] delete_user_account error: {e}")
        return False
    finally:
        conn.close()

def update_user_profile(user_id, name, avatar_url=None):
    conn = get_neon_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            if avatar_url:
                cursor.execute(
                    'UPDATE users SET name = %s, avatar_url = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, name, email, auth_provider, avatar_url, created_at',
                    (name, avatar_url, user_id)
                )
            else:
                cursor.execute(
                    'UPDATE users SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id, name, email, auth_provider, avatar_url, created_at',
                    (name, user_id)
                )
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else None
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_user_profile error: {e}")
        return None
    finally:
        conn.close()

def update_user_password(user_id, password_hash):
    conn = get_neon_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s', (password_hash, user_id))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"[Neon DB] update_user_password error: {e}")
        return False
    finally:
        conn.close()
