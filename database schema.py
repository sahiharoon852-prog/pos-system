"""
Database initialization and schema creation.
Ensures all tables, indexes, default roles, permissions, and
role-permission mappings are present.
"""

import sqlite3
from database.connection import DBConnection


DEFAULT_ROLES = {
    "ADMIN": "Full system administrator",
    "MANAGER": "Management-level access",
    "RECEPTIONIST": "Reception and appointment management",
    "CASHIER": "Point of sale and payments",
    "STYLIST": "Hair stylist with assigned services",
    "BEAUTICIAN": "Beauty services specialist",
}


DEFAULT_PERMISSIONS = {
    "view_dashboard": ("View main dashboard", "dashboard"),
    "manage_users": ("Create, update, deactivate users", "admin"),
    "manage_roles": ("Manage roles and permissions", "admin"),
    "view_sales": ("View sales history", "sales"),
    "create_sale": ("Create new sale", "pos"),
    "manage_products": ("Add/edit products", "inventory"),
    "manage_inventory": ("Manage stock levels", "inventory"),
    "manage_appointments": ("Create/edit appointments", "appointments"),
    "view_appointments": ("View appointment schedule", "appointments"),
    "manage_customers": ("Add/edit customer records", "customers"),
    "view_customers": ("Search and view customers", "customers"),
    "manage_suppliers": ("Manage supplier information", "purchases"),
    "manage_purchases": ("Create purchase orders", "purchases"),
    "manage_expenses": ("Record and manage expenses", "expenses"),
    "view_reports": ("Access business reports", "reports"),
    "manage_settings": ("Modify system settings", "settings"),
    "backup_database": ("Perform database backup", "admin"),
    "view_own_performance": ("View own performance metrics", "staff"),
    "view_own_commission": ("View own commission details", "staff"),
}


ROLE_PERMISSION_MAP = {
    "ADMIN": list(DEFAULT_PERMISSIONS.keys()),  # Admin gets all
    "MANAGER": [
        "view_dashboard",
        "view_sales",
        "create_sale",
        "manage_products",
        "manage_inventory",
        "manage_appointments",
        "view_appointments",
        "manage_customers",
        "view_customers",
        "manage_suppliers",
        "manage_purchases",
        "manage_expenses",
        "view_reports",
        "view_own_performance",
        "view_own_commission",
    ],
    "RECEPTIONIST": [
        "view_dashboard",
        "manage_appointments",
        "view_appointments",
        "manage_customers",
        "view_customers",
        "view_own_performance",
    ],
    "CASHIER": [
        "view_dashboard",
        "view_sales",
        "create_sale",
        "view_customers",
        "view_own_performance",
    ],
    "STYLIST": [
        "view_dashboard",
        "view_appointments",
        "view_customers",
        "view_own_performance",
        "view_own_commission",
    ],
    "BEAUTICIAN": [
        "view_dashboard",
        "view_appointments",
        "view_customers",
        "view_own_performance",
        "view_own_commission",
    ],
}


def init_db() -> None:
    """
    Create all tables and seed default data if not already present.
    Safe to run multiple times (idempotent).
    """
    with DBConnection() as conn:
        _create_tables(conn)
        _insert_default_roles(conn)
        _insert_default_permissions(conn)
        _assign_role_permissions(conn)


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_key TEXT UNIQUE NOT NULL,
            description TEXT,
            module TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE', 'INACTIVE')),
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        );

        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username_snapshot TEXT,
            event_type TEXT NOT NULL
                CHECK (event_type IN ('LOGIN', 'LOGOUT', 'FAILED_LOGIN')),
            success INTEGER NOT NULL DEFAULT 0,
            login_at TIMESTAMP,
            logout_at TIMESTAMP,
            failure_reason_code TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
        CREATE INDEX IF NOT EXISTS idx_login_history_username ON login_history(username_snapshot);
        CREATE INDEX IF NOT EXISTS idx_login_history_event_type ON login_history(event_type);
        """
    )


def _insert_default_roles(conn: sqlite3.Connection) -> None:
    """Insert default roles if they do not exist."""
    for role_name, description in DEFAULT_ROLES.items():
        conn.execute(
            "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
            (role_name, description),
        )


def _insert_default_permissions(conn: sqlite3.Connection) -> None:
    """Insert default permissions if they do not exist."""
    for perm_key, (desc, module) in DEFAULT_PERMISSIONS.items():
        conn.execute(
            "INSERT OR IGNORE INTO permissions (permission_key, description, module) VALUES (?, ?, ?)",
            (perm_key, desc, module),
        )


def _assign_role_permissions(conn: sqlite3.Connection) -> None:
    """
    Ensure each role has the correct permissions.
    This is done by inserting the mapping and also giving ADMIN all permissions.
    """
    # First, give ADMIN all permissions (in case new permissions were added later)
    admin_role_id = conn.execute(
        "SELECT id FROM roles WHERE name = 'ADMIN'"
    ).fetchone()[0]
    all_permission_ids = [
        row[0] for row in conn.execute("SELECT id FROM permissions").fetchall()
    ]
    for perm_id in all_permission_ids:
        conn.execute(
            "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
            (admin_role_id, perm_id),
        )

    # Then assign permissions according to the map
    for role_name, perm_keys in ROLE_PERMISSION_MAP.items():
        if role_name == "ADMIN":
            continue  # already handled
        role_id = conn.execute(
            "SELECT id FROM roles WHERE name = ?", (role_name,)
        ).fetchone()
        if not role_id:
            continue
        role_id = role_id[0]
        for perm_key in perm_keys:
            perm_id = conn.execute(
                "SELECT id FROM permissions WHERE permission_key = ?", (perm_key,)
            ).fetchone()
            if perm_id:
                conn.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (role_id, perm_id[0]),
                )