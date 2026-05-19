Delhi Stationery Account/Superadmin Update Pack

Copy these folders into your Django project root:

accounts/
templates/accounts/
static/accounts/

Included:
- Public login page
- Public signup page
- Custom superadmin dashboard
- Product/category/order/bulk/customer/low-stock superadmin pages
- Printable invoice template
- Confirm delete template
- Auth CSS
- Dashboard CSS
- Superadmin JS
- Accounts URLs and views with invoice + CSV export routes

After copy:
python manage.py check
python manage.py runserver 8080

Test:
/accounts/login/
/accounts/signup/
/accounts/superadmin/dashboard/
/accounts/superadmin/products/
/accounts/superadmin/categories/
/accounts/superadmin/orders/
/accounts/superadmin/bulk-requests/
/accounts/superadmin/customers/
/accounts/superadmin/low-stock/

Git commit safely without migrations:
git add accounts/urls.py accounts/views.py templates/accounts/ static/accounts/
git commit -m "Update account and superadmin frontend"
git push origin main

Do not use git add . if you are intentionally keeping migrations local.
