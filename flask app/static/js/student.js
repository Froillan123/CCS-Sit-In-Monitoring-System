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