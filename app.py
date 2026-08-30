# app.py - Complete Salon POS Authentication System
# Single file solution for Streamlit Community Cloud

import streamlit as st
import sqlite3
import bcrypt
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Set

# ============================================
# DATABASE SETUP
# ============================================

DB_DIR = Path("data")
DB_PATH = DB_DIR / "salon_pos.db"

def get_db_connection():
    """Create database connection with foreign keys enabled"""
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ============================================
# DATABASE SCHEMA
# ============================================

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
    "ADMIN": list(DEFAULT_PERMISSIONS.keys()),
    "MANAGER": [
        "view_dashboard", "view_sales", "create_sale", "manage_products",
        "manage_inventory", "manage_appointments", "view_appointments",
        "manage_customers", "view_customers", "manage_suppliers",
        "manage_purchases", "manage_expenses", "view_reports",
        "view_own_performance", "view_own_commission",
    ],
    "RECEPTIONIST": [
        "view_dashboard", "manage_appointments", "view_appointments",
        "manage_customers", "view_customers", "view_own_performance",
    ],
    "CASHIER": [
        "view_dashboard", "view_sales", "create_sale",
        "view_customers", "view_own_performance",
    ],
    "STYLIST": [
        "view_dashboard", "view_appointments", "view_customers",
        "view_own_performance", "view_own_commission",
    ],
    "BEAUTICIAN": [
        "view_dashboard", "view_appointments", "view_customers",
        "view_own_performance", "view_own_commission",
    ],
}

def init_database():
    """Initialize database with all tables and default data"""
    with get_db_connection() as conn:
        # Create tables
        conn.executescript("""
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
        """)

        # Insert default roles
        for role_name, description in DEFAULT_ROLES.items():
            conn.execute(
                "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
                (role_name, description)
            )

        # Insert default permissions
        for perm_key, (desc, module) in DEFAULT_PERMISSIONS.items():
            conn.execute(
                "INSERT OR IGNORE INTO permissions (permission_key, description, module) VALUES (?, ?, ?)",
                (perm_key, desc, module)
            )

        # Assign ADMIN all permissions
        admin_role_id = conn.execute("SELECT id FROM roles WHERE name = 'ADMIN'").fetchone()[0]
        all_perm_ids = [row[0] for row in conn.execute("SELECT id FROM permissions").fetchall()]
        for perm_id in all_perm_ids:
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                (admin_role_id, perm_id)
            )

        # Assign permissions to other roles
        for role_name, perm_keys in ROLE_PERMISSION_MAP.items():
            if role_name == "ADMIN":
                continue
            role_row = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,)).fetchone()
            if not role_row:
                continue
            role_id = role_row[0]
            for perm_key in perm_keys:
                perm_row = conn.execute(
                    "SELECT id FROM permissions WHERE permission_key = ?", (perm_key,)
                ).fetchone()
                if perm_row:
                    conn.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (role_id, perm_row[0])
                    )

# ============================================
# SECURITY FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except (ValueError, TypeError):
        return False

# ============================================
# VALIDATION FUNCTIONS
# ============================================

def validate_username(username: str) -> Optional[str]:
    """Validate username"""
    username = username.strip()
    if not username:
        return "Username cannot be empty."
    if len(username) < 3:
        return "Username must be at least 3 characters long."
    if len(username) > 50:
        return "Username must be at most 50 characters long."
    if not re.match(r'^[a-zA-Z0-9_.]+$', username):
        return "Username can only contain letters, numbers, underscore, and dot."
    return None

def validate_password(password: str) -> Optional[str]:
    """Validate password strength"""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return "Password must contain at least one number."
    return None

def validate_display_name(name: str) -> Optional[str]:
    """Validate display name"""
    name = name.strip()
    if not name:
        return "Display name cannot be empty."
    if len(name) > 100:
        return "Display name must be at most 100 characters long."
    return None

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def has_permission(permission_key: str) -> bool:
    """Check if current user has permission"""
    if not is_authenticated():
        return False
    if st.session_state.get('role') == 'ADMIN':
        return True
    return permission_key in st.session_state.get('permissions', set())

def require_login():
    """Stop execution if not authenticated"""
    if not is_authenticated():
        st.error("You must be logged in to access this page.")
        st.stop()

def require_permission(permission_key: str):
    """Stop execution if user lacks permission"""
    require_login()
    if not has_permission(permission_key):
        st.error("You do not have permission to access this feature.")
        st.stop()

def load_user_permissions(user_id: int) -> Set[str]:
    """Load user permissions from database"""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT p.permission_key
            FROM users u
            JOIN role_permissions rp ON u.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = ?
        """, (user_id,)).fetchall()
    return {row['permission_key'] for row in rows}

def record_login_event(
    user_id: Optional[int],
    username: str,
    event_type: str,
    success: bool,
    failure_reason: Optional[str] = None,
    login_at: Optional[datetime] = None,
    logout_at: Optional[datetime] = None,
):
    """Record login/logout/failure event"""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO login_history
                (user_id, username_snapshot, event_type, success,
                 failure_reason_code, login_at, logout_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, username, event_type,
            1 if success else 0,
            failure_reason,
            login_at.isoformat() if login_at else None,
            logout_at.isoformat() if logout_at else None,
        ))

def check_login_throttled(username: str) -> bool:
    """Check if username has too many failed attempts"""
    cutoff = datetime.now() - timedelta(minutes=15)
    with get_db_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*) FROM login_history
            WHERE username_snapshot = ?
              AND event_type = 'FAILED_LOGIN'
              AND created_at >= ?
        """, (username, cutoff.isoformat())).fetchone()[0]
    return count >= 5

