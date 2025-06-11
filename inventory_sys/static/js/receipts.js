
        // Set default date to today
        document.addEventListener('DOMContentLoaded', () => {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('dateFilter').value = today;
            filterReceipts();
        });

        function filterReceipts() {
            const dateFilter = document.getElementById('dateFilter').value;
            // This is a placeholder for actual filtering logic
            // In a real application, you'd make an AJAX call to fetch filtered receipts
            const tableBody = document.getElementById('receiptsTableBody');
            // Example: Update table content based on date (replace with actual data fetching)
            tableBody.innerHTML = `
                <tr>
                    <td>${dateFilter}</td>
                    <td>Sample Customer</td>
                    <td><a href="#" class="badge bg-primary badge-btn">REC12345</a></td>
                </tr>
            `;
        }
    