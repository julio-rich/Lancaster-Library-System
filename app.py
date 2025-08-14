from flask import Flask, render_template, redirect, url_for, request, session, flash
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import json
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this!

# Dummy user for demonstration
USER = {'username': 'admin', 'password': 'password'}
LIBRARIAN_CREDENTIALS = {'username': 'librarian', 'password': 'admin123'}

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'student':
            flash('Access denied. Student login required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'librarian':
            flash('Access denied. Librarian login required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

class LibraryManager:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
        self.init_user_tables()
        self.init_enhanced_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_user_tables(self):
        """Initialize user authentication tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE NOT NULL,
                Password TEXT NOT NULL,
                UserType TEXT NOT NULL,  -- 'student' or 'librarian'
                MemberID INTEGER,  -- Link to Members table for students
                Name TEXT NOT NULL,
                Email TEXT,
                CreatedDate DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
            )
        ''')
        
        # Create default users if they don't exist
        cursor.execute('SELECT COUNT(*) FROM Users')
        if cursor.fetchone()[0] == 0:
            # Default librarian
            cursor.execute('''
                INSERT INTO Users (Username, Password, UserType, Name, Email)
                VALUES ('librarian', 'admin123', 'librarian', 'Library Administrator', 'admin@library.com')
            ''')
            
            # Default student (will be linked to member after member creation)
            cursor.execute('''
                INSERT INTO Users (Username, Password, UserType, Name, Email)
                VALUES ('student', 'student123', 'student', 'John Doe', 'john.doe@student.edu')
            ''')
        
        conn.commit()
        conn.close()
    
    def init_enhanced_tables(self):
        """Initialize enhanced tables for new features"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enhanced Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Messages (
                MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
                FromUserID INTEGER,
                ToUserID INTEGER,
                ToUserType TEXT,
                Subject TEXT,
                Message TEXT,
                SentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                IsRead BOOLEAN DEFAULT 0,
                MessageType TEXT DEFAULT 'general',
                Priority TEXT DEFAULT 'normal',
                FOREIGN KEY (FromUserID) REFERENCES Users(UserID),
                FOREIGN KEY (ToUserID) REFERENCES Users(UserID)
            )
        ''')
        
        # Book Categories/Genres management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BookCategories (
                CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                CategoryName TEXT UNIQUE NOT NULL,
                Description TEXT,
                CreatedDate DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Book Reservations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BookReservations (
                ReservationID INTEGER PRIMARY KEY AUTOINCREMENT,
                BookID TEXT NOT NULL,
                MemberID INTEGER NOT NULL,
                ReservationDate DATE DEFAULT CURRENT_DATE,
                ExpiryDate DATE,
                Status TEXT DEFAULT 'active',
                FOREIGN KEY (BookID) REFERENCES Books(ISBN),
                FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
            )
        ''')
        
        # Member Tiers/Categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS MemberTiers (
                TierID INTEGER PRIMARY KEY AUTOINCREMENT,
                TierName TEXT UNIQUE NOT NULL,
                MaxBooks INTEGER DEFAULT 3,
                LoanPeriodDays INTEGER DEFAULT 14,
                FinePerDay DECIMAL(5,2) DEFAULT 0.50,
                Description TEXT
            )
        ''')
        
        # Enhanced Members table (add columns if not exist)
        cursor.execute('PRAGMA table_info(Members)')
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        if 'MembershipTier' not in existing_columns:
            cursor.execute('ALTER TABLE Members ADD COLUMN MembershipTier INTEGER DEFAULT 1')
        if 'Address' not in existing_columns:
            cursor.execute('ALTER TABLE Members ADD COLUMN Address TEXT')
        if 'DateOfBirth' not in existing_columns:
            cursor.execute('ALTER TABLE Members ADD COLUMN DateOfBirth DATE')
        if 'Status' not in existing_columns:
            cursor.execute('ALTER TABLE Members ADD COLUMN Status TEXT DEFAULT "active"')
        if 'PhotoPath' not in existing_columns:
            cursor.execute('ALTER TABLE Members ADD COLUMN PhotoPath TEXT')
        
        # Fines and Fees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Fines (
                FineID INTEGER PRIMARY KEY AUTOINCREMENT,
                MemberID INTEGER NOT NULL,
                LoanID INTEGER,
                FineType TEXT NOT NULL,
                Amount DECIMAL(10,2) NOT NULL,
                IssueDate DATE DEFAULT CURRENT_DATE,
                DueDate DATE,
                PaidDate DATE,
                Status TEXT DEFAULT 'unpaid',
                Description TEXT,
                FOREIGN KEY (MemberID) REFERENCES Members(MemberID),
                FOREIGN KEY (LoanID) REFERENCES Loans(LoanID)
            )
        ''')
        
        # System Settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SystemSettings (
                SettingID INTEGER PRIMARY KEY AUTOINCREMENT,
                SettingKey TEXT UNIQUE NOT NULL,
                SettingValue TEXT,
                Description TEXT,
                LastModified DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AuditLogs (
                LogID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID INTEGER,
                Action TEXT NOT NULL,
                TableName TEXT,
                RecordID INTEGER,
                OldValues TEXT,
                NewValues TEXT,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                IPAddress TEXT,
                FOREIGN KEY (UserID) REFERENCES Users(UserID)
            )
        ''')
        
        # Announcements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Announcements (
                AnnouncementID INTEGER PRIMARY KEY AUTOINCREMENT,
                Title TEXT NOT NULL,
                Content TEXT NOT NULL,
                CreatedBy INTEGER NOT NULL,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                ExpiryDate DATE,
                Priority TEXT DEFAULT 'normal',
                Status TEXT DEFAULT 'active',
                TargetAudience TEXT DEFAULT 'all',
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
        ''')
        
        # Book Reviews/Ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS BookReviews (
                ReviewID INTEGER PRIMARY KEY AUTOINCREMENT,
                BookID TEXT NOT NULL,
                MemberID INTEGER NOT NULL,
                Rating INTEGER CHECK(Rating >= 1 AND Rating <= 5),
                Review TEXT,
                ReviewDate DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (BookID) REFERENCES Books(ISBN),
                FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
            )
        ''')
        
        # Insert default data
        cursor.execute('INSERT OR IGNORE INTO MemberTiers (TierName, MaxBooks, LoanPeriodDays, FinePerDay, Description) VALUES (?, ?, ?, ?, ?)',
                      ('Standard', 3, 14, 0.50, 'Standard membership with basic privileges'))
        cursor.execute('INSERT OR IGNORE INTO MemberTiers (TierName, MaxBooks, LoanPeriodDays, FinePerDay, Description) VALUES (?, ?, ?, ?, ?)',
                      ('Premium', 5, 21, 0.25, 'Premium membership with extended privileges'))
        cursor.execute('INSERT OR IGNORE INTO MemberTiers (TierName, MaxBooks, LoanPeriodDays, FinePerDay, Description) VALUES (?, ?, ?, ?, ?)',
                      ('Student', 4, 30, 0.10, 'Student membership with educational benefits'))
        
        # Insert default book categories
        categories = ['Fiction', 'Non-Fiction', 'Science', 'Technology', 'History', 'Biography', 
                     'Romance', 'Mystery', 'Fantasy', 'Educational', 'Reference', 'Children']
        for category in categories:
            cursor.execute('INSERT OR IGNORE INTO BookCategories (CategoryName) VALUES (?)', (category,))
        
        # Insert default system settings
        settings = [
            ('default_loan_period', '14', 'Default loan period in days'),
            ('max_renewals', '2', 'Maximum number of renewals allowed'),
            ('fine_per_day', '0.50', 'Fine amount per day for overdue books'),
            ('max_books_per_member', '3', 'Maximum books a member can borrow'),
            ('library_name', 'Lancaster University Library', 'Name of the library'),
            ('library_email', 'info@citylibrary.com', 'Library contact email'),
            ('library_phone', '(555) 123-4567', 'Library contact phone'),
            ('reservation_hold_days', '3', 'Days to hold a reserved book')
        ]
        
        for key, value, desc in settings:
            cursor.execute('INSERT OR IGNORE INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, ?)',
                          (key, value, desc))
        
        conn.commit()
        conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT UserID, Username, UserType, Name, Email, MemberID
            FROM Users 
            WHERE Username = ? AND Password = ?
        ''', (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_student_loans(self, member_id):
        """Get loans for a specific student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, b.Author, l.LoanDate, l.DueDate, l.ReturnDate,
                   CASE WHEN l.DueDate < date('now') AND l.ReturnDate IS NULL THEN 1 ELSE 0 END as IsOverdue
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            WHERE l.MemberID = ?
            ORDER BY l.LoanDate DESC
        ''', (member_id,))
        loans = cursor.fetchall()
        conn.close()
        return loans
    
    def get_student_recent_returns(self, member_id, limit=5):
        """Get recently returned books for a student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, b.Author, l.LoanDate, l.DueDate, l.ReturnDate,
                   b.ISBN
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            WHERE l.MemberID = ? AND l.ReturnDate IS NOT NULL
            ORDER BY l.ReturnDate DESC
            LIMIT ?
        ''', (member_id, limit))
        returns = cursor.fetchall()
        conn.close()
        return returns
    
    def get_student_return_notifications(self, member_id):
        """Get return notifications for a student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.MessageID, m.Subject, m.Message, m.SentDate, m.IsRead
            FROM Messages m
            WHERE m.ToUserID = (SELECT UserID FROM Users WHERE MemberID = ?)
                  AND m.MessageType = 'return_confirmation'
                  AND m.SentDate >= date('now', '-7 days')
            ORDER BY m.SentDate DESC
            LIMIT 5
        ''', (member_id,))
        notifications = cursor.fetchall()
        conn.close()
        return notifications
    
    def send_message_to_librarian(self, student_id, message):
        """Send message from student to librarian"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create Messages table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Messages (
                MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
                FromUserID INTEGER,
                ToUserType TEXT,  -- 'librarian' or 'student'
                Subject TEXT,
                Message TEXT,
                SentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                IsRead BOOLEAN DEFAULT 0,
                FOREIGN KEY (FromUserID) REFERENCES Users(UserID)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO Messages (FromUserID, ToUserType, Subject, Message)
            VALUES (?, 'librarian', 'Student Inquiry', ?)
        ''', (student_id, message))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_books(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Books ORDER BY Title')
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_available_books(self):
        """Get only available books for loan processing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Books WHERE AvailabilityStatus = "Available" ORDER BY Title')
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_all_members(self, include_inactive=False):
        """Get all members, optionally including inactive ones"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if include_inactive:
            cursor.execute('SELECT * FROM Members ORDER BY Name')
        else:
            cursor.execute('SELECT * FROM Members WHERE Status = "active" OR Status IS NULL ORDER BY Name')
        
        members = cursor.fetchall()
        conn.close()
        return members
    
    def get_active_loans(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, m.Name, l.LoanDate, l.DueDate
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.ReturnDate IS NULL
            ORDER BY l.DueDate
        ''')
        loans = cursor.fetchall()
        conn.close()
        return loans
    
    def get_overdue_loans(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT 
                l.LoanID,
                b.Title,
                b.Author,
                m.Name,
                m.ContactInfo,
                l.DueDate,
                (julianday('now') - julianday(l.DueDate)) as DaysOverdue
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.DueDate < ? AND l.ReturnDate IS NULL
            ORDER BY l.DueDate ASC
        ''', (today,))
        overdue_loans = cursor.fetchall()
        conn.close()
        return overdue_loans
    
    def search_books(self, search_term):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus
            FROM Books
            WHERE Title LIKE ? OR Author LIKE ? OR Genre LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        books = cursor.fetchall()
        conn.close()
        return books
    
    def add_book(self, isbn, title, author, genre, publication_year):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Books (ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus)
                VALUES (?, ?, ?, ?, ?, 'Available')
            ''', (isbn, title, author, genre, publication_year))
            conn.commit()
            conn.close()
            return True, "Book added successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"Error: Book with ISBN {isbn} already exists!"
    
    def add_member(self, name, contact_info):
        conn = self.get_connection()
        cursor = conn.cursor()
        registration_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO Members (Name, ContactInfo, RegistrationDate)
            VALUES (?, ?, ?)
        ''', (name, contact_info, registration_date))
        conn.commit()
        member_id = cursor.lastrowid
        conn.close()
        return member_id
    
    def loan_book(self, isbn, member_id, loan_days=14):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if book is available
        cursor.execute('SELECT AvailabilityStatus FROM Books WHERE ISBN = ?', (isbn,))
        result = cursor.fetchone()
        
        if not result or result[0] != 'Available':
            conn.close()
            return False, "Book is not available!"
        
        # Create loan record
        loan_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=loan_days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO Loans (BookID, MemberID, LoanDate, DueDate)
            VALUES (?, ?, ?, ?)
        ''', (isbn, member_id, loan_date, due_date))
        
        # Update book availability
        cursor.execute('''
            UPDATE Books SET AvailabilityStatus = 'Loaned' WHERE ISBN = ?
        ''', (isbn,))
        
        conn.commit()
        conn.close()
        return True, f"Book loaned successfully. Due date: {due_date}"
    
    # ===== ENHANCED ANALYTICS & REPORTS =====
    def get_popular_books(self, limit=10):
        """Get most popular books based on loan count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.ISBN, b.Title, b.Author, COUNT(l.LoanID) as loan_count,
                   AVG(COALESCE(br.Rating, 0)) as avg_rating
            FROM Books b
            LEFT JOIN Loans l ON b.ISBN = l.BookID
            LEFT JOIN BookReviews br ON b.ISBN = br.BookID
            GROUP BY b.ISBN, b.Title, b.Author
            ORDER BY loan_count DESC, avg_rating DESC
            LIMIT ?
        ''', (limit,))
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_member_activity_stats(self):
        """Get member activity statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_members,
                COUNT(CASE WHEN Status = 'active' THEN 1 END) as active_members,
                COUNT(CASE WHEN Status = 'inactive' THEN 1 END) as inactive_members,
                COUNT(CASE WHEN RegistrationDate >= date('now', '-30 days') THEN 1 END) as new_members_month
            FROM Members
        ''')
        stats = cursor.fetchone()
        conn.close()
        return stats
    
    def get_loan_trends(self, days=30):
        """Get loan trends for specified period"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DATE(LoanDate) as loan_date, COUNT(*) as loans_count
            FROM Loans
            WHERE LoanDate >= date('now', '-{} days')
            GROUP BY DATE(LoanDate)
            ORDER BY loan_date
        '''.format(days))
        trends = cursor.fetchall()
        conn.close()
        return trends
    
    
    # ===== ENHANCED BOOK MANAGEMENT =====
    def get_book_categories(self):
        """Get all book categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM BookCategories ORDER BY CategoryName')
        categories = cursor.fetchall()
        conn.close()
        return categories
    
    def add_book_category(self, name, description=None):
        """Add new book category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO BookCategories (CategoryName, Description) VALUES (?, ?)',
                          (name, description))
            conn.commit()
            conn.close()
            return True, "Category added successfully!"
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"Category '{name}' already exists!"
    
    def get_low_stock_books(self, threshold=2):
        """Get books with low availability (assuming multiple copies)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # This would require a Copies table in a real system
        cursor.execute('''
            SELECT ISBN, Title, Author, AvailabilityStatus
            FROM Books
            WHERE AvailabilityStatus = 'Available'
            GROUP BY Title, Author
            HAVING COUNT(*) <= ?
        ''', (threshold,))
        books = cursor.fetchall()
        conn.close()
        return books
    
    def bulk_import_books(self, books_data):
        """Import multiple books at once"""
        conn = self.get_connection()
        cursor = conn.cursor()
        success_count = 0
        errors = []
        
        for book in books_data:
            try:
                cursor.execute('''
                    INSERT INTO Books (ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus)
                    VALUES (?, ?, ?, ?, ?, 'Available')
                ''', tuple(book))
                success_count += 1
            except sqlite3.IntegrityError as e:
                errors.append(f"ISBN {book[0]}: {str(e)}")
        
        conn.commit()
        conn.close()
        return success_count, errors
    
    # ===== BOOK RESERVATION SYSTEM =====
    def create_reservation(self, isbn, member_id, days_to_hold=3):
        """Create book reservation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if book is already reserved
        cursor.execute('''
            SELECT COUNT(*) FROM BookReservations 
            WHERE BookID = ? AND Status = 'active'
        ''', (isbn,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, "Book is already reserved!"
        
        expiry_date = (datetime.now() + timedelta(days=days_to_hold)).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO BookReservations (BookID, MemberID, ExpiryDate)
            VALUES (?, ?, ?)
        ''', (isbn, member_id, expiry_date))
        
        conn.commit()
        conn.close()
        return True, f"Book reserved until {expiry_date}"
    
    def get_member_reservations(self, member_id):
        """Get reservations for a member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.ReservationID, b.Title, b.Author, r.ReservationDate, r.ExpiryDate, r.Status
            FROM BookReservations r
            JOIN Books b ON r.BookID = b.ISBN
            WHERE r.MemberID = ? AND r.Status = 'active'
            ORDER BY r.ReservationDate DESC
        ''', (member_id,))
        reservations = cursor.fetchall()
        conn.close()
        return reservations
    
    def cancel_reservation(self, reservation_id):
        """Cancel a book reservation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE BookReservations SET Status = 'cancelled'
            WHERE ReservationID = ?
        ''', (reservation_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== ENHANCED MEMBER MANAGEMENT =====
    def get_member_tiers(self):
        """Get all membership tiers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM MemberTiers ORDER BY TierName')
        tiers = cursor.fetchall()
        conn.close()
        return tiers
    
    def add_enhanced_member(self, name, contact_info, address=None, date_of_birth=None, tier_id=1):
        """Add member with enhanced information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        registration_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO Members (Name, ContactInfo, Address, DateOfBirth, RegistrationDate, MembershipTier)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, contact_info, address, date_of_birth, registration_date, tier_id))
        conn.commit()
        member_id = cursor.lastrowid
        conn.close()
        return member_id
    
    def get_member_profile(self, member_id):
        """Get detailed member profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, mt.TierName, mt.MaxBooks, mt.LoanPeriodDays
            FROM Members m
            LEFT JOIN MemberTiers mt ON m.MembershipTier = mt.TierID
            WHERE m.MemberID = ?
        ''', (member_id,))
        profile = cursor.fetchone()
        conn.close()
        return profile
    
    def update_member_tier(self, member_id, tier_id):
        """Update member's tier"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Members SET MembershipTier = ? WHERE MemberID = ?',
                      (tier_id, member_id))
        conn.commit()
        conn.close()
        return True
    
    def remove_member(self, member_id):
        """Remove/deactivate a member from the library"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if member has any active loans
        cursor.execute('''
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL
        ''', (member_id,))
        
        active_loans = cursor.fetchone()[0]
        
        if active_loans > 0:
            conn.close()
            return False, f"Cannot remove member: {active_loans} active loan(s) found. Please return all books first."
        
        # Check if member has unpaid fines
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) FROM Fines 
            WHERE MemberID = ? AND Status = 'unpaid'
        ''', (member_id,))
        
        outstanding_fines = cursor.fetchone()[0]
        
        if outstanding_fines > 0:
            conn.close()
            return False, f"Cannot remove member: ${outstanding_fines:.2f} in unpaid fines. Please settle all fines first."
        
        # Get member info before removal for logging
        cursor.execute('SELECT Name FROM Members WHERE MemberID = ?', (member_id,))
        member_info = cursor.fetchone()
        
        if not member_info:
            conn.close()
            return False, "Member not found."
        
        member_name = member_info[0]
        
        # Instead of deleting, deactivate the member (safer approach)
        cursor.execute('''
            UPDATE Members SET Status = 'inactive' 
            WHERE MemberID = ?
        ''', (member_id,))
        
        # Also deactivate associated user account if exists
        cursor.execute('''
            UPDATE Users SET UserType = 'inactive_student' 
            WHERE MemberID = ? AND UserType = 'student'
        ''', (member_id,))
        
        conn.commit()
        conn.close()
        
        return True, f"Member '{member_name}' has been successfully removed from the library system."
    
    # ===== FINES AND FEES =====
    def calculate_overdue_fines(self):
        """Calculate fines for overdue books"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get overdue loans that don't have fines yet
        cursor.execute('''
            SELECT l.LoanID, l.MemberID, l.DueDate, mt.FinePerDay,
                   (julianday('now') - julianday(l.DueDate)) as DaysOverdue
            FROM Loans l
            JOIN Members m ON l.MemberID = m.MemberID
            JOIN MemberTiers mt ON m.MembershipTier = mt.TierID
            WHERE l.ReturnDate IS NULL AND l.DueDate < date('now')
            AND NOT EXISTS (
                SELECT 1 FROM Fines f 
                WHERE f.LoanID = l.LoanID AND f.FineType = 'overdue'
            )
        ''')
        
        overdue_loans = cursor.fetchall()
        fines_created = 0
        
        for loan_id, member_id, due_date, fine_per_day, days_overdue in overdue_loans:
            if days_overdue > 0:
                fine_amount = days_overdue * fine_per_day
                cursor.execute('''
                    INSERT INTO Fines (MemberID, LoanID, FineType, Amount, Description)
                    VALUES (?, ?, 'overdue', ?, ?)
                ''', (member_id, loan_id, fine_amount, 
                     f'Overdue fine for {days_overdue} days at ${fine_per_day}/day'))
                fines_created += 1
        
        conn.commit()
        conn.close()
        return fines_created
    
    def get_member_fines(self, member_id):
        """Get all fines for a member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, b.Title
            FROM Fines f
            LEFT JOIN Loans l ON f.LoanID = l.LoanID
            LEFT JOIN Books b ON l.BookID = b.ISBN
            WHERE f.MemberID = ?
            ORDER BY f.IssueDate DESC
        ''', (member_id,))
        fines = cursor.fetchall()
        conn.close()
        return fines
    
    def pay_fine(self, fine_id):
        """Mark fine as paid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Fines SET Status = 'paid', PaidDate = date('now')
            WHERE FineID = ?
        ''', (fine_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== MESSAGING SYSTEM =====
    def send_message(self, from_user_id, to_user_id, subject, message, message_type='general', priority='normal'):
        """Send message between users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Messages (FromUserID, ToUserID, Subject, Message, MessageType, Priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (from_user_id, to_user_id, subject, message, message_type, priority))
        conn.commit()
        conn.close()
        return True
    
    def get_user_messages(self, user_id, message_type=None):
        """Get messages for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if message_type:
            cursor.execute('''
                SELECT m.*, u.Name as SenderName
                FROM Messages m
                LEFT JOIN Users u ON m.FromUserID = u.UserID
                WHERE (m.ToUserID = ? OR m.ToUserType = (SELECT UserType FROM Users WHERE UserID = ?))
                AND m.MessageType = ?
                ORDER BY m.SentDate DESC
            ''', (user_id, user_id, message_type))
        else:
            cursor.execute('''
                SELECT m.*, u.Name as SenderName
                FROM Messages m
                LEFT JOIN Users u ON m.FromUserID = u.UserID
                WHERE (m.ToUserID = ? OR m.ToUserType = (SELECT UserType FROM Users WHERE UserID = ?))
                ORDER BY m.SentDate DESC
            ''', (user_id, user_id))
        
        messages = cursor.fetchall()
        conn.close()
        return messages
    
    def mark_message_read(self, message_id):
        """Mark message as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Messages SET IsRead = 1 WHERE MessageID = ?', (message_id,))
        conn.commit()
        conn.close()
        return True
    
    # ===== ANNOUNCEMENTS =====
    def create_announcement(self, title, content, created_by, expiry_date=None, priority='normal', target_audience='all'):
        """Create system announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Announcements (Title, Content, CreatedBy, ExpiryDate, Priority, TargetAudience)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, content, created_by, expiry_date, priority, target_audience))
        conn.commit()
        conn.close()
        return True
    
    def get_active_announcements(self, target_audience='all'):
        """Get active announcements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, u.Name as CreatedByName
            FROM Announcements a
            JOIN Users u ON a.CreatedBy = u.UserID
            WHERE a.Status = 'active' 
            AND (a.ExpiryDate IS NULL OR a.ExpiryDate >= date('now'))
            AND (a.TargetAudience = ? OR a.TargetAudience = 'all')
            ORDER BY a.Priority DESC, a.CreatedDate DESC
        ''', (target_audience,))
        announcements = cursor.fetchall()
        conn.close()
        return announcements
    
    # ===== SYSTEM ADMINISTRATION =====
    def get_system_setting(self, key):
        """Get system setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SettingValue FROM SystemSettings WHERE SettingKey = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def update_system_setting(self, key, value):
        """Update system setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE SystemSettings 
            SET SettingValue = ?, LastModified = CURRENT_TIMESTAMP
            WHERE SettingKey = ?
        ''', (value, key))
        conn.commit()
        conn.close()
        return True
    
    def get_all_settings(self):
        """Get all system settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM SystemSettings ORDER BY SettingKey')
        settings = cursor.fetchall()
        conn.close()
        return settings
    
    def log_audit(self, user_id, action, table_name=None, record_id=None, old_values=None, new_values=None):
        """Log user action for audit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO AuditLogs (UserID, Action, TableName, RecordID, OldValues, NewValues)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action, table_name, record_id, 
             json.dumps(old_values) if old_values else None,
             json.dumps(new_values) if new_values else None))
        conn.commit()
        conn.close()
        return True
    
    def get_audit_logs(self, limit=100, user_id=None, action=None):
        """Get audit logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT al.*, u.Name as UserName
            FROM AuditLogs al
            LEFT JOIN Users u ON al.UserID = u.UserID
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND al.UserID = ?'
            params.append(user_id)
        
        if action:
            query += ' AND al.Action LIKE ?'
            params.append(f'%{action}%')
        
        query += ' ORDER BY al.Timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    # ===== ADVANCED SEARCH & FILTERING =====
    def advanced_search_books(self, title=None, author=None, genre=None, year_from=None, year_to=None, availability=None):
        """Advanced book search with multiple filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM Books WHERE 1=1'
        params = []
        
        if title:
            query += ' AND Title LIKE ?'
            params.append(f'%{title}%')
        if author:
            query += ' AND Author LIKE ?'
            params.append(f'%{author}%')
        if genre:
            query += ' AND Genre LIKE ?'
            params.append(f'%{genre}%')
        if year_from:
            query += ' AND PublicationYear >= ?'
            params.append(year_from)
        if year_to:
            query += ' AND PublicationYear <= ?'
            params.append(year_to)
        if availability:
            query += ' AND AvailabilityStatus = ?'
            params.append(availability)
        
        query += ' ORDER BY Title'
        
        cursor.execute(query, params)
        books = cursor.fetchall()
        conn.close()
        return books
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute('SELECT COUNT(*) FROM Books')
        total_books = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Books WHERE AvailabilityStatus = "Available"')
        available_books = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Members WHERE Status = "active" OR Status IS NULL')
        total_members = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Loans WHERE ReturnDate IS NULL')
        active_loans = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Loans WHERE DueDate < date("now") AND ReturnDate IS NULL')
        overdue_loans = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM BookReservations WHERE Status = "active"')
        active_reservations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Fines WHERE Status = "unpaid"')
        unpaid_fines = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Messages WHERE IsRead = 0')
        unread_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Members WHERE RegistrationDate >= date("now", "-30 days")')
        new_members_month = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_books': total_books,
            'available_books': available_books,
            'total_members': total_members,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'active_reservations': active_reservations,
            'unpaid_fines': unpaid_fines,
            'unread_messages': unread_messages,
            'new_members_month': new_members_month
        }

# Initialize library manager
library = LibraryManager()

# Authentication routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = library.authenticate_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_type'] = user[2]
            session['name'] = user[3]
            session['email'] = user[4]
            session['member_id'] = user[5]
            
            flash(f'Welcome back, {user[3]}!', 'success')
            
            if user[2] == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('librarian_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login_new.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        email = request.form['email']
        user_type = request.form['user_type']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('login_new.html', show_register=True)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('login_new.html', show_register=True)
        
        # Check if username already exists
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM Users WHERE Username = ?', (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            flash('Username already exists! Please choose a different one.', 'error')
            return render_template('login_new.html', show_register=True)
        
        # Create new user
        try:
            member_id = None
            # If registering as student, create a corresponding member record
            if user_type == 'student':
                cursor.execute('''
                    INSERT INTO Members (Name, ContactInfo, RegistrationDate)
                    VALUES (?, ?, date('now'))
                ''', (name, email))
                member_id = cursor.lastrowid
            
            # Create user account
            cursor.execute('''
                INSERT INTO Users (Username, Password, UserType, Name, Email, MemberID)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password, user_type, name, email, member_id))
            
            conn.commit()
            conn.close()
            
            flash(f'Account created successfully! You can now login as a {user_type}.', 'success')
            return render_template('login_new.html', show_register=False)
            
        except sqlite3.IntegrityError as e:
            conn.close()
            flash('Registration failed. Please try again.', 'error')
            return render_template('login_new.html', show_register=True)
        except Exception as e:
            conn.close()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('login_new.html', show_register=True)
    
    return render_template('login_new.html', show_register=True)

