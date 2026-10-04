STORE_ROLE_PERMISSIONS = {
    "Store Manager": {
        "store.manage_catalog",
        "store.manage_inventory",
        "store.manage_orders",
        "store.manage_bulk_requests",
        "store.view_store_dashboard",
        "accounts.view_store_customers",
        "accounts.manage_store_customers",
    },
    "Catalog Manager": {
        "store.manage_catalog",
    },
    "Inventory Manager": {
        "store.manage_inventory",
    },
    "Order Manager": {
        "store.manage_orders",
    },
    "Bulk Order Manager": {
        "store.manage_bulk_requests",
    },
    "Customer Support": {
        "accounts.view_store_customers",
    },
    "Customer Account Manager": {
        "accounts.view_store_customers",
        "accounts.manage_store_customers",
    },
}


STORE_STAFF_PERMISSIONS = frozenset().union(*STORE_ROLE_PERMISSIONS.values())
