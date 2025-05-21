
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

  
document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('searchTransactions');
  const table = document.querySelector('table');
  const rows = table.querySelectorAll('tbody tr');

  searchInput.addEventListener('input', function () {
      const searchTerm = this.value.toLowerCase();
      rows.forEach(row => {
          const productName = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
          row.style.display = productName.includes(searchTerm) ? '' : 'none';
      });
  });
});

  
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





<!-- Chart.js Script -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  // Inventory Trend Chart
  new Chart(document.getElementById('inventoryTrendChart'), {
    type: 'line',
    data: {
      labels: {{ inventory_trend_labels|safe }},
      datasets: [{
        label: 'Inventory Value (UGX)',
        data: {{ inventory_trend_values|safe }},
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13, 110, 253, 0.2)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Inventory Value Over Time' }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Value (UGX)' } },
        x: { title: { display: true, text: 'Month' } }
      }
    }
  });

  // Category Chart
  new Chart(document.getElementById('categoryChart'), {
    type: 'pie',
    data: {
      labels: {{ category_names|safe }},
      datasets: [{
        label: 'Category Value',
        data: {{ category_values|safe }},
        backgroundColor: [
          '#0d6efd', '#198754', '#dc3545', '#ffc107', '#6f42c1',
          '#fd7e14', '#20c997', '#0dcaf0', '#adb5bd', '#6610f2'
        ],
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right' },
        title: { display: true, text: 'Category Inventory Distribution' }
      }
    }
  });

  // Top Products Chart
  new Chart(document.getElementById('topProductsChart'), {
    type: 'pie',
    data: {
      labels: {{ top_product_names|safe }},
      datasets: [{
        label: 'Revenue (UGX)',
        data: {{ top_product_values|safe }},
        backgroundColor: [
          '#0d6efd', '#198754', '#dc3545', '#ffc107', '#6f42c1',
          '#fd7e14', '#20c997', '#0dcaf0', '#adb5bd', '#6610f2'
        ],
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'right' },
        title: { display: true, text: 'Top Products Revenue' }
      }
    }
  });

  // Monthly Sales Chart
  new Chart(document.getElementById('monthlySalesChart'), {
    type: 'line',
    data: {
      labels: {{ monthly_labels|safe }},
      datasets: [
        {
          label: 'Sales (UGX)',
          data: {{ monthly_sales|safe }},
          borderColor: '#198754',
          backgroundColor: 'rgba(25, 135, 84, 0.2)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'Profit (UGX)',
          data: {{ monthly_profit_data|safe }},
          borderColor: '#0dcaf0',
          backgroundColor: 'rgba(13, 202, 240, 0.2)',
          fill: true,
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Monthly Sales and Profit Trends' }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Value (UGX)' } },
        x: { title: { display: true, text: 'Month' } }
      }
    }
  });
</script>

<!-- DataTables Script -->
<script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
<script>
  $(document).ready(function() {
    $('#inventoryTable, #lowStockTable, #categoryTable, #topSellingTable, #dailySalesTable, #categoryProfitTable, #profitabilityTable, #expiryTable').DataTable({
      responsive: true,
      pageLength: 10,
      order: [[0, 'asc']],
      language: { search: "Filter:", searchPlaceholder: "Search table..." }
    });
  });
</script>

