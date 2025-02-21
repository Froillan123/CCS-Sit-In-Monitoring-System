// SPA Behavior
// Function to navigate to a specific section
function navigateToSection(sectionId) {
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
      section.style.display = section.id === sectionId ? 'block' : 'none';
    });
  }

  // SPA Behavior
  const sections = document.querySelectorAll('section');
  const navLinks = document.querySelectorAll('.nav-link');

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href').substring(1);
      sections.forEach(section => {
        section.style.display = section.id === targetId ? 'block' : 'none';
      });
    });
  });

  // Initialize the landing page as the default view
  window.onload = () => {
    navigateToSection('landing');
  };

// Daily Sit-In Chart
const dailySitInCtx = document.getElementById('dailySitInChart').getContext('2d');
const dailySitInChart = new Chart(dailySitInCtx, {
  type: 'line',
  data: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Daily Sit-Ins',
      data: [20, 25, 30, 35, 40, 45, 50],
      borderColor: '#cb0c9f',
      backgroundColor: 'rgba(203, 12, 159, 0.1)',
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          drawBorder: false,
          borderDash: [5, 5],
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }
});


// Monthly Sit-In Chart
const monthlySitInCtx = document.getElementById('monthlySitInChart').getContext('2d');
const monthlySitInChart = new Chart(monthlySitInCtx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Monthly Sit-Ins',
      data: [500, 600, 700, 800, 900, 1000],
      borderColor: '#cb0c9f',
      backgroundColor: 'rgba(203, 12, 159, 0.1)',
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          drawBorder: false,
          borderDash: [5, 5],
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }
});

// Computer Usage Chart
const computerUsageCtx = document.getElementById('computerUsageChart').getContext('2d');
const computerUsageChart = new Chart(computerUsageCtx, {
  type: 'doughnut',
  data: {
    labels: ['PC-01', 'PC-02', 'PC-03', 'PC-04'],
    datasets: [{
      label: 'Computer Usage',
      data: [30, 25, 20, 25],
      backgroundColor: ['#cb0c9f', '#17c1e8', '#82d616', '#fbcf33'],
      borderWidth: 0
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  }
});

// Resize Observer for Charts
const container = document.querySelector('.main-content');
const resizeObserver = new ResizeObserver(() => {
  dailySitInChart.resize();
  feedbackRatingsChart.resize();
  monthlySitInChart.resize();
  computerUsageChart.resize();
});
resizeObserver.observe(container);


// User Engagement Chart
const userEngagementCtx = document.getElementById('userEngagementChart').getContext('2d');
const userEngagementChart = new Chart(userEngagementCtx, {
  type: 'line',
  data: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'User Engagement',
      data: [200, 300, 400, 350, 500, 450, 600],
      borderColor: '#17c1e8', // Info Color
      backgroundColor: 'rgba(23, 193, 232, 0.1)',
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          drawBorder: false,
          borderDash: [5, 5],
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }
});


const attendanceByGradeCtx = document.getElementById('attendanceByGradeChart').getContext('2d');

// Create gradient for the fill
const gradient = attendanceByGradeCtx.createLinearGradient(0, 0, 0, 400);
gradient.addColorStop(0, 'rgba(203, 12, 159, 0.8)');
gradient.addColorStop(1, 'rgba(203, 12, 159, 0.1)');

const attendanceByGradeChart = new Chart(attendanceByGradeCtx, {
  type: 'line',
  data: {
    labels: ['Grade 7', 'Grade 8', 'Grade 9', 'Grade 10'],
    datasets: [{
      label: 'Attendance',
      data: [85, 90, 88, 92], // Example attendance percentages
      borderColor: '#cb0c9f',
      backgroundColor: gradient,
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100, // Set max to 100 for percentage
        grid: {
          drawBorder: false,
          borderDash: [5, 5],
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          callback: function (value) {
            return value + '%'; // Add percentage sign to y-axis labels
          }
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }
});

const weeklySitInCtx = document.getElementById('weeklySitInChart').getContext('2d');
const weeklySitInChart = new Chart(weeklySitInCtx, {
  type: 'line',
  data: {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [{
      label: 'Weekly Sit-Ins',
      data: [150, 200, 180, 220], // Example weekly sit-in data
      borderColor: '#cb0c9f',
      backgroundColor: 'rgba(203, 12, 159, 0.1)',
      tension: 0.4,
      fill: true
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          drawBorder: false,
          borderDash: [5, 5],
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }
}); 


// Feedback Ratings Chart
const feedbackRatingsCtx = document.getElementById('feedbackRatingsChart').getContext('2d');
const feedbackRatingsChart = new Chart(feedbackRatingsCtx, {
  type: 'bar',
  data: {
    labels: ['Excellent', 'Good', 'Average', 'Poor'],
    datasets: [{
      label: 'Feedback Ratings',
      data: [30, 40, 20, 10], // Example feedback data
      backgroundColor: ['#82d616', '#17c1e8', '#fbcf33', '#ea0606'], // Colors for each rating
      borderRadius: 5, // Rounded corners for bars
      borderWidth: 0 // No border
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
          borderDash: [5, 5], // Dashed grid lines
          color: 'rgba(255, 255, 255, 0.1)' // Light grid line color
        }
      },
      x: {
        grid: {
          display: false // Hide x-axis grid lines
        }
      }
    }
  }
});

const labUsageCtx = document.getElementById('labUsageChart').getContext('2d');
const labUsageChart = new Chart(labUsageCtx, {
    type: 'bar',
    data: {
        labels: ['Student A', 'Student B', 'Student C', 'Student D', 'Student E'],
        datasets: [{
            label: 'Usage Duration (hrs)',
            data: [2, 3.5, 1.2, 4, 2.8], // Example hours used by each student
            backgroundColor: 'rgba(255, 255, 255, 1)', // White bars
            borderColor: 'rgba(255, 255, 255, 1)',
            borderWidth: 1,
            barPercentage: 0.2, // Controls individual bar width (LOWER = THINNER)
            categoryPercentage: 0.5, // Controls spacing between bars
            borderRadius: 10 // Rounds bar edges
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false, // Allow full responsiveness
        scales: {
            x: {
                grid: { display: false, drawBorder: false }, // Hide x-axis grid & border
                ticks: { color: 'white' } // White x-axis labels
            },
            y: {
                grid: { display: false, drawBorder: false }, // Hide y-axis grid & border
                ticks: { display: false } // Hide y-axis labels
            }
        },
        plugins: {
            legend: { display: false }, // Hide legend for a cleaner look
        },
        layout: {
            padding: 10 // Add some space for better visibility
        }
    }
});