# Fix the root route to handle POST properly
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' in session:
        # Redirect to dashboard based on user role
        if session.get('role') == 'librarian':
            return redirect(url_for('librarian_dashboard'))
        elif session.get('role') == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login'))

# Student Dashboard
@app.route('/student')
@student_required
def student_dashboard():
    member_id = session.get('member_id')
    if member_id:
        loans = library.get_student_loans(member_id)
        # Get recent returns for this student
        recent_returns = library.get_student_recent_returns(member_id)
    else:
        loans = []
        recent_returns = []
    
    books = library.get_all_books()
    available_books = [b for b in books if b[5] == 'Available']
    
    # Get messages from librarians (replies to student's messages)
    student_messages = library.get_user_messages(session['user_id'])
    # Filter for messages from librarians (message_type='librarian_reply')
    librarian_messages = [msg for msg in student_messages if msg[8] == 'librarian_reply']
    
    # Get book return notifications for this student
    return_notifications = library.get_student_return_notifications(member_id) if member_id else []
    
    return render_template('student_dashboard.html', 
                         loans=loans, 
                         available_books=available_books[:20],  # Show top 20 available books for display
                         total_available_books=len(available_books),  # Total count for stats
                         student_messages=librarian_messages,
                         recent_returns=recent_returns,
                         return_notifications=return_notifications)

