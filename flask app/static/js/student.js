// Lab Resources Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const resourcesContainer = document.querySelector('.resources-container');
    const resourceModal = document.querySelector('.resource-modal');
    const labSchedulesModal = document.querySelector('.lab-schedules-modal');
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationCount = document.querySelector('.notification-count');
    const notificationList = document.querySelector('.notification-list');
    const notificationDot = document.querySelector('.notification-dot');
    
    if (resourcesContainer) {
        loadLabResources();
        
        // Initialize socket for real-time updates
        if (typeof socket !== 'undefined') {
            // Listen for new resources
            socket.on('new_lab_resource', function(data) {
                console.log('New resource received:', data);
                // Show notification
                showResourceNotification('New Resource Added', `"${data.title}" has been added to lab resources.`, 'success');
                loadLabResources();
            });
            
            // Listen for deleted resources
            socket.on('lab_resource_deleted', function(data) {
                console.log('Resource deleted:', data);
                // Find and remove the resource card with animation
                const resourceCard = document.querySelector(`.resource-card[data-id="${data.resource_id}"]`);
                if (resourceCard) {
                    resourceCard.classList.add('fade-out');
                    setTimeout(() => {
                        resourceCard.remove();
                        // If no resources left, show the empty message
                        if (document.querySelectorAll('.resource-card').length === 0) {
                            document.querySelector('.no-resources-message').style.display = 'flex';
                        }
                    }, 300);
                } else {
                    loadLabResources();
                }
            });
            
            // Listen for updated resources
            socket.on('resource_updated', function(data) {
                console.log('Resource updated:', data);
                // Show notification
                showResourceNotification('Resource Updated', `"${data.title}" has been updated.`, 'info');
                loadLabResources();
            });
        }
    }
    
    // Modal handling
    if (resourceModal) {
        // Close modal when clicking the close button
        const closeBtn = resourceModal.querySelector('.resource-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function(event) {
                resourceModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            });
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === resourceModal) {
                resourceModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    // Lab Schedules Modal Functionality
    if (labSchedulesModal) {
        // Setup tab switching
        const tabs = document.querySelectorAll('.lab-tab');
        const schedules = document.querySelectorAll('.lab-schedule');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs and schedules
                tabs.forEach(t => t.classList.remove('active'));
                schedules.forEach(s => s.classList.remove('active'));
                
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Show corresponding schedule
                const labId = this.getAttribute('data-lab');
                document.getElementById(`${labId}-schedule`).classList.add('active');
                
                // Load the schedule for this lab
                const labIdNumber = labId.replace('lab', '');
                loadLabSchedule(labIdNumber);
            });
        });
        
        // Close modal when clicking the close button
        const closeBtn = labSchedulesModal.querySelector('.lab-schedules-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                labSchedulesModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            });
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === labSchedulesModal) {
                labSchedulesModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
        
        // Print button functionality
        const printBtn = document.querySelector('.schedule-print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', function() {
                // Get the active schedule
                const activeSchedule = document.querySelector('.lab-schedule.active');
                const title = activeSchedule.querySelector('h3').textContent;
                
                // Create a new window for printing
                const printWindow = window.open('', '_blank');
                printWindow.document.write(`
                    <html>
                    <head>
                        <title>${title} - Print</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 20px; }
                            h1 { color: #333; text-align: center; margin-bottom: 20px; }
                            table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
                            th, td { padding: 10px; text-align: left; border: 1px solid #ddd; }
                            th { background-color: #f5f5f5; }
                            .day-header { background-color: #f1f1f1; text-align: center; font-weight: bold; padding: 10px; }
                            .status-badge { display: inline-block; padding: 4px 8px; border-radius: 20px; font-size: 0.9rem; font-weight: 500; }
                            .status-badge.available { background-color: #e8f5e9; color: #2e7d32; }
                            .status-badge.reserved { background-color: #ffebee; color: #c62828; }
                            .status-badge.unavailable { background-color: #f5f5f5; color: #757575; }
                            .legend { display: flex; justify-content: center; gap: 30px; margin-top: 20px; }
                            .legend-item { display: flex; align-items: center; gap: 5px; }
                            .legend-color { width: 16px; height: 16px; border-radius: 3px; }
                            .legend-color.available-slot { background-color: #e8f5e9; border: 1px solid #c8e6c9; }
                            .legend-color.reserved-slot { background-color: #ffebee; border: 1px solid #ffcdd2; }
                            @media print {
                                @page { size: portrait; }
                                .status-badge { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                            }
                        </style>
                    </head>
                    <body>
                        <h1>${title}</h1>
                        ${activeSchedule.querySelector('.schedule-table-container') ? 
                            activeSchedule.querySelector('.schedule-table-container').innerHTML : 
                            '<p>Schedule will be updated soon.</p>'}
                        <div class="legend">
                            <div class="legend-item">
                                <span class="legend-color available-slot"></span>
                                <span>Available</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color reserved-slot"></span>
                                <span>Class in Session</span>
                            </div>
                        </div>
                    </body>
                    </html>
                `);
                printWindow.document.close();
                setTimeout(() => {
                    printWindow.print();
                }, 500);
            });
        }
    }
    
    // Add button to open Lab Schedules modal from the stats box
    const labStatsBox = document.querySelector('.stats-box:nth-child(2)');
    if (labStatsBox && labSchedulesModal) {
        labStatsBox.style.cursor = 'pointer';
        labStatsBox.addEventListener('click', function() {
            labSchedulesModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            
            // Load schedules for all labs when modal is opened
            loadAllLabSchedules();
        });
        
        // Add tooltip to indicate it's clickable
        labStatsBox.setAttribute('title', 'Click to view lab schedules');
        
        // Add a small icon to indicate it's clickable
        const icon = document.createElement('i');
        icon.className = 'fas fa-calendar-alt';
        icon.style.position = 'absolute';
        icon.style.top = '10px';
        icon.style.right = '10px';
        icon.style.color = '#7c4dff';
        icon.style.fontSize = '1.2rem';
        labStatsBox.style.position = 'relative';
        labStatsBox.appendChild(icon);
    }

    // Initialize date pickers - prevent Sunday selection
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // Disable Sundays by setting the input's min attribute
        input.addEventListener('focus', function() {
            // Only add the change listener once
            if (!this.dataset.sundayCheckAdded) {
                this.dataset.sundayCheckAdded = 'true';
                
                this.addEventListener('change', function() {
                    const selectedDate = new Date(this.value);
                    // Check if the date is a Sunday (0 = Sunday, 1 = Monday, etc.)
                    if (selectedDate.getDay() === 0) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Invalid Day',
                            text: 'Reservations are not available on Sundays. Please select another day.',
                            confirmButtonColor: '#7c4dff'
                        });
                        // Reset the input to empty
                        this.value = '';
                    }
                });
            }
        });
    });

    // Initialize lab schedules on page load
    loadAllLabSchedules();
    
    // Restore selected lab from localStorage if available
    const storedLabId = localStorage.getItem('selectedLabId');
    if (storedLabId) {
        const labSelect = document.getElementById('lab-select');
        if (labSelect) {
            labSelect.value = storedLabId;
            
            // Activate the corresponding lab tab
            const labTabs = document.querySelectorAll('.lab-tab');
            labTabs.forEach(tab => {
                if (tab.getAttribute('data-lab') === `lab${storedLabId}`) {
                    tab.click();
                }
            });
        }
    }
    
    // Set up tab switching for lab schedules
    const labTabs = document.querySelectorAll('.lab-tab');
    const labContents = document.querySelectorAll('.lab-schedule-content');
    
    labTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const labId = this.getAttribute('data-lab');
            
            // Deactivate all tabs and hide all content
            labTabs.forEach(t => t.classList.remove('active'));
            labContents.forEach(c => c.classList.remove('active'));
            
            // Activate this tab and show its content
            this.classList.add('active');
            document.getElementById(`${labId}-schedule`).classList.add('active');
            
            // Extract the lab ID number and load the schedule
            const labIdNumber = labId.replace('lab', '');
            loadLabSchedule(labIdNumber);
        });
    });
    
    // Activate the first lab tab by default if none is active
    if (labTabs.length > 0 && !document.querySelector('.lab-tab.active')) {
        labTabs[0].click();
    }

    // Initialize notifications
    updateNotificationCount();
});

