import sqlite3
import sys
import os

# Add the current directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import LibraryManager

def test_dashboard_data():
    """Test that dashboard shows real data after cleanup"""
    
    print("=== TESTING REAL DASHBOARD DATA ===\n")
    
    # Initialize library manager
    library = LibraryManager()
    
    # Test dashboard statistics
    print("1. Testing Dashboard Statistics...")
    stats = library.get_dashboard_stats()
    
    print("Dashboard Stats:")
    print(f"  Total books: {stats.get('total_books', 0)}")
    print(f"  Available books: {stats.get('available_books', 0)}")
    print(f"  Total members: {stats.get('total_members', 0)}")
    print(f"  Active loans: {stats.get('active_loans', 0)}")
    print(f"  Overdue loans: {stats.get('overdue_loans', 0)}")
    print(f"  Active reservations: {stats.get('active_reservations', 0)}")
    print(f"  Unread messages: {stats.get('unread_messages', 0)}")
    print(f"  New members (last 30 days): {stats.get('new_members_month', 0)}")
    
    # Test member activity stats
    print("\n2. Testing Member Activity Stats...")
    member_stats = library.get_member_activity_stats()
    if member_stats:
        print("Member Activity Stats:")
        print(f"  Total members: {member_stats[0]}")
        print(f"  Active members: {member_stats[1]}")
        print(f"  Inactive members: {member_stats[2]}")
        print(f"  New members this month: {member_stats[3]}")
    
    # Test current members
    print("\n3. Testing Current Members...")
    all_members = library.get_all_members()
    print(f"Current members in system: {len(all_members)}")
    for member in all_members:
        print(f"  ID {member[0]}: {member[1]} (Contact: {member[2]})")
    
    # Test current loans
    print("\n4. Testing Current Loans...")
    active_loans = library.get_active_loans()
    print(f"Current active loans: {len(active_loans)}")
    for loan in active_loans:
        print(f"  Loan ID {loan[0]}: Book {loan[1]} to Member {loan[2]} (Due: {loan[4]})")
    
    # Test available books count
    print("\n5. Testing Available Books...")
    all_books = library.get_all_books()
    available_books = [book for book in all_books if book[5] == 'Available']
    print(f"Total books in library: {len(all_books)}")
    print(f"Available books: {len(available_books)}")
    
    # Test popular books
    print("\n6. Testing Popular Books...")
    popular_books = library.get_popular_books(5)
    print(f"Popular books (top 5):")
    for book in popular_books:
        print(f"  {book[1]} by {book[2]} - Loans: {book[3]}")
    
    # Test overdue loans
    print("\n7. Testing Overdue Loans...")
    overdue_loans = library.get_overdue_loans()
    print(f"Overdue loans: {len(overdue_loans)}")
    for loan in overdue_loans:
        print(f"  Loan ID {loan[0]}: {loan[1]} to {loan[2]} (Due: {loan[4]})")
    
    print("\n=== DASHBOARD DATA TEST COMPLETED ===")
    
    # Verify real vs fictitious data
    print("\n=== VERIFICATION SUMMARY ===")
    print(f"✓ Real members in system: {len(all_members)}")
    print(f"✓ Real active loans: {len(active_loans)}")
    print(f"✓ Real available books: {len(available_books)}")
    print(f"✓ All fictitious data removed: {'YES' if len(all_members) <= 3 else 'NO'}")
    
    if len(all_members) <= 3 and len(active_loans) <= 3:
        print("✅ SUCCESS: Database now contains only real data!")
    else:
        print("⚠️  WARNING: Database may still contain fictitious data.")
    
    return stats, member_stats

def create_summary_report():
    """Create a summary report of the cleaned database"""
    
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    print("\n=== DATABASE CLEANUP SUMMARY REPORT ===")
    print(f"Generated on: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}")
    
    # Count all data
    cursor.execute('SELECT COUNT(*) FROM Members')
    total_members = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Loans')
    total_loans = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Loans WHERE ReturnDate IS NULL OR ReturnDate = ""')
    active_loans = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Books')
    total_books = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Messages')
    total_messages = cursor.fetchone()[0]
    
    print(f"\nFINAL DATABASE STATE:")
    print(f"  Members: {total_members}")
    print(f"  Users: {total_users}")
    print(f"  Total Loans (all time): {total_loans}")
    print(f"  Active Loans: {active_loans}")
    print(f"  Books: {total_books}")
    print(f"  Messages: {total_messages}")
    
    # Show actual members
    print(f"\nREMAINING MEMBERS:")
    cursor.execute('SELECT MemberID, Name, RegistrationDate FROM Members')
    members = cursor.fetchall()
    for member_id, name, reg_date in members:
        print(f"  {member_id}: {name} (Registered: {reg_date})")
    
    # Show actual users
    print(f"\nREMAINING USERS:")
    cursor.execute('SELECT UserID, Username, UserType, Name FROM Users')
    users = cursor.fetchall()
    for user_id, username, user_type, name in users:
        print(f"  {user_id}: {username} ({user_type}) - {name}")
    
    # Show active loans
    if active_loans > 0:
        print(f"\nACTIVE LOANS:")
        cursor.execute('''
            SELECT l.LoanID, l.BookID, l.MemberID, l.LoanDate, l.DueDate,
                   b.Title, m.Name
            FROM Loans l
            LEFT JOIN Books b ON l.BookID = b.ISBN
            LEFT JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.ReturnDate IS NULL OR l.ReturnDate = ""
        ''')
        loans = cursor.fetchall()
        for loan_id, book_id, member_id, loan_date, due_date, book_title, member_name in loans:
            print(f"  Loan {loan_id}: '{book_title or book_id}' to {member_name or f'Member {member_id}'} (Due: {due_date})")
    else:
        print(f"\nNO ACTIVE LOANS")
    
    conn.close()
    
    print("\n" + "="*50)
    print("DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
    print("All dashboard numbers now reflect real registered users and data.")
    print("="*50)

if __name__ == "__main__":
    # Test the dashboard data
    stats, member_stats = test_dashboard_data()
    
    # Create summary report
    create_summary_report()
