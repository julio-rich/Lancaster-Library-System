// Theme Toggle Functionality
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        body.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    // Apply theme to dropdown menus in dark mode
    if (savedTheme === 'dark') {
        updateDropdownMenus();
    }
});

// Update dropdown menus for dark mode
function updateDropdownMenus() {
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');
    dropdownMenus.forEach(menu => {
        const currentTheme = document.body.getAttribute('data-theme');
        if (currentTheme === 'dark') {
            menu.style.backgroundColor = '#333';
            menu.style.border = '1px solid #DC143C';
            
            const dropdownItems = menu.querySelectorAll('.dropdown-item');
            dropdownItems.forEach(item => {
                item.style.color = 'white';
                
                item.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#DC143C';
                    this.style.color = 'white';
                });
                
                item.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'transparent';
                    this.style.color = 'white';
                });
            });
        } else {
            // Reset to light mode styles
            menu.style.backgroundColor = 'white';
            menu.style.border = '1px solid #DC143C';
            
            const dropdownItems = menu.querySelectorAll('.dropdown-item');
            dropdownItems.forEach(item => {
                item.style.color = 'black';
                
                item.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#DC143C';
                    this.style.color = 'white';
                });
                
                item.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'transparent';
                    this.style.color = 'black';
                });
            });
        }
    });
}

// Update dropdown menus when theme changes
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        body.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
    
    // Update dropdown menus after theme change
    setTimeout(() => {
        updateDropdownMenus();
    }, 100);
}

// Additional function for smooth transitions
document.addEventListener('DOMContentLoaded', function() {
    // Add transition class to body after initial load
    setTimeout(() => {
        document.body.classList.add('theme-transition');
    }, 100);
});

// Library Management specific JavaScript can be added below
// ...

// Custom JavaScript for the library website
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        });
    });

    // Add buttons for all functionalities if not present
    const functionalities = [
        { id: 'add-book-btn', text: 'Add Book', onClick: function() { window.location.href = '/add-book'; } },
        { id: 'view-books-btn', text: 'View Books', onClick: function() { window.location.href = '/books'; } },
        { id: 'add-member-btn', text: 'Add Member', onClick: function() { window.location.href = '/add-member'; } },
        { id: 'view-members-btn', text: 'View Members', onClick: function() { window.location.href = '/members'; } },
        { id: 'issue-book-btn', text: 'Issue Book', onClick: function() { window.location.href = '/issue-book'; } },
        { id: 'return-book-btn', text: 'Return Book', onClick: function() { window.location.href = '/return-book'; } }
    ];

    const btnContainer = document.getElementById('functionality-buttons');
    if (btnContainer) {
        functionalities.forEach(function(func) {
            if (!document.getElementById(func.id)) {
                const btn = document.createElement('button');
                btn.id = func.id;
                btn.textContent = func.text;
                btn.className = 'functionality-btn';
                btn.addEventListener('click', func.onClick);
                btnContainer.appendChild(btn);
            }
        });
    }
});
