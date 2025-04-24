
  // Top Products Chart
  const topProductsCtx = document.getElementById('topProductsChart').getContext('2d');
  const topProductsChart = new Chart(topProductsCtx, {
    type: 'doughnut',
    data: {
      labels: {{ top_product_names|safe }},
      datasets: [{
        data: {{ top_product_values|safe }},
        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
        hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf', '#dda20a', '#be2617'],
        hoverBorderColor: "rgba(234, 236, 244, 1)",
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });

  // Sales Trend Chart
  const salesTrendCtx = document.getElementById('salesTrendChart').getContext('2d');
  const salesTrendChart = new Chart(salesTrendCtx, {
    type: 'line',
    data: {
      labels: {{ monthly_labels|safe }},
      datasets: [
        {
          label: "Sales Revenue",
          lineTension: 0.3,
          backgroundColor: "rgba(78, 115, 223, 0.05)",
          borderColor: "rgba(78, 115, 223, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(78, 115, 223, 1)",
          pointBorderColor: "rgba(78, 115, 223, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
          pointHoverBorderColor: "rgba(78, 115, 223, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: {{ monthly_sales_data|safe }},
        },
        {
          label: "Gross Profit",
          lineTension: 0.3,
          backgroundColor: "rgba(28, 200, 138, 0.05)",
          borderColor: "rgba(28, 200, 138, 1)",
          pointRadius: 3,
          pointBackgroundColor: "rgba(28, 200, 138, 1)",
          pointBorderColor: "rgba(28, 200, 138, 1)",
          pointHoverRadius: 3,
          pointHoverBackgroundColor: "rgba(28, 200, 138, 1)",
          pointHoverBorderColor: "rgba(28, 200, 138, 1)",
          pointHitRadius: 10,
          pointBorderWidth: 2,
          data: {{ monthly_profit_data|safe }},
        }
      ]
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          ticks: {
            callback: function(value) {
              return '$' + value.toLocaleString();
            }
          }
        }
      }
    }
  });
  <canvas id="inventoryTrendChart" height="250"></canvas>
<script>
  const inventoryTrendCtx = document.getElementById('inventoryTrendChart').getContext('2d');
  const inventoryTrendChart = new Chart(inventoryTrendCtx, {
    type: 'line',
    data: {
      labels: {{ inventory_trend_labels|safe }},
      datasets: [{
        label: "Inventory Value",
        lineTension: 0.3,
        backgroundColor: "rgba(78, 115, 223, 0.05)",
        borderColor: "rgba(78, 115, 223, 1)",
        pointRadius: 3,
        pointBackgroundColor: "rgba(78, 115, 223, 1)",
        pointBorderColor: "rgba(78, 115, 223, 1)",
        pointHoverRadius: 3,
        pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
        pointHoverBorderColor: "rgba(78, 115, 223, 1)",
        pointHitRadius: 10,
        pointBorderWidth: 2,
        data: {{ inventory_trend_values|safe }},
      }]
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: {
          ticks: {
            callback: function(value) {
              return '$' + value.toLocaleString();
            }
          }
        }
      }
    }
  });
</script>