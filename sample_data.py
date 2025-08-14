from library_manager import LibraryManager

def populate_sample_data():
    """Populate the database with sample data for testing"""
    library = LibraryManager()
    
    print("Adding sample data to the library database...")
    
    # Add sample books
    books = [
        ("978-0134685991", "Effective Java", "Joshua Bloch", "Programming", 2017),
        ("978-0596009205", "Head First Design Patterns", "Eric Freeman", "Programming", 2004),
        ("978-0132350884", "Clean Code", "Robert Martin", "Programming", 2008),
        ("978-0201633610", "Design Patterns", "Gang of Four", "Programming", 1994),
        ("978-0134494166", "The Clean Coder", "Robert Martin", "Programming", 2011),
        ("978-0321563842", "The Art of Computer Programming", "Donald Knuth", "Computer Science", 2011),
        ("978-0262033848", "Introduction to Algorithms", "Thomas Cormen", "Computer Science", 2009),
        ("978-0134052427", "Computer Networks", "Andrew Tanenbaum", "Networking", 2010),
        ("978-0321486813", "Compilers: Principles, Techniques, and Tools", "Alfred Aho", "Computer Science", 2006),
        ("978-0133594140", "Computer Organization and Design", "David Patterson", "Computer Architecture", 2013)
    ]
    
    for isbn, title, author, genre, year in books:
        library.add_book(isbn, title, author, genre, year)
    
    # Add sample members
    members = [
        ("Alice Johnson", "alice@email.com"),
        ("Bob Smith", "bob@email.com"),
        ("Charlie Brown", "charlie@email.com"),
        ("Diana Prince", "diana@email.com"),
        ("Eve Davis", "eve@email.com")
    ]
    
    member_ids = []
    for name, contact in members:
        member_id = library.add_member(name, contact)
        member_ids.append(member_id)
    
    # Create some loan transactions
    print("\nCreating sample loan transactions...")
    library.loan_book("978-0134685991", member_ids[0])  # Alice loans Effective Java
    library.loan_book("978-0596009205", member_ids[1])  # Bob loans Head First Design Patterns
    library.loan_book("978-0132350884", member_ids[2])  # Charlie loans Clean Code
    
    # Add sample users (students)
    print("\nAdding sample users...")
    
    import sqlite3
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    # Add student users
    students = [
        ('student1', 'pass123', 'student', 'John Doe', 'john.doe@university.edu'),
        ('student2', 'pass123', 'student', 'Jane Smith', 'jane.smith@university.edu'),
        ('alice', 'alice123', 'student', 'Alice Johnson', 'alice.johnson@university.edu')
    ]
    
    for username, password, role, name, email in students:
        try:
            cursor.execute('''
                INSERT INTO Users (Username, Password, Role, Name, Email)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, role, name, email))
            print(f"Student user '{username}' added successfully!")
        except sqlite3.IntegrityError:
            print(f"User '{username}' already exists!")
    
    conn.commit()
    conn.close()
    
    print("\nSample data has been successfully added to the database!")
    print("\nLogin credentials:")
    print("Librarian: username='admin', password='admin123'")
    print("Students: username='student1' or 'student2' or 'alice', password='pass123' or 'alice123'")
    print("\nYou can now test the library management system with this data.")

if __name__ == "__main__":
    populate_sample_data()
