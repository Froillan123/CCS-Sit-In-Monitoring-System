/**
 * Analytics.js - Dashboard charts for the CCS Sit-In Monitoring System
 * Uses ApexCharts to visualize data from API endpoints
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the charts once the DOM is fully loaded
    initDailySitInsChart();
    initMostActiveLabsChart();
    initTotalSitInsCounter();
    initAvgSitInsPerDayChart();
});

/**
 * Daily Sit-Ins Chart
 * Displays sit-ins per day for the current week
 */
function initDailySitInsChart() {
    const chartElement = document.querySelector('.analytics-card:nth-child(1)');
    const chartContainer = document.createElement('div');
    chartContainer.id = 'dailySitInsChart';
    chartElement.appendChild(chartContainer);

    // Default options with placeholder data
    const options = {
        series: [{
            name: 'Sit-Ins',
            data: [0, 0, 0, 0, 0, 0, 0]
        }],
        chart: {
            type: 'bar',
            height: 280,
            fontFamily: 'Poppins, sans-serif',
            toolbar: {
                show: false
            },
            background: 'transparent'
        },
        colors: ['#8E44AD'],
        plotOptions: {
            bar: {
                borderRadius: 6,
                dataLabels: {
                    position: 'top'
                }
            }
        },
        dataLabels: {
            enabled: true,
            offsetY: -20,
            style: {
                fontSize: '12px',
                colors: ['#fff']
            }
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: false
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        xaxis: {
            categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            labels: {
                style: {
                    colors: '#fff'
                }
            },
            axisBorder: {
                show: false
            },
            axisTicks: {
                show: false
            }
        },
        yaxis: {
            labels: {
                formatter: function(val) {
                    return val.toFixed(0);
                },
                style: {
                    colors: '#fff'
                }
            }
        },
        tooltip: {
            theme: 'dark',
            y: {
                formatter: function(val) {
                    return val + " sit-ins";
                }
            }
        }
    };

    // Create a loading indicator first
    chartContainer.innerHTML = `
        <div class="chart-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading data...</p>
        </div>
    `;

    // Fetch real data from API
    fetch('/api/daily_sitins')
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            chartContainer.innerHTML = '';
            
            if (data.success && data.data) {
                // Format the dates to show only day names
                const dateObjects = data.data.map(item => new Date(item.date));
                const dayNames = dateObjects.map(date => {
                    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                    return days[date.getDay()];
                });
                
                options.xaxis.categories = dayNames;
                options.series[0].data = data.data.map(item => item.count);
            }
            
            // Create chart
            const chart = new ApexCharts(document.querySelector('#dailySitInsChart'), options);
            chart.render();
        })
        .catch(error => {
            console.error('Error fetching daily sit-ins:', error);
            chartContainer.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load data</p>
                </div>
            `;
        });
}

/**
 * Most Active Labs Chart
 * Displays the top labs by usage
 */
function initMostActiveLabsChart() {
    const chartElement = document.querySelector('.analytics-card:nth-child(2)');
    const chartContainer = document.createElement('div');
    chartContainer.id = 'mostActiveLabsChart';
    chartElement.appendChild(chartContainer);

    // Create a loading indicator
    chartContainer.innerHTML = `
        <div class="chart-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading data...</p>
        </div>
    `;

    // Default options with placeholder data
    const options = {
        series: [{
            name: 'Sit-Ins',
            data: []
        }],
        chart: {
            type: 'bar',
            height: 280,
            fontFamily: 'Poppins, sans-serif',
            toolbar: {
                show: false
            },
            background: 'transparent'
        },
        colors: ['#9C27B0'],
        plotOptions: {
            bar: {
                horizontal: true,
                borderRadius: 4,
                barHeight: '60%',
                distributed: true
            }
        },
        dataLabels: {
            enabled: false
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: false
                }
            }
        },
        xaxis: {
            categories: [],
            labels: {
                style: {
                    colors: '#fff',
                    fontSize: '12px'
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: '#fff'
                }
            }
        },
        tooltip: {
            theme: 'dark',
            y: {
                formatter: function(val) {
                    return val + " sit-ins";
                }
            }
        },
        legend: {
            show: false
        }
    };

    // Fetch real data from API
    fetch('/api/most_active_labs')
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            chartContainer.innerHTML = '';
            
            if (data.success && data.data && data.data.length > 0) {
                // Extract data for chart
                const labNames = data.data.map(lab => lab.lab_name);
                const labCounts = data.data.map(lab => lab.count);
                
                // Update chart options
                options.series[0].data = labCounts;
                options.xaxis.categories = labNames;
                
                // Create and render chart
                const chart = new ApexCharts(document.querySelector('#mostActiveLabsChart'), options);
                chart.render();
            } else {
                console.error('No lab data available');
                chartContainer.innerHTML = `
                    <div class="chart-no-data">
                        <i class="fas fa-info-circle"></i>
                        <p>No data available</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching most active labs:', error);
            chartContainer.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load data</p>
                </div>
            `;
        });
}

/**
 * Total Sit-Ins Counter
 * Animated counter showing total sit-ins
 */
function initTotalSitInsCounter() {
    const chartElement = document.querySelector('.analytics-card:nth-child(3)');
    const counterContainer = document.createElement('div');
    counterContainer.id = 'totalSitInsCounter';
    counterContainer.className = 'counter-container';
    chartElement.appendChild(counterContainer);

    // Create styles for the counter
    const style = document.createElement('style');
    style.textContent = `
        .counter-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            text-align: center;
        }
        .counter-value {
            font-size: 60px;
            font-weight: bold;
            color: #9575CD;
            margin: 0;
            font-family: 'Poppins', sans-serif;
        }
        .counter-label {
            font-size: 16px;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 10px;
        }
        .counter-icon {
            font-size: 36px;
            color: #9575CD;
            margin-bottom: 10px;
        }
        .chart-loading,
        .chart-error,
        .chart-no-data {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            text-align: center;
            color: rgba(255,255,255,0.8);
        }
        .chart-loading i,
        .chart-error i,
        .chart-no-data i {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .chart-error i {
            color: #f44336;
        }
    `;
    document.head.appendChild(style);

    // Add loading indicator
    counterContainer.innerHTML = `
        <div class="chart-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading data...</p>
        </div>
    `;

    // Fetch real data from API
    fetch('/api/total_sitins')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add counter elements
                counterContainer.innerHTML = `
                    <div class="counter-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <h2 class="counter-value" id="totalSitInsValue">0</h2>
                    <p class="counter-label">Total Sit-Ins Recorded</p>
                `;
                
                // Animate the counter
                animateCounter('totalSitInsValue', 0, data.total, 2000);
            } else {
                counterContainer.innerHTML = `
                    <div class="chart-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load data</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching total sit-ins:', error);
            counterContainer.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load data</p>
                </div>
            `;
        });
}

/**
 * Average Sit-Ins Per Day Chart
 * Shows the average sit-ins per day of the week
 */
function initAvgSitInsPerDayChart() {
    const chartElement = document.querySelector('.analytics-card:nth-child(4)');
    const chartContainer = document.createElement('div');
    chartContainer.id = 'avgSitInsChart';
    chartElement.appendChild(chartContainer);

    // Create loading indicator
    chartContainer.innerHTML = `
        <div class="chart-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading data...</p>
        </div>
    `;

    // Default options with placeholder data
    const options = {
        series: [{
            name: 'Average Sit-Ins',
            data: [0, 0, 0, 0, 0, 0, 0]
        }],
        chart: {
            type: 'line',
            height: 280,
            fontFamily: 'Poppins, sans-serif',
            toolbar: {
                show: false
            },
            background: 'transparent',
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        colors: ['#7E57C2'],
        stroke: {
            curve: 'smooth',
            width: 4
        },
        markers: {
            size: 6,
            colors: ['#7E57C2'],
            strokeColors: '#fff',
            strokeWidth: 2
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: false
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        xaxis: {
            categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            labels: {
                style: {
                    colors: '#fff'
                }
            }
        },
        yaxis: {
            labels: {
                formatter: function(val) {
                    return val.toFixed(1);
                },
                style: {
                    colors: '#fff'
                }
            }
        },
        tooltip: {
            theme: 'dark',
            y: {
                formatter: function(val) {
                    return val.toFixed(1) + " avg sit-ins";
                }
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'dark',
                type: 'vertical',
                shadeIntensity: 0.5,
                gradientToColors: ['#4527A0'],
                inverseColors: false,
                opacityFrom: 0.7,
                opacityTo: 0.3,
                stops: [0, 90, 100]
            }
        }
    };

    // Fetch real data from API
    fetch('/api/avg_daily_sitins')
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            chartContainer.innerHTML = '';
            
            if (data.success) {
                const average = data.average || 0;
                
                // If we have day-by-day data, use it
                if (data.data && data.data.length > 0) {
                    // Group by day of week
                    const dayOfWeekData = [0, 0, 0, 0, 0, 0, 0]; // Sun-Sat
                    const dayOfWeekCounts = [0, 0, 0, 0, 0, 0, 0]; // How many of each day we've seen
                    
                    data.data.forEach(item => {
                        const date = new Date(item.date);
                        const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
                        dayOfWeekData[dayOfWeek] += item.count;
                        dayOfWeekCounts[dayOfWeek]++;
                    });
                    
                    // Calculate averages
                    const dayAverages = dayOfWeekData.map((total, index) => {
                        return dayOfWeekCounts[index] ? total / dayOfWeekCounts[index] : 0;
                    });
                    
                    // Reorder to Mon-Sun
                    const reorderedAverages = [
                        dayAverages[1], dayAverages[2], dayAverages[3],
                        dayAverages[4], dayAverages[5], dayAverages[6], dayAverages[0]
                    ];
                    
                    options.series[0].data = reorderedAverages;
                } else {
                    // If no data, show the average for all days
                    options.series[0].data = [average, average, average, average, average, average, average];
                }
                
                // Create and render chart
                const chart = new ApexCharts(document.querySelector('#avgSitInsChart'), options);
                chart.render();
            } else {
                console.error('No average daily sit-ins data available');
                chartContainer.innerHTML = `
                    <div class="chart-no-data">
                        <i class="fas fa-info-circle"></i>
                        <p>No data available</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching average daily sit-ins:', error);
            chartContainer.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load data</p>
                </div>
            `;
        });
}

/**
 * Animates a counter from start to end value
 * @param {string} elementId - ID of the element to animate
 * @param {number} start - Starting value
 * @param {number} end - Ending value
 * @param {number} duration - Duration of animation in milliseconds
 */
function animateCounter(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentValue = Math.floor(progress * (end - start) + start);
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    
    window.requestAnimationFrame(step);
} 