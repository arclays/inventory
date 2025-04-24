document.addEventListener("DOMContentLoaded", function () {
    let totalPrice = "{{ order.total_price }}"; 
    document.getElementById("totalprice").value = totalPrice;
});
   
    document.addEventListener("DOMContentLoaded", function () {
        const addProductBtn = document.getElementById("add-product");
        const productContainer = document.getElementById("product-container");

        addProductBtn.addEventListener("click", function () {
            let productItem = document.querySelector(".product-item");
            let newProductItem = productItem.cloneNode(true);

            // Reset input fields inside the cloned product item
            newProductItem.querySelector('select[name="products[]"]').value = "";
            newProductItem.querySelector('input[name="orderQuantity"]').value = 1;
            newProductItem.querySelector('select[name="units[]"]').value = "piece";
            newProductItem.querySelector("#totalprice").value = "";

            // Append new product item to container
            productContainer.appendChild(newProductItem);

        });
    });


        // Remove product on click
        document.addEventListener("click", function (e) {
            if (e.target.classList.contains("remove-product")) {
                e.target.closest(".product-item").remove();
            }
        });
    

    function printStockTable() {
        var stockTable = document.getElementById("stockTable").outerHTML;
        var newWindow = window.open("", "", "width=1000,height=600");
        newWindow.document.write(`
            <html>
            <head>
                <title>Print Stock Table</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    table { width: 100%; border-collapse: collapse;table-striped }
                    th, td { border: 1px solid black; padding: 8px; text-align: center; }
                    th { background-color:rgb(253, 251, 251); }
                    h2 { text-align: center; margin-bottom: 12px; }
                    table-header { font-size:10px; font-weight:bold; background {color:rgb(255,}
                </style>
            </head>
            <body>
                <h2>Stock Report</h2>
                ${stockTable}
                <script>
                    window.onload = function() { window.print(); window.close(); }
                <\/script>
            </body>
            </html>
        `);
        newWindow.document.close();
    }

    document.addEventListener("DOMContentLoaded", function () {
         function updateTotalPrice() {
            let finalTotal = 0;
    
             document.querySelectorAll(".product-item").forEach(item => {
                let quantity = parseFloat(item.querySelector(".quantity").value);
                let pricePerUnitField = item.querySelector(".price_per_unit");
                let totalPriceField = item.querySelector(".total-price");
                let discount = parseFloat(document.getElementById("discount").value) || 0.0;
    
                // Ensure unit price is set to the selling price if it's empty or zero
                if (!pricePerUnitField.value || parseFloat(pricePerUnitField.value) === 0) {
                    let selectedProduct = item.querySelector("select[name='products[]']").value;
                    let sellingPrice = 0;  
                    fetch(`/get-selling-price/${selectedProduct}/`)
                    .then(response => response.json())
                    .then(data => {
                        sellingPrice= data.selling_price || 0;
                         pricePerUnitField.value = sellingPrice;

    
                    // alert(sellingPrice)
                })
                }
    
                let pricePerUnit = parseFloat(pricePerUnitField.value) || 0;
    
                // Calculate total price: (quantity * unit price) - discount(quantity * unit price)
                let totalPrice = (quantity * pricePerUnit) - ((quantity * pricePerUnit) * (discount / 100));
                totalPriceField.value = totalPrice.toFixed(2);
    
                 finalTotal += totalPrice;
            });
    
            // Update final total
            document.getElementById("finalTotal").value = finalTotal.toFixed(2);
        }
    
  
        
        document.addEventListener("input", function (event) {
            if (event.target.matches(".quantity, price_per_unit, #discount, select[name='products[]']")) {
                updateTotalPrice();
            }
        });
    
        // Fullscreen Toggle Button
        document.getElementById('fullscreen-btn')?.addEventListener('click', function () {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });
    
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    });


     


document.addEventListener("DOMContentLoaded", function () {
    let today = new Date().toISOString().split('T')[0]; 
    document.getElementById("orderDate").value = today;
});


