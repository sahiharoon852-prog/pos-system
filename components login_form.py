"""
Reusable login form component.
Handles input, validation feedback, and calls authentication service.
"""

import streamlit as st
from services.auth import authenticate_user


def render_login_form() -> None:
    """Render the login form and process submission."""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
                return

            success, error_msg = authenticate_user(username, password)
            if success:
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(error_msg)