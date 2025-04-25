

document.addEventListener('DOMContentLoaded', function() {
    
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.querySelector('.sidebar'); 
    const mainContent = document.querySelector('.main-content'); 
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    if (sidebar) {
      if (isSidebarCollapsed) {
        collapseSidebar();
      } else {
        expandSidebar();
      }
    }
  
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function() {
        if (sidebar.classList.contains('collapsed')) {
          expandSidebar();
        } else {
          collapseSidebar();
        }
      });
    }
  
    function collapseSidebar() {
      sidebar.classList.add('collapsed');
      mainContent.classList.add('expanded');
      localStorage.setItem('sidebarCollapsed', 'true');
      
      
      const icon = toggleBtn.querySelector('i');
      if (icon) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-indent');
      }
    }
  
    
    function expandSidebar() {
      sidebar.classList.remove('collapsed');
      mainContent.classList.remove('expanded');
      localStorage.setItem('sidebarCollapsed', 'false');
      
      const icon = toggleBtn.querySelector('i');
      if (icon) {
        icon.classList.remove('fa-indent');
        icon.classList.add('fa-bars');
      }
    }
  
    // Optional: Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
      if (window.innerWidth <= 768 && 
          !sidebar.contains(e.target) && 
          !toggleBtn.contains(e.target) &&
          !sidebar.classList.contains('collapsed')) {
        collapseSidebar();
      }
    });
  });
  
  // Prevent zooming on mobile devices
  document.addEventListener('touchmove', function (event) {
    if (event.scale !== 1) { event.preventDefault(); }
  }, { passive: false });

  // Initialize sidebar toggle
  document.getElementById('toggleSidebar').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('active');
    document.querySelector('body').classList.toggle('sidebar-active');
  });
