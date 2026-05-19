# Delhi Stationery Store

Delhi Stationery Store is a Django-based online stationery ordering system for books, notebooks, pens, school supplies, office stationery, and bulk order enquiries.

The project includes a public shopping website, customer order tracking, customer order history, and a fully custom superadmin dashboard. Superadmin users login from the same public login page and manage products, categories, orders, customers, bulk requests, dashboard analytics, and low stock alerts without depending on Django Admin.

---

## Features

### Public Website

- Home page with categories, featured products, latest products, and call-to-action sections
- Product listing page
- Product search
- Category filter
- Product detail page
- Product image support
- Product stock status
- Customer order form
- Order success page
- Customer order tracking page
- About page
- Contact page
- Bulk order request form

### Authentication

- Customer signup
- Public login page
- Logout
- Superuser login through the same public login page
- Superuser automatically redirects to custom superadmin dashboard
- Normal customer redirects to public website
- Inactive users are blocked from login

### Customer Features

- Place product orders
- Track order using mobile number and optional order ID
- Logged-in customers can view their own order history
- Customer can see order status updates

### Custom Superadmin Dashboard

- Dashboard analytics
- Product management
- Category management
- Order management
- Bulk order request management
- Customer/user management
- Low stock alert system
- Quick restock system
- Latest orders table
- Low stock product list
- Revenue estimate
- Monthly order chart
- Payment method analytics
- Order status analytics
- Top ordered product analytics

### Product Management

- Add product
- Edit product
- Delete product
- Upload product image
- Product image preview
- Live product preview
- Featured product option
- Active/inactive product option
- Price and discount price validation
- Stock tracking

### Category Management

- Add category
- Edit category
- Delete category
- Category icon support
- Slug support
- Live category preview
- Product count per category

### Order Management

- View all customer orders
- Search orders
- Filter orders by status
- View order detail
- Update order status
- Add internal admin note
- See billing summary

### Bulk Request Management

- Save public bulk order requests to database
- View all bulk requests in superadmin
- Search requests
- Filter by status
- View request detail
- Update follow-up status
- Add internal admin note
- WhatsApp customer shortcut
- Call customer shortcut

### Customer Management

- View registered customers
- Search customers
- Filter active/inactive customers
- View customer detail
- See customer order history
- See total spent
- Activate/deactivate customer account

### Inventory / Low Stock

- Low stock alert page
- Out of stock filter
- Low stock filter
- Quick restock form
- Dashboard low stock alert
- Product disappears from alert list after stock is above threshold

---

## Tech Stack

- Python
- Django
- SQLite for local development
- Django templates
- HTML
- CSS
- JavaScript
- Pillow for image upload support

---

## Project Structure

```txt
DelhiStationery/
├── accounts/
│   ├── admin.py
│   ├── urls.py
│   └── views.py
│
├── store/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── DelhiStationery/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/
│   ├── accounts/
│   └── store/
│
├── static/
│   ├── accounts/
│   └── store/
│
├── media/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md