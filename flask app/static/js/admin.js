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

    if (!adminUsername) {
        Swal.fire('Error', 'Admin username not found. Please log in again.', 'error');
        return;
    }

    const announcementText = document.getElementById('announcement-text').value;

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
            Swal.fire('Success', 'Announcement posted successfully!', 'success');
            document.getElementById('announcement-text').value = '';
            fetchAnnouncements();
        } else {
            Swal.fire('Error', 'Failed to post announcement: ' + data.message, 'error');
        }
    })
    .catch(error => console.error('Error posting announcement:', error));
});

// Add event listeners for edit and delete buttons
function addEditDeleteListeners() {
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const announcementId = e.target.getAttribute('data-id');
            openEditModal(announcementId);
        });
    });

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
            document.getElementById('editModal').style.display = 'flex';
        })
        .catch(error => console.error('Error fetching announcement:', error));
}

// Close Edit Modal
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
        body: JSON.stringify({ announcement_text: announcementText }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Success', 'Announcement updated successfully!', 'success');
            document.getElementById('editModal').style.display = 'none';
            fetchAnnouncements();
        } else {
            Swal.fire('Error', 'Failed to update announcement: ' + data.message, 'error');
        }
    })
    .catch(error => console.error('Error updating announcement:', error));
});

// Show Delete Confirmation Modal
function showDeleteConfirmation(announcementId) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'You won\'t be able to revert this!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            deleteAnnouncement(announcementId);
        }
    });
}

// Confirm Delete
function deleteAnnouncement(announcementId) {
    fetch(`/delete_announcement/${announcementId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire('Deleted!', 'Announcement has been deleted.', 'success');
            fetchAnnouncements();
        } else {
            Swal.fire('Error', 'Failed to delete announcement: ' + data.message, 'error');
        }
    })
    .catch(error => console.error('Error deleting announcement:', error));
}


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
    BSHRM: [8, 12, 7, 11, 14, 10],
    BSN: [9, 15, 6, 12, 10, 8],
    BEEd: [7, 10, 14, 12, 8, 9],
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
    'rgba(255, 193, 7, 0.6)', 'rgba(96, 125, 139, 0.6)', 'rgba(244, 67, 54, 0.6)',
    'rgba(63, 81, 181, 0.6)', 'rgba(33, 150, 243, 0.6)', 'rgba(255, 87, 34, 0.6)',
];

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
        indexAxis: 'x', 
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Sit-In Count',
                    font: { size: 14 },
                },
                ticks: { font: { size: 12 } },
                grid: { display: false } // Remove background grid lines
            },
            x: {
                title: {
                    display: true,
                    text: 'Programs',
                    font: { size: 14 },
                },
                ticks: {
                    font: { size: 12 },
                    callback: function (value) {
                        return this.getLabelForValue(value).substring(0, 10) + '...';
                    },
                },
                grid: { display: false } // Remove background grid lines
            },
        },
        plugins: {
            legend: {
                display: true,
                labels: { font: { size: 12 } },
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
            padding: { left: 10, right: 10, top: 10, bottom: 10 },
        },
    },
});

// Enable horizontal scrolling for the chart container
const chartContainer = document.getElementById('chart-container');
if (chartContainer) {
    chartContainer.style.overflowX = 'auto';
    chartContainer.style.overflowY = 'hidden';
}



const socketURL =
window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000' // Local WebSocket URL
    : 'https://ccs-sit-in-monitoring-system.onrender.com'; // Render WebSocket URL

const socket = io(socketURL, {
    transports: ['websocket'],  // Force WebSocket transport
    upgrade: false,             // Disable fallback to polling
    reconnection: true,         // Enable reconnection
    reconnectionAttempts: 5,    // Number of reconnection attempts
    reconnectionDelay: 1000,    // Delay between reconnection attempts (1 second)
});

socket.on('update_active_users', function (activeUsers) {
    const activeUsersCountElement = document.getElementById('active-users-count');
    if (activeUsersCountElement) {
        activeUsersCountElement.textContent = activeUsers.length;
    }
});

socket.on('connect', function () {
    console.log('WebSocket connected to', socketURL);
});

socket.on('disconnect', function () {
    console.log('WebSocket disconnected');
});

socket.on('connect_error', function (error) {
    console.error('WebSocket connection error:', error);
});


document.querySelectorAll(".approve-btn").forEach(button => {
    button.addEventListener("click", function () {
        let reservationId = this.dataset.reservationId;
        let studentName = this.closest("tr").querySelector("td:nth-child(2)").textContent;

        Swal.fire({
            title: 'Are you sure?',
            text: `Do you want to approve the reservation for ${studentName}?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Yes, approve it!',
            cancelButtonText: 'No, cancel!',
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(`/approve-reservation/${reservationId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            title: 'Approved!',
                            text: `Reservation for ${studentName} has been approved.`,
                            icon: 'success',
                            confirmButtonText: 'OK',
                        }).then(() => {
                            location.reload(); // Refresh the page after confirmation
                        });
                    } else {
                        Swal.fire({
                            title: 'Error!',
                            text: 'Failed to approve reservation.',
                            icon: 'error',
                            confirmButtonText: 'OK',
                        });
                    }
                })
                .catch(error => {
                    Swal.fire({
                        title: 'Error!',
                        text: 'An error occurred while approving the reservation.',
                        icon: 'error',
                        confirmButtonText: 'OK',
                    });
                });
            }
        });
    });
});
