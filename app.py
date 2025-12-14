import sqlite3
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import datetime

app = Flask(__name__)

# --- 1. LATEST TECH: PERSISTENT DATABASE (SQLite) ---
# We use SQLite so you don't need to install a server. It creates a file 'security.db'.

def init_db():
    conn = sqlite3.connect('security.db')
    c = conn.cursor()
    # Table for training data
    c.execute('''CREATE TABLE IF NOT EXISTS dataset (query_text TEXT, label TEXT)''')
    # Table for logs (The Dashboard)
    c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, timestamp TEXT, query_text TEXT, prediction TEXT, confidence REAL)''')
    
    # Seed data if empty (bootstrap the AI)
    c.execute('SELECT count(*) FROM dataset')
    if c.fetchone()[0] == 0:
        seed_data = [
            ("SELECT * FROM users", "Safe"), ("home/index", "Safe"), ("search?q=shoes", "Safe"),
            ("login.php", "Safe"), ("contact-us.html", "Safe"), ("SELECT * FROM products", "Safe"),
            ("OR 1=1", "Malicious"), ("<script>alert('xss')</script>", "Malicious"),
            ("UNION SELECT 1,2,3", "Malicious"), ("admin' --", "Malicious"),
            ("%3Cscript%3E", "Malicious"), ("DROP TABLE users", "Malicious")
        ]
        c.executemany('INSERT INTO dataset VALUES (?,?)', seed_data)
        conn.commit()
    conn.close()

# Initialize DB on start
init_db()

# --- 2. THE AI ENGINE (Retrains on start) ---
def train_model():
    conn = sqlite3.connect('security.db')
    df = pd.read_sql('SELECT * FROM dataset', conn)
    conn.close()
    model = make_pipeline(CountVectorizer(), MultinomialNB())
    model.fit(df['query_text'], df['label'])
    return model

model = train_model()

# --- 3. THE WEB INTERFACE (Modernized) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SentryAI | Enterprise Security</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #3b82f6;
            --accent: #8b5cf6;
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            /* NEW VARIABLES FOR DARK TEXT ON GLASS CARDS */
            --glass-text-dark: #0f172a; /* Deep Navy */
            --glass-text-grey: #475569; /* Slate Grey */
        }

        body { 
            font-family: 'Inter', sans-serif;
            margin: 0; 
            padding: 0; 
            min-height: 100vh;
            color: var(--text-main);
            
            /* --- DEEP NEBULA BACKGROUND --- */
            background-color: #0f172a;
            background-image: 
                radial-gradient(
                    650px circle at var(--x, 50%) var(--y, 50%), 
                    rgba(138, 43, 226, 0.15), 
                    transparent 40%
                ),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
                
            background-size: 100% 100%, 50px 50px, 50px 50px, 100% 100%;
            background-attachment: fixed;
        }

        /* --- FLOATING GLASS NAVBAR --- */
        .navbar {
            margin: 20px auto; 
            max-width: 90%;
            border-radius: 16px;
            background: rgba(15, 23, 42, 0.6); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            padding: 0.8rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 20px;
            z-index: 1000;
        }

        .brand-box { display: flex; align-items: center; gap: 12px; }

        .logo-icon {
            width: 36px; height: 36px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            color: white; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
        }

        .brand-name { font-size: 1.2rem; font-weight: 800; letter-spacing: -0.5px; color: white; }

        .nav-pills {
            display: flex; background: rgba(0, 0, 0, 0.2); padding: 5px;
            border-radius: 50px; border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .nav-link {
            text-decoration: none; color: #94a3b8; padding: 8px 24px;
            border-radius: 25px; font-size: 0.9rem; font-weight: 600;
            transition: all 0.3s ease; display: flex; align-items: center; gap: 8px;
        }

        .nav-link:hover { color: white; }
        .nav-link.active { background: #3b82f6; color: white; box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3); }

        /* --- GLASS CONTAINER --- */
        .container { 
            max-width: 900px; 
            margin: 40px auto; 
            /* White Glass Background */
            background: rgba(255, 255, 255, 0.85); 
            backdrop-filter: blur(20px); 
            -webkit-backdrop-filter: blur(20px);
            padding: 40px; 
            border-radius: 20px; 
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5); 
            animation: fadeIn 0.6s ease-out;
            color: var(--glass-text-dark); /* Default text color inside cards is now DARK */
        }

        /* --- INPUTS & BUTTONS --- */
        input[type="text"] { 
            width: 100%; padding: 15px; margin: 15px 0; 
            border: 2px solid #cbd5e1; 
            background-color: #ffffff; 
            color: #1e293b;
            border-radius: 10px; box-sizing: border-box; 
            font-size: 16px; font-family: 'Courier New', monospace; 
            transition: all 0.3s ease; 
        }

        input[type="text"]:focus {
            border-color: #3b82f6; 
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2); 
            transform: scale(1.01); outline: none;
        }

        button { 
            background: linear-gradient(45deg, #3b82f6, #8b5cf6); 
            color: white; padding: 15px 30px; border: none; 
            border-radius: 12px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%;
            transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }

        button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5); }

        /* --- DASHBOARD STATS (UPDATED COLORS) --- */
        .stats-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem;
        }

        .stat-card {
            background: #ffffff; /* Pure white card for contrast */
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        /* HERE IS THE FIX: Colors changed to Dark Navy */
        .stat-value { 
            font-size: 2.5rem; 
            font-weight: 800; 
            margin-top: 0.5rem; 
            color: var(--glass-text-dark); /* Dark Navy */
        }
        
        .stat-label { 
            color: var(--glass-text-grey); /* Slate Grey */
            font-size: 0.875rem; 
            text-transform: uppercase; 
            letter-spacing: 0.05em; 
            font-weight: 600;
        }

        /* --- HEADERS --- */
        h2, h3 { color: var(--glass-text-dark); } /* Headers are now dark */
        p { color: var(--glass-text-grey); }

        /* --- TABLE --- */
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 1rem; }
        th { text-align: left; padding: 1rem; color: #64748b; border-bottom: 1px solid #e2e8f0; }
        td { padding: 1rem; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-size: 0.9rem; color: #334155; }

        .result-box { margin-top: 2rem; padding: 1.5rem; border-radius: 12px; text-align: center; border: 1px solid transparent; }
        .Safe { background: rgba(16, 185, 129, 0.15); border-color: #10b981; color: #047857; }
        .Malicious { background: rgba(239, 68, 68, 0.15); border-color: #ef4444; color: #b91c1c; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="brand-box">
            <div class="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <div class="brand-name">SentryAI</div>
        </div>

        <div class="nav-pills">
            <a href="/" class="nav-link {% if request.path == '/' %}active{% endif %}">
                <span>⚡ Scanner</span>
            </a>
            <a href="/dashboard" class="nav-link {% if request.path == '/dashboard' %}active{% endif %}">
                <span>📊 Dashboard</span>
            </a>
        </div>
    </nav>

    <div class="container">
        {% block content %}{% endblock %}
    </div>

    <script>
    document.addEventListener('mousemove', (e) => {
        const body = document.querySelector('body');
        body.style.setProperty('--x', e.clientX + 'px');
        body.style.setProperty('--y', e.clientY + 'px');
    });
    </script>
</body>
</html>
"""

SCANNER_PAGE = """
{% extends "base" %}
{% block content %}
    <h2>🚀 Live Traffic Analysis</h2>
    <p>Test the <strong>Explainable AI (XAI)</strong> engine with a payload:</p>
    <form method="POST">
        <input type="text" name="query" placeholder="Enter SQL query or URL parameter..." required>
        <button type="submit">Analyze Payload</button>
    </form>

    {% if prediction %}
    <div class="result {{ prediction }}">
        <h1>{{ prediction }}</h1>
        <p>Confidence Score: <strong>{{ confidence }}%</strong></p>
        <p><i>The AI model is {{ confidence }}% sure this is {{ prediction }}.</i></p>
    </div>
    {% endif %}
{% endblock %}
"""

DASHBOARD_PAGE = """
{% extends "base" %}
{% block content %}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <h2>📊 Security Operations Center (SOC)</h2>
    
    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
        <div style="flex: 1; padding: 20px; background: rgba(255,255,255,0.9); border: 1px solid rgba(255,255,255,0.5); border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #3498db; text-align: center;">
            <h3 style="margin:0; color: #7f8c8d;">Total Traffic</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0;">{{ total }}</p>
        </div>
        <div style="flex: 1; padding: 20px; background: rgba(255,255,255,0.9); border: 1px solid rgba(255,255,255,0.5); border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #2ecc71; text-align: center;">
            <h3 style="margin:0; color: #7f8c8d;">Safe Requests</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #2ecc71;">{{ safe }}</p>
        </div>
        <div style="flex: 1; padding: 20px; background: rgba(255,255,255,0.9); border: 1px solid rgba(255,255,255,0.5); border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #e74c3c; text-align: center;">
            <h3 style="margin:0; color: #7f8c8d;">Threats Blocked</h3>
            <p style="font-size: 32px; font-weight: bold; margin: 10px 0; color: #e74c3c;">{{ malicious }}</p>
        </div>
    </div>

    <div style="background: rgba(255,255,255,0.9); border: 1px solid rgba(255,255,255,0.5); padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 30px;">
        <h3 style="text-align: center;">Threat Distribution Analytics</h3>
        <div style="height: 300px; width: 100%; display: flex; justify-content: center;">
            <canvas id="threatChart"></canvas>
        </div>
    </div>

    <h3>🔍 Detailed Traffic Logs</h3>
    <table>
        <tr>
            <th>ID</th>
            <th>Timestamp</th>
            <th>Payload</th>
            <th>Verdict</th>
            <th>Confidence</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log[0] }}</td>
            <td>{{ log[1] }}</td>
            <td>{{ log[2] }}</td>
            <td style="color: {% if log[3] == 'Malicious' %}red{% else %}green{% endif %}; font-weight:bold;">{{ log[3] }}</td>
            <td>{{ log[4] }}%</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <form action="/train" method="post" style="text-align: center;">
        <button type="submit" style="background-color: #e67e22; font-size: 18px; padding: 15px 30px;">🔄 Retrain AI Model (Active Learning)</button>
    </form>

    <script>
        // Data passed from Python to JavaScript
        const ctx = document.getElementById('threatChart').getContext('2d');
        const threatChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Safe Traffic', 'Malicious Attacks'],
                datasets: [{
                    data: [{{ safe }}, {{ malicious }}],
                    backgroundColor: ['#2ecc71', '#e74c3c'],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    </script>
{% endblock %}
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction = None
    confidence = None
    if request.method == 'POST':
        user_input = request.form['query']
        
        # 1. Predict
        pred_label = model.predict([user_input])[0]
        
        # 2. Get Confidence (Explainability)
        probs = model.predict_proba([user_input])[0]
        confidence = round(max(probs) * 100, 2)
        
        # 3. Log to Database
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        c.execute("INSERT INTO logs (timestamp, query_text, prediction, confidence) VALUES (?, ?, ?, ?)",
                  (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_input, pred_label, confidence))
        conn.commit()
        conn.close()
        
        return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', SCANNER_PAGE).replace('{% extends "base" %}', ''), 
                                      prediction=pred_label, confidence=confidence)
    
    return render_template_string(HTML_TEMPLATE.replace('{% block content %}{% endblock %}', SCANNER_PAGE).replace('{% extends "base" %}', ''))

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('security.db')
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC") # Removed LIMIT to count everything
    logs = c.fetchall()
    conn.close()

    # --- NEW: Calculate Stats for the Chart ---
    total_traffic = len(logs)
    safe_count = sum(1 for log in logs if log[3] == 'Safe')
    malicious_count = sum(1 for log in logs if log[3] == 'Malicious')
    
    # We only show the last 10 logs in the table to keep it clean, but chart uses all data
    recent_logs = logs[:10]

    return render_template_string(
        HTML_TEMPLATE.replace('{% block content %}{% endblock %}', DASHBOARD_PAGE).replace('{% extends "base" %}', ''), 
        logs=recent_logs, 
        total=total_traffic, 
        safe=safe_count, 
        malicious=malicious_count
    )
@app.route('/train', methods=['POST'])
def retrain():
    global model
    model = train_model()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run()