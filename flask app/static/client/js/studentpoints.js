// Points System Functionality for Student Dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize points functionality
    fetchPointsData();

    // Initialize leaderboard if container exists
    const leaderboardContainer = document.getElementById('leaderboard-container');
    if (leaderboardContainer) {
        fetchStudentLeaderboard();
    }

    // Add event listener for convert points button
    const convertPointsBtn = document.getElementById('convertPointsBtn');
    if (convertPointsBtn) {
        convertPointsBtn.addEventListener('click', convertPointsToSession);
    }

    // Initialize lab resources when on the lab-resources section
    const labResourcesSection = document.getElementById('lab-resources');
    if (labResourcesSection) {
        // Check if we're on lab resources section when section changes
        const links = document.querySelectorAll('.sidebar-links a');
        links.forEach(link => {
            link.addEventListener('click', function() {
                if (this.getAttribute('data-section') === 'lab-resources') {
                    fetchLabResources();
                }
            });
        });
        
        // Also fetch resources if lab-resources is the active section
        if (localStorage.getItem('activeDashboardSection') === 'lab-resources') {
            fetchLabResources();
        }
        
        // Setup resource modal close button
        const modalClose = document.querySelector('.resource-modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', closeResourceModal);
        }
        
        // Close modal when clicking outside of it
        const resourceModal = document.getElementById('resourceViewerModal');
        if (resourceModal) {
            window.addEventListener('click', function(event) {
                if (event.target === resourceModal) {
                    closeResourceModal();
                }
            });
        }
        
        // Listen for new lab resources if socket is available
        if (typeof socket !== 'undefined' && socket) {
            socket.on('new_lab_resource', function(resource) {
                console.log('New lab resource received:', resource);
                fetchLabResources(); // Refresh the resources
            });
            
            socket.on('lab_resource_deleted', function(data) {
                console.log('Lab resource deleted:', data);
                fetchLabResources(); // Refresh the resources
            });
        }
    }
});

/**
 * Fetch student points data from the server
 */
function fetchPointsData() {
    fetch('/points_balance')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const points = data.points || 0;
                updatePointsDisplay(points);
                
                if (data.history) {
                    updatePointsHistory(data.history);
                } else {
                    // Optionally fetch history separately
                    fetchPointsHistory();
                }
            } else {
                const pointsDisplay = document.getElementById('currentPoints');
                const conversionMessage = document.getElementById('conversionMessage');
                
                if (pointsDisplay) {
                    pointsDisplay.textContent = "0";
                }
                if (conversionMessage) {
                    conversionMessage.textContent = data.message || "Error loading points data";
                }
            }
        })
        .catch(error => {
            console.error("Error fetching points data:", error);
            const pointsDisplay = document.getElementById('currentPoints');
            if (pointsDisplay) {
                pointsDisplay.textContent = "Error";
            }
        });
}

/**
 * Fetch points history separately if needed
 */
function fetchPointsHistory() {
    fetch('/get_points_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePointsHistory(data.history);
            } else {
                console.error("Failed to load points history:", data.message);
            }
        })
        .catch(error => {
            console.error("Error fetching points history:", error);
        });
}

/**
 * Update the points display in the UI
 * @param {number} points - Current points balance
 */
function updatePointsDisplay(points) {
    const pointsDisplay = document.getElementById('currentPoints');
    const convertBtn = document.getElementById('convertPointsBtn');
    const conversionMessage = document.getElementById('conversionMessage');
    
    if (pointsDisplay) {
        pointsDisplay.textContent = points;
    }
    
    // Enable/disable convert button based on points
    if (convertBtn && conversionMessage) {
        if (points >= 3) {
            convertBtn.disabled = false;
            const sessions = Math.floor(points / 3);
            conversionMessage.textContent = `You can convert your points to ${sessions} session(s)`;
        } else {
            convertBtn.disabled = true;
            conversionMessage.textContent = "You need at least 3 points to convert to a session";
        }
    }
}

/**
 * Update the points history table
 * @param {Array} history - Array of point history entries
 */
function updatePointsHistory(history) {
    const historyBody = document.getElementById('points-history-body');
    if (!historyBody) return;
    
    historyBody.innerHTML = ''; // Clear existing rows
    
    if (history && history.length > 0) {
        history.forEach(entry => {
            const row = document.createElement('tr');
            const date = new Date(entry.awarded_at);
            
            row.innerHTML = `
                <td>${date.toLocaleString()}</td>
                <td class="${entry.points_change > 0 ? 'positive' : 'negative'}">${entry.points_change > 0 ? '+' : ''}${entry.points_change}</td>
                <td>${entry.reason}</td>
                <td>${entry.awarded_by}</td>
            `;
            historyBody.appendChild(row);
        });
    } else {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="4" class="text-center">No points history available</td>';
        historyBody.appendChild(emptyRow);
    }
}

/**
 * Convert points to session(s)
 */
