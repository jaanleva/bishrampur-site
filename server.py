from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
CORS(app)

DATA_FILE = 'student_registrations.csv'

# ----------- EMAIL CONFIGURATION (CHANGE THESE) -----------
SENDER_EMAIL = 'YOUR_PYTHON_SENDER_EMAIL@gmail.com'
SENDER_PASSWORD = 'YOUR_GENERATED_APP_PASSWORD'
RECEIVER_EMAIL = 'tolaxsamrtb@gmail.com'
# ----------------------------------------------------------

def save_to_csv(data):
    """Saves new registration data to a CSV file."""
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    file_exists = os.path.isfile(DATA_FILE)
    df_new = pd.DataFrame([data])
    df_new.to_csv(DATA_FILE, mode='a', index=False, header=not file_exists)
    print(f"✅ Data saved to {DATA_FILE}: {data}")

def send_email_notification(student_data):
    """Sends an email notification when a new student registers."""
    try:
        subject = f"NEW REGISTRATION: {student_data.get('course', 'Unknown')} from {student_data.get('name', 'Anonymous')}"
        body = (
            f"New Student Registration Details:\n\n"
            f"Name: {student_data.get('name', 'N/A')}\n"
            f"Mobile: {student_data.get('mobile', 'N/A')}\n"
            f"Course: {student_data.get('course', 'N/A')}\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(f"📩 Email notification sent successfully to {RECEIVER_EMAIL}")

    except Exception as e:
        print(f"⚠️ EMAIL ERROR: {e}")

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
    """Endpoint to receive registration data, save it, and send email."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    student_data = request.get_json()
    if not all(key in student_data for key in ['name', 'mobile', 'course']):
        return jsonify({"error": "Missing required fields: name, mobile, course"}), 400

    try:
        save_to_csv(student_data)
        send_email_notification(student_data)
        return jsonify({"message": "✅ Registration successful and notification sent!"}), 200
    except Exception as e:
        print(f"Critical error in registration process: {e}")
        return jsonify({"error": "A critical server error occurred."}), 500

@app.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """Displays the list of registrations and a dynamic graph."""
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
            else '<p style="text-align: center;">Not enough data (minimum 1 registration) for the graph yet.</p>'
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