/**
 * Load schedules for all labs
 */
function loadAllLabSchedules() {
    const labTabs = document.querySelectorAll('.lab-tab');
    
    // If there are no lab tabs, display a message in the modal
    if (labTabs.length === 0) {
        const labContent = document.querySelector('.lab-schedules-content');
        if (labContent) {
            labContent.innerHTML = `
                <div class="no-schedules-message" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 50px; text-align: center;">
                    <i class="fas fa-calendar-times" style="font-size: 48px; color: #7c4dff; margin-bottom: 20px;"></i>
                    <h3 style="margin-bottom: 10px; color: #333;">No Lab Data Available</h3>
                    <p style="color: #666;">Please contact the administrator to set up laboratory data.</p>
                </div>
            `;
        }
        return;
    }
    
    // For each lab tab, load its schedule
    labTabs.forEach(tab => {
        const labId = tab.getAttribute('data-lab').replace('lab', '');
        loadLabSchedule(labId);
    });
    
    // Make sure the first tab is active
    if (labTabs.length > 0 && !document.querySelector('.lab-tab.active')) {
        labTabs[0].classList.add('active');
        const firstLabId = labTabs[0].getAttribute('data-lab');
        const firstSchedule = document.getElementById(`${firstLabId}-schedule`);
        if (firstSchedule) {
            firstSchedule.classList.add('active');
        }
    }
}

/**
 * Load the schedule for a specific lab
 */
function loadLabSchedule(labId) {
    // Get the schedule container for this lab
    const scheduleContainer = document.getElementById(`lab${labId}-schedule`);
    if (!scheduleContainer) return;
    
    // Get the table body
    let tableBody = scheduleContainer.querySelector('tbody');
    
    // Show loading message
    tableBody.innerHTML = `
        <tr>
            <td colspan="3" class="text-center">
                <div style="padding: 20px; text-align: center; display: flex; flex-direction: column; align-items: center;">
                    <div class="spinner" style="border: 4px solid rgba(0, 0, 0, 0.1); width: 36px; height: 36px; border-radius: 50%; border-left-color: #7c4dff; animation: spin 1s linear infinite;"></div>
                    <p style="margin-top: 15px; font-size: 1.5rem; color: #666;">Loading lab schedule...</p>
                </div>
            </td>
        </tr>
    `;
    
    // Fetch the lab schedules from the API
    fetch(`/api/student/lab_schedules/${labId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if we have valid data
            if (!data.success) {
                throw new Error(data.message || 'Failed to load schedule');
            }
            
            // Clear the table body
            tableBody.innerHTML = '';
            
            // Process the schedules
            const schedules = data.schedules || [];
            
            if (schedules.length === 0) {
                // No schedules found
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center">
                            <div style="padding: 20px; text-align: center;">
                                <i class="fas fa-calendar-times" style="font-size: 32px; color: #ccc; margin-bottom: 10px;"></i>
                                <p style="font-size: 1.5rem; color: #666;">No schedules have been set up for this laboratory.</p>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }
            
            // Group schedules by day of the week
            const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            const schedulesByDay = {};
            
            daysOfWeek.forEach(day => {
                schedulesByDay[day] = schedules.filter(schedule => schedule.day_of_week === day);
            });
            
            // Create a header row for each day that has schedules
            daysOfWeek.forEach(day => {
                if (schedulesByDay[day].length === 0) return;
                
                // Create a header row for this day
                const dayHeaderRow = document.createElement('tr');
                dayHeaderRow.innerHTML = `
                    <td colspan="3" class="day-header" style="background-color: #f5f5f5; font-weight: bold; text-align: center; padding: 12px; font-size: 1.6rem;">${day}</td>
                `;
                tableBody.appendChild(dayHeaderRow);
                
                // Sort time slots by start time
                const daySchedules = schedulesByDay[day].sort((a, b) => {
                    return a.start_time.localeCompare(b.start_time);
                });
                
                // Add each time slot for this day
                daySchedules.forEach(schedule => {
                    const row = document.createElement('tr');
                    
                    // Format the time slot
                    const startTimeParts = schedule.start_time.split(':');
                    const endTimeParts = schedule.end_time.split(':');
                    
                    // Convert to 12-hour format with AM/PM
                    const startHour = parseInt(startTimeParts[0]);
                    const startMinute = startTimeParts[1] || '00';
                    const endHour = parseInt(endTimeParts[0]);
                    const endMinute = endTimeParts[1] || '00';
                    
                    const startTime12 = `${startHour > 12 ? startHour - 12 : startHour}:${startMinute.padStart(2, '0')} ${startHour >= 12 ? 'PM' : 'AM'}`;
                    const endTime12 = `${endHour > 12 ? endHour - 12 : endHour}:${endMinute.padStart(2, '0')} ${endHour >= 12 ? 'PM' : 'AM'}`;
                    
                    const timeSlot = `${startTime12} - ${endTime12}`;
                    
                    // Determine subject info
                    let subjectInfo = 'N/A';
                    if (schedule.subject_code && schedule.subject_name) {
                        subjectInfo = `${schedule.subject_code} - ${schedule.subject_name}`;
                    }
                    
                    // Determine status class and style
                    let statusBadge = '';
                    if (schedule.status === 'Available') {
                        statusBadge = '<span class="status-badge available">Available</span>';
                    } else if (schedule.status === 'Reserved') {
                        statusBadge = '<span class="status-badge reserved">Reserved</span>';
                    } else {
                        statusBadge = `<span class="status-badge unavailable">${schedule.status}</span>`;
                    }
                    
                    // Add the cells to the row
                    row.innerHTML = `
                        <td>${timeSlot}</td>
                        <td>${subjectInfo}</td>
                        <td>${statusBadge}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            });
        })
        .catch(error => {
            console.error('Error loading lab schedule:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center error">
                        <span style="font-size: 1.5rem; color: #c62828;">Failed to load schedules: ${error.message || 'Failed to fetch'}</span>
                    </td>
                </tr>
            `;
        });
}

/**
 * Show a notification for resource updates
 */
function showResourceNotification(title, message, type = 'info') {
    if (typeof Swal !== 'undefined') {
        const toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        
        toast.fire({
            icon: type,
            title: title,
            text: message
        });
    } else {
        // Fallback if SweetAlert is not available
        console.log(`${title}: ${message}`);
    }
}

/**
 * Load lab resources from the server
 */
function loadLabResources() {
    const resourcesGrid = document.querySelector('.resources-grid');
    const loadingElement = document.querySelector('.resources-loading');
    const noResourcesMessage = document.querySelector('.no-resources-message');
    
    if (!resourcesGrid) return;
    
    // Clear previous content except loading
    const existingCards = resourcesGrid.querySelectorAll('.resource-card');
    existingCards.forEach(card => card.remove());
    
    // Show loading indicator
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
    
    if (noResourcesMessage) {
        noResourcesMessage.style.display = 'none';
    }
    
    console.log("Loading lab resources...");
    
    // Fetch resources from the server
    fetch('/api/get_lab_resources')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch resources');
            }
            return response.json();
        })
        .then(data => {
            console.log("Resources loaded:", data);
            
            // Hide loading indicator
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            
            // Display the resources
            if (data.success && data.resources && data.resources.length > 0) {
                displayResources(data.resources, resourcesGrid);
                
                // Make sure the no resources message is hidden
                if (noResourcesMessage) {
                    noResourcesMessage.style.display = 'none';
                }
            } else {
                console.log("No resources found");
                // Show the no resources message
                if (noResourcesMessage) {
                    noResourcesMessage.style.display = 'flex';
                }
            }
        })
        .catch(error => {
            console.error('Error loading resources:', error);
            
            // Hide loading indicator on error
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            
            // Show the no resources message on error
            if (noResourcesMessage) {
                noResourcesMessage.style.display = 'flex';
            }
        });
}

/**
 * Display resources in the grid
 */
function displayResources(resources, container) {
    // Clear any existing content except the loading indicator
    const existingNodes = Array.from(container.childNodes);
    existingNodes.forEach(node => {
        if (!node.classList || !node.classList.contains('resources-loading')) {
            container.removeChild(node);
        }
    });
    
    // Sort resources by date (newest first)
    resources.sort((a, b) => {
        const dateA = new Date(a.created_at || a.timestamp);
        const dateB = new Date(b.created_at || b.timestamp);
        return dateB - dateA;
    });
    
    // Add each resource as a card with staggered animation
    resources.forEach((resource, index) => {
        // Parse timestamp to date object
        const date = new Date(resource.created_at || resource.timestamp);
        const formattedDate = date.toLocaleDateString();
        
        const resourceCard = document.createElement('div');
        resourceCard.className = 'resource-card';
        resourceCard.setAttribute('data-id', resource.id);
        
        // Add staggered animation delay
        resourceCard.style.animationDelay = `${index * 0.05}s`;
        
        // Create card HTML
        resourceCard.innerHTML = `
            <div class="resource-card-header">
                <h3>${escapeHtml(resource.title)}</h3>
            </div>
            <div class="resource-card-body">
                <p>${escapeHtml(resource.content)}</p>
            </div>
            <div class="resource-footer">
                <div>
                    <span class="resource-date">${formattedDate}</span>
                    <span class="resource-uploader">By: ${escapeHtml(resource.created_by || resource.uploader)}</span>
                </div>
                <div class="resource-actions">
                    <button class="resource-action view-resource" data-id="${resource.id}">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(resourceCard);
        
        // Add click event to the entire card
        resourceCard.addEventListener('click', function(event) {
            // Don't trigger if clicking on buttons
            if (!event.target.closest('.resource-action')) {
                showResourceDetails(resource);
            }
        });
        
        // Add click events to view buttons
        const viewButton = resourceCard.querySelector('.view-resource');
        if (viewButton) {
            viewButton.addEventListener('click', function(event) {
                event.stopPropagation();
                showResourceDetails(resource);
            });
        }
    });
    
    // Add hover effects to all cards
    addCardEffects();
}

