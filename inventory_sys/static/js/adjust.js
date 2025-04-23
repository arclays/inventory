
    // Initialize tooltips
    document.addEventListener('DOMContentLoaded', function() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });
        
        // Calculate stock after adjustment
        const productSelect = document.getElementById('product_id');
        const batchSelect = document.getElementById('batch_sku');
        const adjustmentType = document.getElementById('adjustment_type');
        const quantityInput = document.getElementById('quantity');
        const currentStock = document.getElementById('current_stock');
        const afterAdjustment = document.getElementById('after_adjustment');
        
        function calculateAdjustment() {
            if (productSelect.value && quantityInput.value) {
                const current = parseInt(currentStock.value) || 0;
                const quantity = parseInt(quantityInput.value) || 0;
                const type = adjustmentType.value;
                
                if (type === 'add') {
                    afterAdjustment.value = current + quantity;
                } else {
                    afterAdjustment.value = current - quantity;
                    if (afterAdjustment.value < 0) {
                        afterAdjustment.classList.add('text-danger');
                    } else {
                        afterAdjustment.classList.remove('text-danger');
                    }
                }
            }
        }
        
        productSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            currentStock.value = selectedOption.getAttribute('data-stock') || '0';
            calculateAdjustment();
        });
        
        adjustmentType.addEventListener('change', calculateAdjustment);
        quantityInput.addEventListener('input', calculateAdjustment);
        
        // Table search functionality
        const searchInput = document.getElementById('searchInput');
        const table = document.getElementById('adjustmentsTable');
        
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                let found = false;
                
                for (let j = 0; j < row.cells.length; j++) {
                    const cell = row.cells[j];
                    if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
                
                row.style.display = found ? '' : 'none';
            }
        });
    });
  
    
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const dateRangeForm = document.getElementById('dateRangeForm');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const quickDateBtns = document.querySelectorAll('.quick-date-btn');
    
    // Format date as YYYY-MM-DD
    function formatDate(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Set quick date range
    quickDateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const days = parseInt(this.dataset.days);
            const endDate = new Date();
            const startDate = new Date();
            
            startDate.setDate(endDate.getDate() - days);
            
            startDateInput.value = formatDate(startDate);
            endDateInput.value = formatDate(endDate);
        });
    });
    
    // Form submission handler
    dateRangeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get current URL and parameters
        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        
        // Update or add date parameters
        if (startDateInput.value) {
            params.set('start_date', startDateInput.value);
        } else {
            params.delete('start_date');
        }
        
        if (endDateInput.value) {
            params.set('end_date', endDateInput.value);
        } else {
            params.delete('end_date');
        }
        
        // Reset pagination if it exists
        params.delete('page');
        
        // Reload page with new parameters
        window.location.href = `${url.pathname}?${params.toString()}`;
    });
    
    // Form reset handler
    dateRangeForm.addEventListener('reset', function() {
        // Get current URL and parameters
        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        
        // Remove date parameters
        params.delete('start_date');
        params.delete('end_date');
        
        // Reset pagination if it exists
        params.delete('page');
        
        // Reload page without date parameters
        window.location.href = `${url.pathname}?${params.toString()}`;
    });
    
    // Show the collapse if dates are already set
    if (startDateInput.value || endDateInput.value) {
        new bootstrap.Collapse(document.getElementById('dateRangeCollapse')).show();
    }
});