function convertPointsToSession() {
    Swal.fire({
        title: 'Convert Points to Sessions',
        text: 'Are you sure you want to convert your points to additional lab sessions?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, convert it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Make API call to convert points
            fetch('/convert_points', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire(
                        'Success!',
                        `Points converted successfully! You now have ${data.sessions_added} additional session(s).`,
                        'success'
                    );
                    // Update the points display
                    updatePointsDisplay(data.remaining_points);
                    // If history is returned, update it
                    if (data.history) {
                        updatePointsHistory(data.history);
                    } else {
                        // Otherwise refresh history separately
                        fetchPointsHistory();
                    }
                } else {
                    Swal.fire(
                        'Error!',
                        data.message || 'Failed to convert points.',
                        'error'
                    );
                }
            })
            .catch(error => {
                console.error("Error converting points:", error);
                Swal.fire(
                    'Error!',
                    'An unexpected error occurred while converting points.',
                    'error'
                );
            });
        }
    });
}

// Function to handle fetching and displaying leaderboard
function fetchStudentLeaderboard() {
    fetch('/get_leaderboard')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLeaderboard(data.leaderboard);
            } else {
                console.error('Failed to fetch leaderboard:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching leaderboard:', error);
        });
}

// Function to display leaderboard data
function displayLeaderboard(leaderboardData) {
    const leaderboardContainer = document.getElementById('leaderboard-container');
    if (!leaderboardContainer) return;
    
    leaderboardContainer.innerHTML = '';
    
    if (!leaderboardData || leaderboardData.length === 0) {
        leaderboardContainer.innerHTML = '<p>No leaderboard data available</p>';
        return;
    }
    
    const leaderboardTable = document.createElement('table');
    leaderboardTable.className = 'leaderboard-table';
    
    // Create table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Rank</th>
            <th>Student</th>
            <th>Course</th>
            <th>Points</th>
        </tr>
    `;
    leaderboardTable.appendChild(thead);
    
    // Create table body
    const tbody = document.createElement('tbody');
    
    leaderboardData.forEach((student, index) => {
        const row = document.createElement('tr');
        
        // Highlight current student
        const isCurrentStudent = student.student_idno === currentStudentId;
        if (isCurrentStudent) {
            row.className = 'current-student';
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${student.student_name}</td>
            <td>${student.course} - Year ${student.year_level}</td>
            <td><span class="points-badge">${student.total_points}</span></td>
        `;
        
        tbody.appendChild(row);
    });
    
    leaderboardTable.appendChild(tbody);
    leaderboardContainer.appendChild(leaderboardTable);
}

function fetchLabResources() {
    const resourcesGrid = document.getElementById('resourcesGrid');
    const noResourcesMessage = document.getElementById('noResourcesMessage');
    
    if (!resourcesGrid || !noResourcesMessage) return;
    
    // Show loading
    resourcesGrid.innerHTML = `
        <div class="resources-loading">
            <div class="spinner"></div>
            <p>Loading resources...</p>
        </div>
    `;
    noResourcesMessage.style.display = 'none';
    
    fetch('/get_lab_resources')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLabResources(data.resources);
            } else {
                resourcesGrid.innerHTML = `
                    <div class="error-message">
                        <p>Error loading resources: ${data.message}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching lab resources:', error);
            resourcesGrid.innerHTML = `
                <div class="error-message">
                    <p>Failed to load resources. Please try again later.</p>
                </div>
            `;
        });
}

function displayLabResources(resources) {
    const resourcesGrid = document.getElementById('resourcesGrid');
    const noResourcesMessage = document.getElementById('noResourcesMessage');
    
    if (!resourcesGrid || !noResourcesMessage) return;
    
    if (!resources || resources.length === 0) {
        resourcesGrid.innerHTML = '';
        noResourcesMessage.style.display = 'block';
        return;
    }
    
    resourcesGrid.innerHTML = '';
    
    resources.forEach(resource => {
        const truncatedContent = resource.content.length > 100 
            ? resource.content.substring(0, 100) + '...' 
            : resource.content;
            
        const card = document.createElement('div');
        card.className = 'resource-card';
        card.setAttribute('data-resource-id', resource.id);
        
        const date = new Date(resource.created_at).toLocaleDateString();
        
        card.innerHTML = `
            <div class="resource-card-header">
                <h3>${resource.title}</h3>
            </div>
            <div class="resource-card-body">
                <p>${truncatedContent}</p>
            </div>
            <div class="resource-footer">
                <div>
                    <div class="resource-date">${date}</div>
                    <div class="resource-uploader">By: ${resource.created_by}</div>
                </div>
                <button class="resource-action view-resource-btn">
                    <i class="fas fa-eye"></i> View
                </button>
            </div>
        `;
        
        resourcesGrid.appendChild(card);
        
        // Add click event to view the resource details
        card.addEventListener('click', function() {
            openResourceModal(resource);
        });
    });
}

function openResourceModal(resource) {
    const modal = document.getElementById('resourceViewerModal');
    if (!modal) return;
    
    document.getElementById('resourceModalTitle').textContent = resource.title;
    document.getElementById('resourceModalDescription').textContent = resource.content;
    document.getElementById('resourceModalDate').textContent = `Added: ${new Date(resource.created_at).toLocaleString()}`;
    document.getElementById('resourceModalUploader').textContent = `By: ${resource.created_by}`;
    
    const link = document.getElementById('resourceModalLink');
    link.href = resource.link;
    
    modal.style.display = 'block';
}

function closeResourceModal() {
    const modal = document.getElementById('resourceViewerModal');
    if (modal) {
        modal.style.display = 'none';
    }
} 