/**
 * Add interactive effects to resource cards
 */
function addCardEffects() {
    document.querySelectorAll('.resource-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            // Add subtle movement on hover
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            // Reset on mouse leave
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
}

/**
 * Show resource details in modal with enhanced animations
 */
function showResourceDetails(resource) {
    const modal = document.querySelector('.resource-modal');
    if (!modal) return;
    
    // Fill modal with resource details
    const titleEl = modal.querySelector('.resource-title');
    const descriptionEl = modal.querySelector('.resource-description');
    const dateEl = modal.querySelector('.resource-date');
    const uploaderEl = modal.querySelector('.resource-uploader');
    const viewLinkEl = modal.querySelector('.resource-view-btn');
    
    if (titleEl) titleEl.textContent = resource.title || '';
    if (descriptionEl) descriptionEl.textContent = resource.content || '';
    
    if (dateEl && (resource.created_at || resource.timestamp)) {
        const date = new Date(resource.created_at || resource.timestamp);
        dateEl.textContent = date.toLocaleString();
    }
    
    if (uploaderEl) {
        uploaderEl.textContent = resource.created_by || resource.uploader || '';
    }
    
    // If there's a link, show the view button
    if (viewLinkEl) {
        if (resource.link) {
            viewLinkEl.style.display = 'inline-block';
            viewLinkEl.href = resource.link;
            
            // Add click tracking for analytics
            viewLinkEl.addEventListener('click', function() {
                // Track resource usage if needed
                console.log(`Resource viewed: ${resource.id} - ${resource.title}`);
            });
        } else {
            viewLinkEl.style.display = 'none';
        }
    }
    
    // Open the modal with enhanced animation
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent scrolling
    
    // Add keyboard support for accessibility
    document.addEventListener('keydown', function escapeKeyListener(e) {
        if (e.key === 'Escape') {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            document.removeEventListener('keydown', escapeKeyListener);
        }
    });
}

/**
 * Helper function to escape HTML to prevent XSS
 */
function escapeHtml(html) {
    if (!html) return '';
    return html
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ===================== RESERVATION MODAL LOGIC =====================

document.addEventListener('DOMContentLoaded', function () {
  // Modal elements
  const reservationModal = document.getElementById('reservationModal');
  const createReservationBtn = document.getElementById('createReservationBtn');
  const modalClose = reservationModal ? reservationModal.querySelector('.modal-close') : null;
  const steps = reservationModal ? reservationModal.querySelectorAll('.step') : [];
  const stepContents = reservationModal ? reservationModal.querySelectorAll('.step-content') : [];
  const prevStepBtn = document.getElementById('prevStepBtn');
  const nextStepBtn = document.getElementById('nextStepBtn');
  const submitReservationBtn = document.getElementById('submitReservationBtn');

  // Step 1
  const labSelect = document.getElementById('modal_lab_id');
  const dateInput = document.getElementById('modal_reservation_date');
  const dateError = document.getElementById('modal_date_error');
  // Step 2
  const timeSlotsList = document.getElementById('time-slots-list');
  const timeSlotsLoading = document.getElementById('time-slots-loading');
  const noTimeSlotsMessage = document.getElementById('no-time-slots-message');
  // Step 3
  const computersGrid = document.getElementById('computers-grid');
  const computersLoading = document.getElementById('computers-loading');
  const noComputersMessage = document.getElementById('no-computers-message');
  // Step 4
  const purposeSelect = document.getElementById('modal_purpose');
  const summaryLab = document.getElementById('summary_lab');
  const summaryDate = document.getElementById('summary_date');
  const summaryTimeSlot = document.getElementById('summary_time_slot');
  const summaryComputer = document.getElementById('summary_computer');
  const summaryPurpose = document.getElementById('summary_purpose');

  // Table
  const reservationsTableBody = document.getElementById('studentReservationsBody');
  const noReservationsMessage = document.getElementById('noReservationsMessage');

  // State
  let currentStep = 1;
  let selectedLab = '';
  let selectedDate = '';
  let selectedTimeSlot = '';
  let selectedTimeSlotLabel = '';
  let selectedComputerId = '';
  let selectedComputerLabel = '';
  let selectedPurpose = '';

  // Modal open/close
  if (createReservationBtn) {
    createReservationBtn.addEventListener('click', function () {
      openReservationModal();
    });
  }
  if (modalClose) {
    modalClose.addEventListener('click', closeReservationModal);
  }
  if (reservationModal) {
    reservationModal.querySelector('.modal-overlay').addEventListener('click', closeReservationModal);
  }
  function openReservationModal() {
    reservationModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    goToStep(1);
    resetModalState();
    
    // Load all lab schedules when the modal is opened
    // This ensures lab schedules are fetched and displayed
    loadAllLabSchedules();
    
    // Add event listener to lab select dropdown if not already added
    if (!labSelect.dataset.listenerAdded) {
      labSelect.dataset.listenerAdded = 'true';
      labSelect.addEventListener('change', function() {
        const selectedLabId = this.value;
        if (selectedLabId) {
          // Activate the corresponding lab tab to show its schedule
          const labTabs = document.querySelectorAll('.lab-tab');
          labTabs.forEach(tab => {
            if (tab.getAttribute('data-lab') === `lab${selectedLabId}`) {
              tab.click();
            }
          });
          
          // If schedules aren't loaded yet, load them
          loadLabSchedule(selectedLabId);
        }
      });
    }
  }
  function closeReservationModal() {
    reservationModal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
  // Step navigation
  if (prevStepBtn) {
    prevStepBtn.addEventListener('click', function () {
      if (currentStep > 1) goToStep(currentStep - 1);
    });
  }
  if (nextStepBtn) {
    nextStepBtn.addEventListener('click', function () {
      if (validateStep(currentStep)) goToStep(currentStep + 1);
    });
  }
  if (submitReservationBtn) {
    submitReservationBtn.addEventListener('click', submitReservation);
  }
  function goToStep(step) {
    currentStep = step;
    steps.forEach((s, i) => s.classList.toggle('active', i === step - 1));
    stepContents.forEach((c, i) => c.style.display = (i === step - 1) ? 'block' : 'none');
    prevStepBtn.style.display = step > 1 ? 'inline-block' : 'none';
    nextStepBtn.style.display = step < 5 ? 'inline-block' : 'none';
    submitReservationBtn.style.display = step === 5 ? 'inline-block' : 'none';
    if (step === 2) loadTimeSlots();
    if (step === 3) loadComputers();
    if (step === 5) updateSummary();
  }
  function resetModalState() {
    labSelect.value = '';
    dateInput.value = '';
    dateError.style.display = 'none';
    timeSlotsList.innerHTML = '';
    selectedTimeSlot = '';
    selectedTimeSlotLabel = '';
    computersGrid.innerHTML = '';
    selectedComputerId = '';
    selectedComputerLabel = '';
    purposeSelect.value = '';
    summaryLab.textContent = '-';
    summaryDate.textContent = '-';
    summaryTimeSlot.textContent = '-';
    summaryComputer.textContent = '-';
    summaryPurpose.textContent = '-';
  }
  // Step validation for 5 steps
  function validateStep(step) {
    if (step === 1) {
      selectedLab = labSelect.value;
      selectedDate = dateInput.value;
      
      // Check if required fields are filled
      if (!selectedLab || !selectedDate) {
        if (!selectedDate) dateError.style.display = 'block';
        return false;
      }
      
      // Check if selected date is a Sunday
      const selectedDay = new Date(selectedDate).getDay();
      if (selectedDay === 0) { // 0 = Sunday
        Swal.fire({
          icon: 'error',
          title: 'Invalid Day',
          text: 'Reservations are not available on Sundays. Please select another day.',
          confirmButtonColor: '#7c4dff'
        });
        return false;
      }
      
      dateError.style.display = 'none';
      return true;
    }
    if (step === 2) {
      if (!selectedTimeSlot) {
        timeSlotsList.classList.add('shake');
        setTimeout(() => timeSlotsList.classList.remove('shake'), 500);
        return false;
      }
      return true;
    }
    if (step === 3) {
      if (!selectedComputerId) {
        computersGrid.classList.add('shake');
        setTimeout(() => computersGrid.classList.remove('shake'), 500);
        return false;
      }
      return true;
    }
    if (step === 4) {
      selectedPurpose = purposeSelect.value;
      if (!selectedPurpose) {
        purposeSelect.classList.add('shake');
        setTimeout(() => purposeSelect.classList.remove('shake'), 500);
        return false;
      }
      return true;
    }
    if (step === 5) {
      // Final check: all fields must be set
      return selectedLab && selectedDate && selectedTimeSlot && selectedComputerId && selectedPurpose;
    }
    return true;
  }
  // Step 2: Load time slots
  function loadTimeSlots() {
    timeSlotsList.innerHTML = '';
    timeSlotsLoading.style.display = 'block';
    noTimeSlotsMessage.style.display = 'none';
    selectedTimeSlot = '';
    selectedTimeSlotLabel = '';
    
    // Store the selected lab in localStorage for persistence across refreshes
    if (selectedLab) {
      localStorage.setItem('selectedLabId', selectedLab);
    }
    
    fetch(`/get_available_time_slots?lab_id=${selectedLab}&date=${selectedDate}`)
      .then(res => res.json())
      .then(data => {
        timeSlotsLoading.style.display = 'none';
        
        if (data.success && data.time_slots && data.time_slots.length > 0) {
          // Display only the slots returned from the server
          data.time_slots.forEach(slot => {
            const slotLabel = `${slot.start_time} - ${slot.end_time}`;
            const isAvailable = slot.status === 'Available';
            
            const btn = document.createElement('button');
            btn.className = 'time-slot-btn';
            
            if (isAvailable) {
              btn.innerHTML = `✅ ${slotLabel} (Available)`;
              btn.style.backgroundColor = '#e8f5e9';
              btn.style.color = '#2e7d32';
              btn.disabled = false;
            } else {
              btn.innerHTML = `⛔ ${slotLabel} (Unavailable)`;
              btn.style.backgroundColor = '#ffebee';
              btn.style.color = '#c62828';
              btn.disabled = true;
            }
            
            btn.setAttribute('data-value', slotLabel);
            btn.onclick = () => {
              if (btn.disabled) return;
              selectedTimeSlot = slotLabel;
              selectedTimeSlotLabel = slotLabel;
              Array.from(timeSlotsList.children).forEach(b => b.classList.remove('selected'));
              btn.classList.add('selected');
              updateSummary();
            };
            timeSlotsList.appendChild(btn);
          });
        } else {
          noTimeSlotsMessage.style.display = 'block';
        }
      })
      .catch(error => {
        console.error('Error loading time slots:', error);
        timeSlotsLoading.style.display = 'none';
        noTimeSlotsMessage.style.display = 'block';
      });
  }
  // Step 3: Load computers
  function loadComputers() {
    computersGrid.innerHTML = '';
    computersLoading.style.display = 'block';
    noComputersMessage.style.display = 'none';
    selectedComputerId = '';
    selectedComputerLabel = '';
    fetch(`/get_available_computers?lab_id=${selectedLab}`)
      .then(res => res.json())
      .then(data => {
        computersLoading.style.display = 'none';
        // Show all computers, not just available
        const totalPCs = 50; // Changed from 20 to 50 to match the database (50 computers per lab)
        const allPCs = Array.from({ length: totalPCs }, (_, i) => i + 1);
        const available = (data.success && data.computers) ? data.computers.map(pc => pc.computer_number) : [];
        if (allPCs.length > 0) {
          allPCs.forEach(num => {
            let status = 'Unavailable';
            let color = '#ccc';
            let icon = '⛔';
            if (available.includes(num)) {
              status = 'Available';
              color = '#43a047';
              icon = '✔️';
            } else if (data.computers && data.computers.some(pc => pc.computer_number === num && pc.status === 'In Use')) {
              status = 'In Use';
              color = '#e53935';
              icon = '❌';
            }
            const btn = document.createElement('button');
            btn.className = 'computer-btn';
            btn.textContent = `${icon} PC #${num} (${status})`;
            btn.style.backgroundColor = status === 'Available' ? '#e8f5e9' : (status === 'In Use' ? '#ffebee' : '#f5f5f5');
            btn.style.color = status === 'Available' ? '#2e7d32' : (status === 'In Use' ? '#c62828' : '#888');
            btn.disabled = status !== 'Available';
            btn.setAttribute('data-id', num);
            btn.onclick = () => {
              if (btn.disabled) return;
              selectedComputerId = num;
              selectedComputerLabel = btn.textContent;
              Array.from(computersGrid.children).forEach(b => b.classList.remove('selected'));
              btn.classList.add('selected');
              updateSummary();
            };
            computersGrid.appendChild(btn);
          });
        } else {
          noComputersMessage.style.display = 'block';
        }
      })
      .catch(() => {
        computersLoading.style.display = 'none';
        noComputersMessage.style.display = 'block';
      });
  }
  // Step 4: Update summary
  function updateSummary() {
    summaryLab.textContent = labSelect.options[labSelect.selectedIndex]?.text || '-';
    summaryDate.textContent = selectedDate || '-';
    summaryTimeSlot.textContent = selectedTimeSlotLabel || '-';
    summaryComputer.textContent = selectedComputerLabel || '-';
    summaryPurpose.textContent = purposeSelect.value || '-';
  }
  // Submit reservation
  function submitReservation() {
    // Get the form data from the modal elements
    const labId = document.getElementById('modal_lab_id').value;
    const reservationDate = document.getElementById('modal_reservation_date').value;
    const purpose = document.getElementById('modal_purpose').value;
    const timeSlot = selectedTimeSlot;
    const computerId = selectedComputerId;
    
    // Validate each field individually for better error reporting
    let errorMessage = '';
    
    if (!labId) {
      errorMessage = 'Please select a laboratory';
    } else if (!reservationDate) {
      errorMessage = 'Please select a date';
    } else if (!purpose) {
      errorMessage = 'Please select a purpose';
    } else if (!timeSlot) {
      errorMessage = 'Please select a time slot';
    } else if (!computerId) {
      errorMessage = 'Please select an available computer';
    }
    
    if (errorMessage) {
      showErrorMessage(errorMessage);
      return;
    }
    
    // Show loading state
    const submitButton = document.getElementById('submitReservationBtn');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    // Create the request data
    const requestData = {
      lab_id: labId,
      reservation_date: reservationDate,
      purpose: purpose,
      time_slot: timeSlot,
      computer_id: computerId
    };
    
    console.log('Submitting reservation with data:', requestData);
    
    // Submit the reservation
    fetch('/create_student_reservation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    })
    .then(response => {
      if (!response.ok) {
        // Try to get the error message from the response
        return response.json().then(data => {
          throw new Error(data.message || 'Failed to create reservation');
        });
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        // Close the modal
        closeReservationModal();
        
        // Show success message with SweetAlert if available
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: 'Your reservation was created successfully.',
            confirmButtonColor: '#7c4dff'
          }).then(() => {
            // Reload the reservations table
            loadStudentReservations();
          });
        } else {
          alert('Reservation created successfully!');
          loadStudentReservations();
        }
      } else {
        showErrorMessage(data.message || 'Failed to create reservation');
      }
    })
    .catch(error => {
      console.error('Error creating reservation:', error);
      showErrorMessage(error.message || 'An unexpected error occurred');
    })
    .finally(() => {
      // Reset button state
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    });
  }

  function showErrorMessage(message) {
    // Show error with SweetAlert if available
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: message,
        confirmButtonColor: '#7c4dff'
      });
    } else {
      // Fallback to basic alert
      alert(message);
    }
  }

  // Load reservations table with improved error handling
  function loadStudentReservations() {
    const reservationsTableBody = document.getElementById('studentReservationsBody');
    const noReservationsMessage = document.getElementById('noReservationsMessage');
        
    if (!reservationsTableBody) {
      console.error('Student reservations table body element not found');
      return;
    }
        
    // Show loading state
    if (reservationsTableBody) {
      reservationsTableBody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center">
            <div class="loading-spinner">
              <i class="fas fa-spinner fa-spin"></i> Loading reservations...
            </div>
          </td>
        </tr>
      `;
    }
        
    fetch('/get_student_reservations', {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
      .then(res => {
        if (!res.ok) {
          throw new Error(`Server responded with status ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        // Clear the loading state
        reservationsTableBody.innerHTML = '';
        
        if (data.success && data.reservations && data.reservations.length > 0) {
          if (noReservationsMessage) {
            noReservationsMessage.style.display = 'none';
          }
          
          data.reservations.forEach(r => {
            const tr = document.createElement('tr');
            // Store reservation data for later access
            tr.setAttribute('data-reservation', JSON.stringify(r));
            
            // Create action buttons for pending reservations
            let actionsHtml = '';
            if (r.status === 'Pending') {
              const reservationId = r.id;
              
              actionsHtml = `
                <div class="action-buttons">
                  <button class="action-btn edit" onclick="openActionModal(${reservationId})" title="Edit Purpose">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button class="action-btn delete" onclick="deleteReservation(${reservationId})" title="Delete Reservation">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              `;
            } else {
              actionsHtml = `<span>-</span>`;
            }
            
            tr.innerHTML = `
              <td>${r.lab_name || '-'}</td>
              <td>${r.computer_number ? 'PC #' + r.computer_number : '-'}</td>
              <td>${r.reservation_date || '-'}</td>
              <td>${r.time_slot || '-'}</td>
              <td>${r.purpose || '-'}</td>
            <td><span class="status-badge status-${(r.status || 'unknown').toLowerCase()}">${r.status || 'Unknown'}</span></td>
              <td>${actionsHtml}</td>
            `;
            reservationsTableBody.appendChild(tr);
          });
        } else {
          // Show no reservations message
          if (noReservationsMessage) {
            noReservationsMessage.style.display = 'block';
          } else {
            reservationsTableBody.innerHTML = `
              <tr>
                <td colspan="7" class="text-center">
                  <div class="no-data-message">
                  <i class="fas fa-calendar-times"></i>
                  <p>You don't have any reservations yet.</p>
                  </div>
                </td>
              </tr>
            `;
          }
        }
      })
      .catch(error => {
        console.error('Error loading reservations:', error);
      
      // Show error message in the table
        reservationsTableBody.innerHTML = `
          <tr>
          <td colspan="7" class="text-center">
              <div class="error-message">
              <i class="fas fa-exclamation-triangle"></i>
              <p>Error loading reservations. ${error.message || ''}</p>
              <button onclick="loadStudentReservations()" class="btn primary">
                <i class="fas fa-sync"></i> Try Again
              </button>
              </div>
            </td>
          </tr>
        `;
      });
  }
  // Initial load
  if (reservationsTableBody) loadStudentReservations();
});

