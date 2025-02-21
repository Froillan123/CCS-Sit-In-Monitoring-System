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

// Dashboard Charts
const activityCtx = document.getElementById('activityChart').getContext('2d');
const activityChart = new Chart(activityCtx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Active Users',
      data: [4000, 3000, 5000, 4500, 6000, 5500],
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

const revenueCtx = document.getElementById('revenueChart').getContext('2d');
const revenueChart = new Chart(revenueCtx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Revenue',
      data: [15000, 20000, 18000, 22000, 25000, 23000],
      backgroundColor: 'rgba(203, 12, 159, 0.8)',
      borderRadius: 5,
      borderWidth: 0
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

// Analytics Charts
const salesGrowthCtx = document.getElementById('salesGrowthChart').getContext('2d');
const salesGrowthChart = new Chart(salesGrowthCtx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Sales Growth',
      data: [5000, 8000, 6000, 7000, 9500, 10500],
      borderColor: '#17c1e8',
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

const engagementCtx = document.getElementById('engagementChart').getContext('2d');
const engagementChart = new Chart(engagementCtx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'User Engagement',
      data: [2000, 3000, 4000, 3500, 5000, 4500],
      backgroundColor: 'rgba(130, 214, 22, 0.8)',
      borderRadius: 5,
      borderWidth: 0
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

const trafficCtx = document.getElementById('trafficChart').getContext('2d');
const trafficChart = new Chart(trafficCtx, {
  type: 'doughnut',
  data: {
    labels: ['Direct', 'Referral', 'Social'],
    datasets: [{
      label: 'Traffic Sources',
      data: [55, 30, 15],
      backgroundColor: ['#cb0c9f', '#17c1e8', '#82d616'],
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

const revenueCategoryCtx = document.getElementById('revenueCategoryChart').getContext('2d');
const revenueCategoryChart = new Chart(revenueCategoryCtx, {
  type: 'bar',
  data: {
    labels: ['Electronics', 'Fashion', 'Home & Kitchen', 'Health'],
    datasets: [{
      label: 'Revenue',
      data: [12000, 8000, 6000, 4000],
      backgroundColor: [
        'rgba(203, 12, 159, 0.8)', // Primary Color
        'rgba(23, 193, 232, 0.8)', // Info Color
        'rgba(130, 214, 22, 0.8)', // Success Color
        'rgba(251, 207, 51, 0.8)'  // Warning Color
      ],
      borderRadius: 5,
      borderWidth: 0
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

// Reports Download Functionality
function downloadReport(format) {
  alert(`Downloading report in ${format.toUpperCase()} format.`);
  // Add actual download logic here
}

// Resize Observer for Charts
const container = document.querySelector('.main-content');
const resizeObserver = new ResizeObserver(() => {
  activityChart.resize();
  revenueChart.resize();
  salesGrowthChart.resize();
  engagementChart.resize();
  trafficChart.resize();
  revenueCategoryChart.resize();
});
resizeObserver.observe(container);
