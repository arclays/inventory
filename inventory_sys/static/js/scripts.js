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





