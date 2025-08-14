import sqlite3

# Connect to the database
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS loans (
    loan_id INTEGER PRIMARY KEY,
    student_id INTEGER,
    book_title TEXT NOT NULL,
    due_date DATE NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
)
''')

# Commit changes and close connection
conn.commit()
conn.close()

