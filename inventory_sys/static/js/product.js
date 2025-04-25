
    let timeout;
    function updateSearchResults(page = 1) {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        const searchQuery = document.getElementById('stockSearch').value;
        const categoryId = document.getElementById('categoryFilter').value;
        const url = `{% url 'products:product_list' %}?search=${encodeURIComponent(searchQuery)}&category=${encodeURIComponent(categoryId)}&page=${page}`;

        fetch(url, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(response => response.json())
          .then(data => {
            // Update table body
            const tbody = document.getElementById('productTableBody');
            tbody.innerHTML = '';
            if (data.results.length > 0) {
              data.results.forEach(product => {
                tbody.innerHTML += `
                  <tr>
                    <td>${product.product_id}</td>
                    <td>${product.name}</td>
                    <td>${product.category}</td>
                    <td>${product.quantity_in_stock}</td>
                    <td>${product.units}</td>
                    <td>${product.selling_price}</td>
                    <td>${product.reorder_quantity}</td>
                    <td>${product.reorder_level}</td>
                  </tr>
                `;
              });
            } else {
              tbody.innerHTML = '<tr><td colspan="8" class="text-center">No products found.</td></tr>';
            }

            // Update pagination
            const pagination = document.getElementById('pagination');
            pagination.innerHTML = '';
            if (data.has_previous) {
              pagination.innerHTML += `
                <li class="page-item">
                  <a class="page-link" href="#" onclick="updateSearchResults(${data.page_number - 1}); return false;">Previous</a>
                </li>
              `;
            }
            for (let i = 1; i <= data.total_pages; i++) {
              pagination.innerHTML += `
                <li class="page-item ${i === data.page_number ? 'active' : ''}">
                  <a class="page-link" href="#" onclick="updateSearchResults(${i}); return false;">${i}</a>
                </li>
              `;
            }
            if (data.has_next) {
              pagination.innerHTML += `
                <li class="page-item">
                  <a class="page-link" href="#" onclick="updateSearchResults(${data.page_number + 1}); return false;">Next</a>
                </li>
              `;
            }
          })
          .catch(error => console.error('Error:', error));
      }, 300); 
    }

    
    document.getElementById('stockSearch').addEventListener('input', () => updateSearchResults());
    document.getElementById('clearFilters').addEventListener('click', () => {
      document.getElementById('stockSearch').value = '';
      document.getElementById('categoryFilter').value = '';
      updateSearchResults();
    });