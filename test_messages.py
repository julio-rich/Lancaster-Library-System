import sqlite3
from datetime import datetime

# Quick test to see if we can create and read a test message
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Insert a test librarian reply message
try:
    cursor.execute("""
        INSERT INTO Messages (FromUserID, ToUserID, Subject, Message, MessageType, Priority)
        VALUES (1, 2, "Test Reply from Librarian", "Hello student! This is a test reply from the librarian system. Your book request has been processed.", "librarian_reply", "normal")
    """)
    conn.commit()
    print('Test message inserted successfully')
except Exception as e:
    print(f'Error inserting test message: {e}')

# Check if messages exist
cursor.execute("SELECT * FROM Messages WHERE MessageType = 'librarian_reply'")
messages = cursor.fetchall()
print(f'Found {len(messages)} librarian reply messages')
for msg in messages:
    print(f'Message ID: {msg[0]}, Subject: {msg[4]}, Content: {msg[5][:50]}...')

# Check message structure
cursor.execute("SELECT * FROM Messages LIMIT 1")
msg = cursor.fetchone()
if msg:
    print(f'Message structure: {len(msg)} fields')
    for i, field in enumerate(msg):
        print(f'  Field {i}: {field}')

conn.close()
