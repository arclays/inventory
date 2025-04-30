

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Date Range Picker
    const startDate = moment('{{ start_date }}', 'YYYY-MM-DD');
    const endDate = moment('{{ end_date }}', 'YYYY-MM-DD');

    $('#daterange').daterangepicker({
        startDate: startDate,
        endDate: endDate,
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        alwaysShowCalendars: true,
        opens: 'left',
        locale: {
            format: 'YYYY-MM-DD',
            separator: ' - '
        }
    }, function(start, end, label) {
        $('#start_date').val(start.format('YYYY-MM-DD'));
        $('#end_date').val(end.format('YYYY-MM-DD'));
    });

    $('#start_date').val(startDate.format('YYYY-MM-DD'));
    $('#end_date').val(endDate.format('YYYY-MM-DD'));

    // Initialize DataTables
    $('#recentOrdersTable').DataTable({
        "pageLength": 5,
        "lengthChange": false,
        "searching": false,
        "ordering": false
    });

    $('#lowStockTable').DataTable({
        "pageLength": 5,
        "lengthChange": false,
        "searching": false,
        "ordering": false
    });

    // Initialize Charts (Placeholder Data)
    const salesChart = new Chart(document.getElementById('salesChart'), {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Sales (UGX)',
                data: [12000, 19000, 15000, 22000, 18000, 25000],
                borderColor: '#0dcaf0',
                backgroundColor: 'rgba(13, 202, 240, 0.2)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    const stockChart = new Chart(document.getElementById('stockChart'), {
        type: 'bar',
        data: {
            labels: ['Product A', 'Product B', 'Product C', 'Product D'],
            datasets: [{
                label: 'Stock Level',
                data: [50, 30, 70, 20],
                backgroundColor: '#28a745',
                borderColor: '#28a745',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Quick Order Modal JavaScript
    const productContainer = document.getElementById('product-container');
    const addProductBtn = document.getElementById('add-product');
    const finalTotalInput = document.getElementById('finalTotal');

    function calculateTotalPrice(row) {
        const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
        const pricePerUnit = parseFloat(row.querySelector('.price-per-unit').value) || 0;
        const discount = parseFloat(row.querySelector('.discount').value) || 0;
        const totalPrice = quantity * pricePerUnit * (1 - discount / 100);
        row.querySelector('.total-price').value = totalPrice.toFixed(2);
        updateFinalTotal();
    }

    function updateFinalTotal() {
        const totalPrices = Array.from(document.querySelectorAll('.total-price'))
            .map(input => parseFloat(input.value) || 0);
        const finalTotal = totalPrices.reduce((sum, price) => sum + price, 0);
        finalTotalInput.value = finalTotal.toFixed(2);
    }

    function populatePricePerUnit(select) {
        const selectedOption = select.options[select.selectedIndex];
        const price = selectedOption.getAttribute('data-price');
        const row = select.closest('.product-item');
        row.querySelector('.price-per-unit').value = price;
        calculateTotalPrice(row);
    }

    productContainer.addEventListener('input', function (e) {
        if (e.target.classList.contains('quantity') || 
            e.target.classList.contains('price-per-unit') || 
            e.target.classList.contains('discount')) {
            const row = e.target.closest('.product-item');
            calculateTotalPrice(row);
        }
    });

    productContainer.addEventListener('change', function (e) {
        if (e.target.classList.contains('product-select')) {
            populatePricePerUnit(e.target);
        }
    });

    addProductBtn.addEventListener('click', function () {
        const newProductItem = productContainer.firstElementChild.cloneNode(true);
        newProductItem.querySelectorAll('input').forEach(input => {
            if (!input.classList.contains('discount')) {
                input.value = '';
            }
        });
        newProductItem.querySelector('.product-select').selectedIndex = 0;
        newProductItem.querySelector('.batch-sku-select').selectedIndex = 0;
        newProductItem.querySelector('.unit').selectedIndex = 0;
        productContainer.appendChild(newProductItem);
    });

    productContainer.addEventListener('click', function (e) {
        if (e.target.closest('.remove-product')) {
            const productItem = e.target.closest('.product-item');
            if (productContainer.children.length > 1) {
                productItem.remove();
                updateFinalTotal();
            }
        }
    });

    const firstProductSelect = document.querySelector('.product-select');
    if (firstProductSelect) {
        populatePricePerUnit(firstProductSelect);
    }
});

    