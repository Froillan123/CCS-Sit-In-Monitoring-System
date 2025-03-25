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
                <td>${reservation.status}</td>
                <td>
                    <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
                </td>
            `;
            
            tableBody.prepend(newRow);
        }
    });


   // Listen for reservation updates (e.g., logout time)
   socket.on('reservation_updated', function (data) {
        // Update current sit-in table
        const currentReservationRow = document.querySelector(`#reservations-table tbody tr[data-reservation-id="${data.reservation_id}"]`);
        if (currentReservationRow) {
            currentReservationRow.remove(); // Remove from current sit-in table
        }
        
        // Update records table
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
                    Swal.fire('Success!', data.message, 'success');
                    // Tables will be updated via socket events
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
            if (data.success) {
                const tableBody = document.querySelector('#reservations-table tbody');
                tableBody.innerHTML = '';

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
                        <td>${reservation.status}</td>
                        <td>
                            <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                console.error('Failed to fetch current sit-ins:', data.message);
                Swal.fire('Error', 'Failed to load current sit-ins', 'error');
            }
        })
        .catch(error => {
            console.error('Error fetching current sit-ins:', error);
            Swal.fire('Error', 'Failed to load current sit-ins', 'error');
        });
}

function fetchAndDisplaySitInRecords() {
    fetch('/get_sitin_records')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tableBody = document.querySelector('#records-table tbody');
                tableBody.innerHTML = '';

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
                        <td>${reservation.logout_time || 'N/A'}</td>
                        <td>Session ${reservation.session_number}</td>
                        <td>${reservation.status}</td>
                        <td>${reservation.feedback_submitted ? 'Submitted' : 'Not Submitted'}</td>
                    `;
                    tableBody.appendChild(row);
                });
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


socket.on('update_session_count', function (data) {
    if (data.student_idno === studentIdno) {
      const sessionsLeftElement = document.getElementById('sessions-left');
      if (sessionsLeftElement) {
        sessionsLeftElement.textContent = data.sessions_left;
      }
    }
  });


document.addEventListener('DOMContentLoaded', function() {
    // Initialize search student modal
    initSearchStudentModal();
    
    // Initialize other modals
    initSearchModal();
    initEditModal();
});
  
function initSearchStudentModal() {
    const modal = document.getElementById('searchStudentModal');
    const searchInput = document.getElementById('studentSearchInput');
    const searchResults = document.getElementById('searchResults');
    const selectedStudentInfo = document.getElementById('selectedStudentInfo');
    const sitInForm = document.getElementById('sitInForm');
    const closeBtn = modal.querySelector('.close-modal'); // Get close button specific to this modal
    
    // Open modal when search student link is clicked
    document.querySelector('[data-bs-target="#searchStudentModal"]').addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'block';
        document.body.classList.add('modal-open');
        searchInput.focus();
    });
    
    // Close modal when close button is clicked
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        document.body.classList.remove('modal-open');
        resetSearchModal();
    });
    
    // Close when clicking outside modal
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
            resetSearchModal();
        }
    });
    
    // Prevent clicks inside modal content from closing the modal
    modal.querySelector('.modal-content').addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // Search as you type with debounce
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const searchTerm = this.value.trim();
            if (searchTerm.length >= 2) {
                searchStudents(searchTerm);
            } else {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
            }
        }, 300);
    });
    
    // Handle form submission
    sitInForm.addEventListener('submit', function(e) {
        e.preventDefault();
        createSitInReservation();
    });
}
  


function initSearchModal() {
    const modal = document.getElementById('searchModal');
    const closeBtn = modal.querySelector('.close-modal'); // Get close button specific to this modal

}

// Close modal when close button is clicked
closeBtn.addEventListener('click', function() {
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
});

    // Close when clicking outside modal
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    });

        // Prevent clicks inside modal content from closing the modal
        modal.querySelector('.modal-content').addEventListener('click', function(e) {
            e.stopPropagation();
        });
        

        function initEditModal() {
            const modal = document.getElementById('editModal');
            const closeBtn = modal.querySelector('.close-modal'); // Get close button specific to this modal
            
            // Close modal when close button is clicked
            closeBtn.addEventListener('click', function() {
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
            });
            
            // Close when clicking outside modal
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                    document.body.classList.remove('modal-open');
                }
            });
            
            // Prevent clicks inside modal content from closing the modal
            modal.querySelector('.modal-content').addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }

        

  function searchStudents(searchTerm) {
    const searchResults = document.getElementById('searchResults');
    
    fetch(`/search_students?q=${encodeURIComponent(searchTerm)}`)
      .then(response => response.json())
      .then(data => {
        if (data.success && data.data.length > 0) {
          searchResults.innerHTML = '';
          data.data.forEach(student => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.innerHTML = `
              <p><strong>${student.idno}</strong> - ${student.lastname}, ${student.firstname}</p>
              <p>${student.course} - Year ${student.year_level}</p>
            `;
            resultItem.addEventListener('click', function() {
              selectStudent(student);
            });
            searchResults.appendChild(resultItem);
          });
          searchResults.style.display = 'block';
        } else {
          searchResults.innerHTML = '<div class="no-results">No students found</div>';
          searchResults.style.display = 'block';
        }
      })
      .catch(error => {
        console.error('Error searching students:', error);
        searchResults.innerHTML = '<div class="error">Error searching students</div>';
        searchResults.style.display = 'block';
      });
  }
  
  function selectStudent(student) {
    const selectedStudentInfo = document.getElementById('selectedStudentInfo');
    const searchResults = document.getElementById('searchResults');
    
    // Display selected student info
    document.getElementById('selectedStudentId').textContent = student.idno;
    document.getElementById('selectedStudentName').textContent = `${student.lastname}, ${student.firstname}`;
    document.getElementById('selectedStudentCourse').textContent = `${student.course} - Year ${student.year_level}`;
    document.getElementById('selectedStudentSessions').textContent = student.sessions_left;
    
    // Set hidden input value
    document.getElementById('selectedStudentIdInput').value = student.idno;
    
    // Hide search results and show selected student info
    searchResults.style.display = 'none';
    selectedStudentInfo.style.display = 'block';
    
    // Clear search input
    document.getElementById('studentSearchInput').value = '';
  }
  
  function resetSearchModal() {
    document.getElementById('studentSearchInput').value = '';
    document.getElementById('searchResults').innerHTML = '';
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('selectedStudentInfo').style.display = 'none';
    document.getElementById('sitInForm').reset();
  }
  
  function createSitInReservation() {
    const studentId = document.getElementById('selectedStudentIdInput').value;
    const lab = document.getElementById('labSelect').value;
    const purpose = document.getElementById('purposeSelect').value;
    const submitBtn = document.querySelector('#sitInForm button[type="submit"]');
    
    if (!studentId || !lab || !purpose) {
      Swal.fire('Error', 'Please fill all required fields', 'error');
      return;
    }
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
    
    fetch('/admin_create_sitin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id: studentId,
        lab: lab,
        purpose: purpose
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        Swal.fire('Success', 'Sit-in reservation created successfully', 'success').then(() => {
          // Close modal and reset
          document.getElementById('searchStudentModal').style.display = 'none';
          resetSearchModal();
          
          // Refresh current sit-in list
          fetchAndDisplayCurrentSitIn();
          
          // Emit socket event to update all clients
          socket.emit('new_sitin', data.reservation);
        });
      } else {
        Swal.fire('Error', data.message || 'Failed to create reservation', 'error');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      Swal.fire('Error', 'An error occurred while creating reservation', 'error');
    })
    .finally(() => {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sit In';
    });
  }

// Listen for new sit-in events to update both admin tables
socket.on('new_sitin', function(reservation) {
    // Add to current sit-in table
    const currentTableBody = document.querySelector('#reservations-table tbody');
    const newRow = createReservationRow(reservation);
    currentTableBody.prepend(newRow);

    // If the student is already in records (unlikely but possible), remove them
    const existingRecord = document.querySelector(`#records-table tbody tr[data-reservation-id="${reservation.id}"]`);
    if (existingRecord) {
        existingRecord.remove();
    }
});

