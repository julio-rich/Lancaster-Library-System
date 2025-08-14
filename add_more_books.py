#!/usr/bin/env python3
"""
Script to add more books to the library database
This will add a diverse collection across multiple genres
"""

import sqlite3
from datetime import datetime

def add_books_to_library():
    # Connect to database
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    # Comprehensive book collection
    books_to_add = [
        # Fiction - Classic Literature
        ("9780141182636", "Pride and Prejudice", "Jane Austen", "Fiction", 1813),
        ("9780486280615", "Great Expectations", "Charles Dickens", "Fiction", 1861),
        ("9780143124177", "The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 1925),
        ("9780141439518", "Jane Eyre", "Charlotte Brontë", "Fiction", 1847),
        ("9780486415871", "Wuthering Heights", "Emily Brontë", "Fiction", 1847),
        ("9780141439601", "Emma", "Jane Austen", "Fiction", 1815),
        ("9780140449136", "Les Misérables", "Victor Hugo", "Fiction", 1862),
        ("9780486411088", "The Picture of Dorian Gray", "Oscar Wilde", "Fiction", 1890),
        ("9780486284736", "Frankenstein", "Mary Shelley", "Fiction", 1818),
        ("9780486270425", "Dracula", "Bram Stoker", "Fiction", 1897),
        
        # Fiction - Modern Literature
        ("9780061120084", "To Kill a Mockingbird", "Harper Lee", "Fiction", 1960),
        ("9780547928227", "The Hobbit", "J.R.R. Tolkien", "Fantasy", 1937),
        ("9780544003415", "The Lord of the Rings", "J.R.R. Tolkien", "Fantasy", 1954),
        ("9780385472579", "The Da Vinci Code", "Dan Brown", "Thriller", 2003),
        ("9780345339706", "The Stand", "Stephen King", "Horror", 1978),
        ("9780385121675", "The Shining", "Stephen King", "Horror", 1977),
        ("9780141439556", "1984", "George Orwell", "Science Fiction", 1949),
        ("9780060850524", "Brave New World", "Aldous Huxley", "Science Fiction", 1932),
        ("9780553293357", "Foundation", "Isaac Asimov", "Science Fiction", 1951),
        ("9780441013593", "Dune", "Frank Herbert", "Science Fiction", 1965),
        
        # Mystery & Crime
        ("9780062073501", "And Then There Were None", "Agatha Christie", "Mystery", 1939),
        ("9780062074010", "Murder on the Orient Express", "Agatha Christie", "Mystery", 1934),
        ("9780486447544", "The Adventures of Sherlock Holmes", "Arthur Conan Doyle", "Mystery", 1892),
        ("9780345538987", "The Girl with the Dragon Tattoo", "Stieg Larsson", "Crime", 2005),
        ("9780307949486", "Gone Girl", "Gillian Flynn", "Thriller", 2012),
        ("9780345542823", "In the Woods", "Tana French", "Mystery", 2007),
        ("9780316066525", "The Catcher in the Rye", "J.D. Salinger", "Fiction", 1951),
        
        # Romance
        ("9780425266748", "It Ends with Us", "Colleen Hoover", "Romance", 2016),
        ("9781501110368", "Me Before You", "Jojo Moyes", "Romance", 2012),
        ("9780449911907", "The Bridges of Madison County", "Robert James Waller", "Romance", 1992),
        ("9780553593716", "Outlander", "Diana Gabaldon", "Romance", 1991),
        ("9780345803481", "Fifty Shades of Grey", "E.L. James", "Romance", 2011),
        ("9780553418026", "The Notebook", "Nicholas Sparks", "Romance", 1996),
        
        # Non-Fiction - Self-Help & Personal Development
        ("9781476765471", "The 7 Habits of Highly Effective People", "Stephen Covey", "Self-Help", 1989),
        ("9780062316110", "Sapiens", "Yuval Noah Harari", "History", 2011),
        ("9780812981609", "Atomic Habits", "James Clear", "Self-Help", 2018),
        ("9780743269513", "How to Win Friends and Influence People", "Dale Carnegie", "Self-Help", 1936),
        ("9781501124020", "The Power of Now", "Eckhart Tolle", "Self-Help", 1997),
        ("9780307887894", "Thinking, Fast and Slow", "Daniel Kahneman", "Psychology", 2011),
        ("9781400067725", "Freakonomics", "Steven Levitt", "Economics", 2005),
        ("9780307465351", "The 4-Hour Workweek", "Tim Ferriss", "Business", 2007),
        
        # Science & Technology
        ("9780307887894", "A Brief History of Time", "Stephen Hawking", "Science", 1988),
        ("9781451648539", "Steve Jobs", "Walter Isaacson", "Biography", 2011),
        ("9780802779045", "The Innovators", "Walter Isaacson", "Technology", 2014),
        ("9781591846147", "Good to Great", "Jim Collins", "Business", 2001),
        ("9780385514231", "The Tipping Point", "Malcolm Gladwell", "Sociology", 2000),
        ("9780316346627", "Outliers", "Malcolm Gladwell", "Sociology", 2008),
        ("9780385537857", "Blink", "Malcolm Gladwell", "Psychology", 2005),
        
        # History & Biography
        ("9781476728759", "Alexander Hamilton", "Ron Chernow", "Biography", 2004),
        ("9780671867065", "John Adams", "David McCullough", "Biography", 2001),
        ("9780743223133", "1776", "David McCullough", "History", 2005),
        ("9780307269751", "The Devil Wears Prada", "Lauren Weisberger", "Fiction", 2003),
        ("9780767905923", "Into Thin Air", "Jon Krakauer", "Adventure", 1997),
        ("9780385486804", "The Kite Runner", "Khaled Hosseini", "Fiction", 2003),
        
        # Young Adult Fiction
        ("9780439358071", "Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fantasy", 1997),
        ("9780439064873", "Harry Potter and the Chamber of Secrets", "J.K. Rowling", "Fantasy", 1998),
        ("9780439136365", "Harry Potter and the Prisoner of Azkaban", "J.K. Rowling", "Fantasy", 1999),
        ("9780439139601", "Harry Potter and the Goblet of Fire", "J.K. Rowling", "Fantasy", 2000),
        ("9780439358078", "The Hunger Games", "Suzanne Collins", "Young Adult", 2008),
        ("9780545586177", "Divergent", "Veronica Roth", "Young Adult", 2011),
        ("9780316015844", "Twilight", "Stephenie Meyer", "Young Adult", 2005),
        ("9780142414932", "The Fault in Our Stars", "John Green", "Young Adult", 2012),
        
        # Children's Books
        ("9780064400558", "Where the Wild Things Are", "Maurice Sendak", "Children", 1963),
        ("9780394800165", "The Cat in the Hat", "Dr. Seuss", "Children", 1957),
        ("9780064430173", "Charlotte's Web", "E.B. White", "Children", 1952),
        ("9780439708180", "Captain Underpants", "Dav Pilkey", "Children", 1997),
        ("9780590353427", "Goosebumps: Welcome to Dead House", "R.L. Stine", "Children", 1992),
        
        # Educational & Reference
        ("9780199571123", "The Oxford English Dictionary", "Oxford University Press", "Reference", 2010),
        ("9780321125217", "Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 2001),
        ("9780134685991", "Effective Java (3rd Edition)", "Joshua Bloch", "Programming", 2017),
        ("9781593279509", "Eloquent JavaScript", "Marijn Haverbeke", "Programming", 2018),
        ("9780596517748", "JavaScript: The Good Parts", "Douglas Crockford", "Programming", 2008),
        ("9781449331818", "Learning Python", "Mark Lutz", "Programming", 2013),
        ("9780134052502", "The Elements of Statistical Learning", "Trevor Hastie", "Statistics", 2009),
        
        # Health & Fitness
        ("9780316322386", "The Blue Zones", "Dan Buettner", "Health", 2008),
        ("9781594868696", "Eat, Pray, Love", "Elizabeth Gilbert", "Memoir", 2006),
        ("9780345472328", "The South Beach Diet", "Arthur Agatston", "Health", 2003),
        ("9780062315007", "The Whole30", "Melissa Hartwig", "Health", 2015),
        
        # Philosophy & Religion
        ("9780486270623", "Meditations", "Marcus Aurelius", "Philosophy", 180),
        ("9780486411132", "The Republic", "Plato", "Philosophy", -380),
        ("9780486280721", "Walden", "Henry David Thoreau", "Philosophy", 1854),
        ("9780062502179", "The Alchemist", "Paulo Coelho", "Fiction", 1988),
        ("9780143126560", "Siddhartha", "Hermann Hesse", "Philosophy", 1922),
        
        # Travel & Adventure
        ("9780525434917", "Wild", "Cheryl Strayed", "Memoir", 2012),
        ("9780767900508", "A Walk in the Woods", "Bill Bryson", "Travel", 1998),
        ("9780307387424", "Under the Tuscan Sun", "Frances Mayes", "Travel", 1996),
        ("9780802713766", "The Beach", "Alex Garland", "Adventure", 1996),
        
        # Art & Culture
        ("9780671027032", "The Story of Art", "E.H. Gombrich", "Art", 1950),
        ("9780307593313", "Just Kids", "Patti Smith", "Memoir", 2010),
        ("9780679640981", "The Birth of Venus", "Sarah Dunant", "Historical Fiction", 2003),
        
        # Comics & Graphic Novels
        ("9781401232597", "Watchmen", "Alan Moore", "Graphic Novel", 1987),
        ("9781779511335", "Batman: The Killing Joke", "Alan Moore", "Graphic Novel", 1988),
        ("9781582406275", "The Walking Dead Vol. 1", "Robert Kirkman", "Graphic Novel", 2004),
        ("9780307279446", "Maus", "Art Spiegelman", "Graphic Novel", 1991),
        
        # Sports
        ("9780743270755", "Moneyball", "Michael Lewis", "Sports", 2003),
        ("9780385537551", "The Blind Side", "Michael Lewis", "Sports", 2006),
        ("9780307594173", "Open", "Andre Agassi", "Biography", 2009),
        
        # Cooking
        ("9780307716182", "Mastering the Art of French Cooking", "Julia Child", "Cooking", 1961),
        ("9780743246262", "Kitchen Confidential", "Anthony Bourdain", "Memoir", 2000),
        ("9780307719218", "The Joy of Cooking", "Irma S. Rombauer", "Cooking", 1931),
    ]
    
    successful_additions = 0
    duplicate_count = 0
    errors = []
    
    print("Adding books to the library database...")
    print("=" * 50)
    
    for isbn, title, author, genre, year in books_to_add:
        try:
            # Check if book already exists
            cursor.execute('SELECT ISBN FROM Books WHERE ISBN = ?', (isbn,))
            if cursor.fetchone():
                print(f"⚠️  DUPLICATE: '{title}' by {author} (ISBN: {isbn})")
                duplicate_count += 1
                continue
            
            # Insert the book
            cursor.execute('''
                INSERT INTO Books (ISBN, Title, Author, Genre, PublicationYear, AvailabilityStatus)
                VALUES (?, ?, ?, ?, ?, 'Available')
            ''', (isbn, title, author, genre, year))
            
            print(f"✅ Added: '{title}' by {author} ({genre}, {year})")
            successful_additions += 1
            
        except sqlite3.Error as e:
            error_msg = f"❌ Failed to add '{title}': {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    # Commit changes
    conn.commit()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"✅ Successfully added: {successful_additions} books")
    print(f"⚠️  Duplicates skipped: {duplicate_count} books")
    print(f"❌ Errors encountered: {len(errors)} books")
    
    # Show final count
    cursor.execute('SELECT COUNT(*) FROM Books')
    total_books = cursor.fetchone()[0]
    print(f"📚 Total books in library: {total_books}")
    
    # Show genre distribution
    print("\n📂 Books by Genre:")
    cursor.execute('SELECT Genre, COUNT(*) FROM Books GROUP BY Genre ORDER BY COUNT(*) DESC')
    genres = cursor.fetchall()
    for genre, count in genres:
        print(f"   {genre}: {count} books")
    
    # Show errors if any
    if errors:
        print("\n❌ Detailed Errors:")
        for error in errors:
            print(f"   {error}")
    
    conn.close()
    print("\n🎉 Book addition process completed!")
    return successful_additions, duplicate_count, len(errors)

if __name__ == "__main__":
    add_books_to_library()