# Student Catalog - Full Book Listing
@app.route('/student/catalog')
@student_required
def student_catalog():
    search_term = request.args.get('search', '')
    if search_term:
        book_list = library.search_books(search_term)
    else:
        book_list = library.get_all_books()
    
    available_books = [b for b in book_list if b[5] == 'Available']
    return render_template('student_catalog.html', books=available_books, search_term=search_term)

# Student Account Management API endpoints
@app.route('/student/borrowing_history', methods=['GET'])
@student_required
def get_student_borrowing_history():
    """Get complete borrowing history for student"""
    try:
        member_id = session.get('member_id')
        if not member_id:
            return {'success': False, 'message': 'Member ID not found'}
        
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, b.Author, b.ISBN, 
                   l.LoanDate, l.DueDate, l.ReturnDate,
                   CASE WHEN l.DueDate < date('now') AND l.ReturnDate IS NULL THEN 1 ELSE 0 END as IsOverdue,
                   CASE WHEN l.ReturnDate IS NOT NULL THEN 1 ELSE 0 END as IsReturned,
                   COALESCE(l.RenewalsUsed, 0) as RenewalsUsed,
                   CASE WHEN l.ReturnDate IS NULL THEN (3 - COALESCE(l.RenewalsUsed, 0)) ELSE 0 END as RenewalsLeft
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            WHERE l.MemberID = ?
            ORDER BY l.LoanDate DESC
        ''', (member_id,))
        
        loans = cursor.fetchall()
        conn.close()
        
        # Format the data for the frontend
        history = []
        for loan in loans:
            history.append({
                'loan_id': loan[0],
                'title': loan[1],
                'author': loan[2],
                'isbn': loan[3],
                'loan_date': loan[4],
                'due_date': loan[5],
                'return_date': loan[6] or None,
                'overdue': bool(loan[7]),
                'returned': bool(loan[8]),
                'renewals_used': loan[9],
                'renewals_left': loan[10]
            })
        
        return {'success': True, 'history': history}
        
    except Exception as e:
        print(f"Error getting borrowing history: {e}")
        return {'success': False, 'message': 'Failed to load borrowing history'}

@app.route('/student/account_info', methods=['GET'])
@student_required
def get_student_account_info():
    """Get detailed student account information"""
    try:
        member_id = session.get('member_id')
        user_id = session.get('user_id')
        
        if not member_id:
            return {'success': False, 'message': 'Member ID not found'}
        
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get member profile with tier information
        cursor.execute('''
            SELECT m.MemberID, m.Name, m.ContactInfo, m.Address, 
                   m.DateOfBirth, m.RegistrationDate, m.Status,
                   mt.TierName, mt.MaxBooks, mt.LoanPeriodDays, mt.FinePerDay,
                   u.Username, u.Email, u.CreatedDate
            FROM Members m
            LEFT JOIN MemberTiers mt ON m.MembershipTier = mt.TierID
            JOIN Users u ON m.MemberID = u.MemberID
            WHERE m.MemberID = ?
        ''', (member_id,))
        
        profile = cursor.fetchone()
        
        # Get loan statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_loans,
                COUNT(CASE WHEN ReturnDate IS NULL THEN 1 END) as active_loans,
                COUNT(CASE WHEN ReturnDate IS NOT NULL THEN 1 END) as completed_loans,
                COUNT(CASE WHEN DueDate < date('now') AND ReturnDate IS NULL THEN 1 END) as overdue_loans
            FROM Loans WHERE MemberID = ?
        ''', (member_id,))
        
        loan_stats = cursor.fetchone()
        
        # Get fine information
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN Status = 'unpaid' THEN Amount ELSE 0 END), 0) as unpaid_fines,
                COALESCE(SUM(CASE WHEN Status = 'paid' THEN Amount ELSE 0 END), 0) as paid_fines,
                COUNT(CASE WHEN Status = 'unpaid' THEN 1 END) as unpaid_fine_count
            FROM Fines WHERE MemberID = ?
        ''', (member_id,))
        
        fine_stats = cursor.fetchone()
        
        # Get reservation count
        cursor.execute('''
            SELECT COUNT(*) FROM BookReservations 
            WHERE MemberID = ? AND Status = 'active'
        ''', (member_id,))
        
        reservation_count = cursor.fetchone()[0]
        
        conn.close()
        
        if not profile:
            return {'success': False, 'message': 'Profile not found'}
        
        account_info = {
            'member_id': profile[0],
            'name': profile[1],
            'contact_info': profile[2],
            'address': profile[3] or 'Not provided',
            'date_of_birth': profile[4] or 'Not provided',
            'registration_date': profile[5],
            'status': profile[6] or 'active',
            'membership_tier': profile[7] or 'Standard',
            'max_books': profile[8] or 3,
            'loan_period_days': profile[9] or 14,
            'fine_per_day': profile[10] or 0.50,
            'username': profile[11],
            'email': profile[12],
            'account_created': profile[13],
            'loan_stats': {
                'total_loans': loan_stats[0],
                'active_loans': loan_stats[1],
                'completed_loans': loan_stats[2],
                'overdue_loans': loan_stats[3]
            },
            'fine_stats': {
                'unpaid_amount': float(fine_stats[0]),
                'paid_amount': float(fine_stats[1]),
                'unpaid_count': fine_stats[2]
            },
            'active_reservations': reservation_count
        }
        
        return {'success': True, 'account_info': account_info}
        
    except Exception as e:
        print(f"Error getting account info: {e}")
        return {'success': False, 'message': 'Failed to load account information'}

@app.route('/student/renewals_info', methods=['GET'])
@student_required
def get_student_renewals_info():
    """Get renewal information for student's current loans"""
    try:
        member_id = session.get('member_id')
        if not member_id:
            return {'success': False, 'message': 'Member ID not found'}
        
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get current active loans with renewal information
        cursor.execute('''
            SELECT l.LoanID, b.Title, b.Author, l.DueDate, 
                   COALESCE(l.RenewalsUsed, 0) as RenewalsUsed,
                   (3 - COALESCE(l.RenewalsUsed, 0)) as RenewalsLeft,
                   CASE WHEN l.DueDate < date('now') THEN 1 ELSE 0 END as IsOverdue,
                   (julianday(l.DueDate) - julianday('now')) as DaysUntilDue
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            WHERE l.MemberID = ? AND l.ReturnDate IS NULL
            ORDER BY l.DueDate ASC
        ''', (member_id,))
        
        loans = cursor.fetchall()
        conn.close()
        
        renewal_info = []
        for loan in loans:
            days_until_due = int(loan[7]) if loan[7] is not None else 0
            can_renew = loan[5] > 0 and not loan[6]  # Has renewals left and not overdue
            
            renewal_info.append({
                'loan_id': loan[0],
                'title': loan[1],
                'author': loan[2],
                'due_date': loan[3],
                'renewals_used': loan[4],
                'renewals_left': loan[5],
                'is_overdue': bool(loan[6]),
                'days_until_due': days_until_due,
                'can_renew': can_renew,
                'status': 'Overdue' if loan[6] else ('Due Soon' if days_until_due <= 3 else 'Active')
            })
        
        return {'success': True, 'renewals': renewal_info}
        
    except Exception as e:
        print(f"Error getting renewals info: {e}")
        return {'success': False, 'message': 'Failed to load renewal information'}

@app.route('/student/holds_info', methods=['GET'])
@student_required
def get_student_holds_info():
    """Get holds/reservations information for student"""
    try:
        member_id = session.get('member_id')
        if not member_id:
            return {'success': False, 'message': 'Member ID not found'}
        
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get active reservations
        cursor.execute('''
            SELECT r.ReservationID, b.Title, b.Author, r.ReservationDate, 
                   r.ExpiryDate, r.Status
            FROM BookReservations r
            JOIN Books b ON r.BookID = b.ISBN
            WHERE r.MemberID = ? AND r.Status = 'active'
            ORDER BY r.ReservationDate DESC
        ''', (member_id,))
        
        reservations = cursor.fetchall()
        conn.close()
        
        holds_info = []
        for reservation in reservations:
            holds_info.append({
                'reservation_id': reservation[0],
                'title': reservation[1],
                'author': reservation[2],
                'reservation_date': reservation[3],
                'expiry_date': reservation[4],
                'status': reservation[5],
                'position': 1  # Simplified - in real system would calculate queue position
            })
        
        return {'success': True, 'holds': holds_info}
        
    except Exception as e:
        print(f"Error getting holds info: {e}")
        return {'success': False, 'message': 'Failed to load holds information'}

# Enhanced Librarian Dashboard
from datetime import datetime

@app.route('/librarian')
@librarian_required
def librarian_dashboard():
    # Get dashboard statistics and content
    stats = library.get_dashboard_stats()
    popular_books = library.get_popular_books(20)
    recent_announcements = library.get_active_announcements('librarian')
    unread_messages = library.get_user_messages(session['user_id'])[:5]

    # Get current login time
    last_login = datetime.now().strftime('%B %d %Y, %I:%M %p')

    print('Gathering enhanced librarian dashboard statistics...')
    try:
        return render_template('enhanced_librarian_dashboard.html', 
                               stats=stats, 
                               popular_books=popular_books,
                               announcements=recent_announcements,
                               messages=unread_messages,
                               last_login=last_login)
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'error')
        return redirect(url_for('login'))


@app.route('/books')
@login_required
def books():
    search_term = request.args.get('search', '')
    if search_term:
        book_list = library.search_books(search_term)
    else:
        book_list = library.get_all_books()
    return render_template('books.html', books=book_list, search_term=search_term)

@app.route('/members')
@login_required
def members():
    member_list = library.get_all_members()
    return render_template('members.html', members=member_list)

@app.route('/loans')
@login_required
def loans():
    active_loans = library.get_active_loans()
    overdue_loans = library.get_overdue_loans()
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('loans.html', 
                         active_loans=active_loans, 
                         overdue_loans=overdue_loans,
                         current_date=current_date)

@app.route('/admin')
@librarian_required
def admin():
    return render_template('admin.html')

@app.route('/add_book', methods=['GET', 'POST'])
@librarian_required
def add_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        year = int(request.form['year'])
        
        success, message = library.add_book(isbn, title, author, genre, year)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('books'))
    
    return render_template('add_book.html')

@app.route('/add_member', methods=['GET', 'POST'])
@librarian_required
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        
        member_id = library.add_member(name, contact)
        flash(f'Member "{name}" added successfully with ID: {member_id}', 'success')
        
        return redirect(url_for('members'))
    
    return render_template('add_member.html')

@app.route('/loan_book', methods=['GET', 'POST'])
@librarian_required
def loan_book():
    if request.method == 'POST':
        isbn = request.form['isbn']
        member_id = request.form['member_id']
        
        library = LibraryManager()
        if library.loan_book(isbn, member_id):
            flash('Book loaned successfully!', 'success')
        else:
            flash('Failed to loan book. Please check availability.', 'error')
        
        return redirect(url_for('loans'))
    
    library = LibraryManager()
    books = library.get_available_books()
    members = library.get_all_members()
    
    # Get book requests from messages
    book_requests = []
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get unread messages that might be book requests
        cursor.execute('''
            SELECT m.MessageID, m.FromUserID, m.Subject, m.Message, 
                   m.SentDate, m.Priority, u.Name as sender_name,
                   mem.MemberID
            FROM Messages m
            JOIN Users u ON m.FromUserID = u.UserID
            LEFT JOIN Members mem ON u.MemberID = mem.MemberID
            WHERE m.ToUserType = 'librarian' 
                  AND m.IsRead = 0
                  AND (LOWER(m.Subject) LIKE '%book%' 
                       OR LOWER(m.Subject) LIKE '%loan%'
                       OR LOWER(m.Subject) LIKE '%request%'
                       OR LOWER(m.Message) LIKE '%book%')
            ORDER BY m.SentDate DESC
            LIMIT 10
        ''', ())
        
        requests = cursor.fetchall()
        
        for req in requests:
            book_requests.append({
                'message_id': req[0],
                'from_user_id': req[1],
                'subject': req[2],
                'message': req[3],
                'sent_date': req[4],
                'priority': req[5] or 'normal',
                'sender_name': req[6],
                'member_id': req[7] or 'Unknown'
            })
        
        conn.close()
    except Exception as e:
        print(f"Error getting book requests: {e}")
    
    # Get recent loans for the sidebar
    recent_loans = []
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, l.LoanDate, m.Name
            FROM Loans l
            JOIN Books b ON l.ISBN = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            ORDER BY l.LoanDate DESC
            LIMIT 10
        ''')
        recent_loans = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Error getting recent loans: {e}")
    
    return render_template('loan_book.html', 
                         books=books, 
                         members=members, 
                         book_requests=book_requests,
                         recent_loans=recent_loans)

