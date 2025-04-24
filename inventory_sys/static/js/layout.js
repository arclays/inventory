
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const toggleButton = document.querySelector('#toggleSidebar');
    const content = document.querySelector('.sidebar');
    const navbar = document.querySelector('.navbar');

    toggleButton.addEventListener('click', function () {
        sidebar.classList.toggle('show');
        if (sidebar.classList.contains('show')) {
            content.style.marginLeft = '200px';
            navbar.style.paddingLeft = '220px';
        } else {
            content.style.marginLeft = '0';
            navbar.style.paddingLeft = '15px';
        }
    });

    // Ensure sidebar text remains black by default
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        if (!link.classList.contains('active')) {
            link.style.color = '#212529';
        }
    });
});




    
    