// SIMPLIFIED ACTION MODALS
// Show a simple edit modal dialog
window.showEditModal = function(reservationId, currentPurpose) {
  // Create a modal HTML string
  const modalHtml = `
    <div class="simple-modal">
      <div class="simple-modal-content">
        <h3>Edit Reservation Purpose</h3>
        <p>Please select a new purpose for your reservation:</p>
        <select id="edit_purpose_select" class="form-select">
          <option value="Assignment" ${currentPurpose === 'Assignment' ? 'selected' : ''}>Assignment</option>
          <option value="Project" ${currentPurpose === 'Project' ? 'selected' : ''}>Project</option>
          <option value="Study" ${currentPurpose === 'Study' ? 'selected' : ''}>Study</option>
          <option value="Research" ${currentPurpose === 'Research' ? 'selected' : ''}>Research</option>
          <option value="Practice" ${currentPurpose === 'Practice' ? 'selected' : ''}>Practice</option>
          <option value="Other" ${currentPurpose === 'Other' ? 'selected' : ''}>Other</option>
        </select>
        <div class="simple-modal-actions">
          <button onclick="cancelEdit()" class="btn cancel">Cancel</button>
          <button onclick="saveEdit(${reservationId})" class="btn primary">Save Changes</button>
        </div>
      </div>
    </div>
  `;
  
  // Append the modal to the body
  const modalContainer = document.createElement('div');
  modalContainer.id = 'edit-modal-container';
  modalContainer.innerHTML = modalHtml;
  document.body.appendChild(modalContainer);
};

