const socketURL =
window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000' // Local WebSocket URL
    : 'https://ccs-sit-in-monitoring-system.onrender.com'; // Render WebSocket URL

const socket = io(socketURL, {
transports: ['websocket'],
upgrade: false,
reconnection: true,
reconnectionAttempts: 5,
reconnectionDelay: 1000,
});


document.addEventListener('DOMContentLoaded', function () {
    // Flash messages logic (unchanged)
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(flashMessage => {
        setTimeout(() => {
            flashMessage.classList.add('fade-out');
        }, 2500);
        flashMessage.addEventListener('animationend', () => {
            flashMessage.remove();
        });
    });

    // Sidebar scrollbar detection
    function checkSidebarScrollable() {
        const sidebar = document.querySelector('aside .sidebar');
        if (sidebar) {
            // Check if content is scrollable
            const isScrollable = sidebar.scrollHeight > sidebar.clientHeight;
            
            // Add or remove 'scrollable' class based on condition
            if (isScrollable) {
                sidebar.classList.add('scrollable');
            } else {
                sidebar.classList.remove('scrollable');
            }
        }
    }
    
    // Check on page load
    checkSidebarScrollable();
    
    // Check when window is resized
    window.addEventListener('resize', checkSidebarScrollable);

    // SPA Behavior (unchanged)
    const sidebarLinks = document.querySelectorAll('.sidebar a');
    const bottomNavLinks = document.querySelectorAll('.bottom-nav a');
    const pageContents = document.querySelectorAll('.page-content');

    // Function to handle page switching (unchanged)
    function switchPage(page) {
        // Hide all pages
        pageContents.forEach(content => {
            content.style.display = 'none';
        });

        // Show the selected page
        const selectedPage = document.getElementById(page);
        if (selectedPage) {
            selectedPage.style.display = 'block';
        }

        // Update the URL hash
        window.location.hash = page;

        // Update active state for sidebar links
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            }
        });

        // Update active state for bottom navigation links
        bottomNavLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            }
        });
        
        // Check if sidebar is scrollable after changing page
        checkSidebarScrollable();

        // Refresh page-specific data
        if (page === 'dashboard') {
            // Refresh the leaderboard data
            if (typeof fetchLeaderboard === 'function') {
                fetchLeaderboard();
            }
            // Update active users count
            updateUserCount();
        } else if (page === 'sit-in') {
            // Fetch current sit-ins
            fetchAndDisplayCurrentSitIn();
        } else if (page === 'records') {
            // Fetch sit-in records
            fetchAndDisplaySitInRecords();
        } else if (page === 'announcements') {
            // Fetch announcements
            fetchAnnouncements();
        } else if (page === 'feedback') {
            // Fetch feedback data
            fetchFeedback();
        } else if (page === 'lab-resources') {
            // Fetch lab resources
            fetchLabResources();
        }
    }

    // Add event listeners to sidebar links (unchanged)
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            switchPage(page);
        });
    });

    // Add event listeners to bottom navigation links (unchanged)
    bottomNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            switchPage(page);
        });
    });

    // Handle page load and hash changes (unchanged)
    function loadPageFromHash() {
        const page = window.location.hash.substring(1);
        if (page) {
            switchPage(page);
        } else {
            switchPage('dashboard');
        }
    }

    // Load the correct page on initial load (unchanged)
    loadPageFromHash();

    // Listen for hash changes to handle page refreshes (unchanged)
    window.addEventListener('hashchange', loadPageFromHash);

    // Search Input Logic
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const modal = document.getElementById('searchModal');
    const modalReservationsBody = document.getElementById('modalReservationsBody');
    const closeModalBtn = document.querySelector('.close-modal');

    function displayReservations(reservations) {
        modalReservationsBody.innerHTML = ''; // Clear existing content
    
        if (reservations.length === 0) {
            modalReservationsBody.innerHTML = '<p>No records found.</p>';
        } else {
            reservations.forEach(reservation => {
                const reservationItem = document.createElement('div');
                reservationItem.classList.add('reservation-item');
                reservationItem.innerHTML = `
                    <h3>${reservation.student_name}</h3>
                    <p>ID: ${reservation.student_idno}</p>
                    <p>Lab: ${reservation.lab_name}</p> <!-- Use lab_name instead of lab_id -->
                    <p>Purpose: ${reservation.purpose}</p>
                    <p>Date: ${reservation.reservation_date}</p>
                    <p>Status: ${reservation.status}</p>
                    <p>Sessions Left: ${reservation.sessions_left}</p> <!-- Display sessions_left -->
                    <div class="reservation-actions">
                        <button class="sit-in-btn" data-reservation-id="${reservation.id}">Sit In</button>
                        <button class="close-btn" data-reservation-id="${reservation.id}">Close</button>
                    </div>
                `;
                modalReservationsBody.appendChild(reservationItem);
            });
        }
    
        // Show the modal
        modal.style.display = 'block';
    }
    

    // Fetch reservations based on search term
    function fetchReservations(searchTerm = '') {
        fetch(`/get_reservations?search=${searchTerm}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && Array.isArray(data.data)) {
                    displayReservations(data.data); // Display reservations in modal
                } else {
                    console.error('Invalid response format:', data);
                    modalReservationsBody.innerHTML = '<p>No records found.</p>';
                    modal.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error fetching reservations:', error);
                modalReservationsBody.innerHTML = '<p>Error fetching records.</p>';
                modal.style.display = 'block';
            });
    }

    // Handle form submission (search)
    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
            fetchReservations(searchTerm);
        } else {
            modalReservationsBody.innerHTML = '<p>Please enter a search term.</p>';
            modal.style.display = 'block';
        }
    });

    // Close modal when the close button is clicked
    closeModalBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close modal when clicking outside of it
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Handle Sit In and Close actions
    modalReservationsBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('sit-in-btn')) {
            const reservationId = e.target.getAttribute('data-reservation-id');
            sitInReservation(reservationId);
        } else if (e.target.classList.contains('close-btn')) {
            const reservationId = e.target.getAttribute('data-reservation-id');
            closeReservation(reservationId);
        }
    });

    function sitInReservation(reservationId) {
        fetch(`/sit-in-reservation/${reservationId}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Reservation approved successfully');
                fetchReservations(searchInput.value.trim()); // Refresh the modal content
            } else {
                alert('Failed to approve reservation');
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function closeReservation(reservationId) {
        fetch(`/close-reservation/${reservationId}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message); // Show success message
                fetchReservations(searchInput.value.trim()); // Refresh the modal content
            } else {
                alert('Failed to close reservation');
            }
        })
        .catch(error => console.error('Error:', error));
    }
});


    // Toggle dropdown on profile click
    const profile = document.getElementById('profile');
    const dropdown = document.getElementById('dropdown');

    if (profile && dropdown) {
        profile.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event from bubbling up
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            profile.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!profile.contains(e.target)) {
                dropdown.style.display = 'none';
                profile.classList.remove('active');
            }
        });
    }

  // Data for programs
const programData = {
    BSIT: [12, 19, 8, 15, 10, 7],
    BSCpE: [5, 14, 10, 8, 12, 9],
    BSBA: [7, 11, 13, 6, 9, 15],
    BSCS: [10, 8, 12, 14, 7, 11],
    BSEd: [6, 9, 15, 10, 8, 12], 
    BSHRM: [8, 12, 7, 11, 14, 10],
    BSN: [9, 15, 6, 12, 10, 8],
    BCE: [11, 7, 14, 9, 12, 6],
    BCrim: [8, 11, 13, 6, 9, 15],
    BAcc: [6, 9, 15, 10, 8, 12],
};

// Violet color scheme
const backgroundColor = 'rgba(138, 43, 226, 0.2)'; // Violet (light)
const borderColor = 'rgba(138, 43, 226, 1)'; // Violet (dark)

// Calculate total sit-ins for each program
const programLabels = Object.keys(programData).map(program => {
    const totalSitIn = programData[program].reduce((sum, num) => sum + num, 0);
    return `${program} (${totalSitIn})`;
});

// Get the chart context
const ctx = document.getElementById('sitInChart1').getContext('2d');
const isMobile = window.innerWidth < 600; // Check if the screen is small

// Create the chart
const sitInChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: isMobile ? Array(programLabels.length).fill('') : programLabels, // Hide labels on mobile
        datasets: [{
            label: 'Total Sit-In Count',
            data: Object.values(programData).map(values => values.reduce((sum, num) => sum + num, 0)),
            backgroundColor: backgroundColor,
            borderColor: borderColor,
            borderWidth: 1,
            barThickness: 'flex',
            categoryPercentage: 0.7,
            barPercentage: 0.9,
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
                    display: !isMobile, 
                    text: 'Sit-In Count', 
                    font: { size: 14 },
                    color: '#ffffff', // White color for y-axis title
                },
                ticks: { 
                    display: !isMobile, 
                    font: { size: 12 },
                    color: '#ffffff', // White color for y-axis labels
                },
                grid: { 
                    display: false,
                    color: 'rgba(255, 255, 255, 0.1)', // Light grid lines for better visibility
                }
            },
            x: {
                title: { 
                    display: !isMobile, 
                    text: 'Programs', 
                    font: { size: 14 },
                    color: '#ffffff', // White color for x-axis title
                },
                ticks: {
                    display: !isMobile, // Hide x-axis labels on mobile
                    autoSkip: false,
                    maxRotation: 45,
                    minRotation: 45,
                    font: { size: 12 },
                    color: '#ffffff', // White color for x-axis labels
                },
                grid: { 
                    display: false,
                    color: 'rgba(255, 255, 255, 0.1)', // Light grid lines for better visibility
                }
            },
        },
        plugins: {
            legend: { 
                display: false, // Hide legend
            },
            tooltip: { 
                enabled: true, // Keep tooltips enabled
                backgroundColor: 'rgba(0, 0, 0, 0.8)', // Dark tooltip background
                titleColor: '#ffffff', // White tooltip title
                bodyColor: '#ffffff', // White tooltip body text
            },
        },
        layout: { 
            padding: { left: 10, right: 10, top: 10, bottom: 10 },
        },
    },
});

// Enable horizontal scrolling for mobile
const chartContainer = document.getElementById('chart-container');
if (chartContainer) {
    chartContainer.style.overflowX = 'auto';
    chartContainer.style.overflowY = 'hidden';
    chartContainer.style.whiteSpace = 'nowrap';
}
// Date Picker Logic
const datePicker = document.getElementById('datePicker');

// Set max date to today
datePicker.max = new Date().toISOString().split('T')[0];

// Add event listener for date change
datePicker.addEventListener('change', (e) => {
    const selectedDate = e.target.value;
    const today = new Date().toISOString().split('T')[0];

    if (selectedDate > today) {
        alert('You cannot select a future date.');
        datePicker.value = today; // Reset to today
        return;
    }

    // Simulate fetching data based on the selected date
    const filteredData = filterDataByDate(selectedDate);

    // Update the chart
    sitInChart.data.datasets[0].data = filteredData;
    sitInChart.update();
});

// Simulate filtering data by date (replace with actual backend logic)
function filterDataByDate(date) {
    // For now, return random data as a placeholder
    return Object.values(programData).map(values => {
        return values[Math.floor(Math.random() * values.length)]; // Random value for demo
    });
}

    // Update user count every second
    function updateUserCount() {
        fetch('/get_user_count')
            .then(response => response.json())
            .then(data => {
                const userCountElement = document.querySelector('.user-count');
                if (userCountElement) {
                    userCountElement.textContent = data.student_count;
                }
            })
            .catch(error => console.error('Error fetching user count:', error));
    }

    setInterval(updateUserCount, 1000); // Update every 1 second
    updateUserCount(); // Call once immediately

    // Socket.IO logic (if applicable)

    socket.on('update_active_users', function (activeUsers) {
        const activeUsersCountElement = document.getElementById('active-users-count');
        if (activeUsersCountElement) {
            // Update only the number, leaving the status circle intact
            activeUsersCountElement.innerHTML = `${activeUsers.length} <span class="status-circle"></span>`;
        }
    });
    

    socket.on('new_announcement', (data) => {
        console.log('New announcement:', data);
        fetchAnnouncements(); // Refresh the announcements list
    });

    socket.on('announcement_updated', (data) => {
    console.log('Updated announcement:', data);
    fetchAnnouncements(); // Refresh the announcements list
    });

    // Listen for deleted announcements
    socket.on('announcement_deleted', (data) => {
        console.log('Deleted announcement:', data);
        fetchAnnouncements(); // Refresh the announcements list
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

    // Announcements logic (if applicable)
    const announcementForm = document.getElementById('announcement-form');
    const announcementsBody = document.getElementById('announcements-body');

    if (announcementForm && announcementsBody) {
        announcementForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const announcementText = document.getElementById('announcement-text').value;

            fetch('/create_announcement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_username: 'Admin', // Replace with dynamic admin username
                    announcement_text: announcementText,
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Success', 'Announcement posted successfully!', 'success');
                    document.getElementById('announcement-text').value = ''; // Clear the textarea
                    fetchAnnouncements(); // Refresh the list
                } else {
                    Swal.fire('Error', 'Failed to post announcement: ' + data.message, 'error');
                }
            })
            .catch(error => console.error('Error posting announcement:', error));
        });

        // Fetch announcements when the page loads
        fetchAnnouncements();
    }

    function fetchAnnouncements() {
        fetch('/get_announcements')
            .then(response => response.json())
            .then(data => {
                const announcementsBody = document.getElementById('announcements-body');
                if (announcementsBody) {
                    announcementsBody.innerHTML = ''; // Clear existing rows
    
                    data.forEach(announcement => {
                        const row = document.createElement('tr');
                        const announcementDate = new Date(announcement.announcement_date).toLocaleString();
    
                        row.innerHTML = `
                            <td data-label="Date">${announcementDate}</td>
                            <td data-label="Admin">${announcement.admin_username}</td>
                            <td data-label="Announcement">${announcement.announcement_text}</td>
                            <td data-label="Actions">
                                <div class="action-buttons">
                                    <button class="edit-btn" data-id="${announcement.id}">
                                        <i class="ri-edit-line"></i> Edit
                                    </button>
                                    <button class="delete-btn" data-id="${announcement.id}">
                                        <i class="ri-delete-bin-line"></i> Delete
                                    </button>
                                </div>
                            </td>
                        `;
    
                        announcementsBody.appendChild(row);
                    });
    
                    // Add event listeners for edit and delete buttons
                    addEditDeleteListeners();
                }
            })
            .catch(error => console.error('Error fetching announcements:', error));
    }
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
                // No need to call fetchAnnouncements() here because the Socket.IO event will handle it
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
            // No need to call fetchAnnouncements() here because the Socket.IO event will handle it
        } else {
            Swal.fire('Error', 'Failed to delete announcement: ' + data.message, 'error');
        }
    })
    .catch(error => console.error('Error deleting announcement:', error));
}



// Daily Sit-Ins Chart (Bar Chart)
const dailySitInsCtx = document.getElementById('dailySitInsChart').getContext('2d');
const dailySitInsChart = new Chart(dailySitInsCtx, {
    type: 'bar',
    data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Sit-Ins',
            data: [12, 19, 3, 5, 2, 3, 7],
            backgroundColor: 'rgba(107, 8, 255, 0.8)', // Brighter color for better contrast
            borderColor: 'rgba(107, 8, 255, 0.8)', // Set to the same as background color or use another color
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false // Hide legend
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    drawBorder: false,
                    borderDash: [5, 5],
                    color: 'rgba(255, 255, 255, 0.1)' // Light grid lines for better contrast
                }
            },
            x: {
                grid: {
                    display: false // Hide x-axis grid lines
                }
            }
        },
        backgroundColor: 'transparent', // Make background transparent
    }
});


// Lab Usage Bar Chart
const labUsageCtx = document.getElementById('labUsageChart').getContext('2d');
const labUsageChart = new Chart(labUsageCtx, {
    type: 'bar',
    data: {
        labels: ['Lab544', 'Lab542', 'Lab530', 'Lab524', 'Lab526', 'Lab525'], // Lab Names
        datasets: [{
            label: 'Current Lab Usage',
            data: [20, 35, 10, 45, 30, 50], // Example data points for lab usage
            backgroundColor: '#17c1e8', // Brighter blue
            hoverBackgroundColor: '#0b8e9d',
            hoverBorderColor: '#0b8e9d'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false // Hide legend
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    drawBorder: false,
                    borderDash: [5, 5],
                    color: 'rgba(255, 255, 255, 0.1)' // Light grid lines for better contrast
                },
                ticks: {
                    color: '#ddd' // Light color for Y-axis ticks
                }
            },
            x: {
                grid: {
                    display: false // Hide x-axis grid lines
                },
                ticks: {
                    color: '#ddd' // Light color for X-axis ticks
                }
            }
        },
        backgroundColor: 'transparent', // Make background transparent
    }
});


const adminAttendanceCtx = document.getElementById('adminAttendanceChart').getContext('2d');

// Base color in HSL format (Purple)
const baseColor = 'hsl(273, 57.30%, 34.90%)';

// Function to generate a lighter or darker shade of the base color
function adjustColor(color, amount) {
    const hsl = color.match(/\d+/g); // Extract HSL values
    let lightness = parseInt(hsl[2]); // Get lightness value
    lightness = Math.min(100, Math.max(0, lightness + amount)); // Adjust lightness
    return `hsl(${hsl[0]}, ${hsl[1]}%, ${lightness}%)`; // Return new HSL color
}

const adminAttendanceChart = new Chart(adminAttendanceCtx, {
    type: 'line',
    data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Admin Attendance',
            data: [85, 80, 75, 90, 85, 95, 80],
            borderColor: adjustColor(baseColor, -10), // Darker purple for the line
            backgroundColor: adjustColor(baseColor, 20), // Lighter purple for the background
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 2, // Smaller dots
            pointBackgroundColor: '#fff', // White color for points (or use the background color)
            pointBorderColor: '#fff', // White border for the points
            pointBorderWidth: 1, // Thinner border for points
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false // Hide legend
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    drawBorder: false,
                    borderDash: [5, 5],
                    color: 'rgba(255, 255, 255, 0.2)' // Light grid lines for dark mode
                },
                ticks: {
                    color: '#ddd' // Light color for Y-axis ticks
                }
            },
            x: {
                grid: {
                    display: false // Hide x-axis grid lines
                },
                ticks: {
                    color: '#ddd' // Light color for X-axis ticks
                }
            }
        }
    }
});


let currentPage = 1;
let rowsPerPage = 10; // Default rows per page
let allFeedbackData = []; // Store all feedback data for pagination
let feedbackRatingsChart; // Store the chart instance globally


// Debug: Check WebSocket connection
socket.on('connect', () => {
    console.log('Admin: Connected to WebSocket server');
});

socket.on('disconnect', () => {
    console.log('Admin: Disconnected from WebSocket server');
});

// Function to adjust rowsPerPage based on screen width
function adjustRowsPerPage() {
    if (window.innerWidth <= 768) {
        rowsPerPage = 5; // Set rows per page to 5 for screens <= 768px
    } else {
        rowsPerPage = 10; // Default rows per page for larger screens
    }
}

// Function to detect and censor foul language
function detectFoulLanguage(text) {
    // List of foul words (can be expanded)
    const foulWords = [
        'fuck', 'shit', 'asshole', 'bitch', 'bastard', 'idiot', 
        'piste', 'atay', 'animal', // Add more as needed
        // Include variations and different languages
        /f\*ck/, /sh\*t/, /b\*tch/, /a\*\*hole/, /id\*ot/
    ];
    
    let hasFoulLanguage = false;
    let censoredText = text;
    
    foulWords.forEach(word => {
        const regex = new RegExp(word, 'gi');
        if (regex.test(text)) {
            hasFoulLanguage = true;
            censoredText = censoredText.replace(regex, match => {
                // Replace with asterisks but keep first and last character
                if (match.length > 2) {
                    return match[0] + '*'.repeat(match.length - 2) + match.slice(-1);
                }
                return '*'.repeat(match.length);
            });
        }
    });
    
    return {
        hasFoulLanguage,
        censoredText: hasFoulLanguage ? censoredText : text,
        originalText: text
    };
}

// Modify the displayTableRows function to highlight foul language
function displayTableRows(data, page) {
    const tableBody = document.querySelector('#feedbackTable tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(feedback => {
        const languageCheck = detectFoulLanguage(feedback.feedback_text);
        const feedbackClass = languageCheck.hasFoulLanguage ? 'foul-language' : '';
        
        const newRow = document.createElement('tr');
        newRow.innerHTML = 
            `<td data-label="Lab">${feedback.lab}</td>
             <td data-label="Student ID">${feedback.student_idno}</td>
             <td data-label="Feedback" class="${feedbackClass}">${languageCheck.censoredText}</td>
             <td data-label="Rating" class="star-rating">${'★'.repeat(feedback.rating)}${'☆'.repeat(5 - feedback.rating)}</td>`;
        
        if (languageCheck.hasFoulLanguage) {
            newRow.dataset.foulLanguage = 'true';
        }
        
        tableBody.appendChild(newRow);
    });

    // Update pagination controls
    updatePaginationControls(data.length);
}

// Function to update pagination controls
function updatePaginationControls(totalRows) {
    const totalPages = Math.ceil(totalRows / rowsPerPage);
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    document.getElementById('prevPage').disabled = currentPage === 1;
    document.getElementById('nextPage').disabled = currentPage === totalPages;
}

// Function to fetch feedback data
function fetchFeedback() {
    fetch('/get-feedback')
        .then(response => response.json())
        .then(data => {
            console.log('Fetched data:', data); // Debug: Log fetched data
            allFeedbackData = data; // Store all feedback data
            displayTableRows(allFeedbackData, currentPage); // Display the first page
            updateChart(data); // Update the chart with the fetched data
        })
        .catch(error => console.error('Error fetching feedback:', error));
}

// Function to update the doughnut chart
function updateChart(data) {
    const ratings = data.map(feedback => feedback.rating);

    // Count the ratings in each category
    const good = ratings.filter(r => r >= 4).length;
    const neutral = ratings.filter(r => r >= 2 && r < 4).length;
    const negative = ratings.filter(r => r < 2).length;

    // If no data, show the prompt
    if (good + neutral + negative === 0) {
        document.getElementById('noDataPrompt').style.display = 'block';
        return;
    }

    // Update the chart data
    if (feedbackRatingsChart) {
        feedbackRatingsChart.data.datasets[0].data = [good, neutral, negative];
        feedbackRatingsChart.update();
    } else {
        // Create the chart if it doesn't exist
        const ctx = document.getElementById('feedbackRatingsChart').getContext('2d');
        feedbackRatingsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Good (4-5)', 'Neutral (2-3)', 'Negative (0-1)'],
                datasets: [{
                    label: 'Feedback Ratings',
                    data: [good, neutral, negative],
                    backgroundColor: [
                        'rgba(173, 255, 47, 0.8)', // Yellow-Green
                        'rgba(0, 191, 255, 0.8)', // Light Blue
                        'rgba(255, 0, 38, 0.8)'  // Light Red
                    ],
                    borderColor: [
                        'rgba(173, 255, 47, 1)', // Yellow-Green border
                        'rgb(0, 191, 255)', // Light Blue border
                        'rgb(255, 0, 38)'  // Light Red border
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allow chart to resize freely
                cutout: '70%', // Make the doughnut hole larger (smaller chart)
                plugins: {
                    legend: {
                        position: 'bottom', // Position the legend below the chart
                        labels: {
                            color: '#fff', // White text for dark theme
                            font: {
                                size: 14
                            },
                            padding: 20 // Add margin around the labels
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)', // Dark tooltip background
                        titleColor: '#fff', // White tooltip title
                        bodyColor: '#fff', // White tooltip text
                        borderColor: '#333', // Dark border for tooltip
                        borderWidth: 1
                    }
                }
            }
        });

        // Adjust canvas size to make the chart smaller
        const canvas = document.getElementById('feedbackRatingsChart');
        canvas.style.width = '300px'; // Set width
        canvas.style.height = '300px'; // Set height
    }
}

// Add event listeners for pagination buttons
document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        displayTableRows(allFeedbackData, currentPage);
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    if (currentPage < Math.ceil(allFeedbackData.length / rowsPerPage)) {
        currentPage++;
        displayTableRows(allFeedbackData, currentPage);
    }
});

// Call adjustRowsPerPage on page load and window resize
window.addEventListener('resize', adjustRowsPerPage);
document.addEventListener('DOMContentLoaded', () => {
    adjustRowsPerPage();
    fetchFeedback(); // Fetch feedback data after adjusting rowsPerPage
});

// Admin Side JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Fetch and display current sit-in reservations when the page loads
    fetchAndDisplayCurrentSitIn();
    fetchAndDisplaySitInRecords();

    // Handle logout button clicks using event delegation
    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('logout-btn')) {
            const reservationId = event.target.getAttribute('data-reservation-id');
            handleLogout(reservationId);
        }
    });

    // Listen for new sit-in events
    socket.on('new_sitin', function(reservation) {
        // Only add to current sit-in if not logged out
        if (reservation.status === 'Approved' && !reservation.logout_time) {
            const tableBody = document.querySelector('#reservations-table tbody');
            
            const newRow = document.createElement('tr');
            newRow.setAttribute('data-reservation-id', reservation.id);
            
            newRow.innerHTML = `
                <td>${reservation.student_idno}</td>
                <td>${reservation.student_name}</td>
                <td>${reservation.lab_name}</td>
                <td>${reservation.purpose}</td>
                <td>${reservation.reservation_date}</td>
                <td>${reservation.login_time}</td>
                <td>N/A</td>
                <td>Session ${reservation.session_number}</td>
                <td class="status">${reservation.status}</td>
                <td>
                    <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
                </td>
            `;
            
            tableBody.prepend(newRow);
        }
    });


    socket.on('reservation_updated', function (data) {
        const tableBody = document.querySelector('#reservations-table tbody');
        const row = tableBody.querySelector(`tr[data-reservation-id="${data.reservation_id}"]`);
    
        if (row) {
            row.remove(); // remove student row
        }
    
        // ✅ Check if table is empty, then show the empty message
        const hasRows = tableBody.querySelectorAll('tr').length > 0;
    
        if (!hasRows) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="10" style="
                    text-align: center;
                    padding: 30px 40px;
                    color: #888;
                    font-size: 17px;
                ">
                    <i class="fas fa-chair" style="margin-right: 10px; color: #ccc; font-size: 18px;"></i>
                    No student is currently sitting in.
                </td>
            `;
            tableBody.appendChild(emptyRow);
        }
    
        // Update other tables if needed
        fetchAndDisplaySitInRecords();
    });
    


    
    // Socket event listener for reservation approvals
    socket.on('reservation_approved', function (data) {
        const reservationId = data.reservation_id;
        const status = data.status;

        // Update the reservation status in the UI
        const reservationRow = document.querySelector(`tr[data-reservation-id="${reservationId}"]`);
        if (reservationRow) {
            reservationRow.querySelector('.status').textContent = status;
        }
    });
});



