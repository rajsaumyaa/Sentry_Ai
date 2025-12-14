import sqlite3
conn = sqlite3.connect('security.db')
c = conn.cursor()
# We teach the AI that this specific query is actually BAD
new_attack = "UNION SELECT 1, table_name FROM information_schema.tables"
c.execute("INSERT INTO dataset VALUES (?, ?)", (new_attack, "Malicious"))
conn.commit()
print("Done! The AI has learned this new attack.")