// Cancel the edit operation
window.cancelEdit = function() {
  const modalContainer = document.getElementById('edit-modal-container');
  if (modalContainer) {
    document.body.removeChild(modalContainer);
  }
};

// Save the edited purpose
window.saveEdit = function(reservationId) {
  const purposeSelect = document.getElementById('edit_purpose_select');
  const newPurpose = purposeSelect.value;
  
  // Show loading state
  const saveButton = document.querySelector('.simple-modal-actions .btn.primary');
  if (saveButton) {
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveButton.disabled = true;
  }
  
  // Send API request to update the reservation
  fetch('/update_student_reservation', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      reservation_id: reservationId,
      purpose: newPurpose
    })
  })
  .then(response => response.json())
  .then(data => {
    // Remove the modal
    cancelEdit();
    
    if (data.success) {
      // Show success message
      showSuccessMessage(data.message || 'Purpose updated successfully');
      // Refresh the page instead of just reloading the reservations
      window.location.reload();
    } else {
      // Show error message
      showErrorMessage(data.message || 'Failed to update purpose');
    }
  })
  .catch(error => {
    console.error('Error updating reservation:', error);
    showErrorMessage('Failed to update reservation');
    cancelEdit();
    // Refresh the page anyway to ensure data consistency
    window.location.reload();
  });
};