function handleLogout(reservationId) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'You are about to log out this student',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, log out!'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/logout-student/${reservationId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: 'Success!',
                        text: `Student logged out successfully. Sessions left: ${data.sessions_left}`,
                        icon: 'success',
                        confirmButtonText: 'OK'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Reload the page after the user clicks OK
                            window.location.reload();
                        }
                    });
                } else {
                    Swal.fire('Error!', data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error!', 'Failed to log out student', 'error');
            });
        }
    });
}

// Function to update a single reservation row
function updateReservationRow(reservation) {
    const row = document.querySelector(`tr[data-reservation-id="${reservation.id}"]`);
    if (row) {
        // Update the row data
        row.querySelector('.logout-time').textContent = reservation.logout_time;
        row.querySelector('.status').textContent = reservation.status;
        row.querySelector('.sessions-left').textContent = reservation.sessions_left;
        
        // Disable the logout button
        const logoutBtn = row.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.disabled = true;
            logoutBtn.classList.add('disabled-btn');
        }
    } else {
        // If row not found (shouldn't happen), refresh the whole table
        fetchAndDisplayCurrentSitIn();
    }
}


// Handle logout button clicks
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('logout-btn') && !event.target.disabled) {
        const reservationId = event.target.getAttribute('data-reservation-id');
        handleLogout(reservationId);
    }
});


