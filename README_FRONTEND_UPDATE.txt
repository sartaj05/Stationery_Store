Delhi Stationery Frontend Update
================================

Replace these files in your Django project:

1. templates/store/base.html
2. templates/store/home.html
3. templates/store/product_card.html
4. templates/store/product_list.html
5. templates/store/product_detail.html
6. templates/store/order_form.html
7. templates/store/order_success.html
8. templates/store/track_order.html
9. templates/store/about.html
10. templates/store/contact.html
11. static/store/css/style.css
12. static/store/js/main.js

Important:
- This frontend supports dummy/sample products only when your store/views.py sends using_dummy_content and dummy products.
- Dummy products should not be saved in DB.
- Once superadmin/admin adds one active real product, dummy products disappear automatically.

Test:
python manage.py check
python manage.py runserver 8080

Open:
/
/products/
/products/<id>/
/contact/
/track-order/
