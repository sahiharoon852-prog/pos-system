"""
Authentication and session management.
Provides functions for user creation, login, logout, and permission checks.
All sensitive operations are performed here, separate from UI code.
"""

import streamlit as st
from typing import Optional, Dict, Any, Tuple, Set
from datetime import datetime, timedelta

from database.connection import get_db_connection
from utils.security import hash_password, verify_password
from utils.validators import validate_username, validate_password, validate_display_name


# Session state keys
SESSION_KEYS = {
    "authenticated": "authenticated",
    "user_id": "user_id",
    "username": "username",
    "display_name": "display_name",
    "role": "role",
    "permissions": "permissions",
}


def is_authenticated() -> bool:
    """Return True if user is logged in."""
    return st.session_state.get(SESSION_KEYS["authenticated"], False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return a dict with current user's session info if authenticated."""
    if not is_authenticated():
        return None
    return {
        "user_id": st.session_state.get(SESSION_KEYS["user_id"]),
        "username": st.session_state.get(SESSION_KEYS["username"]),
        "display_name": st.session_state.get(SESSION_KEYS["display_name"]),
        "role": st.session_state.get(SESSION_KEYS["role"]),
        "permissions": st.session_state.get(SESSION_KEYS["permissions"], set()),
    }


def get_current_role() -> Optional[str]:
    """Return current user's role name if authenticated."""
    return st.session_state.get(SESSION_KEYS["role"]) if is_authenticated() else None


def has_permission(permission_key: str) -> bool:
    """
    Check if the current user has the given permission.
    Returns True if user is ADMIN (admin has all permissions via DB) or
    if the permission is in the session's permission set.
    """
    if not is_authenticated():
        return False
    # Admin always has all permissions (they are loaded from DB anyway)
    if get_current_role() == "ADMIN":
        return True
    permissions = st.session_state.get(SESSION_KEYS["permissions"], set())
    return permission_key in permissions


def require_login():
    """Stop execution if not authenticated. Use at the top of protected pages."""
    if not is_authenticated():
        st.error("You must be logged in to access this page.")
        st.stop()


def require_permission(permission_key: str):
    """Stop execution if current user lacks a permission."""
    require_login()
    if not has_permission(permission_key):
        st.error("You do not have permission to access this feature.")
        st.stop()


def _load_user_permissions(user_id: int) -> Set[str]:
    """Load permission keys for a user from the database."""
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.permission_key
            FROM users u
            JOIN role_permissions rp ON u.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchall()
    return {row["permission_key"] for row in rows}


def _record_login_event(
    user_id: Optional[int],
    username: str,
    event_type: str,
    success: bool,
    failure_reason: Optional[str] = None,
    login_at: Optional[datetime] = None,
    logout_at: Optional[datetime] = None,
) -> None:
    """Insert a record into login_history."""
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO login_history
                (user_id, username_snapshot, event_type, success,
                 failure_reason_code, login_at, logout_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                event_type,
                1 if success else 0,
                failure_reason,
                login_at.isoformat() if login_at else None,
                logout_at.isoformat() if logout_at else None,
                None,  # IP could be captured via st.context if available
                None,  # User agent not easily accessible in Streamlit
            ),
        )


def _check_login_throttled(username: str) -> bool:
    """
    Simple throttle: if there are 5 or more failed login attempts in the last 15 minutes
    for this username, return True.
    """
    cutoff = datetime.now() - timedelta(minutes=15)
    with get_db_connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*) FROM login_history
            WHERE username_snapshot = ?
              AND event_type = 'FAILED_LOGIN'
              AND created_at >= ?
            """,
            (username, cutoff.isoformat()),
        ).fetchone()[0]
    return count >= 5


def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate a user with username and password.
    Returns (success, error_message). On success, sets session state.
    """
    # Normalize username
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."

    # Check throttling
    if _check_login_throttled(username):
        _record_login_event(
            None, username, "FAILED_LOGIN", False, failure_reason="THROTTLED"
        )
        return False, "Invalid username or password."

    # Find user by username
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    if not user:
        _record_login_event(
            None, username, "FAILED_LOGIN", False, failure_reason="INVALID_CREDENTIALS"
        )
        return False, "Invalid username or password."

    # Check password
    if not verify_password(password, user["password_hash"]):
        _record_login_event(
            user["id"], username, "FAILED_LOGIN", False, failure_reason="INVALID_CREDENTIALS"
        )
        return False, "Invalid username or password."

    # Check account status
    if user["status"] != "ACTIVE":
        _record_login_event(
            user["id"], username, "FAILED_LOGIN", False, failure_reason="ACCOUNT_INACTIVE"
        )
        return False, "Your account is inactive. Please contact an administrator."

    # Load permissions
    permissions = _load_user_permissions(user["id"])

    # Update last_login_at
    now = datetime.now()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (now.isoformat(), user["id"]),
        )

    # Set session state
    st.session_state[SESSION_KEYS["authenticated"]] = True
    st.session_state[SESSION_KEYS["user_id"]] = user["id"]
    st.session_state[SESSION_KEYS["username"]] = user["username"]
    st.session_state[SESSION_KEYS["display_name"]] = user["display_name"]
    st.session_state[SESSION_KEYS["role"]] = user["role_name"]
    st.session_state[SESSION_KEYS["permissions"]] = permissions

    # Record successful login
    _record_login_event(user["id"], username, "LOGIN", True, login_at=now)

    return True, ""


def logout() -> None:
    """Clear authentication session state and record logout event."""
    if is_authenticated():
        user_id = st.session_state.get(SESSION_KEYS["user_id"])
        username = st.session_state.get(SESSION_KEYS["username"])
        now = datetime.now()
        _record_login_event(user_id, username, "LOGOUT", True, logout_at=now)

    # Clear only authentication-related keys
    for key in SESSION_KEYS.values():
        if key in st.session_state:
            del st.session_state[key]


def create_admin(
    username: str,
    display_name: str,
    password: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Create the first ADMIN user. Used only during initial setup.
    Performs validation, hashes password, and assigns ADMIN role.
    """
    # Validate inputs
    username_err = validate_username(username)
    if username_err:
        return False, username_err
    password_err = validate_password(password)
    if password_err:
        return False, password_err
    display_err = validate_display_name(display_name)
    if display_err:
        return False, display_err

    # Normalize username
    username = username.strip().lower()

    # Check if any admin already exists
    with get_db_connection() as conn:
        admin_exists = conn.execute(
            "SELECT 1 FROM users u JOIN roles r ON u.role_id = r.id WHERE r.name = 'ADMIN' LIMIT 1"
        ).fetchone()
        if admin_exists:
            return False, "An administrator already exists."

        # Get ADMIN role id
        admin_role = conn.execute(
            "SELECT id FROM roles WHERE name = 'ADMIN'"
        ).fetchone()
        if not admin_role:
            return False, "System error: ADMIN role missing."
        admin_role_id = admin_role["id"]

        # Hash password
        password_hash = hash_password(password)

        # Insert new admin user
        try:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, display_name, role_id, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, password_hash, display_name.strip(), admin_role_id, email, phone),
            )
            return True, "Administrator created successfully."
        except Exception as e:
            # Most likely a duplicate username or other constraint violation
            return False, "Unable to create administrator. Please check the username."