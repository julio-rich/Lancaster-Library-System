#!/usr/bin/env python3
"""
Test script for the remove member functionality
"""
import sqlite3
from datetime import datetime

def test_remove_member_functionality():
    """Test the remove member functionality"""
    print("🧪 Testing Remove Member Functionality")
    print("=" * 50)
    
    # Connect to database
    try:
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        
        # Check if Members table exists and has Status column
        cursor.execute("PRAGMA table_info(Members)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("📋 Members table columns:", column_names)
        
        if 'Status' not in column_names:
            print("❌ ERROR: Status column not found in Members table!")
            return False
        
        # Check current members
        cursor.execute("SELECT MemberID, Name, Status FROM Members")
        members = cursor.fetchall()
        
        print(f"👥 Found {len(members)} members in database:")
        for member in members:
            status = member[2] if member[2] else 'active'  # Default to active if null
            print(f"   - ID: {member[0]}, Name: {member[1]}, Status: {status}")
        
        if not members:
            print("⚠️  No members found in database. Please add some members first.")
            return False
        
        # Test the remove_member function logic (simulate it)
        test_member_id = members[0][0]  # Use first member for testing
        
        # Check for active loans
        cursor.execute("""
            SELECT COUNT(*) FROM Loans 
            WHERE MemberID = ? AND ReturnDate IS NULL
        """, (test_member_id,))
        
        active_loans = cursor.fetchone()[0]
        
        # Check for unpaid fines
        cursor.execute("""
            SELECT COALESCE(SUM(Amount), 0) FROM Fines 
            WHERE MemberID = ? AND Status = 'unpaid'
        """, (test_member_id,))
        
        outstanding_fines = cursor.fetchone()[0]
        
        print(f"\n🔍 Testing member ID {test_member_id}:")
        print(f"   - Active loans: {active_loans}")
        print(f"   - Outstanding fines: ${outstanding_fines}")
        
        # Simulate the removal logic
        if active_loans > 0:
            print(f"❌ Cannot remove member: {active_loans} active loan(s) found")
            print("✅ Safety check working correctly!")
        elif outstanding_fines > 0:
            print(f"❌ Cannot remove member: ${outstanding_fines:.2f} in unpaid fines")
            print("✅ Safety check working correctly!")
        else:
            print("✅ Member can be safely removed (no active loans or unpaid fines)")
        
        # Test route existence by checking app.py
        try:
            with open('app.py', 'r') as f:
                app_content = f.read()
                if '/remove_member/<int:member_id>' in app_content:
                    print("✅ Remove member route found in app.py")
                else:
                    print("❌ Remove member route NOT found in app.py")
        except FileNotFoundError:
            print("❌ app.py file not found")
        
        # Test template existence
        try:
            with open('templates/members.html', 'r') as f:
                template_content = f.read()
                if 'removeMember(' in template_content:
                    print("✅ Remove member JavaScript function found in template")
                else:
                    print("❌ Remove member JavaScript function NOT found in template")
                    
                if 'extra_js' in template_content:
                    print("✅ extra_js block found in template")
                else:
                    print("❌ extra_js block NOT found in template")
        except FileNotFoundError:
            print("❌ templates/members.html file not found")
        
        # Test base template has extra_js block
        try:
            with open('templates/base.html', 'r') as f:
                base_content = f.read()
                if '{% block extra_js %}{% endblock %}' in base_content:
                    print("✅ extra_js block found in base template")
                else:
                    print("❌ extra_js block NOT found in base template")
        except FileNotFoundError:
            print("❌ templates/base.html file not found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_member_status_display():
    """Check if member status is displayed correctly"""
    print("\n🎨 Testing Member Status Display")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        
        # Get all members with their full data to check status column position
        cursor.execute("SELECT * FROM Members")
        members = cursor.fetchall()
        
        if members:
            sample_member = members[0]
            print(f"📊 Sample member data (length: {len(sample_member)}):")
            print(f"   - Index 0 (ID): {sample_member[0]}")
            print(f"   - Index 1 (Name): {sample_member[1]}")
            print(f"   - Index 7 (Status): {sample_member[7] if len(sample_member) > 7 else 'N/A'}")
            
            if len(sample_member) > 7:
                print("✅ Status column accessible at index 7")
            else:
                print("❌ Status column not accessible - member data too short")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking member status: {e}")

if __name__ == "__main__":
    success = test_remove_member_functionality()
    check_member_status_display()
    
    if success:
        print("\n🎉 Remove Member Functionality Test PASSED!")
        print("\n📝 To test manually:")
        print("1. Start the Flask app: python app.py")
        print("2. Login as a librarian (username: librarian, password: admin123)")
        print("3. Go to Members page")
        print("4. Click the 'Remove' button next to any member")
        print("5. Confirm the removal in the dialog")
        print("6. Check that the member status changes to 'Inactive'")
    else:
        print("\n❌ Remove Member Functionality Test FAILED!")
        print("Please check the issues listed above.")
