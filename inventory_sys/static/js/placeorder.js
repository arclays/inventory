document.addEventListener("DOMContentLoaded", function () {
    const productContainer = document.getElementById('product-container');
    const addProductBtn = document.getElementById('add-product');
    const finalTotalInput = document.getElementById('finalTotal');

    function calculateAndUpdate(quantity, price, discount, totalPriceField) {
        const totalPrice = (quantity * price) - ((quantity * price) * (discount / 100));
        totalPriceField.value = totalPrice.toFixed(2);
    }

    function updateTotalPrice(productItem) {
        const quantityInput = productItem.querySelector("input[name='orderQuantity[]']");
        const pricePerUnitField = productItem.querySelector(".price-per-unit");
        const totalPriceField = productItem.querySelector(".total-price");
        const discountField = productItem.querySelector("input[name='productDiscount[]']");
        const productSelect = productItem.querySelector("select[name='products[]']");

        const quantity = parseFloat(quantityInput.value) || 0;
        const discount = parseFloat(discountField.value) || 0.0;
        let pricePerUnit = parseFloat(pricePerUnitField.value) || 0;
        const selectedProduct = productSelect.value;

        if (!pricePerUnitField.value || pricePerUnit === 0) {
            if (selectedProduct) {
                pricePerUnitField.disabled = true;
                pricePerUnitField.value = 'Loading...';
                fetch(`/get-selling-price/${selectedProduct}/`)
                    .then(response => response.json())
                    .then(data => {
                        pricePerUnitField.disabled = false;
                        const sellingPrice = data.selling_price || 0;
                        pricePerUnitField.value = sellingPrice.toFixed(2);
                        calculateAndUpdate(quantity, sellingPrice, discount, totalPriceField);
                        updateFinalTotal();
                    })
                    .catch(error => {
                        pricePerUnitField.disabled = false;
                        console.error('Error fetching selling price:', error);
                        pricePerUnitField.value = '0.00';
                        calculateAndUpdate(quantity, 0, discount, totalPriceField);
                        updateFinalTotal();
                        showError('Failed to fetch selling price.');
                    });
            } else {
                pricePerUnitField.value = '0.00';
                calculateAndUpdate(quantity, 0, discount, totalPriceField);
                updateFinalTotal();
            }
        } else {
            calculateAndUpdate(quantity, pricePerUnit, discount, totalPriceField);
            updateFinalTotal();
        }
    }

    function updateFinalTotal() {
        let grandTotal = 0;
        document.querySelectorAll(".total-price").forEach(input => {
            grandTotal += parseFloat(input.value) || 0;
        });
        finalTotalInput.value = grandTotal.toFixed(2);
    }

    function showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        productContainer.prepend(alert);
    }

    function initializeProductItem(productItem) {
        const productSelect = productItem.querySelector('.product-select');
        const quantityInput = productItem.querySelector('.quantity');
        const pricePerUnitInput = productItem.querySelector('.price-per-unit');
        const discountInput = productItem.querySelector('.discount');

       
        productSelect.addEventListener('change', function () {
            pricePerUnitInput.value = '';
            updateTotalPrice(productItem);
        });

        [quantityInput, pricePerUnitInput, discountInput].forEach(input => {
            input.addEventListener('input', () => updateTotalPrice(productItem));
        });

        updateTotalPrice(productItem);
    }

    productContainer.querySelectorAll('.product-item').forEach(initializeProductItem);

    addProductBtn.addEventListener('click', function () {
        const newProductItem = productContainer.querySelector('.product-item').cloneNode(true);

        newProductItem.querySelector('.quantity').value = '';
        newProductItem.querySelector('.price-per-unit').value = '';
        newProductItem.querySelector('.discount').value = '0';
        newProductItem.querySelector('.total-price').value = '';
        newProductItem.querySelector('.product-select').value = '';
        newProductItem.querySelector('.batch-sku-select').value = '';
        newProductItem.querySelector('.unit').value = 'piece';

        newProductItem.querySelector('.remove-product').addEventListener('click', function () {
            if (productContainer.querySelectorAll('.product-item').length > 1) {
                newProductItem.remove();
                updateFinalTotal();
            }
        });

        productContainer.appendChild(newProductItem);
        initializeProductItem(newProductItem);
        updateFinalTotal();
    });

    productContainer.addEventListener('click', function (e) {
        if (e.target.closest('.remove-product')) {
            const productItem = e.target.closest('.product-item');
            if (productContainer.querySelectorAll('.product-item').length > 1) {
                productItem.remove();
                updateFinalTotal();
            }
        }
    });

    document.querySelector('#placeOrderModal form').addEventListener('submit', function (e) {
        const productSelects = productContainer.querySelectorAll('.product-select');
        let hasValidProduct = false;
        productSelects.forEach(select => {
            if (select.value) hasValidProduct = true;
        });
        if (!hasValidProduct) {
            e.preventDefault();
            showError('Please select at least one product.');
        }
    });
});