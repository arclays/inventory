
document.addEventListener('DOMContentLoaded', function() {
    const fullscreenBtn = document.getElementById('fullscreen-toggle');
    const icon = fullscreenBtn.querySelector('i');
  
    if (!document.fullscreenEnabled) {
      fullscreenBtn.style.display = 'none'; 
      return;
    }
  
    fullscreenBtn.addEventListener('click', toggleFullscreen);

    document.addEventListener('fullscreenchange', updateFullscreenIcon);
    document.addEventListener('webkitfullscreenchange', updateFullscreenIcon); 
    document.addEventListener('msfullscreenchange', updateFullscreenIcon); 
  
    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        enterFullscreen();
      } else {
        exitFullscreen();
      }
    }
  
    function enterFullscreen() {
      const elem = document.documentElement;
      
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) { 
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) { 
        elem.msRequestFullscreen();
      }
    }
  
    function exitFullscreen() {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) { 
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
  
    function updateFullscreenIcon() {
      if (document.fullscreenElement || 
          document.webkitFullscreenElement || 
          document.msFullscreenElement) {
        icon.classList.replace('fa-expand', 'fa-compress');
        fullscreenBtn.setAttribute('title', 'Exit fullscreen');
      } else {
        icon.classList.replace('fa-compress', 'fa-expand');
        fullscreenBtn.setAttribute('title', 'Enter fullscreen');
      }
    }
  
    new bootstrap.Tooltip(fullscreenBtn, {
      placement: 'bottom',
      title: 'Enter fullscreen'
    });
  });
