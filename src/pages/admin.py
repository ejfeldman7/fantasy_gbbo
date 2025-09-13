import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.config import WEEK_DATES
from src.data_manager import DataManager


def show_page(data_manager: DataManager):
    st.title("⚙️ Commissioner Admin Panel")

    try:
        admin_secret = st.secrets["admin_panel"]["admin_password"]
    except (KeyError, FileNotFoundError):
        st.error(
            "Admin password not configured in secrets.toml. Please add `[admin_panel]` section with `admin_password`."
        )
        return

    admin_password = st.text_input(
        "Enter admin password:", type="password", key="admin_pw"
    )
    if admin_password == admin_secret:
        # Admin controls at the top
        st.subheader("🎛️ Admin Controls")

        # Initialize session state for admin settings
        if "admin_allow_all_weeks" not in st.session_state:
            st.session_state.admin_allow_all_weeks = False

        col1, col2 = st.columns([1, 3])
        with col1:
            allow_all_weeks = st.checkbox(
                "🗓️ Allow picks for all weeks",
                value=st.session_state.admin_allow_all_weeks,
                help="When enabled, users can submit picks for any week regardless of deadlines",
            )
            if allow_all_weeks != st.session_state.admin_allow_all_weeks:
                st.session_state.admin_allow_all_weeks = allow_all_weeks
                if allow_all_weeks:
                    st.success("✅ All weeks are now available for picks!")
                else:
                    st.info("📅 Normal week restrictions applied.")

        with col2:
            if st.session_state.admin_allow_all_weeks:
                st.warning(
                    "⚠️ **Admin Override Active**: Users can submit picks for any week"
                )
            else:
                st.info("📅 Normal deadline restrictions in effect")

        st.markdown("---")

        tabs = st.tabs(
            [
                "Episode Results",
                "Manage Bakers",
                "Manage Players",
                "Data Management",
            ]
        )
        with tabs[0]:
            _show_episode_results_tab(data_manager)
        with tabs[1]:
            _show_manage_bakers_tab(data_manager)
        with tabs[2]:
            _show_manage_players_tab(data_manager)
        with tabs[3]:
            _show_data_management_tab(data_manager)

    elif admin_password:
        st.error("❌ Incorrect admin password")


def _show_episode_results_tab(dm: DataManager):
    st.subheader("Enter Episode Results")
    week_options = list(WEEK_DATES.keys())
    result_week_key = st.selectbox(
        "Select Week:",
        options=week_options,
        format_func=lambda key: WEEK_DATES.get(key, f"Week {key}"),
        key="admin_week_select",
    )

    # Get existing results for this week from database
    existing_results = dm.get_weekly_results(int(result_week_key)) or {}

    # Get bakers from database
    bakers = dm.get_active_bakers()
    baker_options = [""] + bakers

    with st.form(f"results_week_{result_week_key}"):
        col1, col2 = st.columns(2)
        with col1:
            sb = st.selectbox(
                "⭐ Actual Star Baker:",
                baker_options,
                index=baker_options.index(existing_results.get("star_baker", ""))
                if existing_results.get("star_baker") in baker_options
                else 0,
            )
            tw = st.selectbox(
                "🏆 Technical Winner:",
                baker_options,
                index=baker_options.index(existing_results.get("technical_winner", ""))
                if existing_results.get("technical_winner") in baker_options
                else 0,
            )
        with col2:
            hh = st.checkbox(
                "🤝 Was a Handshake given?",
                value=existing_results.get("hollywood_handshake", False),
            )
            eb = st.selectbox(
                "😢 Baker Eliminated:",
                baker_options,
                index=baker_options.index(existing_results.get("eliminated_baker", ""))
                if existing_results.get("eliminated_baker") in baker_options
                else 0,
            )

        if st.form_submit_button("Save Episode Results"):
            results_data = {
                "star_baker": sb,
                "technical_winner": tw,
                "hollywood_handshake": hh,
                "eliminated_baker": eb,
            }

            if dm.save_weekly_results(int(result_week_key), results_data):
                st.success(f"✅ Results for {WEEK_DATES.get(result_week_key)} saved!")

                # If a baker was eliminated, mark them as eliminated in the database
                if eb and eb != "":
                    dm.eliminate_baker(eb, int(result_week_key))
                    st.success(f"🏠 {eb} has been marked as eliminated.")
            else:
                st.error("Failed to save results. Please try again.")