document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar"); 
    const toggleBtn = document.getElementById("toggleSidebar");

    if (sidebar && toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            sidebar.classList.toggle("active");
        });
    }
});
document.addEventListener("DOMContentLoaded", function () {
    fetch("/get_sales_data/")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("salesChart").getContext("2d");
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Quantity Ordered",
                        data: data.data,
                        borderColor: "#007bff",
                        backgroundColor: "rgba(0, 123, 255, 0.2)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: "Months" } },
                        y: { title: { display: true, text: "Quantity Ordered" }, beginAtZero: true }
                    }
                }
            });
        });

    // Fetch Stock Data and Render Pie Chart
    fetch("/get_stock_data/")
        .then(response => response.json())
        .then(data => {
            const ctx2 = document.getElementById("stockChart").getContext("2d");
            new Chart(ctx2, {
                type: "pie",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Stock Distribution",
                        data: data.data,
                        backgroundColor: [
                            "#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6610f2",
                            "#fd7e14", "#6c757d", "#20c997", "#e83e8c", "#343a40"
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "right" }
                    }
                }
            });
        });
});

  document.getElementById('filterToggle').addEventListener('click', function () {
    var form = document.getElementById('dateFilterForm');
    form.style.display = form.style.display === 'none' ? 'flex' : 'none';
  });

  
  
  $(document).ready(function() {
    $('#categoryname').select2({
      placeholder: "Select a category",
      allowClear: true,
       });
  });
  $(document).ready(function() {
    $('#suppliername').select2({
      placeholder: "Select a supplier",
      allowClear: true,
       });
  });
  
  $(document).ready(function() {
    $('#orderCustomer').select2({
      placeholder: "Select a customer",
      allowClear: true,
       });
  });
  $(document).ready(function() {
    $('#productname').select2({
      placeholder: "Select Product",
      allowClear: true,
       });
  });

  document.getElementById('searchInput').addEventListener('keyup', function () {
    const filter = this.value.toLowerCase();
    const rows = document.querySelectorAll('#productTable tbody tr');

    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(filter) ? '' : 'none';
    });
  });

  const modals = document.querySelectorAll('.modal');
  modals.forEach(modal => {
    modal.addEventListener('hidden.bs.modal', function () {
      modal.querySelector('form').reset();
    });
  });

  



$(document).ready(function() {
    // Filter Toggle
    $('#filterToggle').click(function() {
        $('#filterPanel').slideToggle();
    });

    // Sales Chart
    const salesChart = new Chart(document.getElementById('salesChart'), {
        type: 'line',
        data: {
            labels: {{ sales_labels|safe }},
            datasets: [
                {
                    label: 'Sales (UGX)',
                    data: {{ sales_data|safe }},
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    fill: true,
                },
                {
                    label: 'Profit (UGX)',
                    data: {{ profit_data|safe }},
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    fill: true,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Amount (UGX)' }
                },
                x: {
                    title: { display: true, text: 'Month' }
                }
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: UGX ${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            }
        }
    });

    // Stock Chart
    const stockChart = new Chart(document.getElementById('stockChart'), {
        type: 'bar',
        data: {
            labels: {{ stock_labels|safe }},
            datasets: [
                {
                    label: 'Stock Quantity',
                    data: {{ stock_data|safe }},
                    backgroundColor: '#36b9cc',
                    yAxisID: 'y',
                },
                {
                    label: 'Stock Value (UGX)',
                    data: {{ stock_value_data|safe }},
                    type: 'line',
                    borderColor: '#f6c23e',
                    backgroundColor: 'rgba(246, 194, 62, 0.1)',
                    fill: true,
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Quantity' },
                    position: 'left',
                },
                y1: {
                    beginAtZero: true,
                    title: { display: true, text: 'Value (UGX)' },
                    position: 'right',
                    grid: { drawOnChartArea: false }
                },
                x: {
                    title: { display: true, text: 'Month' }
                }
            },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} ${context.dataset.label.includes('Value') ? 'UGX' : ''}`;
                        }
                    }
                }
            }
        }
    });
});
