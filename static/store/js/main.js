document.addEventListener("DOMContentLoaded", function () {
    initMobileMenu();
    initAlerts();
    initOrderValidation();
    highlightActiveNav();
});

function initMobileMenu() {
    const toggle = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("[data-nav-menu]");

    if (!toggle || !menu) return;

    toggle.addEventListener("click", function () {
        toggle.classList.toggle("active");
        menu.classList.toggle("active");
        document.body.classList.toggle("menu-open");
    });

    menu.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            toggle.classList.remove("active");
            menu.classList.remove("active");
            document.body.classList.remove("menu-open");
        });
    });
}

function initAlerts() {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "0.45s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";

            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 3500);
    });
}

function initOrderValidation() {
    const form = document.getElementById("orderForm");
    if (!form) return;

    form.addEventListener("submit", function (event) {
        const name = document.querySelector("#id_name");
        const phone = document.querySelector("#id_phone");
        const qty = document.querySelector("#id_quantity");

        if (name && name.value.trim().length < 3) {
            alert("Please enter a valid full name.");
            event.preventDefault();
            return;
        }

        if (phone && !/^[0-9]{10}$/.test(phone.value.trim())) {
            alert("Enter a valid 10 digit mobile number.");
            event.preventDefault();
            return;
        }

        if (qty && parseInt(qty.value || "0", 10) < 1) {
            alert("Quantity must be at least 1.");
            event.preventDefault();
        }
    });
}

function highlightActiveNav() {
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll(".nav-menu a");

    let bestLink = null;
    let bestLength = 0;

    links.forEach(function (link) {
        let path;
        try {
            path = new URL(link.href, window.location.origin).pathname;
        } catch (error) {
            return;
        }

        link.classList.remove("active");

        if (path === "/") {
            if (currentPath === "/") {
                bestLink = link;
                bestLength = 1;
            }
            return;
        }

        if (currentPath.startsWith(path) && path.length > bestLength) {
            bestLink = link;
            bestLength = path.length;
        }
    });

    if (bestLink) bestLink.classList.add("active");
}
