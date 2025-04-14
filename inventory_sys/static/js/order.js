
document.addEventListener("DOMContentLoaded", function () {

    function updateTotalPrice() {
        let finalTotal = 0;

        document.querySelectorAll(".product-item").forEach(item => {
            let quantity = parseFloat(item.querySelector("input[name='orderQuantity[]']").value) || 0;
            let pricePerUnitField = item.querySelector(".price_per_unit");
            let totalPriceField = item.querySelector(".total-price");
            let discountField = item.querySelector("input[name='productDiscount[]']");
            let discount = parseFloat(discountField.value) || 0.0;

            let selectedProduct = item.querySelector("select[name='products[]']").value;
            let pricePerUnit = parseFloat(pricePerUnitField.value) || 0;

            // Fetch and auto-fill price if not set
            if (!pricePerUnitField.value || pricePerUnit === 0) {
                fetch(`/get-selling-price/${selectedProduct}/`)
                    .then(response => response.json())
                    .then(data => {
                        let sellingPrice = data.selling_price || 0;
                        pricePerUnitField.value = sellingPrice;
                        calculateAndUpdate(quantity, sellingPrice, discount, totalPriceField);
                        updateFinalTotal(); // Refresh final total after async update
                    });
            } else {
                calculateAndUpdate(quantity, pricePerUnit, discount, totalPriceField);
            }

            let totalPrice = (quantity * pricePerUnit) - ((quantity * pricePerUnit) * (discount / 100));
            finalTotal += totalPrice;
        });

        document.getElementById("finalTotal").value = finalTotal.toFixed(2);
    }

    function calculateAndUpdate(quantity, price, discount, totalPriceField) {
        let totalPrice = (quantity * price) - ((quantity * price) * (discount / 100));
        totalPriceField.value = totalPrice.toFixed(2);
    }

    function updateFinalTotal() {
        let grandTotal = 0;
        document.querySelectorAll(".total-price").forEach(input => {
            grandTotal += parseFloat(input.value) || 0;
        });
        document.getElementById("finalTotal").value = grandTotal.toFixed(2);
    }

    // Handle dynamic input change
    document.addEventListener("input", function (event) {
        if (event.target.closest(".product-item")) {
            updateTotalPrice();
        }
    });

    // Add event listener to "Add Product" button
    document.getElementById("add-product").addEventListener("click", function () {
        const container = document.getElementById("product-container");
        const original = document.querySelector(".product-item");
        const clone = original.cloneNode(true);

        // Reset input values
        clone.querySelectorAll("input").forEach(input => input.value = '');
        clone.querySelector("input[name='productDiscount[]']").value = '0.0';

        container.appendChild(clone);
    });

});