function fetchAndDisplayCurrentSitIn() {
    fetch('/get_currentsitin')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#reservations-table tbody');
            tableBody.innerHTML = '';

            if (data.success && data.data.length > 0) {
                data.data.forEach(reservation => {
                    const row = document.createElement('tr');
                    row.setAttribute('data-reservation-id', reservation.id);
                    row.innerHTML = `
                        <td>${reservation.student_idno}</td>
                        <td>${reservation.student_name}</td>
                        <td>${reservation.lab_name}</td>
                        <td>${reservation.purpose}</td>
                        <td>${reservation.reservation_date}</td>
                        <td>${reservation.login_time}</td>
                        <td>N/A</td>
                        <td>Session ${reservation.session_number}</td>
                        <td class="status">${reservation.status}</td>
                        <td>
                            <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                // Display "No student sitting in" row with styling and icon
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = `
                    <td colspan="10" style="
                        text-align: center;
                        padding: 30px 40px;
                        color: #888;
                        font-size: 17px;
                        transition: all 0.3s ease;
                    ">
                        <i class="fas fa-chair" style="margin-right: 10px; color: #ccc; font-size: 18px;"></i>
                        No student is currently sitting in.
                    </td>
                `;
                tableBody.appendChild(emptyRow);
            }
        })
        .catch(error => {
            console.error('Error fetching current sit-ins:', error);
            Swal.fire('Error', 'Failed to load current sit-ins', 'error');
        });
}

// Optional: Add new rows in real-time when a new sit-in is approved
socket.on('new_sitin', function (reservation) {
    if (reservation.status === 'Approved' && !reservation.logout_time) {
        const tableBody = document.querySelector('#reservations-table tbody');

        // Remove "no student" row if it exists
        const emptyRow = tableBody.querySelector('tr td[colspan]');
        if (emptyRow) {
            tableBody.innerHTML = '';
        }

        const newRow = document.createElement('tr');
        newRow.setAttribute('data-reservation-id', reservation.id);
        newRow.innerHTML = `
            <td>${reservation.student_idno}</td>
            <td>${reservation.student_name}</td>
            <td>${reservation.lab_name}</td>
            <td>${reservation.purpose}</td>
            <td>${reservation.reservation_date}</td>
            <td>${reservation.login_time}</td>
            <td class="logout-time">N/A</td>
            <td>Session ${reservation.session_number}</td>
            <td class="status">${reservation.status}</td>
            <td>
                <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
            </td>
        `;
        tableBody.prepend(newRow);
    }
});

// Global variables for sit-in records pagination
let sitInRecordsData = [];
let sitInRecordsCurrentPage = 1;
let sitInRecordsPerPage = 5;

function fetchAndDisplaySitInRecords() {
    fetch('/get_sitin_records')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store all records for pagination
                sitInRecordsData = data.data;
                
                // Display the current page
                displaySitInRecordsPage(sitInRecordsCurrentPage);
                
                // Create pagination controls if they don't exist
                if (!document.getElementById('sit-in-records-pagination')) {
                    createSitInRecordsPagination();
                } else {
                    updateSitInRecordsPagination();
                }
            } else {
                console.error('Failed to fetch sit-in records:', data.message);
                Swal.fire('Error', 'Failed to load sit-in records', 'error');
            }
        })
        .catch(error => {
            console.error('Error fetching sit-in records:', error);
            Swal.fire('Error', 'Failed to load sit-in records', 'error');
        });
}

function displaySitInRecordsPage(page) {
                const tableBody = document.querySelector('#records-table tbody');
                tableBody.innerHTML = '';

    // Calculate start and end indices
    const startIndex = (page - 1) * sitInRecordsPerPage;
    const endIndex = Math.min(startIndex + sitInRecordsPerPage, sitInRecordsData.length);
    
    // Slice the data for the current page
    const pageData = sitInRecordsData.slice(startIndex, endIndex);
    
    if (pageData.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="8" style="text-align: center; padding: 20px;">
                No records found.
            </td>
        `;
        tableBody.appendChild(emptyRow);
        return;
    }
    
    pageData.forEach(reservation => {
                    const row = document.createElement('tr');
                    row.setAttribute('data-reservation-id', reservation.id);
                    row.innerHTML = `
                        <td>${reservation.student_idno}</td>
                        <td>${reservation.student_name}</td>
                        <td>${reservation.lab_name}</td>
                        <td>${reservation.purpose}</td>
                        <td>${reservation.reservation_date}</td>
                        <td>${reservation.login_time}</td>
                        <td>${reservation.logout_time || 'N/A'}</td>
            <td>
                <button class="btn-award-points" data-idno="${reservation.student_idno}" 
                    data-reservation-id="${reservation.id}"
                    ${reservation.points_awarded ? 'disabled' : ''}>
                    ${reservation.points_awarded ? 'Points Awarded' : 'Award Points'}
                </button>
            </td>
                    `;
                    tableBody.appendChild(row);
                });

    // Add event listeners to all award buttons
    document.querySelectorAll('.btn-award-points').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                const studentIdno = this.getAttribute('data-idno');
                const reservationId = this.getAttribute('data-reservation-id');
                awardPointsToStudent(studentIdno, this, reservationId);
            }
        });
    });
    
    // Update current page
    sitInRecordsCurrentPage = page;
}