@app.route('/send_reminders')
@librarian_required
def send_reminders():
    overdue_loans = library.get_overdue_loans()
    return render_template('send_reminders.html', overdue_loans=overdue_loans)

# ===== ENHANCED ROUTES =====

# Analytics & Reports
@app.route('/analytics')
@librarian_required
def analytics():
    popular_books = library.get_popular_books(20)
    member_stats = library.get_member_activity_stats()
    loan_trends = library.get_loan_trends(30)
    return render_template('analytics.html', 
                         popular_books=popular_books,
                         member_stats=member_stats,
                         loan_trends=loan_trends)

@app.route('/reports', endpoint='reports')
def reports_page():
    return "<h1>Reports page under construction</h1>"

@app.route('/revenue-report', endpoint='revenue_report')
def revenue_report():
    return "<h1>Revenue Report Page - Coming Soon!</h1>"



# Advanced Book Management
@app.route('/book_categories')
@librarian_required
def book_categories():
    categories = library.get_book_categories()
    return render_template('book_categories.html', categories=categories)

@app.route('/add_category', methods=['POST'])
@librarian_required
def add_category():
    name = request.form['name']
    description = request.form.get('description', '')
    success, message = library.add_book_category(name, description)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('book_categories'))

@app.route('/advanced_search')
@login_required
def advanced_search():
    title = request.args.get('title')
    author = request.args.get('author')
    genre = request.args.get('genre')
    year_from = request.args.get('year_from')
    year_to = request.args.get('year_to')
    availability = request.args.get('availability')
    
    if any([title, author, genre, year_from, year_to, availability]):
        books = library.advanced_search_books(title, author, genre, 
                                            int(year_from) if year_from else None,
                                            int(year_to) if year_to else None,
                                            availability)
    else:
        books = []
    
    categories = library.get_book_categories()
    return render_template('advanced_search.html', books=books, categories=categories)

