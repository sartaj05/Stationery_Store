/* ===============================
   AUTO CLOSE ALERTS
================================= */
document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "0.5s";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";

            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 3000);
    });
});


/* ===============================
   ORDER FORM VALIDATION
================================= */
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("orderForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", function (event) {
        const name = document.querySelector("#id_name");
        const phone = document.querySelector("#id_phone");
        const qty = document.querySelector("#id_quantity");

        if (name && name.value.trim().length < 3) {
            alert("Please enter valid full name.");
            event.preventDefault();
            return;
        }

        if (phone && !/^[0-9]{10}$/.test(phone.value.trim())) {
            alert("Enter valid 10 digit mobile number.");
            event.preventDefault();
            return;
        }

        if (qty && parseInt(qty.value, 10) < 1) {
            alert("Quantity must be at least 1.");
            event.preventDefault();
        }
    });
});


/* ===============================
   NAV ACTIVE LINK
================================= */
document.addEventListener("DOMContentLoaded", function () {
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll(".nav-menu a");

    let bestMatch = null;
    let bestLength = 0;

    links.forEach(function (link) {
        const href = link.getAttribute("href");

        if (!href) {
            return;
        }

        let linkPath;
        try {
            linkPath = new URL(href, window.location.origin).pathname;
        } catch (error) {
            return;
        }

        if (linkPath === "/") {
            if (currentPath === "/") {
                bestMatch = link;
                bestLength = 1;
            }
            return;
        }

        if (currentPath.startsWith(linkPath) && linkPath.length > bestLength) {
            bestMatch = link;
            bestLength = linkPath.length;
        }
    });

    if (bestMatch) {
        bestMatch.style.background = "rgba(232,132,26,.16)";
        bestMatch.style.color = "#fdf8f0";
    }
});


/* ===============================
   IMAGE HOVER ZOOM
================================= */
document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".product-card");

    cards.forEach(function (card) {
        card.addEventListener("mouseenter", function () {
            const img = card.querySelector("img");
            if (img) {
                img.style.transform = "scale(1.05)";
            }
        });

        card.addEventListener("mouseleave", function () {
            const img = card.querySelector("img");
            if (img) {
                img.style.transform = "scale(1)";
            }
        });
    });
});
