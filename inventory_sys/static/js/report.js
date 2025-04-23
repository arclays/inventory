
<!-- JavaScript for Charts -->
<script>
  // Inventory Trend Chart
  const inventoryTrendCtx = document.getElementById('inventoryTrendChart').getContext('2d');
  const inventoryTrendChart = new Chart(inventoryTrendCtx, {
    type: 'line',
    data: {
      labels: {{ inventory_trend_labels|safe }},
      datasets: [{
        label: 'Inventory Value',
        data: {{ inventory_trend_values }},
        borderColor: '#3b7ddd',
        backgroundColor: 'rgba(59, 125, 221, 0.1)',
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return '$' + context.raw.toLocaleString();
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              return '$' + value.toLocaleString();
            }
          }
        }
      }
    }
  });

  // Category Distribution Chart
  const categoryCtx = document.getElementById('inventoryCategoryChart').getContext('2d');
  const categoryChart = new Chart(categoryCtx, {
    type: 'doughnut',
    data: {
      labels: {{ category_names|safe }},
      datasets: [{
        data: {{ category_values }},
        backgroundColor: [
          '#3b7ddd', '#4fc6e1', '#f672a7', '#f7b84b', '#1cbb8c',
          '#727cf5', '#6c757d', '#0acf97', '#e3eaef', '#313a46'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'right',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: $${value.toLocaleString()} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
</script>