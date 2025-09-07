import streamlit as st
from src.data_manager import DataManager
from src.pages import leaderboard, submit_picks, info, admin

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Great Fantasy Bake Off League",
    page_icon="🧁",
    layout="wide"
)

# --- APP STATE MANAGEMENT ---
# Initialize the DataManager which loads all data from JSON files.
# The data is stored in st.session_state to persist across reruns.
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

data_manager = st.session_state.data_manager

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧁 Fantasy Bake Off [Dev]")
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏆 Leaderboard & Stats", "📝 Submit Picks", "📖 Info Page", "⚙️ Admin Panel"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("🧁 *May the best Star Predictor win!*")

# --- PAGE ROUTING ---
# Based on the user's selection, call the appropriate function from the 'pages' module.
if page == "🏆 Leaderboard & Stats":
    leaderboard.show_page(data_manager)
elif page == "📝 Submit Picks":
    submit_picks.show_page(data_manager)
elif page == "📖 Info Page":
    info.show_page()
elif page == "⚙️ Admin Panel":
    admin.show_page(data_manager)

