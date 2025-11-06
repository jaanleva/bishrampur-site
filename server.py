# app.py (updated with your provided admin id/password)
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
CORS(app)

# ---------- CONFIG ----------
DATA_FILE = 'student_registrations.csv'

# Admin credentials: default set to what you provided.
# NOTE: This is insecure for production. Prefer environment variables.
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'vishnu singh')   # your provided id
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '4321')     # your provided password

# Flask session secret key (set this to a strong random value in production)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'replace-this-with-secure-random-key')

# Toggle: if you ever want to re-enable email sending, set to True and implement send_email_notification properly.
ENABLE_EMAIL_NOTIFICATIONS = False
# ----------------------------

def save_to_csv(data):
    """Saves new registration data to a CSV file."""
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    file_exists = os.path.isfile(DATA_FILE)
    df_new = pd.DataFrame([data])
    df_new.to_csv(DATA_FILE, mode='a', index=False, header=not file_exists)
    print(f"✅ Data saved to {DATA_FILE}: {data}")

def generate_course_graph(df):
    """Generates a bar chart of course registrations and returns it as a Base64 string."""
    if df.empty or 'course' not in df.columns or len(df['course'].unique()) < 1:
        return ""

    course_counts = df['course'].value_counts()

    plt.figure(figsize=(9, 5))
    colors = ['#003366', '#FF9933', '#0070c0', '#b74c00']
    course_counts.plot(kind='bar', color=colors[:len(course_counts)])

    plt.title('Live Registration Distribution by Course', fontsize=16, color='#003366')
    plt.ylabel('Number of Students', fontsize=12)
    plt.xlabel('Course Name', fontsize=12)
    plt.xticks(rotation=15)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()

    graph_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{graph_base64}"

@app.route('/register', methods=['POST'])
def register_student():
    """
    Public endpoint to receive registration data and save it.
    Students do NOT need any password — they simply post JSON with name, mobile, course (and optionally other fields).
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    student_data = request.get_json()
    if not all(key in student_data for key in ['name', 'mobile', 'course']):
        return jsonify({"error": "Missing required fields: name, mobile, course"}), 400

    try:
        save_to_csv(student_data)
        return jsonify({"message": "✅ Registration successful!"}), 200
    except Exception as e:
        print(f"Critical error in registration process: {e}")
        return jsonify({"error": "A critical server error occurred."}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Simple admin login page and API.
    - GET: returns a small HTML login form (for browser).
    - POST: accepts JSON { "email": "...", "password": "..." } and sets session if valid.
    """
    if request.method == 'GET':
        return f"""
        <html><body style="font-family:Arial,sans-serif;padding:30px;">
        <h2>Admin Login</h2>
        <form method="post" action="/login">
          <label>ID: <input type="text" name="email"></label><br><br>
          <label>Password: <input type="password" name="password"></label><br><br>
          <input type="submit" value="Login">
        </form>
        <p>Default ID: <strong>{ADMIN_EMAIL}</strong> | Password: <strong>{ADMIN_PASSWORD}</strong></p>
        <p>Note: For security, prefer setting ADMIN_EMAIL and ADMIN_PASSWORD as environment variables.</p>
        </body></html>
        """
    # POST: accept form-data or JSON
    data = request.get_json(silent=True) or request.form
    email = data.get('email')
    password = data.get('password')

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        if request.is_json:
            return jsonify({"message": "Login successful"}), 200
        else:
            return redirect(url_for('admin_dashboard'))
    else:
        if request.is_json:
            return jsonify({"error": "Invalid credentials"}), 401
        else:
            return "<h3>Invalid credentials. <a href='/login'>Try again</a></h3>", 401

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('admin_logged_in', None)
    return "<h3>Logged out. <a href='/login'>Login again</a></h3>"

@app.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """
    Protected dashboard — only visible to admin when logged in via /login.
    Shows table + graph.
    """
    if not session.get('admin_logged_in'):
        if request.headers.get('Accept', '').startswith('application/json'):
            return jsonify({"error": "Unauthorized. Please login at /login"}), 401
        return redirect(url_for('login'))

    try:
        if not os.path.exists(DATA_FILE):
            return "<h3 style='text-align:center;'>No registrations found yet.</h3>", 200

        df = pd.read_csv(DATA_FILE)
        graph_data_uri = generate_course_graph(df)
        total_registrations = len(df)
        table_html = df.to_html(classes='data-table', index=False, border=0)

        graph_tag = (
            f'<img src="{graph_data_uri}" alt="Course Registration Chart" '
            f'style="max-width:800px;width:100%;height:auto;margin:30px auto;display:block;'
            f'border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.1);">'
            if graph_data_uri
            else '<p style="text-align: center;">Not enough data for the graph yet.</p>'
        )

        response_html = f"""
        <html>
        <head><title>Admin Dashboard</title></head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f7f9;">
            <h1 style="color:#003366; text-align:center;">Student Registration Dashboard</h1>
            <div style="max-width:800px;margin:20px auto;padding:15px;background:#fff;border-radius:8px;
                box-shadow:0 2px 10px rgba(0,0,0,0.05);">
                <h2 style="color:#FF9933;">Statistics Overview</h2>
                <p>Total Registrations: <strong style="font-size:1.2em;">{total_registrations}</strong></p>
                <p><a href="/logout">Logout</a></p>
            </div>
            {graph_tag}
            <h2 style="color:#003366; text-align:center;">All Registrations Data</h2>
            <div style="max-width:1000px;margin:20px auto;overflow-x:auto;">{table_html}</div>
        </body>
        </html>
        """
        return response_html

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    print("🚀 Server running on http://127.0.0.1:5000")
    app.run(debug=True)
