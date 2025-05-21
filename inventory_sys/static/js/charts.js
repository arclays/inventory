
document.addEventListener("DOMContentLoaded", function () {
    // SAFELY initialize salesChart if canvas exists
    document.addEventListener("DOMContentLoaded", function () {
    const salesCanvas = document.getElementById('salesChart');
    let salesChart = null;

    if (salesCanvas) {
        const salesCtx = salesCanvas.getContext('2d');
        salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sales (UGX)',
                    data: [],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Period'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Total Sales (UGX)'
                        },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });

        function updateChart() {
            const period = document.getElementById('periodFilter').value;
            fetch('{% url "sales_trends_data" %}?period=' + period)
                .then(response => response.json())
                .then(data => {
                    salesChart.data.labels = data.labels;
                    salesChart.data.datasets[0].data = data.data;
                    salesChart.options.scales.x.title.text = period.charAt(0).toUpperCase() + period.slice(1);
                    salesChart.update();
                })
                .catch(error => console.error('Error fetching chart data:', error));
        }

        const periodFilter = document.getElementById('periodFilter');
        if (periodFilter) {
            periodFilter.addEventListener('change', updateChart);
        }

        // Initial chart load with default period (monthly)
        updateChart();
    }
});

    // SAFELY initialize stockChart if canvas exists
    const stockCanvas = document.getElementById('stockChart');
    let stockChart = null;

    if (stockCanvas) {
        const stockCtx = stockCanvas.getContext('2d');
        stockChart = new Chart(stockCtx, {
            type: 'bar', // Change to 'pie' if needed
            data: {
                labels: [],
                datasets: [{
                    label: 'Stock Levels',
                    data: [],
                    backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Product Stock Levels',
                        font: { size: 18 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Stock Quantity'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Products'
                        }
                    }
                }
            }
        });

        // Fetch and update stock chart data
        function updateStockChart() {
            fetch('/get-stock-data/')
                .then(response => response.json())
                .then(data => {
                    stockChart.data.labels = data.labels;
                    stockChart.data.datasets[0].data = data.data;
                    stockChart.update();
                })
                .catch(error => console.error('Error fetching stock data:', error));
        }

        updateStockChart(); // Initial call
        setInterval(updateStockChart, 5000); 
    }
});

