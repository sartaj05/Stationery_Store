/* ===============================
   AUTO CLOSE ALERTS
================================= */
document.addEventListener("DOMContentLoaded", function () {

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function(alert){
        setTimeout(function(){
            alert.style.transition = "0.5s";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";

            setTimeout(function(){
                alert.remove();
            }, 500);

        }, 3000);
    });

});


/* ===============================
   ORDER FORM VALIDATION
================================= */
document.addEventListener("DOMContentLoaded", function(){

    const form = document.getElementById("orderForm");

    if(form){

        form.addEventListener("submit", function(e){

            let name = document.querySelector("#id_name");
            let phone = document.querySelector("#id_phone");
            let qty = document.querySelector("#id_quantity");

            if(name && name.value.trim().length < 3){
                alert("Please enter valid full name.");
                e.preventDefault();
                return;
            }

            if(phone && !/^[0-9]{10}$/.test(phone.value.trim())){
                alert("Enter valid 10 digit mobile number.");
                e.preventDefault();
                return;
            }

            if(qty && parseInt(qty.value) < 1){
                alert("Quantity must be at least 1.");
                e.preventDefault();
                return;
            }

        });

    }

});


/* ===============================
   NAV ACTIVE LINK
================================= */
document.addEventListener("DOMContentLoaded", function(){

    const current = window.location.pathname;
    const links = document.querySelectorAll(".nav-menu a");

    links.forEach(function(link){
        if(link.getAttribute("href") === current){
            link.style.background = "#2563eb";
        }
    });

});


/* ===============================
   IMAGE HOVER ZOOM
================================= */
document.addEventListener("DOMContentLoaded", function(){

    const cards = document.querySelectorAll(".product-card");

    cards.forEach(function(card){

        card.addEventListener("mouseenter", function(){
            const img = card.querySelector("img");
            if(img){
                img.style.transform = "scale(1.08)";
                img.style.transition = "0.4s";
            }
        });

        card.addEventListener("mouseleave", function(){
            const img = card.querySelector("img");
            if(img){
                img.style.transform = "scale(1)";
            }
        });

    });

});