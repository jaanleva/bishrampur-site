# app.py (with landing page + Admin Login button / in-page login form)
from flask import Flask, request, jsonify, session, redirect, url_for, make_response
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
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'vishnu singh')   # your provided id
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '4321')     # your provided password

# Flask session secret key (set this to a strong random value in production)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'replace-this-with-secure-random-key')

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

@app.route('/', methods=['GET'])
def index():
    """Landing page with Admin Login button and public registration form."""
    # Simple page: top-right admin login button; clicking shows login form; below is student register form.
    page = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Student Registration</title>
      <style>
        body{{font-family: Arial, sans-serif; background:#f4f7f9; margin:0; padding:0;}}
        .header{{background:#003366;color:#fff;padding:20px 30px;display:flex;justify-content:space-between;align-items:center}}
        .container{{max-width:900px;margin:30px auto;padding:20px;background:#fff;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.05)}}
        .btn{{background:#FF9933;color:#fff;padding:10px 16px;border:none;border-radius:6px;cursor:pointer}}
        .btn-secondary{{background:#0070c0}}
        .login-panel{{display:none;position:fixed;right:30px;top:80px;background:#fff;padding:16px;border-radius:8px;box-shadow:0 6px 30px rgba(0,0,0,0.15);width:300px;}}
        label{{display:block;margin-top:8px}}
        input[type=text], input[type=password]{{width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;margin-top:6px}}
        .form-row{{margin-bottom:10px}}
        .success{{color:green}}
        .error{{color:red}}
      </style>
    </head>
    <body>
      <div class="header">
        <div><h2 style="margin:0">Registration Portal</h2></div>
        <div>
          <button class="btn" id="adminBtn">Admin Login</button>
        </div>
      </div>

      <div class="container">
        <h3>Public Student Registration</h3>
        <p>Students can register without any ID/password — fill below.</p>
        <div id="regMsg"></div>
        <div style="max-width:600px;">
          <div class="form-row">
            <label>Name</label>
            <input type="text" id="name">
          </div>
          <div class="form-row">
            <label>Mobile</label>
            <input type="text" id="mobile">
          </div>
          <div class="form-row">
            <label>Course</label>
            <input type="text" id="course" placeholder="Example: Python Basic">
          </div>
          <button class="btn btn-secondary" onclick="submitRegistration()">Register</button>
        </div>
      </div>

      <!-- In-page login panel -->
      <div class="login-panel" id="loginPanel">
        <h4 style="margin-top:0">Admin Login</h4>
        <div id="loginMsg"></div>
        <form id="loginForm" onsubmit="return submitLogin();">
          <label>ID</label>
          <input type="text" id="loginId" value="{ADMIN_EMAIL}">
          <label>Password</label>
          <input type="password" id="loginPassword" value="{ADMIN_PASSWORD}">
          <div style="margin-top:12px;display:flex;justify-content:space-between;">
            <button class="btn" type="submit">Login</button>
            <button class="btn" type="button" onclick="closeLogin()" style="background:#999">Close</button>
          </div>
        </form>
      </div>

      <script>
        const adminBtn = document.getElementById('adminBtn');
        const loginPanel = document.getElementById('loginPanel');
        adminBtn.addEventListener('click', ()=> {{
          loginPanel.style.display = (loginPanel.style.display === 'block') ? 'none' : 'block';
        }});
        function closeLogin() {{ loginPanel.style.display = 'none'; }}

        // Submit registration via fetch to /register (JSON)
        async function submitRegistration() {{
          const name = document.getElementById('name').value.trim();
          const mobile = document.getElementById('mobile').value.trim();
          const course = document.getElementById('course').value.trim();
          const msgDiv = document.getElementById('regMsg');
          msgDiv.innerHTML = '';
          if(!name || !mobile || !course){{ msgDiv.innerHTML = '<p class="error">Please fill all fields.</p>'; return; }}
          try {{
            const res = await fetch('/register', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ name, mobile, course }})
            }});
            const data = await res.json();
            if(res.ok) {{
              msgDiv.innerHTML = '<p class="success">' + data.message + '</p>';
              document.getElementById('name').value='';document.getElementById('mobile').value='';document.getElementById('course').value='';
            }} else {{
              msgDiv.innerHTML = '<p class="error">' + (data.error || 'Error') + '</p>';
            }}
          }} catch(err) {{
            msgDiv.innerHTML = '<p class="error">Request failed.</p>';
          }}
        }}

        // Submit login - posts form to /login and, on success, redirect to /dashboard
        async function submitLogin() {{
          const id = document.getElementById('loginId').value.trim();
          const password = document.getElementById('loginPassword').value.trim();
          const loginMsg = document.getElementById('loginMsg');
          loginMsg.innerHTML = '';
          if(!id || !password){{ loginMsg.innerHTML = '<p class="error">Fill credentials.</p>'; return false; }}
          try {{
            const res = await fetch('/login', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ email: id, password: password }})
            }});
            const data = await res.json();
            if(res.ok) {{
              // Redirect to dashboard
              window.location.href = '/dashboard';
            }} else {{
              loginMsg.innerHTML = '<p class="error">' + (data.error || 'Invalid credentials') + '</p>';
            }}
          }} catch(err) {{
            loginMsg.innerHTML = '<p class="error">Login failed.</p>';
          }}
          return false; // prevent normal form submit
        }}
      </script>
    </body>
    </html>
    """
    resp = make_response(page)
    resp.headers['Content-Type'] = 'text/html'
    return resp

@app.route('/register', methods=['POST'])
def register_student():
    """
    Public endpoint to receive registration data and save it.
    Students do NOT need any password — they simply post JSON with name, mobile, course.
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
    Accepts JSON { "email": "...", "password": "..." } and sets session if valid.
    Also supports form POST (for browser fallback).
    """
    if request.method == 'GET':
        # Redirect to home where the login button exists
        return redirect(url_for('index'))

    # POST: accept JSON or form-data
    data = request.get_json(silent=True) or request.form
    email = data.get('email')
    password = data.get('password')

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        # return JSON for JS clients
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """
    Protected dashboard — only visible to admin when logged in via /login.
    Shows table + graph.
    """
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))

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
            <div style="max-width:900px;margin:20px auto;padding:15px;background:#fff;border-radius:8px;
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
