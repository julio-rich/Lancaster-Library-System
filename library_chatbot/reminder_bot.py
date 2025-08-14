import sqlite3
import smtplib
from email.message import EmailMessage

# Connect to the database
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Query database for loans due
cursor.execute("SELECT students.email, loans.book_title FROM loans JOIN students ON loans.student_id = students.student_id WHERE loans.due_date < CURRENT_DATE")
due_loans = cursor.fetchall()

# Send reminder emails
for email, book_title in due_loans:
    msg = EmailMessage()
    msg.set_content(f"Reminder: Please return the book '{book_title}'.")
    msg['Subject'] = 'Book Return Reminder'
    msg['From'] = 'library@example.com'
    msg['To'] = email

    # Send the message
    with smtplib.SMTP('smtp.example.com') as server:
        server.send_message(msg)

# Close the database connection
conn.close()

