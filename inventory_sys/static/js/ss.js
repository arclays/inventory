document.addEventListener("DOMContentLoaded", function () {
    const productSelect = document.getElementById('productId');
    const periodFilter = document.getElementById('periodFilter');
    const loadingSpinner = document.getElementById('chartLoading');
    const salesChart1 = document.getElementById('salesChart');
    let salesChart = null;

    if (salesChart1) {
        const salesCtx1 = salesChart1.getContext('2d');
        salesChart = new Chart(salesCtx1, {
            type: 'line', 
            data: {
                labels: [],
                datasets: [{
                    label: 'Sales Trend',
                    data: [],
                    backgroundColor: ['#ff6384', '#36a2eb']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'sales trend',
                        font: { size: 18 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text:'Quantity Ordered'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }

    const axisLabels = {
        daily: 'Days',
        weekly: 'Weeks',
        monthly: 'Months',
        quarterly: 'Quarters',
        yearly: 'Years'
    };

    function showLoading(show = true) {
        loadingSpinner.classList.toggle('d-none', !show);
    }

    function updateChart() {
        const productId = productSelect.value;
        const timePeriod = periodFilter.value;

        if (!productId) return;

        showLoading(true);
        const url = `/get-sales-data/?product_id=${productId}&time_period=${timePeriod}`;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                // if (data.error) throw new Error(data.error);
                // renderChart(data, timePeriod);
                // console.log(data);
                salesChart.data.labels = data.labels;
                salesChart.data.datasets[0].data = data.data;
                salesChart.update();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load sales data.');
            })
            .finally(() => showLoading(false));
    }

    // // Trigger chart update on dropdown change
    productSelect.addEventListener('change', updateChart);
    periodFilter.addEventListener('change', updateChart);

    // Optionally load initial chart
    updateChart();
});