@app.route('/bulk_import', methods=['GET', 'POST'])
@librarian_required
def bulk_import():
    if request.method == 'POST':
        # Handle CSV upload and bulk import
        flash('Bulk import feature coming soon!', 'info')
        return redirect(url_for('books'))
    return render_template('bulk_import.html')

@app.route('/inventory_alerts')
@librarian_required
def inventory_alerts():
    low_stock_books = library.get_low_stock_books()
    return render_template('inventory_alerts.html', books=low_stock_books)

# Book Reservations
@app.route('/reservations')
@librarian_required
def reservations():
    # Get all active reservations
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.ReservationID, b.Title, b.Author, m.Name, r.ReservationDate, r.ExpiryDate
        FROM BookReservations r
        JOIN Books b ON r.BookID = b.ISBN
        JOIN Members m ON r.MemberID = m.MemberID
        WHERE r.Status = 'active'
        ORDER BY r.ReservationDate DESC
    ''')
    reservations_list = cursor.fetchall()
    conn.close()
    return render_template('reservations.html', reservations=reservations_list)

@app.route('/create_reservation', methods=['POST'])
@librarian_required
def create_reservation():
    isbn = request.form['isbn']
    member_id = int(request.form['member_id'])
    success, message = library.create_reservation(isbn, member_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('reservations'))

# Enhanced Member Management
@app.route('/member_tiers')
@librarian_required
def member_tiers():
    tiers = library.get_member_tiers()
    return render_template('member_tiers.html', tiers=tiers)

@app.route('/member_profile/<int:member_id>')
@librarian_required
def member_profile(member_id):
    profile = library.get_member_profile(member_id)
    loans = library.get_student_loans(member_id)
    fines = library.get_member_fines(member_id)
    reservations = library.get_member_reservations(member_id)
    return render_template('member_profile.html', 
                         profile=profile, loans=loans, 
                         fines=fines, reservations=reservations)

@app.route('/update_member_tier', methods=['POST'])
@librarian_required
def update_member_tier():
    member_id = int(request.form['member_id'])
    tier_id = int(request.form['tier_id'])
    library.update_member_tier(member_id, tier_id)
    flash('Member tier updated successfully!', 'success')
    return redirect(url_for('member_profile', member_id=member_id))

@app.route('/enhanced_add_member', methods=['GET', 'POST'])
@librarian_required
def enhanced_add_member():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        address = request.form.get('address')
        dob = request.form.get('date_of_birth')
        tier_id = int(request.form.get('tier_id', 1))
        
        member_id = library.add_enhanced_member(name, contact, address, dob, tier_id)
        flash(f'Member "{name}" added successfully with ID: {member_id}', 'success')
        return redirect(url_for('members'))
    
    tiers = library.get_member_tiers()
    return render_template('enhanced_add_member.html', tiers=tiers)

@app.route('/remove_member/<int:member_id>', methods=['POST'])
@librarian_required
def remove_member(member_id):
    """Remove/deactivate a member from the library"""
    try:
        success, message = library.remove_member(member_id)
        
        if success:
            # Log the action for audit trail
            library.log_audit(session['user_id'], f'Removed member ID: {member_id}', 'Members', member_id)
            flash(message, 'success')
        else:
            flash(message, 'error')
    
    except Exception as e:
        flash(f'Error removing member: {str(e)}', 'error')
    
    return redirect(url_for('members'))

# Fines and Fees
@app.route('/fines')
@librarian_required
def fines():
    # Calculate new overdue fines first
    new_fines = library.calculate_overdue_fines()
    if new_fines > 0:
        flash(f'Calculated {new_fines} new overdue fines', 'info')
    
    # Get all unpaid fines
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, m.Name as MemberName, b.Title as BookTitle
        FROM Fines f
        JOIN Members m ON f.MemberID = m.MemberID
        LEFT JOIN Loans l ON f.LoanID = l.LoanID
        LEFT JOIN Books b ON l.BookID = b.ISBN
        WHERE f.Status = 'unpaid'
        ORDER BY f.IssueDate DESC
    ''')
    unpaid_fines = cursor.fetchall()
    conn.close()
    
    return render_template('fines.html', fines=unpaid_fines)

