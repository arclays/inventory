document.addEventListener("DOMContentLoaded", function () {
    let sidebar = document.querySelector(".sidebar");

    window.addEventListener("scroll", function () {
        if (window.scrollY > 50) { 
            sidebar.classList.add("expanded");
        } else {
            sidebar.classList.remove("expanded");
        }
    });
});