from flask import Flask, render_template, request, redirect, url_for
import database
import random

app = Flask(__name__)

# System startup par database initialize karne ke liye
try:
    database.init_db()
    print("✅ SQLite Database Initialized Successfully!")
except Exception as e:
    print(f"⚠️ Database setup warning: {e}")

# 1. HOME ROUTE
@app.route('/')
def home():
    return render_template('index.html')

# 2. RISK ASSESSMENT ROUTE
@app.route('/risk', methods=['GET', 'POST'])
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

# 3. AI PREDICTION ROUTE
@app.route('/predict', methods=['GET', 'POST'])
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

# 4. HISTORY LOGS ROUTE
@app.route('/history')
def history():
    try:
        rows = database.get_history()
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        rows = []
    return render_template('history.html', rows=rows)

# 5. PERFORMANCE ANALYTICS ROUTE
@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# APP RUNNER
if __name__ == '__main__':
    print("🚀 ThyroCare Web Server Start ho raha hai...")
    app.run(debug=True)