"""
Permission constants and helper functions for the authorization system.
These are mirrored in the database; constants are for code convenience.
"""

# Role names
ROLE_ADMIN = "ADMIN"
ROLE_MANAGER = "MANAGER"
ROLE_RECEPTIONIST = "RECEPTIONIST"
ROLE_CASHIER = "CASHIER"
ROLE_STYLIST = "STYLIST"
ROLE_BEAUTICIAN = "BEAUTICIAN"

# Permission keys
PERM_VIEW_DASHBOARD = "view_dashboard"
PERM_MANAGE_USERS = "manage_users"
PERM_MANAGE_ROLES = "manage_roles"
PERM_VIEW_SALES = "view_sales"
PERM_CREATE_SALE = "create_sale"
PERM_MANAGE_PRODUCTS = "manage_products"
PERM_MANAGE_INVENTORY = "manage_inventory"
PERM_MANAGE_APPOINTMENTS = "manage_appointments"
PERM_VIEW_APPOINTMENTS = "view_appointments"
PERM_MANAGE_CUSTOMERS = "manage_customers"
PERM_VIEW_CUSTOMERS = "view_customers"
PERM_MANAGE_SUPPLIERS = "manage_suppliers"
PERM_MANAGE_PURCHASES = "manage_purchases"
PERM_MANAGE_EXPENSES = "manage_expenses"
PERM_VIEW_REPORTS = "view_reports"
PERM_MANAGE_SETTINGS = "manage_settings"
PERM_BACKUP_DATABASE = "backup_database"
PERM_VIEW_OWN_PERFORMANCE = "view_own_performance"
PERM_VIEW_OWN_COMMISSION = "view_own_commission"