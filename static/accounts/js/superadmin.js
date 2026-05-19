/* ============================================================
   DELHI STATIONERY — Custom Superadmin JS
   Handles alerts, delete confirmation, image preview,
   filter helpers, active sidebar, and small UX improvements.
   Humanity survived another dashboard.
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    autoCloseDashboardMessages();
    confirmDeleteActions();
    previewProductImage();
    highlightActiveSidebarLink();
    preventDoubleSubmit();
    autoGenerateSlug();
    initTableSearchKeyboard();
});


/* ===============================
   AUTO CLOSE DASHBOARD MESSAGES
================================= */
function autoCloseDashboardMessages() {
    const messages = document.querySelectorAll(".dash-msg, .alert, .msg");

    messages.forEach(function (message) {
        setTimeout(function () {
            message.style.transition = "0.45s ease";
            message.style.opacity = "0";
            message.style.transform = "translateY(-8px)";

            setTimeout(function () {
                message.remove();
            }, 500);
        }, 3500);
    });
}


/* ===============================
   DELETE CONFIRMATION
================================= */
function confirmDeleteActions() {
    const deleteLinks = document.querySelectorAll(
        "a[href*='delete'], button[data-confirm-delete]"
    );

    deleteLinks.forEach(function (item) {
        item.addEventListener("click", function (event) {
            const message =
                item.getAttribute("data-confirm-message") ||
                "Are you sure you want to delete this item? This action cannot be undone.";

            const confirmed = window.confirm(message);

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
}


/* ===============================
   PRODUCT IMAGE PREVIEW
================================= */
function previewProductImage() {
    const imageInput = document.querySelector(
        "input[type='file'][name='image']"
    );

    const previewBox = document.querySelector("#imagePreviewBox");
    const previewImage = document.querySelector("#imagePreview");

    if (!imageInput || !previewBox || !previewImage) {
        return;
    }

    imageInput.addEventListener("change", function () {
        const file = imageInput.files && imageInput.files[0];

        if (!file) {
            previewBox.style.display = "none";
            previewImage.src = "";
            return;
        }

        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image file.");
            imageInput.value = "";
            previewBox.style.display = "none";
            previewImage.src = "";
            return;
        }

        const maxSizeMB = 3;
        const maxSizeBytes = maxSizeMB * 1024 * 1024;

        if (file.size > maxSizeBytes) {
            alert("Image size must be less than " + maxSizeMB + "MB.");
            imageInput.value = "";
            previewBox.style.display = "none";
            previewImage.src = "";
            return;
        }

        const reader = new FileReader();

        reader.onload = function (event) {
            previewImage.src = event.target.result;
            previewBox.style.display = "block";
        };

        reader.readAsDataURL(file);
    });
}
function highlightActiveSidebarLink() {
    const currentPath = window.location.pathname;
    const links = document.querySelectorAll(".side-menu a");

    links.forEach(function (link) {
        link.classList.remove("active");
    });

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

        /*
           Important:
           "/" should only be active on homepage.
           Otherwise every dashboard URL matches "/".
           Truly elite nonsense, courtesy of path matching.
        */
        if (linkPath === "/") {
            if (currentPath === "/") {
                bestMatch = link;
                bestLength = 1;
            }
            return;
        }

        if (
            currentPath === linkPath ||
            currentPath.startsWith(linkPath)
        ) {
            if (linkPath.length > bestLength) {
                bestMatch = link;
                bestLength = linkPath.length;
            }
        }
    });

    if (bestMatch) {
        bestMatch.classList.add("active");
    }
}
/* ===============================
   PREVENT DOUBLE FORM SUBMIT
================================= */
function preventDoubleSubmit() {
    const forms = document.querySelectorAll("form[data-prevent-double-submit='true']");

    forms.forEach(function (form) {
        form.addEventListener("submit", function () {
            const submitButton = form.querySelector("button[type='submit']");

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.dataset.originalText = submitButton.innerHTML;
                submitButton.innerHTML = "Saving...";
            }
        });
    });
}


/* ===============================
   AUTO GENERATE SLUG
   Works on category form
================================= */
function autoGenerateSlug() {
    const nameInput = document.querySelector("input[name='name']");
    const slugInput = document.querySelector("input[name='slug']");

    if (!nameInput || !slugInput) {
        return;
    }

    let slugEditedManually = false;

    slugInput.addEventListener("input", function () {
        slugEditedManually = true;
    });

    nameInput.addEventListener("input", function () {
        if (slugEditedManually && slugInput.value.trim() !== "") {
            return;
        }

        slugInput.value = makeSlug(nameInput.value);
    });
}


function makeSlug(value) {
    return value
        .toString()
        .toLowerCase()
        .trim()
        .replace(/&/g, "and")
        .replace(/[\s\W-]+/g, "-")
        .replace(/^-+|-+$/g, "");
}


/* ===============================
   ENTER KEY FILTER SEARCH
================================= */
function initTableSearchKeyboard() {
    const searchInput = document.querySelector(
        ".filter-form input[name='q']"
    );

    if (!searchInput) {
        return;
    }

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            searchInput.value = "";
        }
    });
}


/* ===============================
   ORDER STATUS BADGE HELPER
   Optional use if you add dynamic order update later
================================= */
function getOrderStatusLabel(status) {
    const labels = {
        PENDING: "Pending",
        CONFIRMED: "Confirmed",
        PACKED: "Packed",
        OUT_FOR_DELIVERY: "Out for Delivery",
        DELIVERED: "Delivered",
        CANCELLED: "Cancelled"
    };

    return labels[status] || status;
}