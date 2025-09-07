import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.config import WEEK_DATES
from src.data_manager import DataManager
from src.email_utils import send_commissioner_update_email
from src.scoring import calculate_user_scores, run_final_scoring


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
        tabs = st.tabs(
            [
                "Episode Results",
                "Manage Bakers",
                "Manage Players",
                "Data Management",
                "🏆 Final Scoring",
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
        with tabs[4]:
            _show_final_scoring_tab(data_manager)

    elif admin_password:
        st.error("❌ Incorrect admin password")


def _show_episode_results_tab(dm: DataManager):
    st.subheader("Enter Episode Results")
    data = dm.get_data()
    week_options = list(WEEK_DATES.keys())
    result_week_key = st.selectbox(
        "Select Week:",
        options=week_options,
        format_func=lambda key: WEEK_DATES.get(key, f"Week {key}"),
        key="admin_week_select",
    )

    existing_results = data.get("results", {}).get(result_week_key, {})
    baker_options = [""] + data.get("bakers", [])

    with st.form(f"results_week_{result_week_key}"):
        col1, col2 = st.columns(2)
        with col1:
            sb = st.selectbox(
                "⭐ Actual Star Baker:",
                baker_options,
                index=baker_options.index(existing_results.get("star_baker"))
                if existing_results.get("star_baker") in baker_options
                else 0,
            )
            tw = st.selectbox(
                "🏆 Technical Winner:",
                baker_options,
                index=baker_options.index(existing_results.get("technical_winner"))
                if existing_results.get("technical_winner") in baker_options
                else 0,
            )
        with col2:
            hh = st.checkbox(
                "🤝 Was a Handshake given?",
                value=existing_results.get("handshake_given", False),
            )
            eb = st.selectbox(
                "😢 Baker Eliminated:",
                baker_options,
                index=baker_options.index(existing_results.get("eliminated_baker"))
                if existing_results.get("eliminated_baker") in baker_options
                else 0,
            )

        if st.form_submit_button("Save Episode Results"):
            results_data = {
                "star_baker": sb,
                "technical_winner": tw,
                "handshake_given": hh,
                "eliminated_baker": eb,
                "updated_at": datetime.now().isoformat(),
            }
            data["results"][result_week_key] = results_data
            dm.save_data("results")
            st.success(f"✅ Results for {WEEK_DATES.get(result_week_key)} saved!")

            # Trigger commissioner email
            updated_scores = calculate_user_scores(data)
            df_data = [
                {
                    "Player": data["users"].get(uid, {}).get("name"),
                    "Weekly": s["weekly_points"],
                    "Foresight": s["foresight_points"],
                    "Total": s["total_points"],
                }
                for uid, s in updated_scores.items()
            ]
            leaderboard_df = pd.DataFrame(df_data).sort_values("Total", ascending=False)
            leaderboard_df.index = range(1, len(leaderboard_df) + 1)
            send_commissioner_update_email(
                WEEK_DATES.get(result_week_key), results_data, leaderboard_df
            )


def _show_manage_bakers_tab(dm: DataManager):
    st.subheader("Manage Bakers")
    data = dm.get_data()
    new_baker = st.text_input("Add new baker:")
    if st.button("Add Baker") and new_baker:
        if new_baker not in data["bakers"]:
            data["bakers"].append(new_baker)
            dm.save_data("bakers")
            st.success(f"Added {new_baker}")
            st.rerun()

    if data.get("bakers"):
        baker_to_remove = st.selectbox("Remove baker:", [""] + data["bakers"])
        if st.button("Remove Baker") and baker_to_remove:
            data["bakers"].remove(baker_to_remove)
            dm.save_data("bakers")
            st.success(f"Removed {baker_to_remove}")
            st.rerun()
    st.write("**Current Bakers:**", ", ".join(data.get("bakers", [])))


def _show_manage_players_tab(dm: DataManager):
    st.subheader("Manage Players & Emails")
    data = dm.get_data()
    if not data.get("users"):
        st.info("No players have registered yet.")
        return

    player_df = pd.DataFrame(
        [
            {
                "User ID": uid,
                "Name": uinfo.get("name"),
                "Email": uinfo.get("email", "N/A"),
            }
            for uid, uinfo in data["users"].items()
        ]
    )
    st.dataframe(player_df, use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("✏️ Edit or Remove a Player")

    player_list = list(data.get("users", {}).keys())
    player_to_edit = st.selectbox(
        "Select a player to manage:",
        options=[""] + player_list,
        format_func=lambda uid: data.get("users", {})
        .get(uid, {})
        .get("name", "Unknown")
        if uid
        else "--- Select a Player ---",
    )

    if player_to_edit:
        user_info = data["users"][player_to_edit]
        with st.form(f"edit_player_{player_to_edit}"):
            st.write(f"**Editing Profile for: {user_info.get('name')}**")
            new_name = st.text_input("Player Name", value=user_info.get("name", ""))
            new_email = st.text_input("Player Email", value=user_info.get("email", ""))
            if st.form_submit_button("💾 Save Changes"):
                data["users"][player_to_edit]["name"] = new_name
                data["users"][player_to_edit]["email"] = new_email
                dm.save_data("users")
                st.success(f"✅ Player '{new_name}' has been updated.")
                st.rerun()

        with st.expander("🗑️ Remove Player (Permanent)"):
            st.warning(
                f"**Warning:** This will permanently delete **{user_info.get('name')}** and all of their picks."
            )
            if st.button(f"DELETE {user_info.get('name')}'s Profile", type="primary"):
                del data["users"][player_to_edit]
                if player_to_edit in data.get("picks", {}):
                    del data["picks"][player_to_edit]
                    dm.save_data("picks")
                dm.save_data("users")
                st.success(f"🗑️ Player '{user_info.get('name')}' and all data removed.")
                st.rerun()


def _show_data_management_tab(dm: DataManager):
    st.subheader("Data Management")
    if st.button("Download All Data as JSON"):
        all_data_str = json.dumps(dm.get_data(), indent=2)
        st.download_button(
            label="📥 Click to Download",
            data=all_data_str,
            file_name=f"bakeoff_backup_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )

    with st.expander("⚠️ Reset All Data (Permanent)"):
        st.warning(
            "This will delete all users, picks, and results. This cannot be undone."
        )
        if st.button("RESET ALL LEAGUE DATA", type="primary"):
            dm.reset_all_data()
            st.success("All league data has been reset.")
            st.rerun()


def _show_final_scoring_tab(dm: DataManager):
    st.subheader("🏆 Final Season Scoring")
    st.info(
        "Use this tool **only after the season finale** to calculate final Foresight Points."
    )
    data = dm.get_data()
    baker_options = data.get("bakers", [])
    if not baker_options:
        st.warning("Please add bakers in the 'Manage Bakers' tab.")
        return

    with st.form("final_scoring_form"):
        st.write("Select the official season results:")
        final_winner = st.selectbox("👑 Season Winner", options=[""] + baker_options)
        final_finalists = st.multiselect(
            "🥈🥉 The Other Two Finalists", options=baker_options, max_selections=2
        )

        if st.form_submit_button("CALCULATE & SAVE FINAL SCORES"):
            if final_winner and len(final_finalists) == 2:
                if final_winner not in final_finalists:
                    foresight_scores = run_final_scoring(
                        data, final_winner, final_finalists
                    )
                    data["final_scores"] = foresight_scores
                    dm.save_data("final_scores")
                    st.success("Foresight Points calculated and saved successfully!")
                    st.balloons()

                    results_df = pd.DataFrame.from_dict(
                        foresight_scores, orient="index", columns=["Foresight Points"]
                    )
                    results_df.index.name = "User ID"
                    player_names = {
                        uid: u.get("name", "Unknown")
                        for uid, u in data.get("users", {}).items()
                    }
                    results_df["Player"] = results_df.index.map(player_names)
                    st.dataframe(
                        results_df[["Player", "Foresight Points"]].sort_values(
                            "Foresight Points", ascending=False
                        ),
                        use_container_width=True,
                    )
                else:
                    st.error("The winner cannot also be selected as a finalist.")
            else:
                st.error("Please select one winner and two finalists.")
