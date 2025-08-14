import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime
import json
import os

class LibraryChatbot:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
        self.email_config = self.load_email_config()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_name)
    
    def load_email_config(self):
        """Load email configuration from config file or environment variables"""
        config_file = 'email_config.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Default configuration - you'll need to update these
            return {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_library@gmail.com",
                "sender_password": "your_app_password"
            }
    
    def get_overdue_loans(self):
        """Get all overdue loans with member contact information"""
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
    
    def get_loans_due_soon(self, days_ahead=3):
        """Get loans due within specified number of days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        from datetime import timedelta
        future_date = (datetime.now().replace(hour=23, minute=59, second=59) + 
                      timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                l.LoanID,
                b.Title,
                b.Author,
                m.Name,
                m.ContactInfo,
                l.DueDate
            FROM Loans l
            JOIN Books b ON l.BookID = b.ISBN
            JOIN Members m ON l.MemberID = m.MemberID
            WHERE l.DueDate BETWEEN ? AND ? AND l.ReturnDate IS NULL
            ORDER BY l.DueDate ASC
        ''', (today, future_date))
        
        upcoming_due = cursor.fetchall()
        conn.close()
        
        return upcoming_due
    
    def create_reminder_email(self, member_name, book_title, book_author, due_date, is_overdue=False):
        """Create a reminder email message"""
        if is_overdue:
            subject = f"OVERDUE: Library Book Return Reminder - {book_title}"
            greeting = f"Dear {member_name},\n\nThis is an urgent reminder that you have an overdue book:"
            urgency = "\n⚠️ THIS BOOK IS OVERDUE! Please return it as soon as possible to avoid late fees."
        else:
            subject = f"Library Book Due Soon - {book_title}"
            greeting = f"Dear {member_name},\n\nThis is a friendly reminder that you have a book due soon:"
            urgency = "\nPlease return the book by the due date to avoid late fees."
        
        message_body = f"""{greeting}

📚 Book Title: {book_title}
✍️ Author: {book_author}
📅 Due Date: {due_date}
{urgency}

You can return the book during our library hours:
Monday - Friday: 9:00 AM - 8:00 PM
Saturday: 10:00 AM - 6:00 PM
Sunday: 12:00 PM - 5:00 PM

If you need to extend your loan, please contact us immediately.

Thank you for using our library services!

