"""
Login page rendering.
Shows the login form and handles authentication.
"""

import streamlit as st
from components.login_form import render_login_form


def render_login_page() -> None:
    """Render the login page."""
    # Page style
    st.markdown(
        """
        <style>
            .login-container {
                max-width: 400px;
                margin: auto;
                padding-top: 50px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                "https://via.placeholder.com/150x150.png?text=Salon+Logo",
                width=150,
            )  # Placeholder; replace with actual logo
            st.markdown("<h2 style='text-align: center;'>Salon Management System</h2>", unsafe_allow_html=True)
            render_login_form()