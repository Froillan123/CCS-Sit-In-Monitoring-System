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

    const socket = io();

    socket.on('update_active_users', function(activeUsers) {
        const activeUsersCountElement = document.getElementById('active-users-count');
        if (activeUsersCountElement) {
            activeUsersCountElement.textContent = activeUsers.length;
        }
    });

    socket.on('connect', function() {
        console.log('WebSocket connected');
    });

    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
    });

    
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
                        <td>
                            <div class="action-buttons">
                                <button class="edit-btn" data-id="${announcement.id}">
                                    <i class="bx bx-edit"></i> Edit
                                </button>
                                <button class="delete-btn" data-id="${announcement.id}">
                                    <i class="bx bx-trash"></i> Delete
                                </button>
                            </div>
                        </td>
                    `;
    
                    announcementsBody.appendChild(row);
                });
    
                // Add event listeners for edit and delete buttons
                addEditDeleteListeners();
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

    // Add event listeners for edit and delete buttons
    function addEditDeleteListeners() {
        // Edit Button
        document.querySelectorAll('.edit-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const announcementId = e.target.getAttribute('data-id');
                openEditModal(announcementId);
            });
        });

        // Delete Button
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const announcementId = e.target.getAttribute('data-id');
                showDeleteConfirmation(announcementId);
            });
        });
    }

    // Open Edit Modal
    function openEditModal(announcementId) {
        fetch(`/get_announcement/${announcementId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('edit-announcement-id').value = announcementId;
                document.getElementById('edit-announcement-text').value = data.announcement_text;
                document.getElementById('editModal').style.display = 'flex'; // Use flex to center the modal
            })
            .catch(error => console.error('Error fetching announcement:', error));
    }

    // Close Modal
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.getElementById('editModal').style.display = 'none';
    });

    // Handle edit announcement form submission
    document.getElementById('edit-announcement-form').addEventListener('submit', (e) => {
        e.preventDefault();

        const announcementId = document.getElementById('edit-announcement-id').value;
        const announcementText = document.getElementById('edit-announcement-text').value;

        fetch(`/update_announcement/${announcementId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                announcement_text: announcementText,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Announcement updated successfully!');
                document.getElementById('editModal').style.display = 'none';
                fetchAnnouncements(); // Refresh the table
            } else {
                alert('Failed to update announcement: ' + data.message);
            }
        })
        .catch(error => console.error('Error updating announcement:', error));
    });

    let currentAnnouncementIdToDelete = null;

    // Show Delete Confirmation Modal
    function showDeleteConfirmation(announcementId) {
        currentAnnouncementIdToDelete = announcementId;
        document.getElementById('deleteConfirmation').style.display = 'flex';
    }

    // Confirm Delete
    document.getElementById('confirmDelete').addEventListener('click', () => {
        if (currentAnnouncementIdToDelete) {
            fetch(`/delete_announcement/${currentAnnouncementIdToDelete}`, {
                method: 'DELETE',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Announcement deleted successfully!');
                    fetchAnnouncements(); // Refresh the table
                } else {
                    alert('Failed to delete announcement: ' + data.message);
                }
            })
            .catch(error => console.error('Error deleting announcement:', error));
        }
        document.getElementById('deleteConfirmation').style.display = 'none';
    });

    // Cancel Delete
    document.getElementById('cancelDelete').addEventListener('click', () => {
        document.getElementById('deleteConfirmation').style.display = 'none';
    });

    // Section toggling functionality
    const links = document.querySelectorAll('.sidebar a[data-section]'); // Only select links with data-section
    const sections = document.querySelectorAll('.dashboard-section');

    // Function to show the selected section and hide others
    function showSection(sectionId) {
        sections.forEach(section => {
            if (section.id === sectionId) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    }

    // Function to set the active link
    function setActiveLink(sectionId) {
        links.forEach(link => {
            if (link.getAttribute('data-section') === sectionId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // Default to showing the dashboard section
    showSection('dashboard');
    setActiveLink('dashboard');

    // Add click event listeners to sidebar links
    links.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');
            showSection(sectionId);
            setActiveLink(sectionId);
        });
    });
});

const programData = {
    BSIT: [12, 19, 8, 15, 10, 7],
    BSCpE: [5, 14, 10, 8, 12, 9],
    BSBA: [7, 11, 13, 6, 9, 15],
    BSCS: [10, 8, 12, 14, 7, 11],
    BSEd: [6, 9, 15, 10, 8, 12],
    BSEdSec: [7, 10, 14, 12, 8, 9],
    BSHRM: [8, 12, 7, 11, 14, 10],
    BSN: [9, 15, 6, 12, 10, 8],
    BCE: [11, 7, 14, 9, 12, 6],
    BME: [13, 10, 8, 12, 7, 11],
    BEE: [10, 12, 9, 11, 8, 14],
    BIE: [7, 14, 10, 8, 12, 9],
    BNAME: [5, 9, 12, 10, 14, 7],
    BCrim: [8, 11, 13, 6, 9, 15],
    BCom: [10, 8, 12, 14, 7, 11],
    BAcc: [6, 9, 15, 10, 8, 12],
    BCSA: [8, 12, 7, 11, 14, 10],
    BCSec: [9, 15, 6, 12, 10, 8],
    BIP: [11, 7, 14, 9, 12, 6],
    ABPS: [13, 10, 8, 12, 7, 11],
    ABEng: [10, 12, 9, 11, 8, 14],
    CISCO: [7, 14, 10, 8, 12, 9],
    ESL: [5, 9, 12, 10, 14, 7],
    CKor: [8, 11, 13, 6, 9, 15],
    ESLF: [10, 8, 12, 14, 7, 11],
};

// Define a consistent color palette
const colorPalette = [
    'rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)', 'rgba(255, 206, 86, 0.6)',
    'rgba(75, 192, 192, 0.6)', 'rgba(153, 102, 255, 0.6)', 'rgba(255, 159, 64, 0.6)',
    'rgba(233, 30, 99, 0.6)', 'rgba(66, 133, 244, 0.6)', 'rgba(76, 175, 80, 0.6)',
    'rgba(103, 58, 183, 0.6)', 'rgba(255, 87, 34, 0.6)', 'rgba(0, 188, 212, 0.6)',
    'rgba(121, 85, 72, 0.6)', 'rgba(205, 220, 57, 0.6)', 'rgba(158, 158, 158, 0.6)',
    'rgba(192, 192, 192, 0.6)', 'rgba(0, 150, 136, 0.6)', 'rgba(255, 235, 59, 0.6)',
    'rgba(255, 193, 7, 0.6)', 'rgba(158, 158, 158, 0.6)', 'rgba(96, 125, 139, 0.6)',
    'rgba(244, 67, 54, 0.6)', 'rgba(63, 81, 181, 0.6)', 'rgba(33, 150, 243, 0.6)',
    'rgba(255, 87, 34, 0.6)',
];

// Assign colors to programs
const backgroundColors = Object.keys(programData).map((_, i) => colorPalette[i % colorPalette.length]);
const borderColors = backgroundColors.map(color => color.replace('0.6', '1'));

const programLabels = Object.keys(programData).map(program => {
    const totalSitIn = programData[program].reduce((sum, num) => sum + num, 0);
    return `${program} (${totalSitIn})`;
});

const ctx = document.getElementById('sitInChart1').getContext('2d');
const sitInChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: programLabels,
        datasets: [{
            label: 'Total Sit-In Count',
            data: Object.values(programData).map(values => values.reduce((sum, num) => sum + num, 0)),
            backgroundColor: backgroundColors,
            borderColor: borderColors,
            borderWidth: 1,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'x', // Horizontal bars
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Sit-In Count',
                    font: {
                        size: 14, // Smaller font size for mobile
                    },
                },
                ticks: {
                    font: {
                        size: 12, // Smaller font size for mobile
                    },
                },
            },
            x: {
                title: {
                    display: true,
                    text: 'Programs',
                    font: {
                        size: 14, // Smaller font size for mobile
                    },
                },
                ticks: {
                    font: {
                        size: 12, // Smaller font size for mobile
                    },
                    callback: function (value) {
                        // Truncate long labels for better readability
                        return this.getLabelForValue(value).substring(0, 10) + '...';
                    },
                },
            },
        },
        plugins: {
            legend: {
                display: true,
                labels: {
                    font: {
                        size: 12, // Smaller font size for mobile
                    },
                },
            },
            tooltip: {
                enabled: true,
                callbacks: {
                    label: function (context) {
                        const label = context.dataset.label || '';
                        const value = context.raw || 0;
                        return `${label}: ${value}`;
                    },
                },
            },
        },
        layout: {
            padding: {
                left: 10,
                right: 10,
                top: 10,
                bottom: 10,
            },
        },
    },
});

// Enable horizontal scrolling for the chart container
const chartContainer = document.getElementById('chart-container');
if (chartContainer) {
    chartContainer.style.overflowX = 'auto';
    chartContainer.style.overflowY = 'hidden';
}



  