function createSitInRecordsPagination() {
    const tableContainer = document.querySelector('#records .table-container');
    
    // Create pagination container
    const paginationDiv = document.createElement('div');
    paginationDiv.id = 'sit-in-records-pagination';
    paginationDiv.className = 'pagination-controls';
    
    // Create prev button
    const prevButton = document.createElement('button');
    prevButton.id = 'sit-in-records-prev';
    prevButton.textContent = 'Previous';
    prevButton.addEventListener('click', () => {
        if (sitInRecordsCurrentPage > 1) {
            displaySitInRecordsPage(sitInRecordsCurrentPage - 1);
            updateSitInRecordsPagination();
        }
    });
    
    // Create page info
    const pageInfo = document.createElement('span');
    pageInfo.id = 'sit-in-records-page-info';
    
    // Create next button
    const nextButton = document.createElement('button');
    nextButton.id = 'sit-in-records-next';
    nextButton.textContent = 'Next';
    nextButton.addEventListener('click', () => {
        const totalPages = Math.ceil(sitInRecordsData.length / sitInRecordsPerPage);
        if (sitInRecordsCurrentPage < totalPages) {
            displaySitInRecordsPage(sitInRecordsCurrentPage + 1);
            updateSitInRecordsPagination();
        }
    });
    
    // Append elements
    paginationDiv.appendChild(prevButton);
    paginationDiv.appendChild(pageInfo);
    paginationDiv.appendChild(nextButton);
    
    // Append pagination to container
    tableContainer.after(paginationDiv);
    
    // Update pagination controls
    updateSitInRecordsPagination();
}

function updateSitInRecordsPagination() {
    const totalPages = Math.ceil(sitInRecordsData.length / sitInRecordsPerPage);
    const pageInfo = document.getElementById('sit-in-records-page-info');
    const prevButton = document.getElementById('sit-in-records-prev');
    const nextButton = document.getElementById('sit-in-records-next');
    
    if (pageInfo && prevButton && nextButton) {
        pageInfo.textContent = `Page ${sitInRecordsCurrentPage} of ${totalPages}`;
        prevButton.disabled = sitInRecordsCurrentPage === 1;
        nextButton.disabled = sitInRecordsCurrentPage === totalPages;
    }
}

function awardPointsToStudent(studentIdno, buttonElement, reservationId) {
    Swal.fire({
        title: 'Award Points',
        text: 'Give this student 1 point for their lab session?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Award 1 Point',
        cancelButtonText: 'Cancel',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            return fetch('/award_points', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    student_idno: studentIdno,
                    reservation_id: reservationId,
                    reason: 'Reward for lab session'
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(response.statusText);
                }
                return response.json();
            })
            .catch(error => {
                Swal.showValidationMessage(
                    `Request failed: ${error}`
                );
            });
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed) {
            // Display the detailed message from the server
            Swal.fire({
                title: 'Success!',
                html: `
                    <div class="points-info">
                        <p>${result.value.message}</p>
                        <p>Student now has <strong>${result.value.sessions_left}</strong> sessions left.</p>
                    </div>
                `,
                icon: 'success',
                confirmButtonText: 'OK'
            }).then((confirmResult) => {
                if (confirmResult.isConfirmed) {
                    // Refresh the page after clicking OK
                    window.location.reload();
                }
            });
            
            // Disable the button and update text
            if (buttonElement) {
                buttonElement.disabled = true;
                buttonElement.textContent = 'Points Awarded';
                buttonElement.classList.add('disabled');
            }
            
            // Mark this reservation as having points awarded in the data array
            const reservation = sitInRecordsData.find(r => r.id === parseInt(reservationId));
            if (reservation) {
                reservation.points_awarded = true;
            }
            
            // Update the leaderboard if we're on the dashboard page
            if (document.getElementById('leaderboard-top-3')) {
                fetchLeaderboard();
            }
            
            // Refresh sit-in records to update any session counts
            fetchAndDisplaySitInRecords();
            
            // Also refresh current sit-in display if we're on that page
            if (window.location.hash === '#sit-in') {
                fetchAndDisplayCurrentSitIn();
            }
        }
    });
}

// Function to fetch and display the student points leaderboard
function fetchLeaderboard() {
    fetch('/get_leaderboard')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the top 3 cards section
                const top3Container = document.getElementById('leaderboard-top-3');
                const leaderboardTable = document.querySelector('#leaderboard-table tbody');
                
                // Clear previous content
                top3Container.innerHTML = '';
                leaderboardTable.innerHTML = '';
                
                // Check if we have any results
                if (data.leaderboard.length === 0) {
                    top3Container.innerHTML = '<p class="no-data">No student points data available yet.</p>';
                    return;
                }
                
                // Get the top 3 students for cards (or less if we have fewer students)
                const top3 = data.leaderboard.slice(0, Math.min(3, data.leaderboard.length));
                
                // Create the top 3 cards - rearrange them to put #1 in the center if we have 3 students
                if (top3.length === 3) {
                    // Create in order: 2nd (left), 1st (center), 3rd (right)
                    createLeaderboardCard(top3[1], 2, top3Container); // 2nd place (left)
                    createLeaderboardCard(top3[0], 1, top3Container); // 1st place (center)
                    createLeaderboardCard(top3[2], 3, top3Container); // 3rd place (right)
                } else {
                    // If we have fewer than 3, just display them in order
                    top3.forEach((student, index) => {
                        createLeaderboardCard(student, index + 1, top3Container);
                    });
                }
                
                // Populate the table with ranks 4-5 only (or less if we have fewer students)
                const tableData = data.leaderboard.slice(3, 5);
                
                tableData.forEach((student, index) => {
                    const rank = index + 4; // Start at rank 4
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${rank}</td>
                        <td>${student.student_idno}</td>
                        <td>${student.student_name}</td>
                        <td>${student.course}</td>
                        <td>${student.year_level}</td>
                        <td><span class="points-badge">${student.total_points}</span></td>
                        <td><span class="sitin-badge">${student.sitin_count}</span></td>
                    `;
                    leaderboardTable.appendChild(row);
                });
                
                // Hide the table if there are no students beyond top 3
                if (tableData.length === 0) {
                    document.querySelector('.leaderboard-table').style.display = 'none';
                } else {
                    document.querySelector('.leaderboard-table').style.display = 'table';
                }
            } else {
                console.error('Failed to fetch leaderboard:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching leaderboard:', error);
        });
}

// Helper function to create a leaderboard card
function createLeaderboardCard(student, rank, container) {
    // Determine CSS class based on rank
    let rankClass = '';
    let rankText = '';
    
    switch(rank) {
        case 1:
            rankClass = 'first';
            rankText = '1st';
            break;
        case 2:
            rankClass = 'second';
            rankText = '2nd';
            break;
        case 3:
            rankClass = 'third';
            rankText = '3rd';
            break;
        default:
            rankClass = '';
            rankText = `${rank}th`;
    }
    
    // Create the card
    const card = document.createElement('div');
    card.className = `leaderboard-card ${rankClass}`;
    
    // Fetch the student's profile picture
    fetch(`/api/students?idno=${student.student_idno}`)
        .then(response => response.json())
        .then(data => {
            let profilePic = '/static/images/default.png'; // Default profile picture
            
            // If we successfully got student data with a profile picture
            if (data.success && data.students && data.students.length > 0) {
                const studentData = data.students[0];
                if (studentData.profile_picture) {
                    profilePic = `/static/images/${studentData.profile_picture}`;
                }
            }
            
            // Update the card HTML with the profile picture
            card.innerHTML = `
                <div class="rank-badge ${rankClass}">${rankText}</div>
                <img src="${profilePic}" alt="${student.student_name}" class="student-avatar" 
                     onerror="this.src='/static/images/default.png'">
                <div class="student-name">${student.student_name}</div>
                <div class="student-course">${student.course} - Year ${student.year_level}</div>
                <div class="points-badge">${student.total_points} points</div>
                <div class="sitin-badge">${student.sitin_count} sit-ins</div>
            `;
        })
        .catch(error => {
            console.error('Error fetching student profile:', error);
            
            // Fallback to default image if fetch fails
            card.innerHTML = `
                <div class="rank-badge ${rankClass}">${rankText}</div>
                <img src="/static/images/default.png" alt="${student.student_name}" class="student-avatar">
                <div class="student-name">${student.student_name}</div>
                <div class="student-course">${student.course} - Year ${student.year_level}</div>
                <div class="points-badge">${student.total_points} points</div>
                <div class="sitin-badge">${student.sitin_count} sit-ins</div>
            `;
        });
    
    container.appendChild(card);
}

// Student search functionality
document.addEventListener('DOMContentLoaded', function() {
    const studentSearchInput = document.getElementById('studentSearchInput');
    const searchResults = document.getElementById('searchResults');
    const selectedStudentInfo = document.getElementById('selectedStudentInfo');
    const selectedStudentId = document.getElementById('selectedStudentId');
    const selectedStudentName = document.getElementById('selectedStudentName');
    const selectedStudentCourse = document.getElementById('selectedStudentCourse');
    const selectedStudentSessions = document.getElementById('selectedStudentSessions');
    const selectedStudentIdInput = document.getElementById('selectedStudentIdInput');
    const searchStudentModal = document.getElementById('searchStudentModal');
    const sitInForm = document.getElementById('sitInForm');

    if (studentSearchInput) {
        let debounceTimer;

        // Add event listener for student search
        studentSearchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const searchTerm = this.value.trim();
            
            if (searchTerm.length < 2) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }
            
            // Debounce the search to avoid too many requests
            debounceTimer = setTimeout(() => {
                // Show loading indicator
                searchResults.innerHTML = '<div class="searching">Searching...</div>';
                searchResults.style.display = 'block';
                
                // Fetch student data
    fetch(`/search_students?q=${encodeURIComponent(searchTerm)}`)
      .then(response => response.json())
      .then(data => {
          searchResults.innerHTML = '';
                        
                        if (data.success && data.data.length > 0) {
          data.data.forEach(student => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.innerHTML = `
                                    <strong>${student.idno}</strong> - 
                                    ${student.firstname} ${student.lastname}
                                    (${student.course}, Year ${student.year_level})
            `;
                                
                                // Add click event to select student
            resultItem.addEventListener('click', function() {
                                    // Display selected student info
                                    selectedStudentId.textContent = student.idno;
                                    selectedStudentName.textContent = `${student.firstname} ${student.lastname}`;
                                    selectedStudentCourse.textContent = `${student.course} (Year ${student.year_level})`;
                                    selectedStudentSessions.textContent = student.sessions_left;
                                    selectedStudentIdInput.value = student.idno;
                                    
                                    // Show the student info section
                                    selectedStudentInfo.style.display = 'block';
                                    
                                    // Hide search results
                                    searchResults.style.display = 'none';
                                    
                                    // Clear search input
                                    studentSearchInput.value = '';
                                });
                                
            searchResults.appendChild(resultItem);
          });
        } else {
          searchResults.innerHTML = '<div class="no-results">No students found</div>';
        }
                        
                        searchResults.style.display = 'block';
      })
      .catch(error => {
        console.error('Error searching students:', error);
        searchResults.innerHTML = '<div class="error">Error searching students</div>';
        searchResults.style.display = 'block';
      });
            }, 300); // 300ms debounce
        });
        
        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (e.target !== studentSearchInput && e.target !== searchResults) {
    searchResults.style.display = 'none';
            }
        });
        
        // Handle the sit-in form submission
        if (sitInForm) {
            sitInForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const studentId = selectedStudentIdInput.value;
                const labId = document.getElementById('labSelect').value;
    const purpose = document.getElementById('purposeSelect').value;
    
                if (!studentId || !labId || !purpose) {
      Swal.fire('Error', 'Please fill all required fields', 'error');
      return;
    }
    
                // Create a sit-in for the student
    fetch('/admin_create_sitin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id: studentId,
                        lab: labId,
        purpose: purpose
                    }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
                        Swal.fire('Success', 'Student successfully sat in', 'success');
                        
                        // Close the modal
                        const closeModalBtn = searchStudentModal.querySelector('.close-modal');
                        if (closeModalBtn) closeModalBtn.click();
                        
                        // Refresh the current sit-in list if we're on that page
                        if (window.location.hash === '#sit-in') {
          fetchAndDisplayCurrentSitIn();
                        }
                        
                        // Reset the form
                        selectedStudentInfo.style.display = 'none';
                        sitInForm.reset();
      } else {
                        Swal.fire('Error', data.message || 'Failed to sit in student', 'error');
      }
    })
    .catch(error => {
                    console.error('Error creating sit-in:', error);
                    Swal.fire('Error', 'Failed to sit in student', 'error');
                });
            });
        }
    }
});

// Handle Search Student link click
document.addEventListener('DOMContentLoaded', function() {
    const searchStudentLink = document.querySelector('a[data-bs-target="#searchStudentModal"]');
    const searchStudentModal = document.getElementById('searchStudentModal');
    
    if (searchStudentLink && searchStudentModal) {
        searchStudentLink.addEventListener('click', function(e) {
            e.preventDefault();
            searchStudentModal.style.display = 'block';
        });
        
        // Close modal when clicking the X
        const closeBtn = searchStudentModal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                searchStudentModal.style.display = 'none';
                // Reset the form data
                const selectedStudentInfo = document.getElementById('selectedStudentInfo');
                if (selectedStudentInfo) selectedStudentInfo.style.display = 'none';
                
                const sitInForm = document.getElementById('sitInForm');
                if (sitInForm) sitInForm.reset();
            });
        }
        
        // Close modal when clicking outside of it
        window.addEventListener('click', function(e) {
            if (e.target === searchStudentModal) {
                searchStudentModal.style.display = 'none';
            }
        });
    }
});

// Lab Resources Functionality
function fetchLabResources() {
    fetch('/get_lab_resources')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLabResources(data.resources);
            } else {
                console.error('Failed to fetch lab resources:', data.message);
                document.getElementById('resourcesTableBody').innerHTML = `
                    <tr>
                        <td colspan="5" class="error">Error loading resources: ${data.message}</td>
                    </tr>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching lab resources:', error);
            document.getElementById('resourcesTableBody').innerHTML = `
                <tr>
                    <td colspan="5" class="error">Failed to load resources. Please try again later.</td>
                </tr>
            `;
        });
}

