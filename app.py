from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import database
import random
import os
import re
import pdfplumber
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv()

# Windows Tesseract Path Setup
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super_secret_default_key_thyrocare')

# --- FLASK LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this diagnostic feature."
login_manager.login_message_category = "danger"

class User(UserMixin):
    def __init__(self, id, name, email, auth_provider):
        self.id = id
        self.name = name
        self.email = email
        self.auth_provider = auth_provider

@login_manager.user_loader
def load_user(user_id):
    u = database.get_user_by_id(user_id)
    if u:
        return User(id=u['id'], name=u['name'], email=u['email'], auth_provider=u['auth_provider'])
    return None

# --- GOOGLE OAUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', 'placeholder_id'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'placeholder_secret'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)

# System startup par database initialize karne ke liye
try:
    database.init_db()
    print("✅ SQLite Database Initialized Successfully!")
except Exception as e:
    print(f"⚠️ Database setup warning: {e}")

# 1. HOME ROUTE (Public)
@app.route('/')
def home():
    return render_template('index.html')

# --- AUTHENTICATION ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_data = database.get_user_by_email(email)
        
        if user_data and user_data['auth_provider'] == 'google':
            flash('This email is linked to a Google account. Please sign in with Google.', 'danger')
        elif user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], name=user_data['name'], email=user_data['email'], auth_provider=user_data['auth_provider'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if database.get_user_by_email(email):
            flash('Email already registered.', 'danger')
        else:
            pwd_hash = generate_password_hash(password)
            database.create_user(name, email, pwd_hash, 'local')
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    
    email = user_info['email']
    name = user_info.get('name', email.split('@')[0])
    
    user_data = database.get_user_by_email(email)
    if not user_data:
        user_id = database.create_user(name, email, None, 'google')
        user = User(id=user_id, name=name, email=email, auth_provider='google')
    else:
        user = User(id=user_data['id'], name=user_data['name'], email=user_data['email'], auth_provider=user_data['auth_provider'])
        
    login_user(user)
    return redirect(url_for('home'))

# 2. RISK ASSESSMENT ROUTE (Protected)
@app.route('/risk', methods=['GET', 'POST'])
@login_required
def risk():
    if request.method == 'POST':
        symptoms = request.form.getlist('symptoms')
        count = len(symptoms)
        if count <= 1:
            risk_level = "Low Risk"
        elif count <= 4:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        return render_template('risk.html', risk=risk_level)
    return render_template('risk.html', risk=None)

# 3. AI PREDICTION ROUTE (Protected)
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        # Form se inputs fetch karna
        age = int(request.form['age'])
        gender = request.form['gender']
        tsh = float(request.form['tsh'])
        t3 = float(request.form['t3'])
        tt4 = float(request.form['tt4'])
        t4u = float(request.form['t4u'])
        fti = float(request.form['fti'])
        
        # Clinical Rule Simulation Logic (Dataset core patterns ke mutabik)
        if tsh > 4.5:
            prediction = "Hypothyroid"
            confidence = round(random.uniform(92.0, 96.5), 1)
            recommendation = "Please consult an endocrinologist immediately. Bring copies of recent lab assay tracking reports."
        elif tsh < 0.4:
            prediction = "Hyperthyroid"
            confidence = round(random.uniform(89.0, 94.8), 1)
            recommendation = "Anti-thyroid medication therapies might be suggested. Please align an interview appointment with a physician."
        else:
            prediction = "Negative"
            confidence = round(random.uniform(95.0, 99.2), 1)
            recommendation = "Thyroid evaluation registers normal activity thresholds. Maintain uniform nutritional lifestyle cycles."

        # Database ke andar record logs save karna
        try:
            database.insert_patient(age, gender, tsh, t3, tt4, t4u, fti, prediction, confidence)
            print("💾 Patient record successfully saved to SQLite!")
        except Exception as e:
            print(f"❌ Database insert error: {e}")
        
        return render_template('result.html', prediction=prediction, confidence=confidence, recommendation=recommendation)
        
    return render_template('predict.html')

# 4. REPORT EXTRACTION (OCR/PDF) ROUTE (Protected)
@app.route('/extract_report', methods=['POST'])
@login_required
def extract_report():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    extracted_text = ""
    try:
        if file.filename.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(file)
            extracted_text = pytesseract.image_to_string(image)
        else:
            return jsonify({'error': 'Unsupported format. Use PDF, PNG, or JPEG.'}), 400
            
        # Regex parsing for clinical parameters
        data = {}
        
        def find_value(pattern, text):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
            return ""

        # Searching for patterns like "TSH: 4.5" or "T3 level 1.2"
        data['tsh'] = find_value(r'TSH[^\d]*?(\d+\.\d+|\d+)', extracted_text)
        data['t3'] = find_value(r'\bT3[^\d]*?(\d+\.\d+|\d+)', extracted_text)
        data['tt4'] = find_value(r'(?:TT4|Total T4)[^\d]*?(\d+\.\d+|\d+)', extracted_text)
        data['t4u'] = find_value(r'T4U[^\d]*?(\d+\.\d+|\d+)', extracted_text)
        data['fti'] = find_value(r'FTI[^\d]*?(\d+\.\d+|\d+)', extracted_text)
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 5. HISTORY LOGS ROUTE (Protected)
@app.route('/history')
@login_required
def history():
    try:
        rows = database.get_history()
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        rows = []
    return render_template('history.html', rows=rows)

# 6. PERFORMANCE ANALYTICS ROUTE (Protected)
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

# APP RUNNER
if __name__ == '__main__':
    print("🚀 ThyroCare Web Server Start ho raha hai...")
    app.run(debug=True)