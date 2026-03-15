"""Simple password-based authentication for GNOSIS.

Passwords are stored as bcrypt hashes in .streamlit/secrets.toml.
Session state tracks login so the gate only appears once per session.
"""

import bcrypt
import streamlit as st


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(plain: str) -> str:
    """Utility: generate a bcrypt hash for a plaintext password.
    Run: python -c "from auth import hash_password; print(hash_password('mypass'))"
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def require_auth() -> bool:
    """Render the login gate. Returns True if user is authenticated."""
    if st.session_state.get("authenticated"):
        return True

    users: dict = st.secrets.get("passwords", {})
    if not users:
        st.error("No users configured. See README for setup instructions.")
        st.stop()

    st.markdown(
        "<div style='text-align:center;margin-top:15vh'>"
        "<h1 style='font-family:Inter,sans-serif;color:#00d4ff;"
        "text-shadow:0 0 30px rgba(0,212,255,0.4)'>GNOSIS</h1>"
        "<p style='color:#667;font-family:Inter,sans-serif'>"
        "Personal Research Intelligence</p></div>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Authenticate", use_container_width=True
        )

    if submitted:
        if username in users and _check_password(password, users[username]):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Invalid credentials.")

    st.stop()
    return False
