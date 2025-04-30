
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


    // Add product
    $('#add-product').click(function() {
        const $clone = $('.product-item:first').clone();
        $clone.find('input, select').val('');
        $clone.find('.total-price').val('0.00');
        $clone.find('.discount').val('0');
        $clone.appendTo('#product-container');
    });

         // Remove product on click
         document.addEventListener("click", function (e) {
            if (e.target.classList.contains("remove-product")) {
                e.target.closest(".product-item").remove();
            }
        });


    // Bulk actions
    $('#selectAll').change(function() {
        $('.order-checkbox').prop('checked', this.checked);
        toggleBulkActionButton();
    });

    $('.order-checkbox').change(toggleBulkActionButton);

    function toggleBulkActionButton() {
        const checked = $('.order-checkbox:checked').length > 0;
        $('#applyBulkAction').prop('disabled', !checked);
    }

    $('#bulkAction').change(function() {
        const action = $(this).val();
        $('#newStatus').toggle(action === 'update_status');
    });

    // Initialize default prices
    $('.product-item').each(function() {
        updateTotalPrice($(this));
    });




document.addEventListener('DOMContentLoaded', function() {
    const bulkActionForm = document.getElementById('bulkActionForm');
    const bulkAction = document.getElementById('bulkAction');
    const newStatus = document.getElementById('newStatus');
    const applyButton = document.getElementById('applyBulkAction');
    const selectAllCheckbox = document.getElementById('selectAll');
    const orderCheckboxes = document.querySelectorAll('.order-checkbox');
    
    // Show/hide status dropdown based on action selection
    bulkAction.addEventListener('change', function() {
        newStatus.style.display = this.value === 'update_status' ? 'inline-block' : 'none';
    });
    
    // Select all/deselect all functionality
    selectAllCheckbox.addEventListener('change', function() {
        orderCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateApplyButton();
    });
    
    // Update apply button state based on checkbox selection
    function updateApplyButton() {
        const checkedBoxes = document.querySelectorAll('.order-checkbox:checked');
        applyButton.disabled = checkedBoxes.length === 0;
    }
    
    // Add event listeners to all order checkboxes
    orderCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Uncheck "select all" if any checkbox is unchecked
            if (!this.checked && selectAllCheckbox.checked) {
                selectAllCheckbox.checked = false;
            }
            updateApplyButton();
        });
    });
    
    // Form submission validation
    bulkActionForm.addEventListener('submit', function(e) {
        const checkedBoxes = document.querySelectorAll('.order-checkbox:checked');
        const selectedAction = bulkAction.value;
        
        if (checkedBoxes.length === 0) {
            e.preventDefault();
            alert('Please select at least one order.');
            return;
        }
        
        if (selectedAction === 'update_status' && !newStatus.value) {
            e.preventDefault();
            alert('Please select a new status.');
            return;
        }
        
        if (selectedAction === '') {
            e.preventDefault();
            alert('Please select an action.');
            return;
        }
        
        // Confirm destructive actions
        if (selectedAction === 'delete') {
            if (!confirm(`Are you sure you want to delete ${checkedBoxes.length} order(s)? This action cannot be undone.`)) {
                e.preventDefault();
                return;
            }
        }
    });
});

    document.getElementById('startDate').addEventListener('change', function() {
        document.getElementById('endDate').min = this.value;
    });
    document.getElementById('endDate').addEventListener('change', function() {
        document.getElementById('startDate').max = this.value;
    });