// Show delete confirmation dialog
window.showDeleteConfirmation = function(reservationId) {
  // Create a modal HTML string
  const modalHtml = `
    <div class="simple-modal">
      <div class="simple-modal-content">
        <h3>Delete Reservation</h3>
        <p>Are you sure you want to delete this reservation? This action cannot be undone.</p>
        <div class="simple-modal-actions">
          <button onclick="cancelDelete()" class="btn cancel">Cancel</button>
          <button onclick="confirmDelete(${reservationId})" class="btn danger">Delete</button>
        </div>
      </div>
    </div>
  `;
  
  // Append the modal to the body
  const modalContainer = document.createElement('div');
  modalContainer.id = 'delete-modal-container';
  modalContainer.innerHTML = modalHtml;
  document.body.appendChild(modalContainer);
};

// Cancel the delete operation
window.cancelDelete = function() {
  const modalContainer = document.getElementById('delete-modal-container');
  if (modalContainer) {
    document.body.removeChild(modalContainer);
  }
};

// Confirm and process the deletion
window.confirmDelete = function(reservationId) {
  // Show loading state
  const deleteButton = document.querySelector('.simple-modal-actions .btn.danger');
  if (deleteButton) {
    deleteButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    deleteButton.disabled = true;
  }
  
  // Send API request to delete the reservation
  fetch(`/delete_student_reservation/${reservationId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => response.json())
  .then(data => {
    // Remove the modal
    cancelDelete();
    
    if (data.success) {
      // Show success message
      showSuccessMessage(data.message || 'Reservation deleted successfully');
      // Refresh the page instead of just reloading the reservations
      window.location.reload();
    } else {
      // Show error message
      showErrorMessage(data.message || 'Failed to delete reservation');
    }
  })
  .catch(error => {
    console.error('Error deleting reservation:', error);
    showErrorMessage('Failed to delete reservation');
    cancelDelete();
    // Refresh the page anyway to ensure data consistency
    window.location.reload();
  });
};

// Helper function to show success messages
function showSuccessMessage(message) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      icon: 'success',
      title: 'Success',
      text: message,
      confirmButtonColor: '#7c4dff'
    });
  } else {
    alert(message);
  }
}

// Delete reservation using SweetAlert confirmation
function deleteReservation(reservationId) {
  Swal.fire({
    title: 'Are you sure?',
    text: "You won't be able to revert this reservation!",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#7c4dff',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Yes, delete it!',
    cancelButtonText: 'Cancel'
  }).then((result) => {
    if (result.isConfirmed) {
      // Show loading indicator
      Swal.fire({
        title: 'Deleting...',
        text: 'Please wait while we process your request',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        willOpen: () => {
          Swal.showLoading();
        }
      });
      
      // Proceed with deletion
      fetch(`/delete_student_reservation/${reservationId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          Swal.fire({
            title: 'Deleted!',
            text: 'Your reservation has been deleted.',
            icon: 'success',
            confirmButtonColor: '#7c4dff'
          }).then(() => {
            // Refresh the entire page for better UX
            window.location.reload();
          });
        } else {
          throw new Error(data.message || 'Failed to delete reservation');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        
        // Check if it's a network error
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
          Swal.fire({
            title: 'Network Error',
            text: 'Could not connect to the server. Please check your internet connection.',
            icon: 'error',
            confirmButtonColor: '#7c4dff'
          }).then(() => {
            // Refresh the page to get the latest data anyway
            window.location.reload();
          });
        } else {
          Swal.fire({
            title: 'Error!',
            text: error.message || 'An error occurred while deleting the reservation.',
            icon: 'error',
            confirmButtonColor: '#7c4dff'
          }).then(() => {
            // Refresh the page to get the latest data anyway
            window.location.reload();
          });
        }
      });
    }
  });
}

// Toggle purpose editing with better UI
function toggleEditPurpose() {
  const purposeText = document.getElementById('action_purpose_text');
  const purposeSelect = document.getElementById('action_purpose');
  const editBtn = document.getElementById('editPurposeBtn');
  const saveBtn = document.getElementById('saveChangesBtn');
  
  // Add transition effect
  purposeText.style.opacity = '0';
  setTimeout(() => {
    purposeText.style.display = 'none';
    purposeSelect.style.display = 'block';
    purposeSelect.style.opacity = '0';
    setTimeout(() => {
      purposeSelect.style.opacity = '1';
    }, 50);
  }, 200);
  
  editBtn.style.display = 'none';
  saveBtn.style.display = 'inline-flex';
  
  // Set the current purpose as selected
  const currentPurpose = purposeText.textContent.trim();
  const options = purposeSelect.options;
  for (let i = 0; i < options.length; i++) {
    if (options[i].value === currentPurpose) {
      purposeSelect.selectedIndex = i;
      break;
    }
  }
}

// Save reservation changes with improved UX and error handling
function saveReservationChanges() {
  const reservationId = document.getElementById('current_reservation_id').value;
  const newPurpose = document.getElementById('action_purpose').value;
  
  if (!newPurpose) {
    Swal.fire({
      icon: 'error',
      title: 'Error',
      text: 'Please select a purpose',
      confirmButtonColor: '#7c4dff'
    });
    return;
  }
  
  // Show loading state
  const saveBtn = document.getElementById('saveChangesBtn');
  saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
  saveBtn.disabled = true;
  
  fetch('/update_student_reservation', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    },
    body: JSON.stringify({
      reservation_id: reservationId,
      purpose: newPurpose
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      // Show success toast
      Swal.fire({
        icon: 'success',
        title: 'Success!',
        text: 'Your reservation has been updated.',
        confirmButtonColor: '#7c4dff'
      }).then(() => {
        // Close the modal and refresh the page for better UX
        closeActionModal();
        window.location.reload();
      });
    } else {
      throw new Error(data.message || 'Failed to update reservation');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    
    // Reset button state
    saveBtn.innerHTML = 'Save Changes';
    saveBtn.disabled = false;
    
    // Check if it's a network error
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      Swal.fire({
        title: 'Network Error',
        text: 'Could not connect to the server. Please check your internet connection.',
        icon: 'error',
        confirmButtonColor: '#7c4dff'
      }).then(() => {
        closeActionModal();
        // Refresh the page to get the latest data anyway
        window.location.reload();
      });
    } else {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: error.message || 'An error occurred while updating the reservation.',
        confirmButtonColor: '#7c4dff'
      }).then(() => {
        // Close the modal and refresh the page if there was an error
        closeActionModal();
        window.location.reload();
      });
    }
  });
}

