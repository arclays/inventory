

document.addEventListener('DOMContentLoaded', function () {
    const productContainer = document.getElementById('product-container');
    const addProductBtn = document.getElementById('add-product');

    addProductBtn.addEventListener('click', function () {
        const productItem = document.querySelector('.product-item');
        const clone = productItem.cloneNode(true);

        // Clear input fields in the cloned item
        clone.querySelectorAll('input').forEach(input => input.value = '');
        clone.querySelectorAll('select').forEach(select => select.selectedIndex = 0);

        productContainer.appendChild(clone);
    });
    productContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-product')) {
            const items = document.querySelectorAll('.product-item');
            if (items.length > 1) {
                e.target.closest('.product-item').remove();
            } else {
                alert('At least one product must be selected.');
            }
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    let totalPrice = "{{ order.total_price }}"; // Fetch from Django context
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

            // Add event listener for remove button
            newProductItem.querySelector(".remove-product").addEventListener("click", function () {
                newProductItem.remove();
            });
        });

        // Remove product on click
        document.addEventListener("click", function (e) {
            if (e.target.classList.contains("remove-product")) {
                e.target.closest(".product-item").remove();
            }
        });
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
    
document.getElementById('fullscreen-btn').addEventListener('click', function () {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
});

// Sales Chart
// var salesCtx = document.getElementById('salesChart').getContext('2d');
// var salesChart = new Chart(salesCtx, {
//     type: 'line',
//     data: {
//         labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
//         datasets: [{
//             label: 'Sales ($)',
//             data: [5000, 7000, 8000, 12000, 15000, 20000],
//             borderColor: 'blue',
//             borderWidth: 2,
//             fill: false
//         }]
//     }
// });
var stockCtx = document.getElementById('stockChart').getContext('2d');
var stockChart = new Chart(stockCtx, {
    type: 'pie',
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
        }
    }
});

// Fetch stock data from Django view
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

// Update stock chart every 5 seconds (or on page load)
setInterval(updateStockChart, 5000);
updateStockChart();

var salesCtx = document.getElementById('salesChart').getContext('2d');
var salesChart = new Chart(salesCtx, {
    type: 'line',
    data: {
        labels: [],  // Initially empty
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

// Fetch data from Django view
fetch('/get-sales-data/')
    .then(response => response.json())
    .then(data => {
        salesChart.data.labels = data.labels;
        salesChart.data.datasets[0].data = data.data;
        salesChart.update();
    })
    .catch(error => console.error('Error fetching data:', error));


// Stock Chart
var stockCtx = document.getElementById('stockChart').getContext('2d');
var stockChart = new Chart(stockCtx, {
    type: 'bar',
    data: {
        labels: ['Product A', 'Product B', 'Product C', 'Product D'],
        datasets: [{
            label: 'Stock Levels',
            data: [40, 60, 30, 80],
            backgroundColor: ['red', 'blue', 'green', 'purple']
        }]
    }
});
     
document.addEventListener("DOMContentLoaded", function () {
    let sidebar = document.querySelector(".sidebar");

    window.addEventListener("scroll", function () {
        if (window.scrollY > 50) { 
            sidebar.classList.add("expanded");
        } else {
            sidebar.classList.remove("expanded");
        }
    });
});

document.addEventListener("DOMContentLoaded", function () {
    let today = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD
    document.getElementById("orderDate").value = today;
});


document.querySelector('form').addEventListener('submit', function(e) {
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirm_password').value;

    if (password !== confirmPassword) {
        e.preventDefault();
        alert('Passwords do not match.');
    }
});
