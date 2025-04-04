!function(t){"use strict";function s(){for(var e=document.getElementById("topnav-menu-content").getElementsByTagName("a"),t=0,n=e.length;t<n;t++)"nav-item dropdown active"===e[t].parentElement.getAttribute("class")&&(e[t].parentElement.classList.remove("active"),e[t].nextElementSibling.classList.remove("show"))}function n(e){1==t("#light-mode-switch").prop("checked")&&"light-mode-switch"===e?(t("html").removeAttr("dir"),t("#dark-mode-switch").prop("checked",!1),t("#rtl-mode-switch").prop("checked",!1),t("#bootstrap-style").attr("href","assets/css/bootstrap.min.css"),t("#app-style").attr("href","assets/css/app.min.css"),sessionStorage.setItem("is_visited","light-mode-switch")):1==t("#dark-mode-switch").prop("checked")&&"dark-mode-switch"===e?(t("html").removeAttr("dir"),t("#light-mode-switch").prop("checked",!1),t("#rtl-mode-switch").prop("checked",!1),t("#bootstrap-style").attr("href","assets/css/bootstrap-dark.min.css"),t("#app-style").attr("href","assets/css/app-dark.min.css"),sessionStorage.setItem("is_visited","dark-mode-switch")):1==t("#rtl-mode-switch").prop("checked")&&"rtl-mode-switch"===e&&(t("#light-mode-switch").prop("checked",!1),t("#dark-mode-switch").prop("checked",!1),t("#bootstrap-style").attr("href","assets/css/bootstrap-rtl.min.css"),t("#app-style").attr("href","assets/css/app-rtl.min.css"),t("html").attr("dir","rtl"),sessionStorage.setItem("is_visited","rtl-mode-switch"))}function e(){document.webkitIsFullScreen||document.mozFullScreen||document.msFullscreenElement||(console.log("pressed"),t("body").removeClass("fullscreen-enable"))}var a;t("#side-menu").metisMenu(),t("#vertical-menu-btn").on("click",function(e){e.preventDefault(),t("body").toggleClass("sidebar-enable"),992<=t(window).width()?t("body").toggleClass("vertical-collpsed"):t("body").removeClass("vertical-collpsed")}),t("#sidebar-menu a").each(function(){var e=window.location.href.split(/[?#]/)[0];this.href==e&&(t(this).addClass("active"),t(this).parent().addClass("mm-active"),t(this).parent().parent().addClass("mm-show"),t(this).parent().parent().prev().addClass("mm-active"),t(this).parent().parent().parent().addClass("mm-active"),t(this).parent().parent().parent().parent().addClass("mm-show"),t(this).parent().parent().parent().parent().parent().addClass("mm-active"))}),t(".navbar-nav a").each(function(){var e=window.location.href.split(/[?#]/)[0];this.href==e&&(t(this).addClass("active"),t(this).parent().addClass("active"),t(this).parent().parent().addClass("active"),t(this).parent().parent().parent().addClass("active"),t(this).parent().parent().parent().parent().addClass("active"),t(this).parent().parent().parent().parent().parent().addClass("active"))}),t(document).ready(function(){var e;0<t("#sidebar-menu").length&&0<t("#sidebar-menu .mm-active .active").length&&(300<(e=t("#sidebar-menu .mm-active .active").offset().top)&&(e-=300,t(".vertical-menu .simplebar-content-wrapper").animate({scrollTop:e},"slow")))}),t('[data-bs-toggle="fullscreen"]').on("click",function(e){e.preventDefault(),t("body").toggleClass("fullscreen-enable"),document.fullscreenElement||document.mozFullScreenElement||document.webkitFullscreenElement?document.cancelFullScreen?document.cancelFullScreen():document.mozCancelFullScreen?document.mozCancelFullScreen():document.webkitCancelFullScreen&&document.webkitCancelFullScreen():document.documentElement.requestFullscreen?document.documentElement.requestFullscreen():document.documentElement.mozRequestFullScreen?document.documentElement.mozRequestFullScreen():document.documentElement.webkitRequestFullscreen&&document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT)}),document.addEventListener("fullscreenchange",e),document.addEventListener("webkitfullscreenchange",e),document.addEventListener("mozfullscreenchange",e),t(".right-bar-toggle").on("click",function(e){t("body").toggleClass("right-bar-enabled")}),t(document).on("click","body",function(e){0<t(e.target).closest(".right-bar-toggle, .right-bar").length||t("body").removeClass("right-bar-enabled")}),function(){if(document.getElementById("topnav-menu-content")){for(var e=document.getElementById("topnav-menu-content").getElementsByTagName("a"),t=0,n=e.length;t<n;t++)e[t].onclick=function(e){"#"===e.target.getAttribute("href")&&(e.target.parentElement.classList.toggle("active"),e.target.nextElementSibling.classList.toggle("show"))};window.addEventListener("resize",s)}}(),t(function(){t('[data-bs-toggle="tooltip"]').tooltip()}),t(function(){t('[data-bs-toggle="popover"]').popover()}),window.sessionStorage&&((a=sessionStorage.getItem("is_visited"))?(t(".right-bar input:checkbox").prop("checked",!1),t("#"+a).prop("checked",!0),n(a)):sessionStorage.setItem("is_visited","light-mode-switch")),t("#light-mode-switch, #dark-mode-switch, #rtl-mode-switch").on("change",function(e){n(e.target.id)}),t(window).on("load",function(){t("#status").fadeOut(),t("#preloader").delay(350).fadeOut("slow")}),Waves.init()}(jQuery);
document.addEventListener('DOMContentLoaded', function () {
    const productContainer = document.getElementById('product-container');
    const addProductBtn = document.getElementById('add-product');

    // Function to add a new product block
    addProductBtn.addEventListener('click', function () {
        const productItem = document.querySelector('.product-item');
        const clone = productItem.cloneNode(true);

        // Clear input fields in the cloned item
        clone.querySelectorAll('input').forEach(input => input.value = '');
        clone.querySelectorAll('select').forEach(select => select.selectedIndex = 0);

        productContainer.appendChild(clone);
    });

    // Remove product item when clicking the "Remove" button
    productContainer.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-product')) {
            const items = document.querySelectorAll('.product-item');
            if (items.length > 1) {
                e.target.closest('.product-item').remove();
            } else {
                alert('At least one product must be selected.');
            }
        }
    });
});
document.addEventListener("DOMContentLoaded", function () {
    // Fetch Sales Data and Render Line Chart
    fetch("/get_sales_data/")
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById("salesChart").getContext("2d");
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Quantity Ordered",
                        data: data.data,
                        borderColor: "#007bff",
                        backgroundColor: "rgba(0, 123, 255, 0.2)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: "Months" } },
                        y: { title: { display: true, text: "Quantity Ordered" }, beginAtZero: true }
                    }
                }
            });
        });

    // Fetch Stock Data and Render Pie Chart
    fetch("/get_stock_data/")
        .then(response => response.json())
        .then(data => {
            const ctx2 = document.getElementById("stockChart").getContext("2d");
            new Chart(ctx2, {
                type: "pie",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: "Stock Distribution",
                        data: data.data,
                        backgroundColor: [
                            "#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6610f2",
                            "#fd7e14", "#6c757d", "#20c997", "#e83e8c", "#343a40"
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "right" }
                    }
                }
            });
        });
});