Best regards,
Library Management System
"""
        return subject, message_body
    
    def send_email(self, recipient_email, subject, message_body):
        """Send email using SMTP"""
        try:
            msg = EmailMessage()
            msg.set_content(message_body)
            msg['Subject'] = subject
            msg['From'] = self.email_config['sender_email']
            msg['To'] = recipient_email
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()  # Enable encryption
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
            
            return True, "Email sent successfully"
        
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_overdue_reminders(self):
        """Send reminder emails for all overdue books"""
        overdue_loans = self.get_overdue_loans()
        
        if not overdue_loans:
            print("✅ No overdue books found!")
            return
        
        print(f"📧 Found {len(overdue_loans)} overdue loans. Sending reminders...")
        
        sent_count = 0
        failed_count = 0
        
        for loan in overdue_loans:
            loan_id, title, author, member_name, contact_info, due_date, days_overdue = loan
            
            # Extract email from contact info (assuming it contains email)
            email = self.extract_email(contact_info)
            
            if not email:
                print(f"❌ No valid email found for {member_name} (Contact: {contact_info})")
                failed_count += 1
                continue
            
            subject, message_body = self.create_reminder_email(
                member_name, title, author, due_date, is_overdue=True
            )
            
            success, result = self.send_email(email, subject, message_body)
            
            if success:
                print(f"✅ Reminder sent to {member_name} ({email}) for '{title}' - {int(days_overdue)} days overdue")
                sent_count += 1
            else:
                print(f"❌ Failed to send to {member_name} ({email}): {result}")
                failed_count += 1
        
        print(f"\n📊 Summary: {sent_count} emails sent, {failed_count} failed")
    
    def send_upcoming_due_reminders(self, days_ahead=3):
        """Send reminder emails for books due soon"""
        upcoming_loans = self.get_loans_due_soon(days_ahead)
        
        if not upcoming_loans:
            print(f"✅ No books due within {days_ahead} days!")
            return
        
        print(f"📧 Found {len(upcoming_loans)} books due within {days_ahead} days. Sending reminders...")
        
        sent_count = 0
        failed_count = 0
        
        for loan in upcoming_loans:
            loan_id, title, author, member_name, contact_info, due_date = loan
            
            email = self.extract_email(contact_info)
            
            if not email:
                print(f"❌ No valid email found for {member_name} (Contact: {contact_info})")
                failed_count += 1
                continue
            
            subject, message_body = self.create_reminder_email(
                member_name, title, author, due_date, is_overdue=False
            )
            
            success, result = self.send_email(email, subject, message_body)
            
            if success:
                print(f"✅ Due soon reminder sent to {member_name} ({email}) for '{title}' - due {due_date}")
                sent_count += 1
            else:
                print(f"❌ Failed to send to {member_name} ({email}): {result}")
                failed_count += 1
        
        print(f"\n📊 Summary: {sent_count} emails sent, {failed_count} failed")
    
    def extract_email(self, contact_info):
        """Extract email address from contact info string"""
        import re
        
        # Simple email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, contact_info)
        
        return emails[0] if emails else None
    
    def display_overdue_report(self):
        """Display detailed overdue report"""
        overdue_loans = self.get_overdue_loans()
        
        if not overdue_loans:
            print("✅ No overdue books!")
            return
        
        print(f"\n📋 OVERDUE BOOKS REPORT ({len(overdue_loans)} items)")
        print("=" * 80)
        
        for loan in overdue_loans:
            loan_id, title, author, member_name, contact_info, due_date, days_overdue = loan
            print(f"📚 {title} by {author}")
            print(f"👤 Member: {member_name}")
            print(f"📧 Contact: {contact_info}")
            print(f"📅 Due Date: {due_date} ({int(days_overdue)} days overdue)")
            print("-" * 80)
    
    def chat_interface(self):
        """Interactive chatbot interface"""
        print("🤖 Welcome to the Library Reminder Chatbot!")
        print("I can help you manage overdue books and send reminder emails.")
        
        while True:
            print("\n" + "="*50)
            print("What would you like to do?")
            print("1. 📋 View overdue books report")
            print("2. 📧 Send overdue reminders")
            print("3. 📅 Send due soon reminders")
            print("4. ⚙️ Configure email settings")
            print("5. 🧪 Test email configuration")
            print("6. 🚪 Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self.display_overdue_report()
            
            elif choice == '2':
                confirm = input("Send reminder emails to all members with overdue books? (y/n): ")
                if confirm.lower() == 'y':
                    self.send_overdue_reminders()
            
            elif choice == '3':
                days = input("How many days ahead to check for due books? (default: 3): ").strip()
                days = int(days) if days.isdigit() else 3
                confirm = input(f"Send reminder emails for books due within {days} days? (y/n): ")
                if confirm.lower() == 'y':
                    self.send_upcoming_due_reminders(days)
            
            elif choice == '4':
                self.configure_email()
            
            elif choice == '5':
                self.test_email_config()
            
            elif choice == '6':
                print("👋 Thank you for using the Library Reminder Chatbot!")
                break
            
            else:
                print("❌ Invalid choice! Please try again.")
    
    def configure_email(self):
        """Configure email settings"""
        print("\n⚙️ Email Configuration")
        print("Current settings:", json.dumps(self.email_config, indent=2))
        
        if input("Update email settings? (y/n): ").lower() == 'y':
            self.email_config['smtp_server'] = input("SMTP Server (e.g., smtp.gmail.com): ") or self.email_config['smtp_server']
            self.email_config['smtp_port'] = int(input("SMTP Port (e.g., 587): ") or self.email_config['smtp_port'])
            self.email_config['sender_email'] = input("Sender email: ") or self.email_config['sender_email']
            self.email_config['sender_password'] = input("Email password/app password: ") or self.email_config['sender_password']
            
            # Save to file
            with open('email_config.json', 'w') as f:
                json.dump(self.email_config, f, indent=2)
            
            print("✅ Email configuration saved!")
    
    def test_email_config(self):
        """Test email configuration"""
        test_email = input("Enter test email address: ")
        subject = "Library Chatbot Test"
        message = "This is a test email from the Library Reminder Chatbot. Configuration is working correctly!"
        
        success, result = self.send_email(test_email, subject, message)
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print(f"❌ Test failed: {result}")

def main():
    # Initialize the chatbot with your existing database
    chatbot = LibraryChatbot('library.db')
    chatbot.chat_interface()

if __name__ == "__main__":
    main()
