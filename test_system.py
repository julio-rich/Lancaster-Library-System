from library_manager import LibraryManager

# Create library manager instance
library = LibraryManager()

print("=== Library Database System Test ===\n")

print("1. Viewing all books in the library:")
library.view_all_books()

print("\n2. Searching for 'Java' books:")
library.search_books("Java")

print("\n3. Checking overdue books:")
library.view_overdue_books()

print("\n=== System is ready to use! ===")
print("Run 'python library_manager.py' to start the interactive menu system.")
