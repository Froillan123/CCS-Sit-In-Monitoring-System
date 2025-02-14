document.addEventListener('DOMContentLoaded', () => {
    // Input handling (focus/blur events)
    const inputs = document.querySelectorAll('.form__input');
    inputs.forEach(input => {
        input.value = '';
        let parent = input.parentNode.parentNode;
        parent.classList.remove("focus");
    });

    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(flashMessage => {
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
        }, 2500);
        flashMessage.addEventListener('animationend', () => {
            flashMessage.remove();
        });
    });

    function addfocus() {
        let parent = this.parentNode.parentNode;
        parent.classList.add("focus");
    }

    function remfocus() {
        let parent = this.parentNode.parentNode;
        if (this.value == "") {
            parent.classList.remove("focus");
        }
    }

    inputs.forEach(input => {
        input.addEventListener("focus", addfocus);
        input.addEventListener("blur", remfocus);
    });

    // Sidebar menu toggle functionality
    const sideMenu = document.querySelector('aside');
    const menuBtn = document.getElementById('menu-btn');
    const closeBtn = document.getElementById('close-btn');

    menuBtn.addEventListener('click', () => {
        sideMenu.style.display = 'block';
    });

    closeBtn.addEventListener('click', () => {
        sideMenu.style.display = 'none';
    });

    // Dark mode functionality
    const darkMode = document.querySelector('.dark-mode');

    function applyDarkModePreference() {
        const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
        if (isDarkMode) {
            document.body.classList.add('dark-mode-variables');
            darkMode.querySelector('span:nth-child(1)').classList.remove('active');
            darkMode.querySelector('span:nth-child(2)').classList.add('active');
        } else {
            document.body.classList.remove('dark-mode-variables');
            darkMode.querySelector('span:nth-child(1)').classList.add('active');
            darkMode.querySelector('span:nth-child(2)').classList.remove('active');
        }
    }

    applyDarkModePreference();

    darkMode.addEventListener('click', () => {
        const isDarkMode = document.body.classList.toggle('dark-mode-variables');
        if (isDarkMode) {
            localStorage.setItem('darkMode', 'enabled');
            darkMode.querySelector('span:nth-child(1)').classList.remove('active');
            darkMode.querySelector('span:nth-child(2)').classList.add('active');
        } else {
            localStorage.setItem('darkMode', 'disabled');
            darkMode.querySelector('span:nth-child(1)').classList.add('active');
            darkMode.querySelector('span:nth-child(2)').classList.remove('active');
        }
    });

    // Update user count every second
    function updateUserCount() {
        fetch('/get_user_count')
            .then(response => response.json())
            .then(data => {
                document.querySelector('.info h1').textContent = data.student_count;
            })
            .catch(error => console.error('Error fetching user count:', error));
    }

    setInterval(updateUserCount, 1000); // Update every 1 second
    updateUserCount();

    const eventSource = new EventSource("/sse/active_users");

    eventSource.onmessage = function (event) {
        const activeUsersCount = JSON.parse(event.data);
        const activeUsersCountElement = document.getElementById('active-users-count');
        if (activeUsersCountElement) {
            activeUsersCountElement.textContent = activeUsersCount;
        }
    };
    
    eventSource.onerror = function (error) {
        console.error('EventSource failed:', error);
        eventSource.close(); // Close the connection after error
    };
    // Fetch announcements
    const announcementForm = document.getElementById('announcement-form');
    const announcementsBody = document.getElementById('announcements-body');

    function fetchAnnouncements() {
        fetch('/get_announcements')
            .then(response => response.json())
            .then(data => {
                announcementsBody.innerHTML = ''; // Clear existing rows

                data.forEach(announcement => {
                    const row = document.createElement('tr');
                    const announcementDate = new Date(announcement.announcement_date).toLocaleString();

                    row.innerHTML = `
                        <td>${announcementDate}</td>
                        <td>${announcement.admin_username}</td>
                        <td>${announcement.announcement_text}</td>
                    `;

                    announcementsBody.appendChild(row);
                });
            })
            .catch(error => console.error('Error fetching announcements:', error));
    }

    // Fetch announcements when the page loads
    fetchAnnouncements();

    // Handle announcement form submission
    announcementForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Validate adminUsername
        if (!adminUsername) {
            alert('Admin username not found. Please log in again.');
            return;
        }

        const announcementText = document.getElementById('announcement-text').value;

        // Submit the new announcement
        fetch('/create_announcement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                admin_username: adminUsername,
                announcement_text: announcementText,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Announcement posted successfully!');
                document.getElementById('announcement-text').value = ''; // Clear the textarea
                fetchAnnouncements(); // Refresh the announcements table
            } else {
                alert('Failed to post announcement: ' + data.message);
            }
        })
        .catch(error => console.error('Error posting announcement:', error));
    });
});
