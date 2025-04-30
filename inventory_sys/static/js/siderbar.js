       
   
        // Update your JavaScript
        document.addEventListener('DOMContentLoaded', function () {
          const sidebar = document.querySelector('.sidebar');
          const toggleButton = document.querySelector('#toggleSidebar');
          // const content = document.querySelector('.content');
      
          function toggleSidebar() {
              if (window.innerWidth <= 768) {
                  // Mobile behavior (overlay)
                  sidebar.classList.toggle('active');
              } else {
                  // Desktop behavior (push content)
                  sidebar.classList.toggle('collapsed');
              }
          }
      
          toggleButton.addEventListener('click', toggleSidebar);
      
          // Close mobile sidebar when clicking outside
          document.addEventListener('click', function(e) {
              if (window.innerWidth <= 768 && 
                  !sidebar.contains(e.target) && 
                  !toggleButton.contains(e.target) && 
                  sidebar.classList.contains('active')) {
                  sidebar.classList.remove('active');
              }
          });
      
          // Handle window resize
          window.addEventListener('resize', function() {
              if (window.innerWidth > 768) {
                  sidebar.classList.remove('active');
              } else {
                  sidebar.classList.remove('collapsed');
              }
          });
      });