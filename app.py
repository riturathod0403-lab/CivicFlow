"""
CivicFlow – Smart Municipal Complaint Management System (app.py)
Streamlit Main Application Entrypoint with Role-Based Access Control (RBAC),
Session Management, and Dynamic View Routing.
"""

import streamlit as st
import pandas as pd
from database import init_db, authenticate_user, register_citizen

# Initialize SQLite database schema and seed accounts
init_db()

st.set_page_config(
    page_title="CivicFlow – Smart Municipal Complaint Management",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None

def login_form():
    st.markdown("## 🏛️ CivicFlow Login")
    st.markdown("Sign in to access municipal services, staff workflows, or administrative controls.")

    tab_login, tab_register, tab_quick = st.tabs(["Sign In", "Citizen Registration", "Demo Credentials"])

    with tab_login:
        with st.form("form_login"):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

    with tab_register:
        st.info("Registration is for Citizens only. Municipal Staff and Administrators are provisioned by central IT.")
        with st.form("form_register"):
            r_full_name = st.text_input("Full Name *")
            r_username = st.text_input("Choose Username *")
            r_password = st.text_input("Choose Password *", type="password")
            r_email = st.text_input("Email Address")
            r_phone = st.text_input("Phone Number")
            r_submit = st.form_submit_button("Register as Citizen", use_container_width=True)

            if r_submit:
                if not r_username or not r_password or not r_full_name:
                    st.error("Please fill in required fields (Name, Username, Password).")
                else:
                    ok, msg = register_citizen(r_username, r_password, r_full_name, r_email, r_phone)
                    if ok:
                        st.success("Account registered successfully! Please log in above.")
                    else:
                        st.error(msg)

    with tab_quick:
        st.caption("One-click demo logins for evaluation:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Citizen (Aarav)", use_container_width=True):
                user = authenticate_user("citizen1", "citizen123")
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.rerun()
        with col2:
            if st.button("Administrator (Commissioner)", use_container_width=True):
                user = authenticate_user("admin1", "admin123")
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.rerun()
        with col3:
            if st.button("Roads Staff (Vikram)", use_container_width=True):
                user = authenticate_user("roads_staff", "staff123")
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.rerun()

def main():
    if not st.session_state["authenticated"]:
        login_form()
        return

    user = st.session_state["user"]

    # Sidebar Header and User Info
    with st.sidebar:
        st.markdown(f"### 🏛️ CivicFlow")
        st.caption("Smart Municipal Complaint System")
        st.divider()

        role_badge = {
            "citizen": "👤 Citizen",
            "admin": "🛡️ Municipal Administrator",
            "staff": f"🛠️ Staff ({user.get('department', 'General')})"
        }.get(user["role"], "User")

        st.markdown(f"**Logged in as:** {user['full_name']}")
        st.markdown(f"**Role:** {role_badge}")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.rerun()

        st.divider()

    # Route based on authenticated role
    if user["role"] == "citizen":
        import pages_citizen
        pages_citizen.render_citizen_portal(user)
    elif user["role"] == "admin":
        import pages_admin
        pages_admin.render_admin_portal(user)
    elif user["role"] == "staff":
        import pages_staff
        pages_staff.render_staff_portal(user)

if __name__ == "__main__":
    main()