function displayLabResources(resources) {
    const resourcesTableBody = document.getElementById('resourcesTableBody');
    
    if (!resources || resources.length === 0) {
        resourcesTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center;">No resources uploaded yet.</td>
            </tr>
        `;
        return;
    }
    
    resourcesTableBody.innerHTML = '';
    
    resources.forEach(resource => {
        const date = new Date(resource.created_at).toLocaleString();
    const row = document.createElement('tr');
        row.setAttribute('data-resource-id', resource.id);
        
        const truncatedContent = resource.content.length > 50 
            ? resource.content.substring(0, 50) + '...' 
            : resource.content;
            
        const truncatedLink = resource.link.length > 40
            ? resource.link.substring(0, 40) + '...'
            : resource.link;
    
    row.innerHTML = `
            <td>${resource.title}</td>
            <td title="${resource.content}">${truncatedContent}</td>
            <td title="${resource.link}">${truncatedLink}</td>
            <td>${date}<br><small>by ${resource.created_by}</small></td>
            <td>
                <div class="resource-actions">
                    <a href="${resource.link}" target="_blank" class="resource-link-btn">
                        <i class="ri-external-link-line"></i> Open
                    </a>
                    <button class="resource-delete-btn" data-resource-id="${resource.id}">
                        <i class="ri-delete-bin-line"></i> Delete
                    </button>
                </div>
        </td>
    `;
    
        resourcesTableBody.appendChild(row);
    });
    
    // Add event listeners to delete buttons
    addResourceDeleteListeners();
}

function addResourceDeleteListeners() {
    document.querySelectorAll('.resource-delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const resourceId = this.getAttribute('data-resource-id');
            deleteLabResource(resourceId);
        });
    });
}

function deleteLabResource(resourceId) {
    Swal.fire({
        title: 'Are you sure?',
        text: "This resource will be permanently deleted.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/delete_lab_resource/${resourceId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire(
                        'Deleted!',
                        'The lab resource has been deleted.',
                        'success'
                    );
                    // No need to refresh manually, socket will handle it
                } else {
                    Swal.fire(
                        'Error!',
                        data.message || 'Failed to delete resource',
                        'error'
                    );
                }
            })
            .catch(error => {
                console.error('Error deleting resource:', error);
                Swal.fire(
                    'Error!',
                    'An unexpected error occurred',
                    'error'
                );
            });
        }
    });
}

// Initialize Lab Resources functionality
document.addEventListener('DOMContentLoaded', function() {
    const resourceUploadForm = document.getElementById('resourceUploadForm');
    const resourceUploadModal = document.getElementById('resourceUploadModal');
    const openResourceModalBtn = document.getElementById('openResourceModalBtn');
    const closeResourceModalBtn = document.querySelector('.resource-upload-modal .resource-modal-close');
    const cancelResourceBtn = document.querySelector('.btn-resource-cancel');
    
    // Open modal when the upload button is clicked
    if (openResourceModalBtn) {
        openResourceModalBtn.addEventListener('click', function() {
            if (resourceUploadModal) {
                resourceUploadModal.style.display = 'block';
                // Focus on the first field
                document.getElementById('resourceTitle').focus();
            }
        });
    }
    
    // Close modal when the close button is clicked
    if (closeResourceModalBtn) {
        closeResourceModalBtn.addEventListener('click', function() {
            if (resourceUploadModal) {
                resourceUploadModal.style.display = 'none';
                // Reset form
                if (resourceUploadForm) resourceUploadForm.reset();
            }
        });
    }
    
    // Close modal when Cancel button is clicked
    if (cancelResourceBtn) {
        cancelResourceBtn.addEventListener('click', function() {
            if (resourceUploadModal) {
                resourceUploadModal.style.display = 'none';
                // Reset form
                if (resourceUploadForm) resourceUploadForm.reset();
            }
        });
    }
    
    // Close modal when clicking outside the content
    window.addEventListener('click', function(event) {
        if (event.target === resourceUploadModal) {
            resourceUploadModal.style.display = 'none';
            // Reset form
            if (resourceUploadForm) resourceUploadForm.reset();
        }
    });
    
    if (resourceUploadForm) {
        resourceUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('resourceTitle').value.trim();
            const content = document.getElementById('resourceContent').value.trim();
            const link = document.getElementById('resourceLink').value.trim();
            
            if (!title || !content || !link) {
        Swal.fire({
                    title: 'Error',
                    text: 'All fields are required',
                    icon: 'error',
                    confirmButtonColor: '#8a2be2'
                });
                return;
            }
            
            // Validate URL format
            try {
                new URL(link);
            } catch (_) {
                Swal.fire({
                    title: 'Invalid URL',
                    text: 'Please enter a valid URL',
                    icon: 'error',
                    confirmButtonColor: '#8a2be2'
                });
                return;
            }
            
            // Show loading state
            const submitBtn = resourceUploadForm.querySelector('.btn-resource-submit');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="ri-loader-4-line"></i> Uploading...';
            
            fetch('/create_lab_resource', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title, content, link })
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                if (data.success) {
                    // Close modal
                    resourceUploadModal.style.display = 'none';
                    // Reset form
                    resourceUploadForm.reset();
                    
                    Swal.fire({
                        title: 'Success!',
                        text: 'Lab resource has been uploaded',
                        icon: 'success',
                        confirmButtonColor: '#8a2be2'
                    });
                    
                    // No need to refresh manually, socket will handle it
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message || 'Failed to upload resource',
                        icon: 'error',
                        confirmButtonColor: '#8a2be2'
                    });
                }
            })
            .catch(error => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                console.error('Error uploading resource:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'An unexpected error occurred',
                    icon: 'error',
                    confirmButtonColor: '#8a2be2'
                });
            });
        });
    }
    
    // Socket.IO listeners for real-time updates
    socket.on('new_lab_resource', function(resource) {
        console.log('New lab resource received:', resource);
        fetchLabResources(); // Refresh the resources list
    });
    
    socket.on('lab_resource_deleted', function(data) {
        console.log('Lab resource deleted:', data);
        fetchLabResources(); // Refresh the resources list
    });
});
    
// Add lab management functionality
let selectedLabId = null;
let selectedLabComputers = [];
let currentScheduleDay = 'Monday';
let selectedScheduleLabId = null;

// Initialization for lab management
function initializeLabManagement() {
    console.log("DEBUG: initializing lab management");
    
    try {
        // Lab selection
        const labButtons = document.querySelectorAll('.lab-button');
        if (!labButtons || labButtons.length === 0) {
            console.error("DEBUG: No lab buttons found");
            return;
        }
        
        console.log(`DEBUG: Found ${labButtons.length} lab buttons`);
        
        labButtons.forEach(button => {
            button.addEventListener('click', function() {
                const labId = parseInt(this.dataset.labId);
                console.log(`DEBUG: Selected lab ID: ${labId}`);
                selectLab(labId);
                
                // Update active button
                document.querySelectorAll('.lab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
            });
        });
        
        // Setup tab management
        const computerManagementTab = document.getElementById('computer-management-tab');
        const scheduleManagementTab = document.getElementById('schedule-management-tab');
        const computerManagementSection = document.getElementById('computer-management-section');
        const scheduleManagementSection = document.getElementById('schedule-management-section');
        
        console.log("DEBUG: Setting up tab event listeners");
        
        if (computerManagementTab && scheduleManagementTab && computerManagementSection && scheduleManagementSection) {
            computerManagementTab.addEventListener('click', function() {
                computerManagementSection.style.display = 'block';
                scheduleManagementSection.style.display = 'none';
                computerManagementTab.classList.add('active');
                scheduleManagementTab.classList.remove('active');
            });
            
            scheduleManagementTab.addEventListener('click', function() {
                computerManagementSection.style.display = 'none';
                scheduleManagementSection.style.display = 'block';
                computerManagementTab.classList.remove('active');
                scheduleManagementTab.classList.add('active');
                
                // Initialize schedule management if not already done
                if (!scheduleManagementInitialized) {
                    initializeScheduleManagement();
                }
            });
        } else {
            console.error("DEBUG: One or more tab elements not found");
        }
        
        // Computer modal setup
        const closeComputerModal = document.getElementById('close-computer-modal');
        if (closeComputerModal) {
            closeComputerModal.addEventListener('click', function() {
                document.getElementById('computer-modal').style.display = 'none';
            });
        }
        
        // Student assignment modal setup
        const closeStudentModal = document.getElementById('close-student-modal');
        const cancelAssignBtn = document.getElementById('cancel-assign-btn');
        const assignStudentBtn = document.getElementById('assign-student-btn');
        
        if (closeStudentModal) {
            closeStudentModal.addEventListener('click', function() {
                document.getElementById('student-assignment-modal').style.display = 'none';
            });
        }
        
        if (cancelAssignBtn) {
            cancelAssignBtn.addEventListener('click', function() {
                document.getElementById('student-assignment-modal').style.display = 'none';
            });
        }
        
        if (assignStudentBtn) {
            assignStudentBtn.addEventListener('click', assignStudentToComputer);
        }
        
        // Student search
        const studentSearchInput = document.getElementById('student-search-input');
        if (studentSearchInput) {
            studentSearchInput.addEventListener('input', debounce(searchStudents, 300));
        }
        
        console.log("DEBUG: Lab management initialization complete");
        
        // Auto-select the first lab if available
        if (labButtons.length > 0) {
            console.log("DEBUG: Auto-selecting first lab");
            labButtons[0].click();
        }
    } catch (e) {
        console.error("DEBUG: Error in lab management initialization:", e);
    }
}

function selectLab(labId) {
    console.log(`DEBUG: Selecting lab ID ${labId}`);
    selectedLabId = labId;
    const loadingMessage = `<div class="loading-message">Loading computers for Lab ${labId}...</div>`;
    const computerGrid = document.getElementById('computer-grid');
    
    if (!computerGrid) {
        console.error("DEBUG: computer-grid element not found");
        return;
    }
    
    computerGrid.innerHTML = loadingMessage;
    
    // Fetch computers for this lab
    fetch(`/api/lab_computers/${labId}`)
        .then(response => response.json())
        .then(data => {
            console.log(`DEBUG: Received data for lab ${labId}:`, data);
            if (data.success) {
                selectedLabComputers = data.computers;
                renderLabComputers(data);
            } else {
                computerGrid.innerHTML = 
                    `<div class="loading-message">Error loading computers: ${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('DEBUG: Error fetching lab computers:', error);
            computerGrid.innerHTML = 
                `<div class="loading-message">Error loading computers. Please try again.</div>`;
        });
}