// Open the modal with better styling and improved error handling
function openActionModal(reservationId) {
  const modal = document.getElementById('reservationActionModal');
  if (!modal) {
    console.error('Reservation action modal element not found');
    return;
  }
  
  // Show loading state
  Swal.fire({
    title: 'Loading...',
    text: 'Fetching reservation details',
    allowOutsideClick: false,
    allowEscapeKey: false,
    showConfirmButton: false,
    willOpen: () => {
      Swal.showLoading();
    }
  });
  
  fetch(`/get_reservation/${reservationId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      // Close loading dialog
      Swal.close();
      
      if (data.success) {
        // Fill in reservation details
        document.getElementById('action_lab').textContent = data.reservation.lab_name || '-';
        document.getElementById('action_date').textContent = data.reservation.reservation_date || '-';
        document.getElementById('action_time').textContent = data.reservation.time_slot || '-';
        document.getElementById('action_computer').textContent = data.reservation.computer_name || '-';
        document.getElementById('action_purpose_text').textContent = data.reservation.purpose || '-';
        document.getElementById('current_reservation_id').value = reservationId;
        
        // Reset UI state
        document.getElementById('action_purpose').style.display = 'none';
        document.getElementById('action_purpose_text').style.display = 'block';
        document.getElementById('action_purpose_text').style.opacity = '1';
        document.getElementById('editPurposeBtn').style.display = 'inline-flex';
        document.getElementById('saveChangesBtn').style.display = 'none';
        
        // Show modal with animation
        modal.classList.add('animate-fade-in');
        modal.style.display = 'flex';
        
        // Add click event to close modal when clicking overlay
        const overlay = modal.querySelector('.modal-overlay');
        if (overlay) {
          overlay.onclick = closeActionModal;
        }
        
        // Add escape key listener
        document.addEventListener('keydown', function escKeyHandler(e) {
          if (e.key === 'Escape') {
            closeActionModal();
            document.removeEventListener('keydown', escKeyHandler);
          }
        });
      } else {
        throw new Error(data.message || 'Failed to load reservation details');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      
      // Check if it's a network error
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        Swal.fire({
          title: 'Network Error',
          text: 'Could not connect to the server. Please check your internet connection.',
          icon: 'error',
          confirmButtonColor: '#7c4dff'
        });
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: error.message || 'Failed to load reservation details.',
          confirmButtonColor: '#7c4dff'
        });
      }
    });
}

// Close the modal with animation
function closeActionModal() {
  const modal = document.getElementById('reservationActionModal');
  if (!modal) return;
  
  modal.classList.add('animate-fade-out');
  setTimeout(() => {
    modal.style.display = 'none';
    modal.classList.remove('animate-fade-in', 'animate-fade-out');
  }, 300);
}

/**
 * Handle reservation notifications 
 */
function loadReservationNotifications() {
  fetch('/api/student/notifications')
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch notifications');
        }
        return response.json();
    })
    .then(data => {
          if (data.success) {
            updateNotificationsUI(data.notifications);
        }
    })
    .catch(error => {
        console.error('Error loading notifications:', error);
    });
}

/**
 * Update the notifications UI with the provided notifications
 */
function updateNotificationsUI(notifications) {
    const notificationItems = document.getElementById('notificationItems');
    if (!notificationItems) return;
    
    // Clear existing notifications
    notificationItems.innerHTML = '';
    
    if (!notifications || notifications.length === 0) {
        notificationItems.innerHTML = `
            <div class="notification-empty">
                <i class="fas fa-bell-slash"></i>
                <p>No notifications</p>
            </div>
        `;
        return;
    }
    
    // Add each notification to the dropdown
    notifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.classList.add('notification-item');
        notificationItem.setAttribute('data-id', notification.id);
        
        if (!notification.is_read) {
            notificationItem.classList.add('unread');
        }
        
        // Set notification icon based on type
        let iconClass = 'fas fa-bell';
        if (notification.notification_type === 'status_update') {
            iconClass = 'fas fa-sync';
        } else if (notification.notification_type === 'upcoming') {
            iconClass = 'fas fa-clock';
        } else if (notification.notification_type === 'system') {
            iconClass = 'fas fa-exclamation-circle';
        }
        
        // Add reservation type badge if applicable
        let reservationTypeBadge = '';
        if (notification.details && notification.details.reservation_type) {
            const type = notification.details.reservation_type;
            const badgeClass = type === 'sitin' ? 'type-sitin' : 'type-reservation';
            const typeLabel = type === 'sitin' ? 'Sit-in' : 'Reservation';
            reservationTypeBadge = `<span class="reservation-type-badge ${badgeClass}">${typeLabel}</span>`;
        }
        
        notificationItem.innerHTML = `
            <div class="notification-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">
                    ${notification.title}
                    ${reservationTypeBadge}
                </div>
                <div class="notification-text">${notification.message}</div>
                <div class="notification-time">${formatDateTime(notification.created_at)}</div>
            </div>
        `;
        
        // Add click event to mark notification as read
        notificationItem.addEventListener('click', () => {
            markNotificationAsRead(notification.id);
        });
        
        notificationItems.appendChild(notificationItem);
    });
    
    // Update notification count
    updateNotificationCount();
}

/**
 * Mark a notification as read
 */
function markNotificationAsRead(notificationId) {
    fetch('/api/student/notifications/read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notification_id: notificationId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove unread class from the notification item
            const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.classList.remove('unread');
                updateNotificationCount();
            }
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

/**
 * Mark all notifications as read
 */
function markAllNotificationsAsRead() {
    fetch('/api/student/notifications/read-all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove unread class from all notification items
          document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationCount();
        }
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
}

/**
 * Update the notification count badge
 */
function updateNotificationCount() {
    const unreadCount = document.querySelectorAll('.notification-item.unread').length;
    const notificationBadge = document.getElementById('notificationBadge');
    
    if (notificationBadge) {
        if (unreadCount > 0) {
            notificationBadge.textContent = unreadCount;
            notificationBadge.style.display = 'block';
        } else {
            notificationBadge.textContent = '0';
            notificationBadge.style.display = 'none';
        }
    }
}

/**
 * Format a date string to a more readable format
 */
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return 'Unknown';
    
    const date = new Date(dateTimeStr);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
        return 'Just now';
    } else if (diffMin < 60) {
        return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
        return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    } else if (diffDay < 7) {
        return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    } else {
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString(undefined, options);
    }
}

/**
* Set up socket.io event listeners for reservation notifications
 */
function setupReservationNotifications() {
  // Check if socket.io is available
    if (typeof socket === 'undefined') {
      console.error('Socket.io not initialized');
        return;
    }
    
  // Listen for reservation status updates
  socket.on('reservation_status_updated', function(data) {
      // First check if this notification is for the current student
        if (data.student_idno === currentStudentId) {
          // Show a notification
          showReservationNotification(data.title, data.message);
          
          // Refresh notifications list
          loadReservationNotifications();
          
          // Refresh reservations if on the reservations page
          if (document.getElementById('reservation-student').style.display === 'block') {
              loadStudentReservations();
          }
      }
  });
  
  // Listen for upcoming reservation notifications
  socket.on('reservation_upcoming', function(data) {
      if (data.student_idno === currentStudentId) {
                showReservationNotification(data.title, data.message);
          loadReservationNotifications();
        }
    });
    
  // Listen for reservation ended notifications
  socket.on('reservation_ended', function(data) {
        if (data.student_idno === currentStudentId) {
          showReservationNotification(data.title, data.message);
            loadReservationNotifications();
          
          // Refresh reservations if on the reservations page
          if (document.getElementById('reservation-student').style.display === 'block') {
              loadStudentReservations();
          }
        }
    });
}

/**
 * Show a notification using SweetAlert2
 */
function showReservationNotification(title, message, details = {}) {
    // Prepare the type badge if available
    let typeBadge = '';
    if (details.reservation_type) {
        const type = details.reservation_type;
        const badgeClass = type === 'sitin' ? 'type-sitin' : 'type-reservation';
        const typeLabel = type === 'sitin' ? 'Sit-in' : 'Reservation';
        typeBadge = `<span class="reservation-type-badge ${badgeClass}">${typeLabel}</span>`;
    }
    
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: `${title} ${typeBadge}`,
            html: message,
            icon: 'info',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 5000,
            timerProgressBar: true,
            customClass: {
                popup: 'swal-notification-popup'
            }
        });
    } else {
        // Fallback to alert if SweetAlert2 is not available
        alert(`${title}: ${message}`);
    }
    
    // Also trigger a refresh of the notifications list
    loadReservationNotifications();
}

/**
 * Update the current sit in section to show reservation type
 */
function updateCurrentSitInSection() {
    // This could be expanded based on your actual UI needs
    const sitInTab = document.querySelector('[data-section="sit-in"]');
    if (sitInTab) {
        // Add badges to show reservation type in the sit-in table
        document.querySelectorAll('#reservations-table tbody tr').forEach(row => {
            const typeCell = document.createElement('td');
            const isReservation = row.getAttribute('data-is-reservation') === 'true';
            
            if (isReservation) {
                typeCell.innerHTML = '<span class="reservation-badge">Reservation</span>';
            } else {
                typeCell.innerHTML = '<span class="sit-in-badge">Sit In</span>';
            }
            
            // Insert after status column
            const statusCell = row.querySelector('td:nth-child(8)');
            if (statusCell) {
                statusCell.parentNode.insertBefore(typeCell, statusCell.nextSibling);
            }
        });
    }
}

// Initialize the notifications system when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup for existing functionality
    
    // Load notifications
    loadReservationNotifications();
    
    // Setup socket.io notification listeners
    setupReservationNotifications();
    
    // Mark all as read button
    const markAllReadBtn = document.getElementById('markAllRead');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(event) {
            event.stopPropagation();
            markAllNotificationsAsRead();
        });
    }
    
    // Update sit-in/reservation tables when the tab is clicked
    const sitInTab = document.querySelector('[data-section="sit-in"]');
    if (sitInTab) {
        sitInTab.addEventListener('click', function() {
            setTimeout(updateCurrentSitInSection, 500); // Wait for the table to load
        });
    }
});

// Initialize notification functionality for the modal
document.addEventListener('DOMContentLoaded', function () {
    // View all notifications button event
    const viewAllNotificationsBtn = document.getElementById('viewAllNotifications');
    const notificationsModal = document.getElementById('notificationsModal');
    const closeNotificationsModalBtn = document.getElementById('closeNotificationsModal');
    const markAllReadModalBtn = document.getElementById('markAllReadModal');
    
    if (viewAllNotificationsBtn) {
        viewAllNotificationsBtn.addEventListener('click', function() {
            loadAllNotifications();
            notificationsModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    }

    if (closeNotificationsModalBtn) {
        closeNotificationsModalBtn.addEventListener('click', function() {
            notificationsModal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Restore scrolling
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === notificationsModal) {
            notificationsModal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Restore scrolling
        }
    });

    if (markAllReadModalBtn) {
        markAllReadModalBtn.addEventListener('click', function() {
            markAllNotificationsAsRead();
        });
    }
});

/**
 * Load all notifications for the modal view
 */
function loadAllNotifications() {
    const notificationsContainer = document.getElementById('notificationsModalList');
    
    if (!notificationsContainer) {
        console.error('Notifications container not found');
        return;
    }
    
    // Show loading indicator
    notificationsContainer.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
            <p>Loading notifications...</p>
        </div>
    `;
    
    // Fetch all notifications (including read ones)
    // Set include_read=true to get all notifications, not just unread ones
    fetch('/api/student/notifications?limit=100&include_read=true', {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch notifications');
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.notifications) {
            displayAllNotifications(data.notifications);
        } else {
            notificationsContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                    <p>No notifications found</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading notifications:', error);
        notificationsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                <p>Failed to load notifications</p>
            </div>
        `;
    });
}

/**
 * Display all notifications in the modal
 * @param {Array} notifications - List of notifications
 */
function displayAllNotifications(notifications) {
    const modalList = document.getElementById('notificationsModalList');
    
    if (!modalList) {
        console.error('Notifications modal list container not found');
        return;
    }
    
    if (!notifications || notifications.length === 0) {
        modalList.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-bell-slash fa-3x text-muted mb-3"></i>
                <p>No notifications to display</p>
            </div>
        `;
        return;
    }
    
    modalList.innerHTML = '';
    
    notifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.className = `notification-modal-item ${notification.is_read ? '' : 'unread'}`;
        notificationItem.dataset.id = notification.id;
        
        const currentTime = new Date().toISOString();
        const timestamp = notification.created_at || currentTime;
        
        notificationItem.innerHTML = `
            <div class="notification-modal-icon">
                <i class="fas fa-${getNotificationIcon(notification.notification_type)}"></i>
            </div>
            <div class="notification-modal-content">
                <div class="notification-modal-title">${notification.title}</div>
                <div class="notification-modal-text">${notification.message}</div>
                <div class="notification-modal-time" data-timestamp="${timestamp}">${formatTimeAgo(timestamp)}</div>
            </div>
        `;
        
        notificationItem.addEventListener('click', () => {
            if (!notification.is_read) {
                markNotificationAsRead(notification.id);
                notificationItem.classList.remove('unread');
            }
        });
        
        modalList.appendChild(notificationItem);
    });
}