def _show_manage_bakers_tab(dm: DataManager):
    st.subheader("Manage Bakers")

    # Add new baker
    new_baker = st.text_input("Add new baker:")
    if st.button("Add Baker") and new_baker:
        if dm.add_baker(new_baker):
            st.success(f"Added {new_baker}")
            st.rerun()
        else:
            st.error("Failed to add baker")

    # Display all bakers
    all_bakers = dm.get_all_bakers()
    if all_bakers:
        st.subheader("Current Bakers")
        df = pd.DataFrame(all_bakers)
        st.dataframe(df[["name", "is_eliminated"]], use_container_width=True)

        # Remove baker option
        baker_names = [baker["name"] for baker in all_bakers]
        baker_to_remove = st.selectbox("Remove baker:", [""] + baker_names)
        if st.button("Remove Baker") and baker_to_remove:
            baker_id = next(
                (
                    baker["id"]
                    for baker in all_bakers
                    if baker["name"] == baker_to_remove
                ),
                None,
            )
            if baker_id and dm.delete_baker(baker_id):
                st.success(f"Removed {baker_to_remove}")
                st.rerun()
            else:
                st.error("Failed to remove baker")
    else:
        st.info("No bakers added yet.")


def _show_manage_players_tab(dm: DataManager):
    st.subheader("Manage Players & Emails")

    # Get all users from database
    users = dm.get_all_users()
    if not users:
        st.info("No players have registered yet.")
        return

    # Display users table
    player_df = pd.DataFrame(
        [
            {
                "ID": user["id"],
                "Name": user["name"],
                "Email": user["email"],
                "Created": str(user.get("created_at", ""))[:16]
                if user.get("created_at")
                else "",
            }
            for user in users
        ]
    )
    st.dataframe(
        player_df[["Name", "Email", "Created"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("✏️ Edit or Remove a Player")

    # Player selection dropdown
    player_options = [""] + [f"{user['name']} ({user['email']})" for user in users]
    selected_player = st.selectbox("Select a player to manage:", options=player_options)

    if selected_player and selected_player != "":
        # Find the selected user
        user_email = selected_player.split("(")[1].split(")")[0]
        user = next((u for u in users if u["email"] == user_email), None)

        if user:
            with st.form(f"edit_player_{user['id']}"):
                st.write(f"**Editing Profile for: {user['name']}**")
                new_name = st.text_input("Player Name", value=user["name"])
                new_email = st.text_input("Player Email", value=user["email"])
                if st.form_submit_button("💾 Save Changes"):
                    if dm.update_user(user["id"], new_name, new_email):
                        st.success(f"✅ Player '{new_name}' has been updated.")
                        st.rerun()
                    else:
                        st.error("Failed to update player.")

            with st.expander("🗑️ Remove Player (Permanent)"):
                st.warning(
                    f"**Warning:** This will permanently delete **{user['name']}** and all of their picks."
                )
                if st.button(f"DELETE {user['name']}'s Profile", type="primary"):
                    if dm.delete_user(user["id"]):
                        st.success(f"🗑️ Player '{user['name']}' and all data removed.")
                        st.rerun()
                    else:
                        st.error("Failed to delete player.")


def _show_data_management_tab(dm: DataManager):
    st.subheader("Data Management")

    # Backup data
    if st.button("Create Data Backup"):
        backup_data = dm.backup_data()
        if backup_data:
            backup_str = json.dumps(backup_data, indent=2, default=str)
            st.download_button(
                label="📥 Click to Download Backup",
                data=backup_str,
                file_name=f"bakeoff_backup_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
            )
            st.success("Backup created successfully!")
        else:
            st.error("Failed to create backup")

    # Show data summary
    st.subheader("📊 Data Summary")
    users = dm.get_all_users()
    all_picks = dm.get_all_picks()
    all_bakers = dm.get_all_bakers()
    weekly_results = dm.get_all_weekly_results()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Users", len(users))
    with col2:
        st.metric("Total Picks", len(all_picks))
    with col3:
        st.metric("Bakers", len(all_bakers))
    with col4:
        st.metric("Weekly Results", len(weekly_results))

    # Reset data
    with st.expander("⚠️ Reset All Data (Permanent)"):
        st.warning(
            "This will delete all users, picks, bakers, and results. This cannot be undone."
        )
        if st.button("RESET ALL LEAGUE DATA", type="primary"):
            if dm.reset_all_data():
                st.success("All league data has been reset.")
                st.rerun()
            else:
                st.error("Failed to reset data")
