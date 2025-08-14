import sqlite3
import os
from datetime import datetime

def check_database():
    """Check current database structure and data"""
    db_path = 'library.db'
    
    if not os.path.exists(db_path):
        print("Database does not exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print('=== DATABASE STRUCTURE ===')
    
    # Check Members table structure
    cursor.execute('PRAGMA table_info(Members)')
    members_columns = cursor.fetchall()
    print('Members table columns:')
    for col in members_columns:
        print(f'  {col[1]} ({col[2]})')
    
    print('\n=== CURRENT DATA ===')
    
    # Check current members
    cursor.execute('SELECT * FROM Members')
    members = cursor.fetchall()
    print(f'Total members: {len(members)}')
    
    if members:
        print('Current members:')
        for member in members:
            print(f'  ID: {member[0]}, Name: {member[1]}')
    
    # Check current loans
    cursor.execute('SELECT * FROM Loans WHERE ReturnDate IS NULL OR ReturnDate = ""')
    active_loans = cursor.fetchall()
    print(f'\nActive loans: {len(active_loans)}')
    
    if active_loans:
        print('Active loans (first 5):')
        for loan in active_loans[:5]:
            print(f'  Loan ID: {loan[0]}, Member: {loan[1]}, Book: {loan[2]}')
    
    # Check books
    cursor.execute('SELECT COUNT(*) FROM Books')
    total_books = cursor.fetchone()[0]
    print(f'\nTotal books: {total_books}')
    
    # Check Users table if it exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
    if cursor.fetchone():
        cursor.execute('SELECT * FROM Users')
        users = cursor.fetchall()
        print(f'\nTotal users: {len(users)}')
        if users:
            print('Current users:')
            for user in users:
                print(f'  ID: {user[0]}, Username: {user[1]}, Type: {user[4]}, Name: {user[6]}')
    
    conn.close()

if __name__ == "__main__":
    check_database()
