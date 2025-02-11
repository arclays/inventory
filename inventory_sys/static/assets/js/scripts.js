

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