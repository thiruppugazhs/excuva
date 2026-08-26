import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
import database as db
import ai_engine
import storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='')
CORS(app)

def send_email_via_resend(to_email, subject, html_content):
    resend_key = os.environ.get('RESEND_API_KEY')
    if not resend_key:
        print("[Resend] No RESEND_API_KEY set, skipping email dispatch.")
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Excuva <onboarding@resend.dev>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            },
            timeout=10
        )
        if resp.status_code in [200, 201]:
            print(f"[Resend] Email successfully sent to {to_email}")
            return True
        else:
            print(f"[Resend] Email dispatch error: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"[Resend] Email dispatch exception: {e}")
        return False

def send_otp_email(to_email, otp_code, purpose="account_verification", name="User"):
    if purpose == "account_verification":
        subject = f"{otp_code} is your Excuva verification code"
        title = "Verify Your Excuva Account"
        msg = f"Thank you for signing up for Excuva. Please use the 6-digit verification code below to activate your account:"
    else:
        subject = f"{otp_code} is your Excuva password verification code"
        title = "Excuva Password Verification Code"
        msg = f"We received a request to change/reset the password for your Excuva account. Enter the 6-digit code below to proceed:"

    email_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px; background: #fbf9f5; border: 1px solid #e8dfd3; border-radius: 16px; color: #1c1815;">
      <h2 style="color: #854d0e; margin: 0 0 16px; font-size: 24px; font-weight: 800;">Excuva</h2>
      <h3 style="color: #1c1815; margin: 0 0 12px; font-size: 18px;">{title}</h3>
      <p style="color: #574e46; line-height: 1.6; font-size: 14px;">Hello {name},</p>
      <p style="color: #574e46; line-height: 1.6; font-size: 14px;">{msg}</p>
      <div style="text-align: center; margin: 28px 0;">
        <div style="display: inline-block; background-color: #f6efe6; border: 2px dashed #b45309; padding: 14px 32px; border-radius: 12px; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #78350f; font-family: monospace;">
          {otp_code}
        </div>
      </div>
      <p style="color: #8c8075; font-size: 12px; line-height: 1.5; text-align: center;">This verification code is valid for 10 minutes. If you did not make this request, you can safely ignore this message.</p>
    </div>
    """
    return send_email_via_resend(to_email, subject, email_html)

def get_auth_user():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        return db.get_session_user(token)
    return None

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

# Serve Frontend
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Health Check & DB Status
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'database': db.get_active_engine_name(),
        'is_neon': db.is_using_neon(),
        'is_supabase': db.is_using_supabase()
    })

@app.route('/api/system/db-status')
def db_status():
    return jsonify({
        'database_engine': db.get_active_engine_name(),
        'is_neon': db.is_using_neon(),
        'is_supabase': db.is_using_supabase(),
        'neon_configured': bool(os.environ.get('DATABASE_URL') or os.environ.get('NEON_DATABASE_URL')),
        'supabase_configured': bool(os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY'))
    })

# ----------------- AUTHENTICATION ENDPOINTS -----------------

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    terms_accepted = data.get('terms_accepted', False)

    if not name:
        return jsonify({'error': 'Full name is required.'}), 400
    if not email or not is_valid_email(email):
        return jsonify({'error': 'Please provide a valid email address.'}), 400
    if db.get_user_by_email(email):
        return jsonify({'error': 'An account with this email address already exists.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters in length.'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400
    if not terms_accepted:
        return jsonify({'error': 'You must agree to the Terms of Service and Privacy Policy.'}), 400

    user = db.create_user(name=name, email=email, password=password, auth_provider='email')
    if not user:
        return jsonify({'error': 'Failed to create user account. Please try again.'}), 500

    token = db.create_session(user['id'], remember_me=True)
    return jsonify({
        'message': 'Account created successfully.',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'avatar_url': user.get('avatar_url')
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)

    if not email or not password:
        return jsonify({'error': 'Incorrect email or password.'}), 401

    user = db.verify_user_credentials(email, password)
    if not user:
        return jsonify({'error': 'Incorrect email or password.'}), 401

    token = db.create_session(user['id'], remember_me=remember_me)
    return jsonify({
        'message': 'Login successful.',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'avatar_url': user.get('avatar_url')
        }
    })

@app.route('/api/auth/google', methods=['POST'])
def google_oauth():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    name = data.get('name', 'Google User').strip()
    avatar_url = data.get('avatar_url', '')

    if not email:
        return jsonify({'error': 'Google authentication failed: Email not provided.'}), 400

    user = db.get_user_by_email(email)
    if not user:
        user = db.create_user(name=name, email=email, auth_provider='google', avatar_url=avatar_url)
        if not user:
            return jsonify({'error': 'Could not create account with Google credentials.'}), 500

    token = db.create_session(user['id'], remember_me=True)
    return jsonify({
        'message': 'Google authentication successful.',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'avatar_url': user.get('avatar_url')
        }
    })

@app.route('/api/auth/send-registration-otp', methods=['POST'])
def send_registration_otp():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not name:
        return jsonify({'error': 'Full name is required.'}), 400
    if not email or not is_valid_email(email):
        return jsonify({'error': 'Please provide a valid email address.'}), 400
    if db.get_user_by_email(email):
        return jsonify({'error': 'An account with this email address already exists.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters in length.'}), 400

    otp_code = db.create_otp_code(email, purpose='account_verification')
    send_otp_email(email, otp_code, purpose='account_verification', name=name)

    return jsonify({
        'message': f'A 6-digit verification code has been dispatched to {email}.',
        'email': email,
        'debug_otp': otp_code
    })

@app.route('/api/auth/verify-registration-otp', methods=['POST'])
def verify_registration_otp():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    otp_code = data.get('otp_code', '').strip()

    if not email or not otp_code:
        return jsonify({'error': 'Email and verification code are required.'}), 400

    verified, msg, _ = db.verify_otp_code(email, otp_code, purpose='account_verification')
    if not verified:
        return jsonify({'error': msg}), 400

    user = db.get_user_by_email(email)
    if not user:
        user = db.create_user(name=name or 'User', email=email, password=password, auth_provider='email')
        if not user:
            return jsonify({'error': 'Failed to create user account.'}), 500

    token = db.create_session(user['id'], remember_me=True)
    return jsonify({
        'message': 'Account verified and created successfully.',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'avatar_url': user.get('avatar_url')
        }
    }), 201

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    if not email or not is_valid_email(email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    user = db.get_user_by_email(email)
    otp_code = None
    if user:
        otp_code = db.create_otp_code(email, purpose='password_reset', user_id=user['id'])
        send_otp_email(email, otp_code, purpose='password_reset', name=user.get('name', 'User'))

    return jsonify({
        'message': f'If an account exists for {email}, a 6-digit password verification code has been dispatched.',
        'email': email,
        'debug_otp': otp_code
    })

@app.route('/api/auth/reset-password-otp', methods=['POST'])
def reset_password_otp():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    otp_code = data.get('otp_code', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not email or not otp_code:
        return jsonify({'error': 'Email and verification code are required.'}), 400
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters.'}), 400
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    success, msg = db.reset_password_with_otp(email, otp_code, new_password)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg})

@app.route('/api/user/request-password-otp', methods=['POST'])
def user_request_password_otp():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    otp_code = db.create_otp_code(user['email'], purpose='password_reset', user_id=user['id'])
    send_otp_email(user['email'], otp_code, purpose='password_reset', name=user.get('name', 'User'))

    return jsonify({
        'message': f'A 6-digit security code has been dispatched to {user["email"]}.',
        'debug_otp': otp_code
    })

@app.route('/api/user/verify-password-otp', methods=['POST'])
def user_verify_password_otp():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    otp_code = data.get('otp_code', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not otp_code:
        return jsonify({'error': 'Verification code is required.'}), 400
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters.'}), 400
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    success, msg = db.reset_password_with_otp(user['email'], otp_code, new_password)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': 'Your password has been updated securely.'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'user': user})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        db.delete_session(token)
    return jsonify({'message': 'Logged out successfully.'})

# ----------------- EXCUSE GENERATION ENDPOINTS -----------------

@app.route('/api/excuses/generate', methods=['POST'])
def generate_excuse():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please log in to generate an excuse.'}), 401

    data = request.get_json() or {}
    scenario = data.get('scenario', '').strip()
    recipient = data.get('recipient', 'Manager').strip()
    situation_type = data.get('situation_type', 'Missed deadline').strip()
    tone = data.get('tone', 'Professional').strip()
    length = data.get('length', 'Medium').strip()
    delivery_method = data.get('delivery_method', 'Email').strip()
    urgency = data.get('urgency', 'medium').lower()
    details = data.get('details', '').strip()

    if not scenario:
        return jsonify({'error': 'Please describe the situation.'}), 400

    # Check for custom Gemini API key or environment variable
    settings = db.get_user_settings(user['id'])
    api_key = settings.get('custom_api_key') or os.getenv('GOOGLE_API_KEY')

    result = None
    if api_key:
        result = ai_engine.generate_excuse_with_gemini(
            api_key=api_key,
            scenario=scenario,
            recipient=recipient,
            situation_type=situation_type,
            tone=tone,
            length=length,
            delivery_method=delivery_method,
            user_name=user['name'],
            details=details
        )

    if not result:
        result = ai_engine.generate_excuse_contextual(
            scenario=scenario,
            recipient=recipient,
            situation_type=situation_type,
            tone=tone,
            length=length,
            delivery_method=delivery_method,
            user_name=user['name'],
            details=details
        )

    saved = db.save_excuse(
        user_id=user['id'],
        scenario=scenario,
        urgency=urgency,
        recipient=recipient,
        tone=tone,
        details=f"Type: {situation_type} | Length: {length} | Channel: {delivery_method}",
        primary_text=result['primary_text'],
        variations=result.get('variations', []),
        score=result.get('believability_score', 95),
        risk=result.get('risk_level', 'Low'),
        tips=result.get('tips', [])
    )

    if saved:
        saved['situation_type'] = situation_type
        saved['length'] = length
        saved['delivery_method'] = delivery_method

    return jsonify({'excuse': saved}), 201

@app.route('/api/excuses/rewrite', methods=['POST'])
def rewrite_excuse():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    original_text = data.get('text', '').strip()
    instruction = data.get('instruction', 'Make it more concise').strip()
    tone = data.get('tone', 'Professional').strip()

    if not original_text:
        return jsonify({'error': 'Original text is required.'}), 400

    settings = db.get_user_settings(user['id'])
    api_key = settings.get('custom_api_key') or os.getenv('GOOGLE_API_KEY')

    rewritten = None
    if api_key:
        rewritten = ai_engine.rewrite_excuse_with_gemini(
            api_key=api_key,
            original_text=original_text,
            instruction=instruction,
            tone=tone,
            user_name=user['name']
        )

    if not rewritten:
        rewritten = ai_engine.rewrite_excuse_contextual(original_text, instruction)

    return jsonify({'rewritten_text': rewritten})

@app.route('/api/excuses', methods=['GET'])
def list_excuses():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    search = request.args.get('search', '').strip()
    favorites_only = request.args.get('favorites', 'false').lower() == 'true'
    excuses = db.get_user_excuses(user['id'], limit=100, favorites_only=favorites_only, search=search)
    return jsonify({'excuses': excuses})

@app.route('/api/excuses/<int:excuse_id>/favorite', methods=['POST'])
def favorite_excuse(excuse_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    is_fav = db.toggle_excuse_favorite(excuse_id, user['id'])
    return jsonify({'is_favorite': is_fav})

@app.route('/api/excuses/<int:excuse_id>', methods=['PUT'])
def edit_excuse(excuse_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    primary_text = data.get('primary_text', '').strip()
    if not primary_text:
        return jsonify({'error': 'Primary text cannot be empty.'}), 400

    updated = db.update_excuse_text(excuse_id, user['id'], primary_text)
    if not updated:
        return jsonify({'error': 'Excuse not found.'}), 404
    return jsonify({'excuse': updated})

@app.route('/api/excuses/<int:excuse_id>', methods=['DELETE'])
def remove_excuse(excuse_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    success = db.delete_excuse(excuse_id, user['id'])
    if not success:
        return jsonify({'error': 'Excuse not found or already deleted.'}), 404
    return jsonify({'message': 'Excuse deleted successfully.'})

# ----------------- SUPPORTING DOCUMENTS ENDPOINTS -----------------

@app.route('/api/documents/generate', methods=['POST'])
def generate_document():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    doc_type = data.get('doc_type', 'Explanation Letter').strip()
    title = data.get('title', '').strip()
    recipient = data.get('recipient', 'Manager').strip()
    issue_date = data.get('issue_date', datetime.now().strftime('%d %B %Y')).strip()
    reason = data.get('reason', '').strip()
    additional_details = data.get('additional_details', '').strip()

    # Generate formal document content
    content = ai_engine.generate_formal_document_content(
        doc_type=doc_type,
        title=title,
        recipient=recipient,
        issue_date=issue_date,
        reason=reason,
        additional_details=additional_details,
        user_name=user['name']
    )

    doc = db.save_document(
        user_id=user['id'],
        doc_type=doc_type,
        title=title or content['title'],
        recipient=recipient,
        issue_date=issue_date,
        organization=f"Official {doc_type}",
        content_dict=content
    )

    return jsonify({'document': doc}), 201

@app.route('/api/documents/<int:doc_id>', methods=['PUT'])
def edit_document(doc_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content_text = data.get('content_text', '').strip()
    
    doc = db.get_document_by_id(doc_id, user['id'])
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404
    
    content_dict = doc.get('content', {})
    content_dict['content_text'] = content_text
    if title:
        content_dict['title'] = title

    updated = db.update_document_content(doc_id, user['id'], title or doc['title'], content_dict)
    return jsonify({'document': updated})

@app.route('/api/documents', methods=['GET'])
def list_documents():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    favorites_only = request.args.get('favorites', 'false').lower() == 'true'
    documents = db.get_user_documents(user['id'], limit=100, favorites_only=favorites_only)
    return jsonify({'documents': documents})

@app.route('/api/documents/<int:doc_id>/favorite', methods=['POST'])
def favorite_document(doc_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    is_fav = db.toggle_document_favorite(doc_id, user['id'])
    return jsonify({'is_favorite': is_fav})

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def remove_document(doc_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    success = db.delete_document(doc_id, user['id'])
    if not success:
        return jsonify({'error': 'Document not found or already deleted.'}), 404
    return jsonify({'message': 'Document deleted successfully.'})

# ----------------- DASHBOARD & USER SETTINGS ENDPOINTS -----------------

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    stats = db.get_user_dashboard_stats(user['id'])
    recent_excuses = db.get_user_excuses(user['id'], limit=5)
    return jsonify({'stats': stats, 'recent_excuses': recent_excuses})

@app.route('/api/user/settings', methods=['GET'])
def get_settings():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    settings = db.get_user_settings(user['id'])
    # Mask API key if set
    if settings.get('custom_api_key'):
        masked = settings['custom_api_key'][:4] + '...' + settings['custom_api_key'][-4:]
        settings['has_custom_api_key'] = True
        settings['masked_api_key'] = masked
    else:
        settings['has_custom_api_key'] = False
        settings['masked_api_key'] = ''
    return jsonify({'settings': settings})

@app.route('/api/user/settings', methods=['POST', 'PUT'])
@app.route('/api/settings', methods=['GET', 'PUT', 'POST'])
def handle_settings():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        settings = db.get_user_settings(user['id'])
        if settings.get('custom_api_key'):
            masked = settings['custom_api_key'][:4] + '...' + settings['custom_api_key'][-4:]
            settings['has_custom_api_key'] = True
            settings['masked_api_key'] = masked
        else:
            settings['has_custom_api_key'] = False
            settings['masked_api_key'] = ''
        return jsonify({'settings': settings})

    data = request.get_json() or {}
    default_tone = data.get('default_tone', 'Professional')
    default_recipient = data.get('default_recipient', 'Manager')
    theme_preference = data.get('theme_preference', 'dark')
    custom_api_key = data.get('custom_api_key', None)

    if custom_api_key is not None and custom_api_key.strip() == '':
        custom_api_key = None

    updated = db.update_user_settings(
        user_id=user['id'],
        default_tone=default_tone,
        default_recipient=default_recipient,
        theme_preference=theme_preference,
        custom_api_key=custom_api_key
    )
    return jsonify({'message': 'Settings saved successfully.', 'settings': updated})

@app.route('/api/user/profile', methods=['GET', 'POST', 'PUT'])
def handle_profile():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        return jsonify({'user': user})

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required.'}), 400

    avatar_url = data.get('avatar_url')
    updated = db.update_user_profile(user['id'], name, avatar_url)
    return jsonify({'message': 'Profile updated.', 'user': updated})

@app.route('/api/user/avatar', methods=['POST'])
def upload_avatar():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    avatar_data = None
    if 'avatar_file' in request.files:
        file = request.files['avatar_file']
        if file and file.filename:
            file_bytes = file.read()
            mime = file.content_type or 'image/jpeg'
            b64_str = base64.b64encode(file_bytes).decode('utf-8')
            avatar_data = f"data:{mime};base64,{b64_str}"
    else:
        data = request.get_json() or {}
        avatar_data = data.get('avatar_data') or data.get('avatar_url')

    if not avatar_data:
        return jsonify({'error': 'Please select an image file to upload.'}), 400

    updated = db.update_user_profile(user['id'], user['name'], avatar_data)
    return jsonify({'message': 'Avatar updated successfully.', 'user': updated})

@app.route('/api/user/history', methods=['DELETE'])
def clear_user_history():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db.delete_all_user_history(user['id'])
    return jsonify({'message': 'All history records cleared successfully.'})

@app.route('/api/user/account', methods=['DELETE'])
def delete_account():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db.delete_user_account(user['id'])
    return jsonify({'message': 'Account and all associated records permanently deleted.'})

@app.route('/api/documents/<int:doc_id>/pdf', methods=['GET'])
def export_document_pdf(doc_id):
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    doc = db.get_document_by_id(doc_id, user['id'])
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    content = doc.get('content', {})
    text = content.get('content_text', '')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{doc.get('title', 'Supporting Document')}</title>
<style>
  @page {{ margin: 20mm; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #111827; margin: 0; padding: 20px; line-height: 1.6; font-size: 14px; }}
  .header {{ text-align: center; border-bottom: 2px solid #111827; padding-bottom: 15px; margin-bottom: 25px; }}
  .title {{ font-size: 18px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }}
  .meta {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 12px; color: #4b5563; }}
  .body-content {{ white-space: pre-wrap; margin-bottom: 40px; font-size: 14px; }}
  .signature-area {{ margin-top: 50px; border-top: 1px solid #9ca3af; width: 250px; padding-top: 5px; }}
  .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 8px; }}
</style>
</head>
<body onload="window.print()">
  <div class="header">
    <div class="title">{doc.get('title', 'FORMAL STATEMENT')}</div>
  </div>
  <div class="body-content">{text}</div>
  <div class="footer">
    AI-generated draft — verify all information before use.
  </div>
</body>
</html>"""
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/user/change-password', methods=['POST'])
@app.route('/api/user/password', methods=['POST', 'PUT'])
def change_password():
    user = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters.'}), 400
    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    success, msg = db.change_user_password(user['id'], old_password, new_password)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Excuva application on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
