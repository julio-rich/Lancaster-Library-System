import sqlite3

conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print('Existing tables:', tables)

# Initialize missing tables if needed
if 'Books' not in tables:
    print('Creating Books table...')
    cursor.execute('''
        CREATE TABLE Books (
            ISBN TEXT PRIMARY KEY,
            Title TEXT NOT NULL,
            Author TEXT NOT NULL,
            Genre TEXT,
            PublicationYear INTEGER,
            AvailabilityStatus TEXT DEFAULT 'Available'
        )
    ''')
    
    # Add sample books
    sample_books = [
        ('978-0-13-110362-7', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 1925, 'Available'),
        ('978-0-06-112008-4', 'To Kill a Mockingbird', 'Harper Lee', 'Fiction', 1960, 'Available'),
        ('978-0-452-28423-4', '1984', 'George Orwell', 'Dystopian Fiction', 1949, 'Available'),
        ('978-0-7432-7356-5', 'The Da Vinci Code', 'Dan Brown', 'Mystery', 2003, 'Available'),
        ('978-0-14-118776-1', 'Pride and Prejudice', 'Jane Austen', 'Romance', 1813, 'Available')
    ]
    
    cursor.executemany('''
        INSERT INTO Books (ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_books)
    print('Added sample books')

if 'Members' not in tables:
    print('Creating Members table...')
    cursor.execute('''
        CREATE TABLE Members (
            MemberID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            ContactInfo TEXT,
            RegistrationDate DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Add sample members
    sample_members = [
        ('John Doe', 'john.doe@email.com'),
        ('Jane Smith', 'jane.smith@email.com'),
        ('Bob Johnson', 'bob.johnson@email.com')
    ]
    
    cursor.executemany('''
        INSERT INTO Members (Name, ContactInfo)
        VALUES (?, ?)
    ''', sample_members)
    print('Added sample members')

if 'Loans' not in tables:
    print('Creating Loans table...')
    cursor.execute('''
        CREATE TABLE Loans (
            LoanID INTEGER PRIMARY KEY AUTOINCREMENT,
            BookID TEXT,
            MemberID INTEGER,
            LoanDate DATE,
            DueDate DATE,
            ReturnDate DATE,
            FOREIGN KEY (BookID) REFERENCES Books(ISBN),
            FOREIGN KEY (MemberID) REFERENCES Members(MemberID)
        )
    ''')
    print('Created Loans table')

# Check counts
cursor.execute('SELECT COUNT(*) FROM Books')
books_count = cursor.fetchone()[0]
print(f'Books count: {books_count}')

cursor.execute('SELECT COUNT(*) FROM Members')
members_count = cursor.fetchone()[0]
print(f'Members count: {members_count}')

cursor.execute('SELECT COUNT(*) FROM Loans')
loans_count = cursor.fetchone()[0]
print(f'Loans count: {loans_count}')

conn.commit()
conn.close()
print('Database check complete!')
