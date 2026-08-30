"""
First-run administrator setup page.
Only shown when no ADMIN user exists in the database.
"""

import streamlit as st
from services.auth import create_admin


def render_setup_page() -> None:
    """Render the first-run admin setup form."""
    st.title("First-Time Setup")
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
                    st.success("Administrator created! You can now log in.")
                    st.info("Please refresh the page or click below to proceed to login.")
                    if st.button("Go to Login"):
                        st.rerun()
                else:
                    st.error(message)