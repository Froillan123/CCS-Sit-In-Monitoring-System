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

    const passwordAccess = (passwordFieldId, eyeIconId) => {
      const input = document.getElementById(passwordFieldId);
      const iconEye = document.getElementById(eyeIconId);

      console.log(`Input: ${passwordFieldId}`, input); // Debugging
      console.log(`Icon: ${eyeIconId}`, iconEye); // Debugging

      if (input && iconEye) {
          iconEye.addEventListener('click', () => {
              input.type = input.type === 'password' ? 'text' : 'password';
              iconEye.classList.toggle('ri-eye-fill');
              iconEye.classList.toggle('ri-eye-off-fill');
          });
      } else {
          console.error(`Element not found: ${passwordFieldId} or ${eyeIconId}`); // Debugging
      }
  };

  // Initialize password visibility toggles
  passwordAccess('login_password', 'loginPasswordEye'); // Login Password
  passwordAccess('reg_password', 'regPasswordEye'); // Registration Password
  passwordAccess('repeat_password', 'repeatPasswordEye'); // Repeat Password



});

const labData = {
  labels: ["Lab 544", "Lab 542", "Lab 530", "Lab 524", "Lab 526", "Lab 525"], // Lab names
  datasets: [{
      label: 'Sit-In Usage', // Updated label for the dataset
      data: [12, 19, 8, 15, 10, 7], // Example sit-in usage for each lab
      backgroundColor: [
          '#FF6384', // Lab 544
          '#36A2EB', // Lab 542
          '#FFCE56', // Lab 530
          '#4BC0C0', // Lab 524
          '#9966FF', // Lab 526
          '#FF9F40', // Lab 525
      ],
      borderColor: [
          '#FF6384',
          '#36A2EB',
          '#FFCE56',
          '#4BC0C0',
          '#9966FF',
          '#FF9F40',
      ],
      borderWidth: 0, // Remove border around bars
      borderRadius: 0, // Add border radius to bars
      hoverBackgroundColor: [
          '#FF6384', // Lab 544
          '#36A2EB', // Lab 542
          '#FFCE56', // Lab 530
          '#4BC0C0', // Lab 524
          '#9966FF', // Lab 526
          '#FF9F40', // Lab 525
      ],
      hoverBorderWidth: 0, // Add border on hover
      hoverBorderColor: '#fff', // White border on hover
  }]
};

// Chart configuration
const config = {
  type: 'bar', // Bar chart type
  data: labData,
  options: {
      responsive: true,
      maintainAspectRatio: false, // Allow chart to fit the container height
      scales: {
          y: {
              beginAtZero: true, // Start y-axis from 0
              grid: {
                  display: false, // Hide y-axis grid lines
              },
              title: {
                  display: true,
                  text: 'Sit-In Usage', // Updated y-axis label
                  font: {
                      size: 14,
                      weight: 'bold',
                  },
              },
              ticks: {
                  font: {
                      size: 12,
                  },
              },
          },
          x: {
              grid: {
                  display: false, // Hide x-axis grid lines
              },
              title: {
                  display: true,
                  text: 'Labs', // X-axis label
                  font: {
                      size: 14,
                      weight: 'bold',
                  },
              },
              ticks: {
                  font: {
                      size: 12,
                  },
              },
          },
      },
      plugins: {
          legend: {
              display: false, // Hide the legend
          },
          tooltip: {
              enabled: true, // Enable tooltips on hover
              backgroundColor: 'rgba(0, 0, 0, 0.8)', // Dark background for tooltips
              titleFont: {
                  size: 14,
                  weight: 'bold',
              },
              bodyFont: {
                  size: 12,
              },
              callbacks: {
                  title: (tooltipItems) => {
                      return tooltipItems[0].label; // Show lab name in tooltip title
                  },
                  label: (tooltipItem) => {
                      return `Sit-In Usage: ${tooltipItem.raw}`; // Updated tooltip label
                  },
              },
          },
      },
      animation: {
          duration: 1000, // Smooth animation duration
          easing: 'easeInOutQuart', // Smooth easing function
      },
  },
};

// Render the chart
const labUsageChart = new Chart(
  document.getElementById('labUsageChart'),
  config
);

// Adjust chart for smaller screens
const updateChartForSmallScreens = () => {
  const isSmallScreen = window.innerWidth <= 980;

  if (isSmallScreen) {
      labUsageChart.options.scales.x.display = false; // Hide x-axis labels
      labUsageChart.options.scales.y.title.display = false; // Hide y-axis title
  } else {
      labUsageChart.options.scales.x.display = true; // Show x-axis labels
      labUsageChart.options.scales.y.title.display = true; // Show y-axis title
  }

  labUsageChart.update(); // Update the chart
};

// Add event listener for window resize
window.addEventListener('resize', updateChartForSmallScreens);

// Initial check for screen size
updateChartForSmallScreens();


async function fetchActivityBreakdown() {
    try {
        console.log("Fetching activity breakdown data...");
        const response = await fetch('/activity_breakdown');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Received data:", data);

        // Define default activities and count from database
        const activityLabels = ["Research", "Meeting", "Coding", "Assignment Work", "Project Development"];
        const activityCounts = activityLabels.map(label => data[label] || 0); // Default to 0 if missing

        // Check if all counts are zero
        const noData = activityCounts.every(count => count === 0);

        // Ensure canvas exists
        const canvas = document.getElementById('activityBreakdownChart');
        const noDataPrompt = document.getElementById('noDataPrompt');

        if (!canvas) {
            console.error("Canvas element not found!");
            return;
        }

        // Show or hide the no data prompt
        if (noData) {
            noDataPrompt.style.display = 'block';
            canvas.style.display = 'none'; // Hide the canvas if no data
        } else {
            noDataPrompt.style.display = 'none';
            canvas.style.display = 'block'; // Show the canvas if data is present
        }

        // Destroy previous chart if it exists and is a valid chart object
        if (window.activityBreakdownChart instanceof Chart) {
            console.log("Destroying existing chart...");
            window.activityBreakdownChart.destroy();
        }

        // Create new chart only if there is data
        if (!noData) {
            const ctx = canvas.getContext('2d');
            window.activityBreakdownChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: activityLabels,
                    datasets: [{
                        data: activityCounts,
                        backgroundColor: [
                            '#3498db', // Blue for Research
                            '#9b59b6', // Purple for Meetings
                            '#e74c3c', // Red for Coding
                            '#f1c40f', // Yellow for Assignment Work
                            '#e67e22'  // Orange for Project Development
                        ],
                        borderColor: '#fff',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#2c3e50',
                                font: { size: 14 },
                                padding: 20,
                            }
                        },
                        tooltip: {
                            enabled: true,
                            backgroundColor: '#2c3e50',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            padding: 10,
                            cornerRadius: 5,
                        }
                    }
                }
            });

            // Force chart update
            window.activityBreakdownChart.update();
        }

    } catch (error) {
        console.error("Error fetching activity breakdown data:", error);
    }
}

// Fetch chart data on page load
fetchActivityBreakdown();

const socket = io('https://css-sit-in-monitoring-system.onrender.com', {
    transports: ['websocket'],  // Force WebSocket transport
    upgrade: false,             // Disable fallback to polling
});