/**
 * Format notification date for display
 * @param {Date} date - The notification date
 * @returns {string} - Formatted date string
 */
function formatTimeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const secondsAgo = Math.floor((now - date) / 1000);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
        return 'Invalid date';
    }

    // Less than a minute
    if (secondsAgo < 60) {
        return 'Just now';
    }
    
    // Less than an hour
    if (secondsAgo < 3600) {
        const minutes = Math.floor(secondsAgo / 60);
        return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    }
    
    // Less than a day
    if (secondsAgo < 86400) {
        const hours = Math.floor(secondsAgo / 3600);
        return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    }
    
    // Less than a week
    if (secondsAgo < 604800) {
        const days = Math.floor(secondsAgo / 86400);
        return `${days} ${days === 1 ? 'day' : 'days'} ago`;
    }
    
    // For older dates, return the actual date
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
        day: 'numeric'
    });
}

// Helper function to get notification icon based on type
function getNotificationIcon(type) {
  switch(type) {
    case 'status_update':
      return 'sync';
    case 'upcoming':
      return 'clock';
    case 'start_time':
      return 'play-circle';
    case 'end_time':
      return 'stop-circle';
    case 'system':
      return 'exclamation-circle';
    case 'sit_in':
      return 'chair';
    default:
      return 'bell';
    }
}