function renderLabComputers(data) {
    console.log(`DEBUG: Rendering computers for lab ${data.lab_name}`);
    const computerGrid = document.getElementById('computer-grid');
    const labName = document.getElementById('selected-lab-name');
    
    if (!computerGrid || !labName) {
        console.error("DEBUG: Required elements for rendering computers not found");
        return;
    }
    
    // Update lab name
    labName.textContent = data.lab_name;
    
    // Count status
    let availableCount = 0;
    let inUseCount = 0;
    let unavailableCount = 0;
    
    // Generate computer grid
    let gridHtml = '';
    
    data.computers.forEach(computer => {
        const status = computer.status.toLowerCase().replace(' ', '-');
        let statusClass = '';
        let statusIcon = '';
        
        // Set appropriate status class and icon
        switch(status) {
            case 'available':
                statusClass = 'available';
                statusIcon = 'ri-computer-line';
                availableCount++;
                break;
            case 'in-use':
                statusClass = 'in-use';
                statusIcon = 'ri-user-line';
                inUseCount++;
                break;
            case 'unavailable':
                statusClass = 'unavailable';
                statusIcon = 'ri-error-warning-line';
                unavailableCount++;
                break;
            default:
                statusClass = '';
                statusIcon = 'ri-computer-line';
        }
        
        gridHtml += `
            <div class="computer-item ${statusClass}" data-id="${computer.id}" data-number="${computer.computer_number}">
                <i class="${statusIcon}"></i>
                <div class="computer-number">PC ${computer.computer_number}</div>
                <div class="computer-status">${computer.status}</div>
            </div>
        `;
    });
    
    computerGrid.innerHTML = gridHtml;
    
    // Update stat counters
    const availableElement = document.getElementById('available-count');
    const inUseElement = document.getElementById('in-use-count');
    const unavailableElement = document.getElementById('unavailable-count');
    
    if (availableElement) availableElement.textContent = availableCount;
    if (inUseElement) inUseElement.textContent = inUseCount;
    if (unavailableElement) unavailableElement.textContent = unavailableCount;
    
    // Add click event to computers
    document.querySelectorAll('.computer-item').forEach(item => {
        item.addEventListener('click', function() {
            const computerId = parseInt(this.dataset.id);
            const computerNumber = parseInt(this.dataset.number);
            showComputerModal(computerId, computerNumber);
        });
    });
    
    console.log(`DEBUG: Rendered ${data.computers.length} computers`);
}

function showComputerModal(computerId, computerNumber) {
    const modal = document.getElementById('computer-modal');
    const title = document.getElementById('computer-modal-title');
    const content = document.getElementById('computer-modal-content');
    const actions = document.getElementById('computer-modal-actions');
    
    // Find computer details
    const computer = selectedLabComputers.find(c => c.id === computerId);
    
    if (!computer) {
        console.error('Computer not found:', computerId);
        return;
    }
    
    // Set title
    title.textContent = `Computer ${computerNumber}`;
    
    // Set content based on status
    if (computer.status === 'In Use') {
        // Show student info
        content.innerHTML = `
            <div class="student-info">
                <p><strong>Status:</strong> <span class="status-badge in-use">${computer.status}</span></p>
                <p><strong>Student ID:</strong> ${computer.student_idno || 'N/A'}</p>
                <p><strong>Student Name:</strong> ${computer.firstname ? `${computer.firstname} ${computer.lastname}` : 'N/A'}</p>
                <p><strong>Time:</strong> ${formatTimestamp(computer.timestamp)}</p>
            </div>
        `;
        
        // Set actions
        actions.innerHTML = `
            <button class="btn-action" onclick="setComputerStatus(${computerId}, 'Available')">
                <i class="ri-checkbox-circle-line"></i> Set Available
            </button>
            <button class="btn-action btn-delete" onclick="setComputerStatus(${computerId}, 'Unavailable')">
                <i class="ri-close-circle-line"></i> Set Unavailable
            </button>
        `;
    } else if (computer.status === 'Available') {
        // Show available info
        content.innerHTML = `
            <div class="student-info">
                <p><strong>Status:</strong> <span class="status-badge available">${computer.status}</span></p>
                <p>This computer is available for use.</p>
            </div>
        `;
        
        // Set actions
        actions.innerHTML = `
            <button class="btn-action" onclick="showStudentAssignmentModal(${computerId})">
                <i class="ri-user-add-line"></i> Assign Student
            </button>
            <button class="btn-action btn-delete" onclick="setComputerStatus(${computerId}, 'Unavailable')">
                <i class="ri-close-circle-line"></i> Set Unavailable
            </button>
        `;
    } else if (computer.status === 'Unavailable') {
        // Show unavailable info
        content.innerHTML = `
            <div class="student-info">
                <p><strong>Status:</strong> <span class="status-badge unavailable">${computer.status}</span></p>
                <p>This computer is marked as unavailable.</p>
            </div>
        `;
        
        // Set actions
        actions.innerHTML = `
            <button class="btn-action" onclick="setComputerStatus(${computerId}, 'Available')">
                <i class="ri-checkbox-circle-line"></i> Set Available
            </button>
        `;
    }
    
    // Show modal
    modal.style.display = 'block';
}

function setComputerStatus(computerId, status) {
    fetch(`/api/computer_status/${computerId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: status,
            student_idno: null // Clear student if setting to available or unavailable
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            document.getElementById('computer-modal').style.display = 'none';
            
            // Refresh computers
            selectLab(selectedLabId);
            
            // Show success message
            showAlert('success', data.message);
        } else {
            showAlert('error', data.message || 'Failed to update computer status');
        }
    })
    .catch(error => {
        console.error('Error updating computer status:', error);
        showAlert('error', 'Failed to update computer status. Please try again.');
    });
}

function showStudentAssignmentModal(computerId) {
    // Store the computer ID for later use
    document.getElementById('student-assignment-modal').dataset.computerId = computerId;
    
    // Reset the search and selected student
    document.getElementById('student-search-input').value = '';
    document.getElementById('student-search-results').innerHTML = '';
    document.getElementById('selected-student-info').style.display = 'none';
    document.getElementById('assign-student-btn').disabled = true;
    
    // Close computer modal
    document.getElementById('computer-modal').style.display = 'none';
    
    // Show student assignment modal
    document.getElementById('student-assignment-modal').style.display = 'block';
}

function searchStudents() {
    const searchTerm = document.getElementById('student-search-input').value.trim();
    const resultsContainer = document.getElementById('student-search-results');
    
    if (searchTerm.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    resultsContainer.innerHTML = '<div class="searching">Searching...</div>';
    
    fetch(`/search_students?q=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data && data.data.length > 0) {
                let html = '';
                data.data.forEach(student => {
                    html += `
                        <div class="search-result-item" data-id="${student.idno}" data-name="${student.firstname} ${student.lastname}" data-sessions="${student.sessions_left}">
                            ${student.idno} - ${student.firstname} ${student.lastname} (${student.sessions_left} sessions)
                        </div>
                    `;
                });
                resultsContainer.innerHTML = html;
                
                // Add click event to results
                document.querySelectorAll('.search-result-item').forEach(item => {
                    item.addEventListener('click', function() {
                        selectStudent(this.dataset.id, this.dataset.name, this.dataset.sessions);
                    });
                });
            } else {
                resultsContainer.innerHTML = '<div class="no-results">No students found</div>';
            }
        })
        .catch(error => {
            console.error('Error searching students:', error);
            resultsContainer.innerHTML = '<div class="error">Error searching students</div>';
        });
}

