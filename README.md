# Library Database Project

This project includes an SQLite database for managing a library system. The database stores information about books, members, and loans.

## Project Structure
- `database.py`: Python script to manage database operations
- `library.db`: SQLite database file

## Tables
1. **Books**
   - ISBN
   - Title
   - Author
   - Genre
   - Publication Year
   - Availability Status

2. **Members**
   - Member ID
   - Name
   - Contact Info
   - Registration Date

3. **Loans**
   - Loan ID
   - Book ID
   - Member ID
   - Loan Date
   - Due Date
   - Return Date

4. **Authors** (optional)
   - Author ID
   - Name
   - Biography

5. **Categories/Genres** (optional)

## Setup
Run the `database.py` script to initialize the database and tables.

