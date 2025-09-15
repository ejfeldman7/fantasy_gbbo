"""
Main Streamlit application for Fantasy GBBO - Updated for PostgreSQL
"""

import streamlit as st
from src.auth import normalize_email
from src.data_manager import DataManager
import src.pages.admin as admin_page
import src.pages.info as info_page
import src.pages.leaderboard as leaderboard_page
import src.pages.submit_picks as submit_picks_page
from src.auth import is_email_allowed

# Page configuration
st.set_page_config(
    page_title="Fantasy GBBO",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize data manager (now using PostgreSQL)
@st.cache_resource
def init_data_manager():
    """Initialize the data manager with database connection"""
    dm = DataManager()

    # Initialize week settings from config if needed
    from src.config import REVEAL_DATES_UTC

    dm.initialize_week_settings(REVEAL_DATES_UTC)

    return dm


# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False


def show_login_form(data_manager):
    """Show login/registration form"""
    st.title("🍰 Fantasy GBBO")
    st.subheader("Welcome to the Fantasy Great British Bake Off League!")

    # Check if registration is open
    with st.expander("ℹ️ About this league", expanded=False):
        st.write("""
        This is a fantasy league for The Great British Bake Off! Each week, you'll make predictions about:
        - ⭐ Who will be Star Baker
        - 🏆 Who will win the Technical Challenge  
        - 😢 Who will be eliminated
        - 🤝 Whether there will be a Hollywood Handshake
        - Plus season-long predictions for the winner and finalists!
        """)

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")

        if st.button("Login", key="login_button"):
            if email:
                norm_email = normalize_email(email)
                user = data_manager.get_user_by_email(norm_email)
                if user:
                    st.session_state.user_email = norm_email
                    st.session_state.user_name = user["name"]
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("User not found. Please register first.")
            else:
                st.error("Please enter your email.")

    with tab2:
        st.subheader("Register")
        name = st.text_input("Name", key="register_name")
        email = st.text_input("Email", key="register_email")
        norm_email = normalize_email(email)
        if st.button("Register", key="register_button"):
            if name and email:
                # Check if email is allowed (if allow-list is configured)
                if not is_email_allowed(norm_email):
                    st.error(
                        "Sorry, registration is currently limited to invited participants."
                    )
                    return

                # Check if user already exists
                existing_user = data_manager.get_user_by_email(norm_email)
                if existing_user:
                    st.error(
                        "A user with this email already exists. Please login instead."
                    )
                    return

                # Register new user
                if data_manager.add_user(name, norm_email):
                    st.session_state.user_email = norm_email
                    st.session_state.user_name = name
                    st.session_state.logged_in = True
                    st.success(f"Welcome to the league, {name}!")
                    st.rerun()
                else:
                    st.error("Registration failed. Please try again.")
            else:
                st.error("Please fill in both name and email.")


def show_sidebar_navigation(data_manager):
    """Show sidebar navigation for logged-in users"""
    st.sidebar.title("🍰 Fantasy GBBO")
    st.sidebar.write(f"Welcome, {st.session_state.user_name}!")

    # Navigation
    pages = {
        "📝 Submit Picks": "submit_picks",
        "🏆 Leaderboard": "leaderboard",
        "ℹ️ Info": "info",
        "⚙️ Admin": "admin",
    }

    selected_page = st.sidebar.radio("Navigate to:", list(pages.keys()))

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.rerun()

    return pages[selected_page]


def main():
    """Main application function"""
    init_session_state()
    data_manager = init_data_manager()

    # Test database connection
    try:
        # Simple test query to ensure database is working
        data_manager.get_all_users()
        # Database is working
    except Exception as e:
        st.error("Database connection failed. Please check your connection settings.")
        st.error(f"Error: {e}")
        st.stop()

    if not st.session_state.logged_in:
        show_login_form(data_manager)
    else:
        # Show main app
        selected_page = show_sidebar_navigation(data_manager)

        # Route to selected page
        if selected_page == "submit_picks":
            submit_picks_page.show_page(data_manager, st.session_state.user_email)
        elif selected_page == "leaderboard":
            leaderboard_page.show_page(data_manager)
        elif selected_page == "info":
            info_page.show_page()
        elif selected_page == "admin":
            admin_page.show_page(data_manager)


if __name__ == "__main__":
    main()