function selectStudent(id, name, sessions) {
    // Store the selected student data
    const selectedStudentInfo = document.getElementById('selected-student-info');
    selectedStudentInfo.dataset.studentId = id;
    
    // Update display
    document.getElementById('student-id').textContent = id;
    document.getElementById('student-name').textContent = name;
    document.getElementById('student-sessions').textContent = sessions;
    
    // Show selected student info
    selectedStudentInfo.style.display = 'block';
    
    // Clear search results
    document.getElementById('student-search-results').innerHTML = '';
    
    // Enable assign button if sessions > 0
    document.getElementById('assign-student-btn').disabled = parseInt(sessions) <= 0;
}

function assignStudentToComputer() {
    const computerId = parseInt(document.getElementById('student-assignment-modal').dataset.computerId);
    const studentId = document.getElementById('selected-student-info').dataset.studentId;
    
    if (!computerId || !studentId) {
        showAlert('error', 'Missing computer or student information');
        return;
    }
    
    fetch(`/api/computer_status/${computerId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: 'In Use',
            student_idno: studentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            document.getElementById('student-assignment-modal').style.display = 'none';
            
            // Refresh computers
            selectLab(selectedLabId);
            
            // Show success message
            showAlert('success', 'Student assigned successfully');
        } else {
            showAlert('error', data.message || 'Failed to assign student');
        }
    })
    .catch(error => {
        console.error('Error assigning student:', error);
        showAlert('error', 'Failed to assign student. Please try again.');
    });
}

// Lab Schedule Management
function initializeScheduleManagement() {
    console.log("DEBUG: Initializing schedule management");
    
    try {
        // Lab selection for schedules
        const scheduleLabButtons = document.querySelectorAll('.schedule-lab-button');
        if (!scheduleLabButtons || scheduleLabButtons.length === 0) {
            console.error("DEBUG: No schedule lab buttons found");
            return;
        }
        
        console.log(`DEBUG: Found ${scheduleLabButtons.length} schedule lab buttons`);
        
        scheduleLabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const labId = parseInt(this.dataset.labId);
                console.log(`DEBUG: Selected schedule lab ID: ${labId}`);
                selectedScheduleLabId = labId;
                
                // Update active button
                document.querySelectorAll('.schedule-lab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                
                // Load schedules for selected lab and day
                loadLabSchedules(labId, currentScheduleDay);
            });
        });
        
        // Day selection
        const dayButtons = document.querySelectorAll('.day-button');
        if (!dayButtons || dayButtons.length === 0) {
            console.error("DEBUG: No day buttons found");
            return;
        }
        
        console.log(`DEBUG: Found ${dayButtons.length} day buttons`);
        
        dayButtons.forEach(button => {
            button.addEventListener('click', function() {
                const day = this.dataset.day;
                console.log(`DEBUG: Selected day: ${day}`);
                currentScheduleDay = day;
                
                // Update active button
                document.querySelectorAll('.day-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                
                // Load schedules if lab is selected
                if (selectedScheduleLabId) {
                    loadLabSchedules(selectedScheduleLabId, day);
                }
            });
        });
        
        // Add schedule button
        const addScheduleBtn = document.getElementById('add-schedule-btn');
        if (addScheduleBtn) {
            addScheduleBtn.addEventListener('click', function() {
                if (!selectedScheduleLabId) {
                    showAlert('error', 'Please select a laboratory first');
                    return;
                }
                
                showScheduleModal();
            });
        } else {
            console.warn("DEBUG: add-schedule-btn element not found");
        }
        
        // Import schedules button
        const importSchedulesBtn = document.getElementById('import-schedules-btn');
        if (importSchedulesBtn) {
            importSchedulesBtn.addEventListener('click', function() {
                console.log("DEBUG: Import schedules button clicked");
                importDefaultSchedules();
            });
        } else {
            console.warn("DEBUG: import-schedules-btn element not found");
        }
        
        // Schedule form submit
        const scheduleForm = document.getElementById('schedule-form');
        if (scheduleForm) {
            scheduleForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveSchedule();
            });
        } else {
            console.warn("DEBUG: schedule-form element not found");
        }
        
        // Cancel schedule button
        const cancelScheduleBtn = document.getElementById('cancel-schedule-btn');
        if (cancelScheduleBtn) {
            cancelScheduleBtn.addEventListener('click', function() {
                document.getElementById('schedule-modal').style.display = 'none';
            });
        } else {
            console.warn("DEBUG: cancel-schedule-btn element not found");
        }
        
        // Close schedule modal
        const closeScheduleModal = document.getElementById('close-schedule-modal');
        if (closeScheduleModal) {
            closeScheduleModal.addEventListener('click', function() {
                document.getElementById('schedule-modal').style.display = 'none';
            });
        } else {
            console.warn("DEBUG: close-schedule-modal element not found");
        }
        
        // Show/hide fields based on status selection
        const scheduleStatus = document.getElementById('schedule-status');
        if (scheduleStatus) {
            scheduleStatus.addEventListener('change', function() {
                const status = this.value;
                console.log(`DEBUG: Schedule status changed to ${status}`);
                
                const subjectFields = document.getElementById('subject-fields');
                const unavailableReasonField = document.getElementById('unavailable-reason-field');
                
                if (status === 'Reserved') {
                    if (subjectFields) subjectFields.style.display = 'block';
                    if (unavailableReasonField) unavailableReasonField.style.display = 'none';
                } else if (status === 'Unavailable') {
                    if (subjectFields) subjectFields.style.display = 'none';
                    if (unavailableReasonField) unavailableReasonField.style.display = 'block';
                } else {
                    if (subjectFields) subjectFields.style.display = 'none';
                    if (unavailableReasonField) unavailableReasonField.style.display = 'none';
                }
            });
        } else {
            console.warn("DEBUG: schedule-status element not found");
        }
        
        // Set the initialized flag
        scheduleManagementInitialized = true;
        
        console.log("DEBUG: Schedule management initialization complete");
        
        // Auto-select the first lab and day if available
        if (scheduleLabButtons.length > 0) {
            console.log("DEBUG: Auto-selecting first lab button");
            scheduleLabButtons[0].click();
        } else {
            console.warn("DEBUG: No lab buttons available to auto-select");
        }
        
        // Make sure a day is selected
        const activeDay = document.querySelector('.day-button.active');
        if (!activeDay && dayButtons.length > 0) {
            console.log("DEBUG: Auto-selecting first day button");
            dayButtons[0].click();
        }
    } catch (e) {
        console.error("DEBUG: Error in schedule management initialization:", e);
        showAlert('error', 'Error initializing schedule management. Please try again.');
        scheduleManagementInitialized = false;
    }
}

function loadLabSchedules(labId, day) {
    if (!labId) {
        console.error("DEBUG: No lab ID provided to loadLabSchedules");
        return;
    }
    
    if (!day) {
        console.error("DEBUG: No day provided to loadLabSchedules");
        return;
    }
    
    const tableBody = document.getElementById('schedule-table-body');
    if (!tableBody) {
        console.error("DEBUG: schedule-table-body element not found");
        return;
    }
    
    console.log(`DEBUG: Loading schedules for lab ${labId} on ${day}`);
    tableBody.innerHTML = '<tr><td colspan="4" class="loading-message">Loading schedules...</td></tr>';
    
    fetch(`/api/lab_schedules/${labId}?day=${day}`)
        .then(response => {
            console.log(`DEBUG: API response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("DEBUG: Received schedule data:", data);
            
            if (data.success) {
                // Get the schedules from the response
                const schedules = data.schedules || [];
                
                // If we have schedules, render them
                if (schedules.length > 0) {
                    renderSchedules(schedules);
                } else {
                    // If no schedules found for this day, show a message
                    console.log(`DEBUG: No schedules found for lab ${labId} on ${day}`);
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="4" class="no-schedules-message">
                                No schedules found for this day. 
                                <button onclick="showScheduleModal()" class="quick-add-btn">
                                    <i class="ri-add-line"></i> Add Schedule
                                </button>
                            </td>
                        </tr>`;
                }
            } else {
                console.error(`DEBUG: Failed to load schedules: ${data.message || 'Unknown error'}`);
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="error-message">
                            Error loading schedules: ${data.message || 'Unknown error'}
                            <button onclick="loadLabSchedules(${labId}, '${day}')" class="retry-btn">
                                <i class="ri-refresh-line"></i> Retry
                            </button>
                        </td>
                    </tr>`;
                showAlert('error', 'Failed to load schedule details');
            }
        })
        .catch(error => {
            console.error('DEBUG: Error loading schedules:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="error-message">
                        Error loading schedules: ${error.message}
                        <button onclick="loadLabSchedules(${labId}, '${day}')" class="retry-btn">
                            <i class="ri-refresh-line"></i> Retry
                        </button>
                    </td>
                </tr>`;
            showAlert('error', 'Failed to load schedule details');
        });
}

function renderSchedules(schedules) {
    const tableBody = document.getElementById('schedule-table-body');
    
    if (!schedules || schedules.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="loading-message">No schedules found for this day</td></tr>';
        return;
    }
    
    // Sort schedules by start time
    schedules.sort((a, b) => {
        return a.start_time.localeCompare(b.start_time);
    });
    
    let html = '';
    schedules.forEach(schedule => {
        // Format the time slot
        const timeSlot = `${formatTime(schedule.start_time)} - ${formatTime(schedule.end_time)}`;
        
        // Format subject info
        let subjectInfo = 'N/A';
        if (schedule.status === 'Reserved' && schedule.subject_code) {
            subjectInfo = `${schedule.subject_code} - ${schedule.subject_name}`;
        } else if (schedule.status === 'Unavailable' && schedule.reason) {
            subjectInfo = `Reason: ${schedule.reason}`;
        }
        
        // Determine status badge class
        let statusClass = '';
        switch(schedule.status) {
            case 'Available':
                statusClass = 'available';
                break;
            case 'Reserved':
                statusClass = 'reserved';
                break;
            case 'Unavailable':
                statusClass = 'unavailable';
                break;
        }
        
        html += `
            <tr data-id="${schedule.id}">
                <td>${timeSlot}</td>
                <td>${subjectInfo}</td>
                <td><span class="status-badge ${statusClass.toLowerCase()}">${schedule.status}</span></td>
                <td class="schedule-actions">
                    <button class="action-btn edit" onclick="editSchedule(${schedule.id})">
                        <i class="ri-edit-line"></i>
                    </button>
                    <button class="action-btn delete" onclick="deleteSchedule(${schedule.id})">
                        <i class="ri-delete-bin-line"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

function saveSchedule() {
    // Get form data
    const scheduleId = document.getElementById('schedule-id').value;
    const labId = document.getElementById('schedule-lab-id').value || selectedScheduleLabId;
    const dayOfWeek = document.getElementById('schedule-day').value || currentScheduleDay;
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;
    const status = document.getElementById('schedule-status').value;
    
    // Validate required fields
    if (!labId) {
        showAlert('error', 'No laboratory selected');
        return;
    }
    
    if (!dayOfWeek) {
        showAlert('error', 'No day selected');
        return;
    }
    
    if (!startTime || !endTime) {
        showAlert('error', 'Start time and end time are required');
        return;
    }
    
    if (!status) {
        showAlert('error', 'Status is required');
        return;
    }
    
    // Get subject fields based on status
    let subjectCode = null;
    let subjectName = null;
    let reason = null;
    
    if (status === 'Reserved') {
        subjectCode = document.getElementById('subject-code').value;
        subjectName = document.getElementById('subject-name').value;
        
        if (!subjectCode || !subjectName) {
            showAlert('error', 'Subject code and name are required for reserved status');
            return;
        }
    } else if (status === 'Unavailable') {
        reason = document.getElementById('unavailable-reason').value;
        
        if (!reason) {
            showAlert('error', 'Reason is required for unavailable status');
            return;
        }
    }
    
    // Create schedule data
    const scheduleData = {
        lab_id: parseInt(labId),
        day_of_week: dayOfWeek,
        start_time: startTime,
        end_time: endTime,
        status: status,
        subject_code: subjectCode,
        subject_name: subjectName,
        reason: reason
    };
    
    // Add schedule ID if editing existing schedule
    if (scheduleId) {
        scheduleData.schedule_id = parseInt(scheduleId);
    }
    
    console.log('Saving schedule with data:', scheduleData);
    
    // Show loading state
    const submitBtn = document.querySelector('#schedule-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
    }
    
    // Send request to save schedule
    fetch('/api/lab_schedules', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(scheduleData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Hide modal
            document.getElementById('schedule-modal').style.display = 'none';
            
            // Refresh schedules
            loadLabSchedules(selectedScheduleLabId, currentScheduleDay);
            
            // Show success message
            showAlert('success', data.message || 'Schedule saved successfully');
        } else {
            showAlert('error', data.message || 'Failed to save schedule');
        }
    })
    .catch(error => {
        console.error('Error saving schedule:', error);
        showAlert('error', 'Failed to save schedule. Please try again.');
    })
    .finally(() => {
        // Reset loading state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Schedule';
        }
    });
}

function editSchedule(scheduleId) {
    console.log(`DEBUG: Editing schedule ID: ${scheduleId}`);
    if (!scheduleId) {
        showAlert('error', 'Invalid schedule ID');
        return;
    }
    
    // Show schedule modal with the schedule ID
    showScheduleModal(scheduleId);
}

function deleteSchedule(scheduleId) {
    console.log(`DEBUG: Deleting schedule ID: ${scheduleId}`);
    if (!scheduleId) {
        showAlert('error', 'Invalid schedule ID');
        return;
    }
    
    // Confirm deletion
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Delete Schedule',
            text: 'Are you sure you want to delete this schedule?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it'
        }).then((result) => {
            if (result.isConfirmed) {
                performScheduleDeletion(scheduleId);
            }
        });
    } else {
        // Fallback to regular confirm dialog
        if (confirm('Are you sure you want to delete this schedule?')) {
            performScheduleDeletion(scheduleId);
        }
    }
}

