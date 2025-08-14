-- Library Database SQL Queries
-- These queries demonstrate various database operations for the library system

-- 1. View all books in the library
SELECT ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus 
FROM Books;

-- 2. View all members
SELECT MemberID, Name, ContactInfo, RegistrationDate 
FROM Members;

-- 3. View all active loans (books currently on loan)
SELECT 
    l.LoanID,
    b.Title,
    b.Author,
    m.Name as MemberName,
    l.LoanDate,
    l.DueDate
FROM Loans l
JOIN Books b ON l.BookID = b.ISBN
JOIN Members m ON l.MemberID = m.MemberID
WHERE l.ReturnDate IS NULL;

-- 4. Find overdue books
SELECT 
    l.LoanID,
    b.Title,
    b.Author,
    m.Name as MemberName,
    l.DueDate,
    (julianday('now') - julianday(l.DueDate)) as DaysOverdue
FROM Loans l
JOIN Books b ON l.BookID = b.ISBN
JOIN Members m ON l.MemberID = m.MemberID
WHERE l.ReturnDate IS NULL 
AND l.DueDate < date('now');

-- 5. Search for books by author
SELECT ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus
FROM Books
WHERE Author LIKE '%Robert Martin%';

-- 6. Search for books by title
SELECT ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus
FROM Books
WHERE Title LIKE '%Java%';

-- 7. Find available books in a specific genre
SELECT ISBN, Title, Author, PublicationYear
FROM Books
WHERE Genre = 'Programming' 
AND AvailabilityStatus = 'Available';

-- 8. Count books by genre
SELECT Genre, COUNT(*) as BookCount
FROM Books
GROUP BY Genre
ORDER BY BookCount DESC;

-- 9. Find members who have never borrowed a book
SELECT m.MemberID, m.Name, m.ContactInfo
FROM Members m
LEFT JOIN Loans l ON m.MemberID = l.MemberID
WHERE l.MemberID IS NULL;

-- 10. Find the most popular books (most frequently borrowed)
SELECT 
    b.Title,
    b.Author,
    COUNT(l.LoanID) as TimesBorrowed
FROM Books b
LEFT JOIN Loans l ON b.ISBN = l.BookID
GROUP BY b.ISBN, b.Title, b.Author
ORDER BY TimesBorrowed DESC;

-- 11. View complete loan history
SELECT 
    l.LoanID,
    b.Title,
    b.Author,
    m.Name as MemberName,
    l.LoanDate,
    l.DueDate,
    l.ReturnDate,
    CASE 
        WHEN l.ReturnDate IS NULL THEN 'Active'
        WHEN l.ReturnDate > l.DueDate THEN 'Returned Late'
        ELSE 'Returned On Time'
    END as Status
FROM Loans l
JOIN Books b ON l.BookID = b.ISBN
JOIN Members m ON l.MemberID = m.MemberID
ORDER BY l.LoanDate DESC;

-- 12. Find books published in the last 10 years
SELECT ISBN, Title, Author, Genre, PublicationYear
FROM Books
WHERE PublicationYear >= (strftime('%Y', 'now') - 10)
ORDER BY PublicationYear DESC;

-- 13. Member activity report
SELECT 
    m.Name,
    COUNT(l.LoanID) as TotalLoans,
    COUNT(CASE WHEN l.ReturnDate IS NULL THEN 1 END) as ActiveLoans,
    COUNT(CASE WHEN l.ReturnDate > l.DueDate THEN 1 END) as LateReturns
FROM Members m
LEFT JOIN Loans l ON m.MemberID = l.MemberID
GROUP BY m.MemberID, m.Name
ORDER BY TotalLoans DESC;

-- 14. Books that have never been borrowed
SELECT ISBN, Title, Author, Genre
FROM Books b
LEFT JOIN Loans l ON b.ISBN = l.BookID
WHERE l.BookID IS NULL;

-- 15. Average loan duration
SELECT 
    AVG(julianday(ReturnDate) - julianday(LoanDate)) as AvgLoanDays
FROM Loans
WHERE ReturnDate IS NOT NULL;
