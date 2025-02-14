

function fetchInitialStock(productId) {
    if (productId) {
        $.ajax({
            url: "{% url 'get_initial_stock' %}",
            data: {
                'product_id': productId
            },
            dataType: 'json',
            success: function (data) {
                if (data.quantity_in_stock !== undefined) {
                    $('#initialStock').val(data.quantity_in_stock);
                } else {
                    $('#initialStock').val('');
                }
            },
            error: function (xhr, status, error) {
                console.error('Error fetching initial stock:', error);
                $('#initialStock').val('');
            }
        });
    } else {
        $('#initialStock').val('');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const productContainer = document.getElementById('product-container');
    const addProductBtn = document.getElementById('add-product');

    // Function to add a new product block
    addProductBtn.addEventListener('click', function () {
        const productItem = document.querySelector('.product-item');
        const clone = productItem.cloneNode(true);

        // Clear input fields in the cloned item
        clone.querySelectorAll('input').forEach(input => input.value = '');
        clone.querySelectorAll('select').forEach(select => select.selectedIndex = 0);

        productContainer.appendChild(clone);
    });

    // Remove product item when clicking the "Remove" button
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



    function fetchInitialStock(productId) {
        if (productId) {
            fetch(`/get-initial-stock/${productId}/`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('initialStock').value = data.initial_stock;
                })
                .catch(error => console.error('Error fetching initial stock:', error));
        } else {
            document.getElementById('initialStock').value = '';
        }
    }


   
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
            let quantity = item.querySelector(".quantity").value;
            let unitPrice = item.querySelector(".unit-price").value;
            let totalPriceField = item.querySelector(".total-price");

            let totalPrice = (quantity && unitPrice) ? (quantity * unitPrice) : 0;
            totalPriceField.value = totalPrice.toFixed(2);

            finalTotal += totalPrice;
        });

        let discount = document.getElementById("discount").value;
        if (discount) {
            finalTotal -= (finalTotal * discount / 100);
        }

        document.getElementById("finalTotal").value = finalTotal.toFixed(2);
    }
    // Event Listeners for quantity and unit price inputs
    document.addEventListener("input", function (event) {
        if (event.target.matches(".quantity, .unit-price")) {
            updateTotalPrice();
        }
    });

    // Event Listeners
    document.addEventListener("input", function (event) {
        if (event.target.matches(".quantity, .unit-price, #discount")) {
            updateTotalPrice();
        }
    });
});
