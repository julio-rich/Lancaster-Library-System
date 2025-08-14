import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('library.db')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# Drop tables if they already exist
cursor.execute('''DROP TABLE IF EXISTS Books''')
cursor.execute('''DROP TABLE IF EXISTS Members''')
cursor.execute('''DROP TABLE IF EXISTS Loans''')
cursor.execute('''DROP TABLE IF EXISTS Authors''')
cursor.execute('''DROP TABLE IF EXISTS Categories''')

# Create Books table
cursor.execute('''
CREATE TABLE Books (
    ISBN TEXT PRIMARY KEY,
    Title TEXT NOT NULL,
    Author TEXT NOT NULL,
    Genre TEXT,
    PublicationYear INT,
    AvailabilityStatus TEXT
)
''')

# Create Members table
cursor.execute('''
CREATE TABLE Members (
    MemberID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    ContactInfo TEXT,
    RegistrationDate DATE
)
''')

# Create Loans table
cursor.execute('''
CREATE TABLE Loans (
    LoanID INTEGER PRIMARY KEY AUTOINCREMENT,
    BookID TEXT NOT NULL,
    MemberID INT NOT NULL,
    LoanDate DATE,
    DueDate DATE,
    ReturnDate DATE,
    FOREIGN KEY (BookID) REFERENCES Books(ISBN),
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
)
''')

# Create Authors table (optional)
cursor.execute('''
CREATE TABLE Authors (
    AuthorID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Biography TEXT
)
''')

# Create Categories table (optional)
cursor.execute('''
CREATE TABLE Categories (
    CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    Genre TEXT NOT NULL
)
''')

# Create Users table for authentication
cursor.execute('''
CREATE TABLE Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Role TEXT NOT NULL CHECK(Role IN ('librarian', 'student')),
    Name TEXT NOT NULL,
    Email TEXT,
    CreatedDate DATE DEFAULT CURRENT_DATE
)
''')

# Default librarian
cursor.execute('''
    INSERT INTO Users (Username, Password, Role, Name, Email)
    VALUES ('libadmin', 'mynewpass', 'librarian', 'Library Administrator', 'admin@library.com')
''')

# Commit the transaction
conn.commit()

# Close the connection
conn.close()

