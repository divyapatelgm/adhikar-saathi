import sqlite3

conn = sqlite3.connect('data/adhikar_saathi.db')
cursor = conn.cursor()

# 1. Delete automated test rows
cursor.execute("DELETE FROM users WHERE contact NOT IN ('1234567890', '0987654321')")

# 2. Update remaining citizen accounts to role = 'user'
cursor.execute("UPDATE users SET role = 'user'")
conn.commit()

cursor.execute("SELECT id, name, contact, dob, role FROM users")
print("Remaining users in database:")
for row in cursor.fetchall():
    print(" ", row)

conn.close()
