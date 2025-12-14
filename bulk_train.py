import sqlite3

# Connect to your existing database
conn = sqlite3.connect('security.db')
c = conn.cursor()

# 50+ Training Examples
training_data = [
    # --- MALICIOUS SQL INJECTION ---
    ("UNION SELECT 1, version()", "Malicious"),
    ("' OR 1=1 --", "Malicious"),
    ("admin' #", "Malicious"),
    ("ORDER BY 10--", "Malicious"),
    ("WAITFOR DELAY '0:0:5'", "Malicious"),
    ("AND 1=1", "Malicious"),
    ("SELECT * FROM information_schema.tables", "Malicious"),
    ("DROP TABLE users", "Malicious"),
    
    # --- MALICIOUS XSS ---
    ("<script>prompt(1)</script>", "Malicious"),
    ("<iframe src='javascript:alert(1)'>", "Malicious"),
    ("<input onfocus=alert(1) autofocus>", "Malicious"),
    ("onmouseover=alert(1)", "Malicious"),
    
    # --- MALICIOUS PATH TRAVERSAL ---
    ("/etc/passwd", "Malicious"),
    ("../../../windows/win.ini", "Malicious"),
    ("C:\\Windows\\System32\\cmd.exe", "Malicious"),
    
    # --- SAFE TRAFFIC (Make sure these are marked Safe!) ---
    ("SELECT * FROM products WHERE id=10", "Safe"),
    ("search.php?query=student_list", "Safe"),
    ("user_profile.php?id=505", "Safe"),
    ("INSERT INTO logs (message) VALUES ('Login successful')", "Safe"),
    ("UPDATE items SET stock=stock-1 WHERE id=5", "Safe"),
    ("/images/logo.png", "Safe"),
    ("contact.html", "Safe"),
    ("about-us.php", "Safe"),
    ("123 Main Street, New York", "Safe"),
    ("Hello, how can I help you?", "Safe"),
    ("ORDER BY date DESC", "Safe"),
    ("WHERE category = 'books'", "Safe")
]

# Insert them into the DB
c.executemany("INSERT INTO dataset VALUES (?, ?)", training_data)
conn.commit()
conn.close()

print(f"Successfully added {len(training_data)} new patterns to the brain!")
print("Now go to your Dashboard and click 'Retrain AI Model'.")