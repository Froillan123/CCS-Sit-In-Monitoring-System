// Lab Resources Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const resourcesContainer = document.querySelector('.resources-container');
    const resourceModal = document.querySelector('.resource-modal');
    const labSchedulesModal = document.querySelector('.lab-schedules-modal');
    
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
                            th, td { padding: 10px; text-align: center; border: 1px solid #ddd; }
                            th { background-color: #f5f5f5; }
                            .time-slot { background-color: #f9f9f9; font-weight: bold; }
                            .empty-slot { background-color: #e8f5e9; }
                            .class-slot { background-color: #ffebee; }
                            .legend { display: flex; justify-content: center; gap: 30px; margin-top: 20px; }
                            .legend-item { display: flex; align-items: center; gap: 5px; }
                            .legend-color { width: 16px; height: 16px; border-radius: 3px; }
                            .legend-color.empty-slot { background-color: #e8f5e9; border: 1px solid #c8e6c9; }
                            .legend-color.class-slot { background-color: #ffebee; border: 1px solid #ffcdd2; }
                            @media print {
                                @page { size: landscape; }
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
                                <span class="legend-color empty-slot"></span>
                                <span>Available</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-color class-slot"></span>
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
}

/**
 * Load the schedule for a specific lab
 */
function loadLabSchedule(labId) {
    // Get the schedule container for this lab
    const scheduleContainer = document.getElementById(`lab${labId}-schedule`);
    if (!scheduleContainer) return;
    
    // Get the table body
    const tableBody = scheduleContainer.querySelector('tbody');
    if (!tableBody) return;
    
    // Create loading indicator
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align: center; padding: 40px;">
                <div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">
                    <div class="spinner" style="border: 4px solid rgba(0, 0, 0, 0.1); width: 36px; height: 36px; border-radius: 50%; border-left-color: #7c4dff; animation: spin 1s linear infinite;"></div>
                    <p style="margin-top: 15px;">Loading lab schedule...</p>
                </div>
            </td>
        </tr>
    `;
    
    // Define time slots
    const timeSlots = [
        "07:00 - 08:30", "08:30 - 10:00", "10:00 - 11:30", "11:30 - 13:00", 
        "13:00 - 14:30", "14:30 - 16:00", "16:00 - 17:30", "17:30 - 19:00", 
        "19:00 - 21:00"
    ];
    
    // Define weekdays
    const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    
    // Initialize the schedule grid
    let scheduleGrid = {};
    timeSlots.forEach(timeSlot => {
        scheduleGrid[timeSlot] = {};
        weekdays.forEach(day => {
            scheduleGrid[timeSlot][day] = {
                status: "Available",
                subject: null
            };
        });
    });
    
    // Fetch the lab schedules from the API
    fetchLabSchedules(labId)
        .then(schedules => {
            // Process the schedules and update the grid
            schedules.forEach(schedule => {
                const day = schedule.day_of_week;
                const timeSlot = `${schedule.start_time} - ${schedule.end_time}`;
                
                // If this time slot is in our grid
                if (scheduleGrid[timeSlot] && scheduleGrid[timeSlot][day]) {
                    scheduleGrid[timeSlot][day] = {
                        status: schedule.status,
                        subject: schedule.subject_name || schedule.subject_code,
                        reason: schedule.reason
                    };
                }
            });
            
            // Build the HTML table
            let tableHtml = '';
            timeSlots.forEach(timeSlot => {
                tableHtml += `<tr>
                    <td class="time-slot">${timeSlot}</td>`;
                
                weekdays.forEach(day => {
                    const cell = scheduleGrid[timeSlot][day];
                    const isAvailable = cell.status === 'Available';
                    const cellClass = isAvailable ? 'empty-slot' : 'class-slot';
                    const cellContent = isAvailable ? 'Available' : (cell.subject || cell.reason || 'Reserved');
                    
                    tableHtml += `<td class="${cellClass}">${cellContent}</td>`;
                });
                
                tableHtml += `</tr>`;
            });
            
            // Update the table
            tableBody.innerHTML = tableHtml;
            
            // Add hover effects to the cells
            const cells = tableBody.querySelectorAll('td:not(.time-slot)');
            cells.forEach(cell => {
                cell.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.05)';
                    this.style.zIndex = '1';
                });
                
                cell.addEventListener('mouseleave', function() {
                    this.style.transform = '';
                    this.style.zIndex = '';
                });
            });
        })
        .catch(error => {
            console.error(`Error loading schedule for lab ${labId}:`, error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: #d32f2f;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 24px; margin-bottom: 10px;"></i>
                        <p>Failed to load schedule. Please try again later.</p>
                    </td>
                </tr>
            `;
        });
}

/**
 * Fetch lab schedules from the API
 */
async function fetchLabSchedules(labId) {
    try {
        // Create a non-authenticated version of the API call
        const response = await fetch(`/api/student/lab_schedules/${labId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch lab schedules: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.schedules || [];
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (error) {
        console.error(`Error fetching lab schedules: ${error.message}`);
        return []; // Return empty array on error
    }
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
      if (!selectedLab || !selectedDate) {
        if (!selectedDate) dateError.style.display = 'block';
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
    fetch(`/get_available_time_slots?lab_id=${selectedLab}&date=${selectedDate}`)
      .then(res => res.json())
      .then(data => {
        timeSlotsLoading.style.display = 'none';
        // Show all possible slots, not just available
        const allSlots = [
          { start: '07:00', end: '08:30' },
          { start: '08:30', end: '10:00' },
          { start: '10:00', end: '11:30' },
          { start: '11:30', end: '13:00' },
          { start: '13:00', end: '14:30' },
          { start: '14:30', end: '16:00' },
          { start: '16:00', end: '17:30' },
          { start: '17:30', end: '19:00' },
          { start: '19:00', end: '21:00' }
        ];
        // Map available slots for quick lookup
        const available = (data.success && data.time_slots) ? data.time_slots.map(s => `${s.start_time} - ${s.end_time}`) : [];
        if (allSlots.length > 0) {
          allSlots.forEach(slot => {
            const slotLabel = `${slot.start} - ${slot.end}`;
            let status = 'Unavailable';
            let color = '#ccc';
            let icon = '⛔';
            if (available.includes(slotLabel)) {
              status = 'Available';
              color = '#43a047';
              icon = '✔️';
            } else if (data.time_slots && data.time_slots.some(s => s.time_slot === slotLabel && s.status === 'Reserved')) {
              status = 'Reserved';
              color = '#e53935';
              icon = '❌';
            }
            const btn = document.createElement('button');
            btn.className = 'time-slot-btn';
            btn.textContent = `${icon} ${slotLabel} (${status})`;
            btn.style.backgroundColor = status === 'Available' ? '#e8f5e9' : (status === 'Reserved' ? '#ffebee' : '#f5f5f5');
            btn.style.color = status === 'Available' ? '#2e7d32' : (status === 'Reserved' ? '#c62828' : '#888');
            btn.disabled = status !== 'Available';
            btn.setAttribute('data-value', slotLabel);
            btn.onclick = () => {
              if (btn.disabled) return;
              selectedTimeSlot = slotLabel;
              selectedTimeSlotLabel = btn.textContent;
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
      .catch(() => {
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
        const totalPCs = 20; // or fetch from backend if dynamic
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