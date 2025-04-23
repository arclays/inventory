


document.addEventListener('DOMContentLoaded', function() {
    $('#stockTable').DataTable({
        responsive: true,
        dom: '<"top"lf>rt<"bottom"ip>',
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
        initComplete: function() {
            // Add custom filtering for stock status
            $.fn.dataTable.ext.search.push(
                function(settings, data, dataIndex) {
                    const statusFilter = $('#stockStatusFilter').val();
                    if (!statusFilter) return true;
                    
                    const row = $('#stockTable').DataTable().row(dataIndex).node();
                    const currentStock = parseInt($(row).attr('data-stock'));
                    const minStock = parseInt($(row).attr('data-minstock'));
                    
                    if (statusFilter === 'critical' && currentStock <= minStock * 0.5) return true;
                    if (statusFilter === 'low' && currentStock <= minStock && currentStock > minStock * 0.5) return true;
                    if (statusFilter === 'normal' && currentStock > minStock) return true;
                    
                    return false;
                }
            );
        }
    });
    
    // Stock history modal
    $('.stock-history').click(function() {
        const productId = $(this).data('product-id');
        $.get(`/stock/history/${productId}/`, function(data) {
            $('#stockHistoryModal').html(data);
            $('#stockHistoryModal').modal('show');
        });
    });
    
    // Export functionality
    $('#exportExcel').click(function() {
        window.location.href = '/stock/export/excel/';
    });
    
    $('#exportPDF').click(function() {
        window.location.href = '/stock/export/pdf/';
    });
    
    $('#exportCSV').click(function() {
        window.location.href = '/stock/export/csv/';
    });
});

function printStockTable() {
    const printContent = document.getElementById('stockTable').outerHTML;
    const originalContent = document.body.innerHTML;
    document.body.innerHTML = `
        <h2 class="text-center mb-3">Stock Report - {{ selected_date }}</h2>
        ${printContent}
        <div class="mt-4 text-end">
            <p>Generated on: {% now "DATETIME_FORMAT" %}</p>
        </div>
    `;
    window.print();
    document.body.innerHTML = originalContent;
}