function createReservationRow(reservation) {
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
        <td>${reservation.status}</td>
        <td>
            <button class="logout-btn" data-reservation-id="${reservation.id}">Logout</button>
        </td>
    `;
    
    return row;
}

// Student side - handle logout updates
socket.on(`student_${studentId}_reservation_updated`, function(data) {
    // Find the reservation in history table
    const reservationRow = document.querySelector(`#historyBody tr[data-reservation-id="${data.reservation_id}"]`);
    
    if (reservationRow) {
        // Update status and logout time
        reservationRow.querySelector('td:nth-child(4)').textContent = data.status;
        reservationRow.querySelector('td:nth-child(5)').textContent = data.logout_time;
        
        // Enable feedback button if logged out
        if (data.status === 'Logged Out') {
            const feedbackBtn = reservationRow.querySelector('.submit-feedback-btn');
            feedbackBtn.disabled = false;
            feedbackBtn.style.backgroundColor = '';
            feedbackBtn.style.cursor = '';
        }
    } else if (currentView === 'history') {
        // If row not found but we're on history page, refresh
        fetchReservationHistory();
    }
    
    // Show notification if not on history page
    if (currentView !== 'history') {
        Swal.fire({
            title: 'Session Updated',
            text: `Your session at ${data.lab_name} has been logged out`,
            icon: 'info',
            timer: 3000
        });
    }
});