function performScheduleDeletion(scheduleId) {
    fetch(`/api/lab_schedules/${scheduleId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Refresh schedules
            loadLabSchedules(selectedScheduleLabId, currentScheduleDay);
            
            // Show success message
            showAlert('success', data.message || 'Schedule deleted successfully');
        } else {
            showAlert('error', data.message || 'Failed to delete schedule');
        }
    })
    .catch(error => {
        console.error('Error deleting schedule:', error);
        showAlert('error', 'Failed to delete schedule. Please try again.');
    });
}

function importDefaultSchedules() {
    console.log("DEBUG: Importing default schedules");
    
    // Disable the button while importing
    const importBtn = document.getElementById('import-schedules-btn');
    if (importBtn) {
        importBtn.disabled = true;
        importBtn.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Importing...';
    }
    
    fetch('/import_default_schedules', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({}) // Empty body since we're just triggering the import
    })
    .then(response => {
        console.log(`DEBUG: Import response status: ${response.status}`);
        return response.json().catch(error => {
            // Handle case where the response isn't valid JSON
            console.error("DEBUG: Error parsing JSON response:", error);
            return { success: false, message: "Failed to parse server response" };
        });
    })
    .then(data => {
        console.log("DEBUG: Import response data:", data);
        if (data.success) {
            // Refresh schedules if lab is selected
            if (selectedScheduleLabId) {
                loadLabSchedules(selectedScheduleLabId, currentScheduleDay);
            }
            
            // Show success message
            showAlert('success', data.message || 'Default schedules imported successfully');
        } else {
            showAlert('error', data.message || 'Failed to import default schedules. Schedules may already exist or another error occurred.');
        }
    })
    .catch(error => {
        console.error("DEBUG: Error importing default schedules:", error);
        showAlert('error', 'Failed to import default schedules. Please try again.');
    })
    .finally(() => {
        // Re-enable the button
        if (importBtn) {
            importBtn.disabled = false;
            importBtn.innerHTML = '<i class="ri-download-line"></i> Import Default Schedules';
        }
    });
}
// Helper functions
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function formatTime(timeString) {
    if (!timeString) return 'N/A';
    
    // Convert 24-hour time to 12-hour format
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const period = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    
    return `${hour12}:${minutes} ${period}`;
}

function showAlert(type, message) {
    console.log(`DEBUG: Showing alert - Type: ${type}, Message: ${message}`);
    
    // Check if SweetAlert is available
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: type,
            title: type.charAt(0).toUpperCase() + type.slice(1),
            text: message,
            timer: 3000,
            timerProgressBar: true
        });
    } else {
        // Fallback to regular alert
        alert(`${type.toUpperCase()}: ${message}`);
    }
}

function debounce(func, delay) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

// Initialize lab management when the management tab is shown
document.addEventListener('DOMContentLoaded', function() {
    console.log("DEBUG: Document loaded, setting up management initialization");
    
    // Initialize when management page is shown
    const managementLink = document.querySelector('[data-page="management"]');
    if (managementLink) {
        console.log("DEBUG: Found management link, adding click listener");
        managementLink.addEventListener('click', function() {
            console.log("DEBUG: Management link clicked, initializing lab management");
            // Give time for the page to be displayed before initializing
            setTimeout(() => {
                try {
                    initializeLabManagement();
                } catch (e) {
                    console.error("DEBUG: Error initializing lab management:", e);
                }
            }, 300);
        });
        
        // Check if we're already on the management page from hash in URL
        if (window.location.hash === '#management') {
            console.log("DEBUG: Starting on management page, initializing lab management");
            setTimeout(() => {
                try {
                    // First ensure the page is shown
                    const managementPage = document.getElementById('management');
                    if (managementPage) {
                        managementPage.style.display = 'block';
                        // Then initialize
                        initializeLabManagement();
                    }
                } catch (e) {
                    console.error("DEBUG: Error initializing lab management from hash:", e);
                }
            }, 500);
        }
    } else {
        console.error("DEBUG: Management link not found");
    }
});

// Document ready event
document.addEventListener('DOMContentLoaded', function() {
    console.log("DEBUG: Document ready event fired");
    
    // Setup all event listeners
    setupEventListeners();
    
    // Load page from hash URL if present
    loadPageFromHash();
    
    // Get user count initially
    updateUserCount();
    
    // Set up search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            fetchReservations(this.value);
        }, 300));
    }
    
    // Get leaderboard data
    fetchLeaderboard();
    
    // Initialize WebSocket
    initializeSocket();
    
    // Check if we need to initialize the management page based on hash
    const hash = window.location.hash;
    if (hash === '#management') {
        console.log("DEBUG: Hash points to management page, initializing");
        setTimeout(() => {
            try {
                initializeManagementPage();
            } catch (e) {
                console.error("DEBUG: Error initializing management page:", e);
            }
        }, 300);
    }
});

// Setup event listeners for the entire dashboard
function setupEventListeners() {
    console.log("DEBUG: Setting up event listeners");

    // Management tab event listeners
    const managementLink = document.querySelector('[data-page="management"]');
    if (managementLink) {
        managementLink.addEventListener('click', function() {
            console.log("DEBUG: Management link clicked");
            setTimeout(() => {
                initializeManagementPage();
            }, 300);
        });
    }

    // Lab management tab switching
    const computerManagementTab = document.getElementById('computer-management-tab');
    const scheduleManagementTab = document.getElementById('schedule-management-tab');
    
    if (computerManagementTab && scheduleManagementTab) {
        computerManagementTab.addEventListener('click', function() {
            console.log("DEBUG: Switched to Computer Lab Management tab");
            document.getElementById('computer-management-section').style.display = 'block';
            document.getElementById('schedule-management-section').style.display = 'none';
            computerManagementTab.classList.add('active');
            scheduleManagementTab.classList.remove('active');
        });
        
        scheduleManagementTab.addEventListener('click', function() {
            console.log("DEBUG: Switched to Lab Schedule Management tab");
            document.getElementById('computer-management-section').style.display = 'none';
            document.getElementById('schedule-management-section').style.display = 'block';
            computerManagementTab.classList.remove('active');
            scheduleManagementTab.classList.add('active');
            
            // Initialize schedule management if not already done
            if (!scheduleManagementInitialized) {
                initializeScheduleManagement();
            }
        });
    }
}

// Initialize management page components
function initializeManagementPage() {
    console.log("DEBUG: Initializing management page");
    
    // Initialize lab management
    try {
        initializeLabManagement();
    } catch (e) {
        console.error("DEBUG: Error initializing lab management:", e);
    }
    
    // Initialize schedule management (but don't display it yet)
    try {
        initializeScheduleManagement();
    } catch (e) {
        console.error("DEBUG: Error initializing schedule management:", e);
    }
}

// Track if schedule management has been initialized
let scheduleManagementInitialized = false;