@app.route('/pay_fine/<int:fine_id>')
@librarian_required
def pay_fine(fine_id):
    library.pay_fine(fine_id)
    flash('Fine marked as paid!', 'success')
    return redirect(url_for('fines'))


# Messaging System
@app.route('/messages')
@login_required
def messages():
    user_messages = library.get_user_messages(session['user_id'])
    return render_template('messages.html', messages=user_messages)

@app.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        to_user_id = int(request.form['to_user_id'])
        subject = request.form['subject']
        message = request.form['message']
        priority = request.form.get('priority', 'normal')
        
        library.send_message(session['user_id'], to_user_id, subject, message, priority=priority)
        flash('Message sent successfully!', 'success')
        return redirect(url_for('messages'))
    
    # Get all users for recipient selection
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT UserID, Name, UserType FROM Users WHERE UserID != ?', (session['user_id'],))
    users = cursor.fetchall()
    conn.close()
    
    return render_template('send_message.html', users=users)

@app.route('/mark_message_read/<int:message_id>')
@login_required
def mark_message_read(message_id):
    library.mark_message_read(message_id)
    return redirect(url_for('messages'))

# Student message to librarian route
@app.route('/student/send_message', methods=['POST'])
@student_required
def student_send_message():
    from flask import jsonify
    try:
        data = request.get_json()
        subject = data.get('subject', 'Student Inquiry')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Get all librarians to send the message to
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT UserID FROM Users WHERE UserType = "librarian"')
        librarians = cursor.fetchall()
        conn.close()
        
        if not librarians:
            return jsonify({'success': False, 'error': 'No librarians available to receive messages'}), 500
        
        # Send message to all librarians
        for librarian in librarians:
            library.send_message(
                from_user_id=session['user_id'],
                to_user_id=librarian[0],
                subject=subject,
                message=message,
                message_type='student_inquiry',
                priority='normal'
            )
        
        return jsonify({'success': True, 'message': 'Message sent to librarian successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Book request route
@app.route('/student/request_book', methods=['POST'])
@student_required
def student_request_book():
    from flask import jsonify
    try:
        data = request.get_json()
        isbn = data.get('isbn', '')
        title = data.get('title', '')
        author = data.get('author', '')
        note = data.get('note', '')
        
        if not isbn or not title:
            return jsonify({'success': False, 'error': 'Book information missing'}), 400
        
        # Get student name and member ID from session
        student_name = session.get('name', 'Unknown Student')
        student_member_id = session.get('member_id', 'N/A')
        
        # Create message content with student information
        message_content = f"Book Request from: {student_name} (Member ID: {student_member_id})\n\n"
        message_content += f"Book Details:\n"
        message_content += f"- Title: \"{title}\"\n"
        message_content += f"- Author: {author}\n"
        message_content += f"- ISBN: {isbn}\n\n"
        
        if note:
            message_content += f"Student's Note: {note}\n\n"
        
        message_content += f"Please process this book request at your earliest convenience."
        
        # Get all librarians to send the message to
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT UserID FROM Users WHERE UserType = "librarian"')
        librarians = cursor.fetchall()
        conn.close()
        
        if not librarians:
            return jsonify({'success': False, 'error': 'No librarians available to receive requests'}), 500
        
        # Send request to all librarians
        for librarian in librarians:
            library.send_message(
                from_user_id=session['user_id'],
                to_user_id=librarian[0],
                subject=f'Book Request from {student_name}: {title}',
                message=message_content,
                message_type='book_request',
                priority='normal'
            )
        
        return jsonify({'success': True, 'message': f'Book request for "{title}" sent to librarian!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/librarian/reply_message', methods=['POST'])
@librarian_required
def librarian_reply_message():
    from flask import jsonify
    try:
        data = request.get_json()
        original_message_id = data.get('original_message_id')
        reply_message = data.get('message', '')
        student_user_id = data.get('student_user_id')
        subject = data.get('subject', 'Re: Message from Librarian')
        
        if not all([original_message_id, reply_message, student_user_id]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Send reply to student
        library.send_message(
            from_user_id=session['user_id'],
            to_user_id=student_user_id,
            subject=subject,
            message=reply_message,
            message_type='librarian_reply',
            priority='normal'
        )
        
        # Mark original message as read
        library.mark_message_read(original_message_id)
        
        return jsonify({
            'success': True, 
            'message': 'Reply sent successfully!'
        })
        
    except Exception as e:
        print(f"Error sending reply: {e}")
        return jsonify({'success': False, 'message': 'Failed to send reply'}), 500

# Handle book requests for books not in system
@app.route('/add_book_from_request', methods=['POST'])
@librarian_required
def add_book_from_request():
    """Add a book from a student request and optionally loan it immediately"""
    from flask import jsonify
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Extract book information
        isbn = data.get('isbn', '').strip()
        title = data.get('title', '').strip()
        author = data.get('author', '').strip()
        genre = data.get('genre', 'General').strip() or 'General'
        year = data.get('year', '')
        
        # Extract request information
        message_id = data.get('message_id')
        member_id = data.get('member_id')
        student_user_id = data.get('student_user_id')
        loan_immediately = data.get('loan_immediately', 'false').lower() == 'true'
        
        # Validation
        if not all([isbn, title, author]):
            return jsonify({'success': False, 'error': 'ISBN, Title, and Author are required'}), 400
        
        # Set default year if not provided
        try:
            publication_year = int(year) if year else 2024
        except ValueError:
            publication_year = 2024
        
        # Add book to system
        success, message = library.add_book(isbn, title, author, genre, publication_year)
        
        if not success:
            return jsonify({'success': False, 'error': message}), 400
        
        # Log the action
        library.log_audit(session['user_id'], f'Added book from request: {title} (ISBN: {isbn})', 'Books', isbn)
        
        response_data = {'success': True, 'message': f'Book "{title}" added successfully!'}
        
        # If requested, loan the book immediately
        if loan_immediately and member_id:
            try:
                loan_success, loan_message = library.loan_book(isbn, int(member_id))
                if loan_success:
                    response_data['message'] += f' Book loaned successfully to member.'  
                    # Log loan action
                    library.log_audit(session['user_id'], f'Loaned book from request: {isbn} to member {member_id}')
                    
                    # Send success message to student
                    if student_user_id:
                        library.send_message(
                            from_user_id=session['user_id'],
                            to_user_id=int(student_user_id),
                            subject=f'Book Request Approved: {title}',
                            message=f'Good news! Your requested book "{title}" by {author} has been added to our library and is now loaned to you. Please visit the library to collect it.',
                            message_type='librarian_reply',
                            priority='high'
                        )
                else:
                    response_data['warning'] = f'Book added but loan failed: {loan_message}'
            except Exception as e:
                response_data['warning'] = f'Book added but loan failed: {str(e)}'
        
        # Mark original request message as read
        if message_id:
            library.mark_message_read(int(message_id))
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error adding book from request: {e}")
        return jsonify({'success': False, 'error': f'Failed to process request: {str(e)}'}), 500

@app.route('/extract_book_info_from_message', methods=['POST'])
@librarian_required
def extract_book_info_from_message():
    """Extract book information from a message text"""
    from flask import jsonify
    import re
    try:
        data = request.get_json()
        message_text = data.get('message', '')
        
        # Initialize extracted info
        extracted_info = {
            'title': '',
            'author': '',
            'isbn': '',
            'genre': 'General'
        }
        
        
        
        # Try to extract author
        author_patterns = [
            r'- Author:\s*([^\r\n]*)',
            r'Author:\s*([^\r\n]*)',
            r'by\s+([^\r\n(]*?)(?:\s*\(|\s*$)',
            r'written by\s+([^\r\n]*)',
            r'author\s*:?\s*([^\r\n]*)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                extracted_info['author'] = match.group(1).strip()
                break
        
        # Try to extract ISBN
        isbn_patterns = [
            r'- ISBN:\s*([^\r\n]*)',
            r'ISBN:\s*([^\r\n]*)',
            r'ISBN[\s-]*([0-9X-]{10,17})',
            r'\b(\d{9}[\dX])\b',  # ISBN-10
            r'\b(\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-[\dX])\b'  # ISBN-13 with hyphens
        ]
        
        for pattern in isbn_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                extracted_info['isbn'] = match.group(1).strip()
                break
        
        # If no ISBN found, generate a simple one based on title
        if not extracted_info['isbn'] and extracted_info['title']:
            import hashlib
            title_hash = hashlib.md5(extracted_info['title'].encode()).hexdigest()[:10]
            extracted_info['isbn'] = f"REQ{title_hash.upper()}"
        
        return jsonify({
            'success': True,
            'extracted_info': extracted_info
        })
        
    except Exception as e:
        print(f"Error extracting book info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent_returns')
@librarian_required
def api_recent_returns():
    """Get recent book returns for librarian dashboard"""
    from flask import jsonify
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.LoanID, b.Title, b.Author, m.Name, l.ReturnDate, b.ISBN
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.ReturnDate IS NOT NULL
            ORDER BY l.ReturnDate DESC
            LIMIT 10
        ''')
        returns = cursor.fetchall()
        conn.close()
        
        returns_data = []
        for ret in returns:
            returns_data.append({
                'loan_id': ret[0],
                'book_title': ret[1],
                'book_author': ret[2],
                'member_name': ret[3],
                'return_date': ret[4],
                'isbn': ret[5]
            })
        
        return jsonify({'success': True, 'returns': returns_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/student_dashboard_refresh')
@student_required
def api_student_dashboard_refresh():
    """Refresh student dashboard data via API"""
    from flask import jsonify
    try:
        member_id = session.get('member_id')
        if not member_id:
            return jsonify({'success': False, 'error': 'Member ID not found'}), 400
        
        # Get updated loan information
        loans = library.get_student_loans(member_id)
        recent_returns = library.get_student_recent_returns(member_id)
        return_notifications = library.get_student_return_notifications(member_id)
        
        # Get updated book count
        books = library.get_all_books()
        available_books_count = len([b for b in books if b[5] == 'Available'])
        
        # Get updated messages
        student_messages = library.get_user_messages(session['user_id'])
        librarian_messages = [msg for msg in student_messages if msg[8] == 'librarian_reply']
        
        # Format data for JSON response
        loans_data = []
        for loan in loans:
            loans_data.append({
                'loan_id': loan[0],
                'title': loan[1],
                'author': loan[2],
                'loan_date': loan[3],
                'due_date': loan[4],
                'return_date': loan[5],
                'is_overdue': loan[6]
            })
        
        returns_data = []
        for ret in recent_returns:
            returns_data.append({
                'loan_id': ret[0],
                'title': ret[1],
                'author': ret[2],
                'loan_date': ret[3],
                'due_date': ret[4],
                'return_date': ret[5],
                'isbn': ret[6]
            })
        
        messages_data = []
        for msg in librarian_messages:
            messages_data.append({
                'message_id': msg[0],
                'subject': msg[4],
                'message': msg[5],
                'sent_date': msg[6],
                'is_read': msg[7],
                'sender_name': msg[10] if len(msg) > 10 else 'Librarian'
            })
        
        notifications_data = []
        for notif in return_notifications:
            notifications_data.append({
                'message_id': notif[0],
                'subject': notif[1],
                'message': notif[2],
                'sent_date': notif[3],
                'is_read': notif[4]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'loans': loans_data,
                'recent_returns': returns_data,
                'available_books_count': available_books_count,
                'messages': messages_data,
                'return_notifications': notifications_data,
                'stats': {
                    'active_loans': len([l for l in loans if l[5] is None]),
                    'overdue_books': len([l for l in loans if l[6] == 1]),
                    'recent_returns_count': len(returns_data)
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Announcements
@app.route('/announcements')
@login_required
def announcements():
    user_type = session.get('user_type', 'all')
    announcements_list = library.get_active_announcements(user_type)
    return render_template('announcements.html', announcements=announcements_list)

@app.route('/create_announcement', methods=['GET', 'POST'])
@librarian_required
def create_announcement():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        expiry_date = request.form.get('expiry_date')
        priority = request.form.get('priority', 'normal')
        target_audience = request.form.get('target_audience', 'all')
        
        library.create_announcement(title, content, session['user_id'], 
                                  expiry_date, priority, target_audience)
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('announcements'))
    
    return render_template('create_announcement.html')

# System Administration
@app.route('/system_settings')
@librarian_required
def system_settings():
    settings = library.get_all_settings()
    return render_template('system_settings.html', settings=settings)

@app.route('/update_setting', methods=['POST'])
@librarian_required
def update_setting():
    key = request.form['key']
    value = request.form['value']
    library.update_system_setting(key, value)
    flash(f'Setting "{key}" updated successfully!', 'success')
    return redirect(url_for('system_settings'))

@app.route('/audit_logs')
@librarian_required
def audit_logs():
    limit = int(request.args.get('limit', 100))
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    
    logs = library.get_audit_logs(limit, 
                                int(user_id) if user_id else None, 
                                action)
    
    # Get all users for filtering
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT UserID, Name FROM Users ORDER BY Name')
    users = cursor.fetchall()
    conn.close()
    
    return render_template('audit_logs.html', logs=logs, users=users)

@app.route('/user_management')
@librarian_required
def user_management():
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT UserID, Username, Name, UserType, Email, CreatedDate FROM Users ORDER BY Name')
    users = cursor.fetchall()
    conn.close()
    return render_template('user_management.html', users=users)

@app.route('/create_user', methods=['POST'])
@librarian_required
def create_user():
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    email = request.form['email']
    user_type = request.form['user_type']
    
    conn = library.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Users (Username, Password, UserType, Name, Email)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, user_type, name, email))
        conn.commit()
        flash(f'User "{name}" created successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Username "{username}" already exists!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

# Quick Actions
@app.route('/quick_loan', methods=['POST'])
@librarian_required
def quick_loan():
    isbn = request.form['isbn']
    member_id = int(request.form['member_id'])
    success, message = library.loan_book(isbn, member_id)
    
    if success:
        # Log the action
        library.log_audit(session['user_id'], f'Quick loan: {isbn} to member {member_id}')
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(request.referrer or url_for('librarian_dashboard'))

@app.route('/return_book/<int:loan_id>')
@librarian_required
def return_book(loan_id):
    conn = library.get_connection()
    cursor = conn.cursor()
    
    # Get loan details including member and book information
    cursor.execute('''
        SELECT l.BookID, l.MemberID, b.Title, b.Author, m.Name, u.UserID
        FROM Loans l
        JOIN Books b ON l.BookID = b.ISBN
        JOIN Members m ON l.MemberID = m.MemberID
        LEFT JOIN Users u ON m.MemberID = u.MemberID
        WHERE l.LoanID = ?
    ''', (loan_id,))
    loan_result = cursor.fetchone()
    
    if loan_result:
        book_id, member_id, book_title, book_author, member_name, student_user_id = loan_result
        
        # Update loan record
        cursor.execute('UPDATE Loans SET ReturnDate = date("now") WHERE LoanID = ?', (loan_id,))
        # Update book availability
        cursor.execute('UPDATE Books SET AvailabilityStatus = "Available" WHERE ISBN = ?', (book_id,))
        
        # Send confirmation message to student if they have a user account
        if student_user_id:
            return_message = f"""Book Return Confirmation
            
Dear {member_name},
            
Your book has been successfully returned to the library:
            
📚 Book Details:
            - Title: "{book_title}"
            - Author: {book_author}
            - ISBN: {book_id}
            - Return Date: {datetime.now().strftime('%Y-%m-%d')}
            
Thank you for returning your book on time!
            
Best regards,
            Library Staff"""
            
            cursor.execute('''
                INSERT INTO Messages (FromUserID, ToUserID, Subject, Message, MessageType, Priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], student_user_id, f'Book Return Confirmation: {book_title}', 
                 return_message, 'return_confirmation', 'normal'))
        
        conn.commit()
        
        # Log the action
        library.log_audit(session['user_id'], f'Book returned: {book_title} by {member_name} (LoanID {loan_id})')
        flash(f'Book "{book_title}" returned successfully by {member_name}!', 'success')
    else:
        flash('Loan not found!', 'error')
    
    conn.close()
    return redirect(request.referrer or url_for('loans'))

# Student message API routes
@app.route('/student/mark_message_read', methods=['POST'])
@student_required
def student_mark_message_read():
    from flask import jsonify
    try:
        data = request.get_json()
        message_id = data.get('message_id')
        
        if not message_id:
            return jsonify({'success': False, 'error': 'Message ID required'}), 400
        
        library.mark_message_read(message_id)
        return jsonify({'success': True, 'message': 'Message marked as read'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/student/get_all_messages')
@student_required
def student_get_all_messages():
    from flask import jsonify
    try:
        # Get messages from librarians (replies to student's messages)
        student_messages = library.get_user_messages(session['user_id'])
        # Filter for messages from librarians (message_type='librarian_reply')
        librarian_messages = [msg for msg in student_messages if msg[8] == 'librarian_reply']
        
        # Format messages for JSON response
        messages_data = []
        for msg in librarian_messages:
            messages_data.append({
                'message_id': msg[0],
                'from_user_id': msg[1],
                'to_user_id': msg[2],
                'to_user_type': msg[3],
                'subject': msg[4],
                'message': msg[5],
                'sent_date': msg[6],
                'is_read': msg[7],
                'message_type': msg[8],
                'priority': msg[9],
                'sender_name': msg[10] if len(msg) > 10 else 'Librarian'
            })
        
        return jsonify({'success': True, 'messages': messages_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Dashboard APIs for AJAX calls
@app.route('/api/dashboard_stats')
@librarian_required
def api_dashboard_stats():
    from flask import jsonify
    stats = library.get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/recent_activities')
@librarian_required
def api_recent_activities():
    from flask import jsonify
    # Get recent loans, returns, etc.
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 'loan' as type, l.LoanDate as date, b.Title, m.Name
        FROM Loans l
        JOIN Books b ON l.BookID = b.ISBN
        JOIN Members m ON l.MemberID = m.MemberID
        WHERE l.LoanDate >= date('now', '-7 days')
        ORDER BY l.LoanDate DESC
        LIMIT 10
    ''')
    activities = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'type': activity[0],
        'date': activity[1],
        'book_title': activity[2],
        'member_name': activity[3]
    } for activity in activities])

# Additional API routes for system functionality
@app.route('/api/calculate_fines', methods=['POST'])
@librarian_required
def api_calculate_fines():
    from flask import jsonify
    try:
        fines_created = library.calculate_overdue_fines()
        return jsonify({
            'success': True,
            'fines_created': fines_created,
            'message': f'Successfully calculated {fines_created} new fines.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/deactivate_announcement/<int:announcement_id>', methods=['POST'])
@librarian_required
def deactivate_announcement(announcement_id):
    from flask import jsonify
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Announcements SET Status = "inactive" WHERE AnnouncementID = ?', (announcement_id,))
        conn.commit()
        conn.close()
        
        # Log the action
        library.log_audit(session['user_id'], f'Deactivated announcement ID {announcement_id}')
        
        return jsonify({
            'success': True,
            'message': 'Announcement deactivated successfully.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/update_announcement', methods=['POST'])
@librarian_required
def update_announcement():
    announcement_id = request.form['announcement_id']
    title = request.form['title']
    content = request.form['content']
    priority = request.form.get('priority', 'normal')
    target_audience = request.form.get('target_audience', 'all')
    expiry_date = request.form.get('expiry_date')
    
    conn = library.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Announcements 
        SET Title = ?, Content = ?, Priority = ?, TargetAudience = ?, ExpiryDate = ?
        WHERE AnnouncementID = ?
    ''', (title, content, priority, target_audience, expiry_date, announcement_id))
    conn.commit()
    conn.close()
    
    # Log the action
    library.log_audit(session['user_id'], f'Updated announcement: {title}')
    
    flash('Announcement updated successfully!', 'success')
    return redirect(url_for('announcements'))

@app.route('/update_user', methods=['POST'])
@librarian_required
def update_user():
    user_id = int(request.form['user_id'])
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    user_type = request.form['user_type']
    
    conn = library.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE Users 
            SET Username = ?, Name = ?, Email = ?, UserType = ?
            WHERE UserID = ?
        ''', (username, name, email, user_type, user_id))
        conn.commit()
        
        # Log the action
        library.log_audit(session['user_id'], f'Updated user: {name} (ID: {user_id})')
        
        flash(f'User "{name}" updated successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Username "{username}" already exists!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

# API Routes for enhanced loan processing
@app.route('/api/member_loan_details/<int:member_id>')
@librarian_required
def get_member_loan_details(member_id):
    """Get current loan status for a member"""
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get current loans count
        cursor.execute('''
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL
        ''', (member_id,))
        current_loans = cursor.fetchone()[0]
        
        # Get overdue books count
        cursor.execute('''
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL AND DueDate < DATE('now')
        ''', (member_id,))
        overdue_books = cursor.fetchone()[0]
        
        # Get outstanding fines
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) FROM Fines 
            WHERE MemberID = ? AND Status = 'unpaid'
        ''', (member_id,))
        outstanding_fines = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'current_loans': current_loans,
            'overdue_books': overdue_books,
            'outstanding_fines': float(outstanding_fines)
        }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/member_full_details/<int:member_id>')
@librarian_required
def get_member_full_details(member_id):
    """Get comprehensive member details including loan history"""
    try:
        conn = library.get_connection()
        cursor = conn.cursor()
        
        # Get member basic info
        cursor.execute('''
            SELECT MemberID, Name, Email, Phone, Address, JoinDate 
            FROM Members WHERE MemberID = ?
        ''', (member_id,))
        member_info = cursor.fetchone()
        
        if not member_info:
            return {'error': 'Member not found'}, 404
        
        # Get loan statistics
        cursor.execute('''
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL
        ''', (member_id,))
        current_loans = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL AND DueDate < DATE('now')
        ''', (member_id,))
        overdue_books = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM Loans WHERE MemberID = ?
        ''', (member_id,))
        total_borrowed = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(Amount), 0) FROM Fines 
            WHERE MemberID = ? AND Status = 'unpaid'
        ''', (member_id,))
        outstanding_fines = cursor.fetchone()[0]
        
        # Get recent loan history
        cursor.execute('''
            SELECT b.Title, l.LoanDate 
            FROM Loans l
            JOIN Books b ON l.ISBN = b.ISBN
            WHERE l.MemberID = ?
            ORDER BY l.LoanDate DESC
            LIMIT 5
        ''', (member_id,))
        recent_loans = cursor.fetchall()
        
        conn.close()
        
        return {
            'member_id': member_info[0],
            'name': member_info[1],
            'email': member_info[2],
            'phone': member_info[3],
            'address': member_info[4],
            'join_date': member_info[5],
            'current_loans': current_loans,
            'overdue_books': overdue_books,
            'total_borrowed': total_borrowed,
            'outstanding_fines': float(outstanding_fines),
            'recent_loans': [{
                'book_title': loan[0],
                'loan_date': loan[1]
            } for loan in recent_loans]
        }
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