def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate user with username and password"""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."

    if check_login_throttled(username):
        record_login_event(None, username, "FAILED_LOGIN", False, "THROTTLED")
        return False, "Invalid username or password."

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.username = ?",
            (username,)
        ).fetchone()

    if not user:
        record_login_event(None, username, "FAILED_LOGIN", False, "INVALID_CREDENTIALS")
        return False, "Invalid username or password."

    if not verify_password(password, user['password_hash']):
        record_login_event(user['id'], username, "FAILED_LOGIN", False, "INVALID_CREDENTIALS")
        return False, "Invalid username or password."

    if user['status'] != 'ACTIVE':
        record_login_event(user['id'], username, "FAILED_LOGIN", False, "ACCOUNT_INACTIVE")
        return False, "Your account is inactive. Please contact an administrator."

    permissions = load_user_permissions(user['id'])
    now = datetime.now()

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (now.isoformat(), user['id'])
        )

    st.session_state['authenticated'] = True
    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    st.session_state['display_name'] = user['display_name']
    st.session_state['role'] = user['role_name']
    st.session_state['permissions'] = permissions

    record_login_event(user['id'], username, "LOGIN", True, login_at=now)
    return True, ""

def logout():
    """Clear session state and record logout"""
    if is_authenticated():
        user_id = st.session_state.get('user_id')
        username = st.session_state.get('username')
        now = datetime.now()
        record_login_event(user_id, username, "LOGOUT", True, logout_at=now)

    for key in ['authenticated', 'user_id', 'username', 'display_name', 'role', 'permissions']:
        if key in st.session_state:
            del st.session_state[key]

def create_admin(username, display_name, password, email=None, phone=None):
    """Create first admin user"""
    # Validate inputs
    username_error = validate_username(username)
    if username_error:
        return False, username_error
    
    password_error = validate_password(password)
    if password_error:
        return False, password_error
    
    display_error = validate_display_name(display_name)
    if display_error:
        return False, display_error

    username = username.strip().lower()

    with get_db_connection() as conn:
        # Check if admin exists
        admin_exists = conn.execute("""
            SELECT 1 FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'ADMIN' LIMIT 1
        """).fetchone()

        if admin_exists:
            return False, "An administrator already exists."

        # Get admin role
        admin_role = conn.execute("SELECT id FROM roles WHERE name = 'ADMIN'").fetchone()
        if not admin_role:
            return False, "System error: ADMIN role missing."

        # Create user
        password_hash = hash_password(password)
        try:
            conn.execute("""
                INSERT INTO users (username, password_hash, display_name, role_id, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password_hash, display_name.strip(), admin_role['id'], email, phone))
            return True, "Administrator created successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose a different username."

# ============================================
# UI COMPONENTS
# ============================================

def render_setup_page():
    """Render first-run admin setup"""
    st.title("🔐 First-Time Setup")
    st.write("No administrator account found. Create the initial admin account.")
    
    with st.form("admin_setup_form", clear_on_submit=True):
        username = st.text_input("Username", max_chars=50)
        display_name = st.text_input("Display Name", max_chars=100)
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        email = st.text_input("Email (optional)")
        phone = st.text_input("Phone (optional)")
        
        submitted = st.form_submit_button("Create Administrator")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = create_admin(
                    username=username,
                    display_name=display_name,
                    password=password,
                    email=email if email else None,
                    phone=phone if phone else None,
                )
                if success:
                    st.success(message)
                    st.info("Please refresh the page to go to login.")
                    if st.button("Go to Login"):
                        st.rerun()
                else:
                    st.error(message)

def render_login_page():
    """Render login page"""
    st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: auto;
                padding-top: 30px;
            }
            .salon-title {
                text-align: center;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="salon-title">', unsafe_allow_html=True)
        st.markdown("### 💇 Salon Management System")
        st.markdown("#### Login to continue")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    success, message = authenticate_user(username, password)
                    if success:
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(message)

def render_dashboard():
    """Render protected dashboard shell"""
    require_login()
    
    st.title(f"Welcome, {st.session_state.display_name}! 👋")
    st.markdown(f"**Role:** {st.session_state.role}")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        st.write(f"Logged in as: **{st.session_state.display_name}**")
        st.write(f"Role: **{st.session_state.role}**")
        
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    # Main content
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", "Active", "✅")
    with col2:
        st.metric("Role", st.session_state.role)
    with col3:
        st.metric("Authentication", "Secure", "🔒")
    
    st.info("""
        Authentication foundation is ready!
        
        Future modules will be added here:
        - 📊 Dashboard
        - 💰 POS
        - 👥 Customers
        - 📅 Appointments
        - 📦 Inventory
        - 📈 Reports
    """)

# ============================================
# MAIN APP
# ============================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Salon Management System",
        page_icon="💇",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Initialize database
    init_database()
    
    # Check if admin exists
    with get_db_connection() as conn:
        admin_exists = conn.execute("""
            SELECT 1 FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name = 'ADMIN' LIMIT 1
        """).fetchone() is not None
    
    # Route to appropriate page
    if not admin_exists:
        render_setup_page()
    elif not is_authenticated():
        render_login_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
