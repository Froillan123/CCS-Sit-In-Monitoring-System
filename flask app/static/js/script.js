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

// Password visibility toggle for Login and Registration
const passwordAccess = (passwordFieldId, eyeIconId) => {
    const input = document.getElementById(passwordFieldId);
    const iconEye = document.getElementById(eyeIconId);
    if (input && iconEye) {
        iconEye.addEventListener('click', () => {
            input.type = input.type === 'password' ? 'text' : 'password';
            iconEye.classList.toggle('ri-eye-fill');
            iconEye.classList.toggle('ri-eye-off-fill');
        });
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
      borderWidth: 1, // Border width for bars
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
          title: {
            display: true,
            text: 'Sit-In Usage', // Updated y-axis label
          }
        },
        x: {
          title: {
            display: true,
            text: 'Labs', // X-axis label
          }
        }
      },
      plugins: {
        legend: {
          display: false, // Hide the legend
        },
        tooltip: {
          enabled: true, // Enable tooltips on hover
          callbacks: {
            title: (tooltipItems) => {
              return tooltipItems[0].label; // Show lab name in tooltip title
            },
            label: (tooltipItem) => {
              return `Sit-In Usage: ${tooltipItem.raw}`; // Updated tooltip label
            }
          }
        }
      }
    }
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
    } else {
      labUsageChart.options.scales.x.display = true; // Show x-axis labels
    }
  
    labUsageChart.update(); // Update the chart
  };
  
  // Add event listener for window resize
  window.addEventListener('resize', updateChartForSmallScreens);
  
  // Initial check for screen size
  updateChartForSmallScreens();

  const activityCtx = document.getElementById('activityBreakdownChart').getContext('2d');
  const activityBreakdownChart = new Chart(activityCtx, {
    type: 'doughnut', // You can also use 'pie' if you prefer
    data: {
      labels: ['Coding', 'Research', 'Meetings', 'Break'],
      datasets: [{
        data: [40, 30, 20, 10],
        backgroundColor: [
          '#1abc9c', // Green for Coding
          '#3498db', // Blue for Research
          '#9b59b6', // Purple for Meetings
          '#e74c3c'  // Red for Break
        ],
        borderColor: '#fff', // White border for better separation
        borderWidth: 2, // Border width
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // Allow the chart to fit its container
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#2c3e50', // Dark text color for legend
            font: {
              size: 14, // Adjust font size
            },
            padding: 20, // Add padding to legend items
          }
        },
        tooltip: {
          enabled: true,
          backgroundColor: '#2c3e50', // Dark tooltip background
          titleColor: '#fff', // White tooltip title
          bodyColor: '#fff', // White tooltip body
          padding: 10, // Add padding to tooltip
          cornerRadius: 5, // Rounded corners for tooltip
        }
      }
    }
  });
  
