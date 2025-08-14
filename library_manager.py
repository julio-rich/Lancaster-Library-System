import sqlite3
from datetime import datetime, timedelta

class User:
    def __init__(self, username, password, role, name, email):
        self.username = username
        self.password = password
        self.role = role
        self.name = name
        self.email = email

class LibraryManager:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def add_book(self, isbn, title, author, genre, publication_year):
        """Add a new book to the library"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO Books (ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus)
                VALUES (?, ?, ?, ?, ?, 'Available')
            ''', (isbn, title, author, genre, publication_year))
            
            conn.commit()
            print(f"Book '{title}' added successfully!")
            
        except sqlite3.IntegrityError:
            print(f"Error: Book with ISBN {isbn} already exists!")
        
        finally:
            conn.close()
    
    def add_member(self, name, contact_info):
        """Add a new member to the library"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        registration_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO Members (Name, ContactInfo, RegistrationDate)
            VALUES (?, ?, ?)
        ''', (name, contact_info, registration_date))
        
        conn.commit()
        member_id = cursor.lastrowid
        print(f"Member '{name}' added successfully with ID: {member_id}")
        conn.close()
        
        return member_id
    
    def loan_book(self, isbn, member_id, loan_days=14):
        """Loan a book to a member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if book is available
        cursor.execute('SELECT AvailabilityStatus FROM Books WHERE ISBN = ?', (isbn,))
        result = cursor.fetchone()
        
        if not result:
            print("Error: Book not found!")
            conn.close()
            return
        
        if result[0] != 'Available':
            print("Error: Book is not available!")
            conn.close()
            return
        
        # Check if member exists
        cursor.execute('SELECT Name FROM Members WHERE MemberID = ?', (member_id,))
        member = cursor.fetchone()
        
        if not member:
            print("Error: Member not found!")
            conn.close()
            return
        
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
        print(f"Book loaned successfully to {member[0]}. Due date: {due_date}")
        conn.close()
    
    def return_book(self, isbn):
        """Return a book"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Find the active loan
        cursor.execute('''
            SELECT LoanID FROM Loans 
            WHERE BookID = ? AND ReturnDate IS NULL
        ''', (isbn,))
        
        loan = cursor.fetchone()
        
        if not loan:
            print("Error: No active loan found for this book!")
            conn.close()
            return
        
        # Update loan record
        return_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            UPDATE Loans SET ReturnDate = ? WHERE LoanID = ?
        ''', (return_date, loan[0]))
        
        # Update book availability
        cursor.execute('''
            UPDATE Books SET AvailabilityStatus = 'Available' WHERE ISBN = ?
        ''', (isbn,))
        
        conn.commit()
        print("Book returned successfully!")
        conn.close()
    
    def search_books(self, search_term):
        """Search for books by title or author"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus
            FROM Books
            WHERE Title LIKE ? OR Author LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        books = cursor.fetchall()
        
        if books:
            print("\nSearch Results:")
            print("-" * 80)
            for book in books:
                print(f"ISBN: {book[0]}")
                print(f"Title: {book[1]}")
                print(f"Author: {book[2]}")
                print(f"Genre: {book[3]}")
                print(f"Year: {book[4]}")
                print(f"Status: {book[5]}")
                print("-" * 80)
        else:
            print("No books found matching your search.")
        
        conn.close()
    
    def view_all_books(self):
        """Display all books in the library"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM Books')
        books = cursor.fetchall()
        
        if books:
            print("\nAll Books in Library:")
            print("-" * 80)
            for book in books:
                print(f"ISBN: {book[0]}")
                print(f"Title: {book[1]}")
                print(f"Author: {book[2]}")
                print(f"Genre: {book[3]}")
                print(f"Year: {book[4]}")
                print(f"Status: {book[5]}")
                print("-" * 80)
        else:
            print("No books found in the library.")
        
        conn.close()
    
    def view_overdue_books(self):
        """Display overdue books"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT l.LoanID, b.Title, m.Name, l.DueDate
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.DueDate < ? AND l.ReturnDate IS NULL
        ''', (today,))
        
        overdue = cursor.fetchall()
        
        if overdue:
            print("\nOverdue Books:")
            print("-" * 60)
            for loan in overdue:
                print(f"Loan ID: {loan[0]}")
                print(f"Book: {loan[1]}")
                print(f"Member: {loan[2]}")
                print(f"Due Date: {loan[3]}")
                print("-" * 60)
        else:
            print("No overdue books!")
        
        conn.close()

def authenticate(username, password):
    """Authenticate user credentials"""
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT Username, Password, Role, Name, Email FROM Users WHERE Username = ? AND Password = ?', (username, password))
    user = cursor.fetchone()
    
    if user:
        return User(*user)
    else:
        return None

# Interface for Librarian
def librarian_interface(library):
    while True:
        print("\n=== Librarian Menu ===")
        print("1. Add Book")
        print("2. Add Member")
        print("3. Loan Book")
        print("4. Return Book")
        print("5. View All Books")
        print("6. View Overdue Books")
        print("7. Logout")
        
        choice = input("Enter your choice (1-7): ")
        
        if choice == '1':
            isbn = input("Enter ISBN: ")
            title = input("Enter Title: ")
            author = input("Enter Author: ")
            genre = input("Enter Genre: ")
            year = int(input("Enter Publication Year: "))
            library.add_book(isbn, title, author, genre, year)
        
        elif choice == '2':
            name = input("Enter Member Name: ")
            contact = input("Enter Contact Info: ")
            library.add_member(name, contact)
        
        elif choice == '3':
            isbn = input("Enter Book ISBN: ")
            member_id = int(input("Enter Member ID: "))
            library.loan_book(isbn, member_id)
        
        elif choice == '4':
            isbn = input("Enter Book ISBN: ")
            library.return_book(isbn)
        
        elif choice == '5':
            library.view_all_books()
        
        elif choice == '6':
            library.view_overdue_books()
        
        elif choice == '7':
            break
        
        else:
            print("Invalid choice! Please try again.")

# Interface for Student

def student_interface(library):
    while True:
        print("\n=== Student Menu ===")
        print("1. Search Books")
        print("2. Logout")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == '1':
            search_term = input("Enter search term (title or author): ")
            library.search_books(search_term)
        
        elif choice == '2':
            break
        
        else:
            print("Invalid choice! Please try again.")

# Main function for authentication and interface selection

def main():
    library = LibraryManager()
    
    print("Welcome to the Library System")
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    user = authenticate(username, password)
    
    if user:
        print(f"\nWelcome {user.name}!")
        if user.role == 'librarian':
            librarian_interface(library)
        elif user.role == 'student':
            student_interface(library)
    else:
        print("Invalid credentials!")

if __name__ == "__main__":
    main()
