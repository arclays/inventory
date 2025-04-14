
document.addEventListener("DOMContentLoaded", function () {
    // SAFELY initialize salesChart if canvas exists
    const salesCanvas = document.getElementById('salesChart');
    let salesChart = null;

    if (salesCanvas) {
        const salesCtx = salesCanvas.getContext('2d');
        salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Orders',
                    data: [],
                    borderColor: '#007bff',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Sales Quantity',
                        font: { size: 18 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Total Quantity Ordered'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Months'
                        }
                    }
                }
            }
        });

        // Fetch and update sales chart data
        function updateSalesChart() {
            fetch('/get-sales-data/')
                .then(response => response.json())
                .then(data => {
                    salesChart.data.labels = data.labels;
                    salesChart.data.datasets[0].data = data.data;
                    salesChart.update();
                })
                .catch(error => console.error('Error fetching sales data:', error));
        }

        updateSalesChart(); // Initial call
    }

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

