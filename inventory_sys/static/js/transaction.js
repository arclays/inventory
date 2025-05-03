
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Animated Counter for Summary Cards
    document.querySelectorAll('.count-up').forEach(element => {
        const target = parseInt(element.getAttribute('data-target'));
        let count = 0;
        const increment = target / 50;
        const updateCount = () => {
            count += increment;
            if (count < target) {
                element.textContent = Math.ceil(count);
                requestAnimationFrame(updateCount);
            } else {
                element.textContent = target;
            }
        };
        updateCount();
    });


    // Table Search and Filter
    function filterTable() {
        const searchTerm = document.getElementById('searchTransactions').value.toLowerCase();
        const categoryFilter = document.getElementById('categoryFilter').value;
        const rows = document.querySelectorAll('#transactionsTable tbody tr');

        rows.forEach(row => {
            const product = row.cells[1].textContent.toLowerCase();
            const category = row.cells[5].textContent;
            const matchesSearch = product.includes(searchTerm);
            const matchesCategory = !categoryFilter || category === categoryFilter;
            row.style.display = matchesSearch && matchesCategory ? '' : 'none';
        });
    }

    document.getElementById('searchTransactions').addEventListener('input', filterTable);
    document.getElementById('categoryFilter').addEventListener('change', filterTable);

    // Table Sorting
    let sortDirection = {};
    window.sortTable = function(column) {
        const table = document.getElementById('transactionsTable');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = [2, 3, 4].includes(column);

        sortDirection[column] = !sortDirection[column];
        rows.sort((a, b) => {
            let aValue = a.cells[column].textContent;
            let bValue = b.cells[column].textContent;
            if (isNumeric) {
                aValue = parseFloat(aValue) || 0;
                bValue = parseFloat(bValue) || 0;
            } else {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
            return sortDirection[column] ? (aValue > bValue ? 1 : -1) : (aValue < bValue ? 1 : -1);
        });

        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    };

    // Reset Filters
    window.resetFilters = function() {
        document.getElementById('searchTransactions').value = '';
        document.getElementById('categoryFilter').value = '';
        filterTable();
    };

    // Export to CSV
    window.exportToCSV = function() {
        const rows = document.querySelectorAll('#transactionsTable tr');
        let csv = 'No,Product,Stock In,Stock Out,Adjustments,Category\n';
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');
            if (cells.length) {
                csv += Array.from(cells).map(cell => `"${cell.textContent.replace(/"/g, '""')}"`).join(',') + '\n';
            }
        });
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'stock_transactions.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // Export to PDF
    window.exportToPDF = function() {
        const { jsPDF } = window.jspdf;
        html2canvas(document.querySelector('#transactionsTable')).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const imgWidth = 190;
            const pageHeight = 295;
            const imgHeight = canvas.height * imgWidth / canvas.width;
            let heightLeft = imgHeight;
            let position = 10;

            pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;

            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }

            pdf.save('stock_transactions.pdf');
        });
    };
});