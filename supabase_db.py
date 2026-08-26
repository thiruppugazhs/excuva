import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
    
    if url and key and create_client:
        try:
            _supabase_client = create_client(url, key)
            return _supabase_client
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            return None
    return None

def is_supabase_enabled():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
    return bool(url and key and create_client)

# --- Supabase User CRUD ---

def create_user(name, email, password=None, auth_provider='email', avatar_url=None):
    client = get_supabase_client()
    if not client:
        return None
    
    password_hash = generate_password_hash(password) if password else None
    email_clean = email.lower().strip()
    
    data = {
        'name': name.strip(),
        'email': email_clean,
        'password_hash': password_hash,
        'auth_provider': auth_provider,
        'avatar_url': avatar_url
    }
    
    try:
        res = client.table('users').insert(data).execute()
        if res.data and len(res.data) > 0:
            user = res.data[0]
            # Create user_settings entry
            client.table('user_settings').upsert({'user_id': user['id']}).execute()
            return user
        return None
    except Exception as e:
        print(f"Supabase create_user error: {e}")
        return None

def get_user_by_email(email):
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table('users').select('*').eq('email', email.lower().strip()).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print(f"Supabase get_user_by_email error: {e}")
    return None

def get_user_by_id(user_id):
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table('users').select('*').eq('id', user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print(f"Supabase get_user_by_id error: {e}")
    return None

def update_user_profile(user_id, name, avatar_url=None):
    client = get_supabase_client()
    if not client:
        return None
    update_data = {'name': name.strip(), 'updated_at': datetime.now(timezone.utc).isoformat()}
    if avatar_url:
        update_data['avatar_url'] = avatar_url
    try:
        res = client.table('users').update(update_data).eq('id', user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print(f"Supabase update_user_profile error: {e}")
    return get_user_by_id(user_id)

def change_user_password(user_id, old_password, new_password):
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    if user.get('password_hash') and not check_password_hash(user['password_hash'], old_password):
        return False, "Current password does not match"
    
    new_hash = generate_password_hash(new_password)
    client = get_supabase_client()
    if not client:
        return False, "Supabase connection unavailable"
    
    try:
        client.table('users').update({
            'password_hash': new_hash,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', user_id).execute()
        return True, "Password updated successfully"
    except Exception as e:
        return False, f"Update failed: {str(e)}"

def verify_user_credentials(email, password):
    user = get_user_by_email(email)
    if not user or not user.get('password_hash'):
        return None
    if check_password_hash(user['password_hash'], password):
        return user
    return None

# --- Supabase Session CRUD ---

def create_session(user_id, remember_me=False):
    client = get_supabase_client()
    if not client:
        return None
    token = secrets.token_hex(32)
    duration_days = 30 if remember_me else 2
    expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
    
    try:
        client.table('sessions').insert({
            'token': token,
            'user_id': user_id,
            'expires_at': expires_at
        }).execute()
        return token
    except Exception as e:
        print(f"Supabase create_session error: {e}")
        return None

def get_session_user(token):
    if not token:
        return None
    client = get_supabase_client()
    if not client:
        return None
    
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        res = client.table('sessions').select('user_id, expires_at').eq('token', token).gt('expires_at', now_str).execute()
        if res.data and len(res.data) > 0:
            user_id = res.data[0]['user_id']
            return get_user_by_id(user_id)
    except Exception as e:
        print(f"Supabase get_session_user error: {e}")
    return None

def delete_session(token):
    client = get_supabase_client()
    if not client:
        return
    try:
        client.table('sessions').delete().eq('token', token).execute()
    except Exception as e:
        print(f"Supabase delete_session error: {e}")

# --- Supabase Password Resets ---

def create_password_reset_token(user_id):
    client = get_supabase_client()
    if not client:
        return None
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    try:
        client.table('password_resets').insert({
            'token': token,
            'user_id': user_id,
            'expires_at': expires_at,
            'used': 0
        }).execute()
        return token
    except Exception as e:
        print(f"Supabase create_password_reset_token error: {e}")
        return None

def verify_and_consume_reset_token(token, new_password):
    client = get_supabase_client()
    if not client:
        return False
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        res = client.table('password_resets').select('*').eq('token', token).eq('used', 0).gt('expires_at', now_str).execute()
        if not res.data or len(res.data) == 0:
            return False
        
        record = res.data[0]
        user_id = record['user_id']
        new_hash = generate_password_hash(new_password)
        
        client.table('users').update({
            'password_hash': new_hash,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', user_id).execute()
        
        client.table('password_resets').update({'used': 1}).eq('token', token).execute()
        client.table('sessions').delete().eq('user_id', user_id).execute()
        return True
    except Exception as e:
        print(f"Supabase verify_and_consume_reset_token error: {e}")
        return False

# --- Supabase Excuses CRUD ---

def save_excuse(user_id, scenario, urgency, recipient, tone, details, primary_text, variations=None, score=95, risk='Low', tips=None):
    client = get_supabase_client()
    if not client:
        return None
    
    data = {
        'user_id': user_id,
        'scenario': scenario,
        'urgency': urgency,
        'recipient': recipient,
        'tone': tone,
        'details': details,
        'primary_text': primary_text,
        'variations_json': json.dumps(variations or []),
        'believability_score': score,
        'risk_level': risk,
        'tips_json': json.dumps(tips or []),
        'is_favorite': 0
    }
    
    try:
        res = client.table('excuses').insert(data).execute()
        if res.data and len(res.data) > 0:
            item = res.data[0]
            item['variations'] = json.loads(item.get('variations_json') or '[]')
            item['tips'] = json.loads(item.get('tips_json') or '[]')
            return item
    except Exception as e:
        print(f"Supabase save_excuse error: {e}")
    return None

def get_excuse_by_id(excuse_id, user_id):
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table('excuses').select('*').eq('id', excuse_id).eq('user_id', user_id).execute()
        if res.data and len(res.data) > 0:
            item = res.data[0]
            item['variations'] = json.loads(item.get('variations_json') or '[]')
            item['tips'] = json.loads(item.get('tips_json') or '[]')
            return item
    except Exception as e:
        print(f"Supabase get_excuse_by_id error: {e}")
    return None

def get_user_excuses(user_id, limit=50, favorites_only=False, search=''):
    client = get_supabase_client()
    if not client:
        return []
    try:
        query = client.table('excuses').select('*').eq('user_id', user_id)
        if favorites_only:
            query = query.eq('is_favorite', 1)
        if search:
            query = query.ilike('scenario', f'%{search}%')
        
        query = query.order('created_at', desc=True).limit(limit)
        res = query.execute()
        
        results = []
        for row in (res.data or []):
            item = dict(row)
            item['variations'] = json.loads(item.get('variations_json') or '[]')
            item['tips'] = json.loads(item.get('tips_json') or '[]')
            results.append(item)
        return results
    except Exception as e:
        print(f"Supabase get_user_excuses error: {e}")
        return []

def toggle_excuse_favorite(excuse_id, user_id):
    client = get_supabase_client()
    if not client:
        return False
    try:
        curr = get_excuse_by_id(excuse_id, user_id)
        if not curr:
            return False
        new_fav = 1 if not curr.get('is_favorite') else 0
        client.table('excuses').update({'is_favorite': new_fav}).eq('id', excuse_id).eq('user_id', user_id).execute()
        return new_fav == 1
    except Exception as e:
        print(f"Supabase toggle_excuse_favorite error: {e}")
        return False

def delete_excuse(excuse_id, user_id):
    client = get_supabase_client()
    if not client:
        return False
    try:
        res = client.table('excuses').delete().eq('id', excuse_id).eq('user_id', user_id).execute()
        return bool(res.data and len(res.data) > 0)
    except Exception as e:
        print(f"Supabase delete_excuse error: {e}")
        return False

# --- Supabase Documents CRUD ---

def save_document(user_id, doc_type, title, recipient, issue_date, organization, content_dict):
    client = get_supabase_client()
    if not client:
        return None
    data = {
        'user_id': user_id,
        'doc_type': doc_type,
        'title': title,
        'recipient': recipient,
        'issue_date': issue_date,
        'organization': organization,
        'content_json': json.dumps(content_dict),
        'is_favorite': 0
    }
    try:
        res = client.table('documents').insert(data).execute()
        if res.data and len(res.data) > 0:
            doc = res.data[0]
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            return doc
    except Exception as e:
        print(f"Supabase save_document error: {e}")
    return None

def get_document_by_id(doc_id, user_id):
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table('documents').select('*').eq('id', doc_id).eq('user_id', user_id).execute()
        if res.data and len(res.data) > 0:
            doc = res.data[0]
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            return doc
    except Exception as e:
        print(f"Supabase get_document_by_id error: {e}")
    return None

def get_user_documents(user_id, limit=50, favorites_only=False):
    client = get_supabase_client()
    if not client:
        return []
    try:
        query = client.table('documents').select('*').eq('user_id', user_id)
        if favorites_only:
            query = query.eq('is_favorite', 1)
        query = query.order('created_at', desc=True).limit(limit)
        res = query.execute()
        results = []
        for row in (res.data or []):
            doc = dict(row)
            doc['content'] = json.loads(doc.get('content_json') or '{}')
            results.append(doc)
        return results
    except Exception as e:
        print(f"Supabase get_user_documents error: {e}")
        return []

def toggle_document_favorite(doc_id, user_id):
    client = get_supabase_client()
    if not client:
        return False
    try:
        curr = get_document_by_id(doc_id, user_id)
        if not curr:
            return False
        new_fav = 1 if not curr.get('is_favorite') else 0
        client.table('documents').update({'is_favorite': new_fav}).eq('id', doc_id).eq('user_id', user_id).execute()
        return new_fav == 1
    except Exception as e:
        print(f"Supabase toggle_document_favorite error: {e}")
        return False

def delete_document(doc_id, user_id):
    client = get_supabase_client()
    if not client:
        return False
    try:
        res = client.table('documents').delete().eq('id', doc_id).eq('user_id', user_id).execute()
        return bool(res.data and len(res.data) > 0)
    except Exception as e:
        print(f"Supabase delete_document error: {e}")
        return False

# --- Supabase Settings & Dashboard ---

def get_user_settings(user_id):
    client = get_supabase_client()
    if not client:
        return {}
    try:
        res = client.table('user_settings').select('*').eq('user_id', user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        # Create default
        client.table('user_settings').upsert({'user_id': user_id}).execute()
        res = client.table('user_settings').select('*').eq('user_id', user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception as e:
        print(f"Supabase get_user_settings error: {e}")
    return {}

def update_user_settings(user_id, default_tone, default_recipient, theme_preference, custom_api_key=None):
    client = get_supabase_client()
    if not client:
        return {}
    try:
        client.table('user_settings').upsert({
            'user_id': user_id,
            'default_tone': default_tone,
            'default_recipient': default_recipient,
            'theme_preference': theme_preference,
            'custom_api_key': custom_api_key
        }).execute()
        return get_user_settings(user_id)
    except Exception as e:
        print(f"Supabase update_user_settings error: {e}")
        return {}

def get_user_dashboard_stats(user_id):
    client = get_supabase_client()
    if not client:
        return {'total_excuses': 0, 'total_documents': 0, 'total_favorites': 0, 'avg_believability': 96}
    try:
        excuses_res = client.table('excuses').select('id, believability_score, is_favorite').eq('user_id', user_id).execute()
        docs_res = client.table('documents').select('id, is_favorite').eq('user_id', user_id).execute()
        
        excuses = excuses_res.data or []
        docs = docs_res.data or []
        
        total_excuses = len(excuses)
        total_docs = len(docs)
        fav_excuses = sum(1 for e in excuses if e.get('is_favorite'))
        fav_docs = sum(1 for d in docs if d.get('is_favorite'))
        
        scores = [e.get('believability_score', 95) for e in excuses if e.get('believability_score')]
        avg_score = round(sum(scores) / len(scores)) if scores else 96
        
        return {
            'total_excuses': total_excuses,
            'total_documents': total_docs,
            'total_favorites': fav_excuses + fav_docs,
            'avg_believability': avg_score
        }
    except Exception as e:
        print(f"Supabase get_user_dashboard_stats error: {e}")
        return {'total_excuses': 0, 'total_documents': 0, 'total_favorites': 0, 'avg_believability': 96}
