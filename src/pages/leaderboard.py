from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.config import REVEAL_DATES_UTC, WEEK_DATES
from src.data_manager import DataManager
from src.scoring import calculate_user_scores


def show_page(data_manager: DataManager):
    st.title("🏆 Great Fantasy Bake Off League")

    # Get users from database
    users = data_manager.get_all_users()
    if not users:
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
        return

    # For now, create a simplified leaderboard showing users and their pick counts
    # TODO: Implement proper scoring system with database queries
    leaderboard_data = []
    for user in users:
        # Count how many weeks this user has submitted picks
        # This is a temporary implementation - proper scoring would calculate points
        user_picks = data_manager.get_all_picks()
        user_pick_count = len(
            [pick for pick in user_picks if pick.get("user_name") == user["name"]]
        )

        leaderboard_data.append(
            {
                "Player": user["name"],
                "Picks Submitted": user_pick_count,
                "Email": user["email"],
            }
        )

    if leaderboard_data:
        st.subheader("Current Standings")
        st.info(
            "🚧 Scoring system is being updated. Currently showing pick submission counts."
        )
        df = (
            pd.DataFrame(leaderboard_data)
            .sort_values("Picks Submitted", ascending=False)
            .reset_index(drop=True)
        )
        df.index += 1
        st.dataframe(df[["Player", "Picks Submitted"]], use_container_width=True)

    with st.expander("📋 View All Picks History"):
        all_picks = data_manager.get_all_picks()
        if all_picks:
            now_utc = datetime.now(timezone.utc)

            # Group picks by week
            weeks_with_picks = {}
            for pick in all_picks:
                week = str(pick.get("week_number", ""))
                if week not in weeks_with_picks:
                    weeks_with_picks[week] = []
                weeks_with_picks[week].append(pick)

            # Sort weeks numerically
            sorted_weeks = sorted(
                weeks_with_picks.keys(), key=lambda x: int(x) if x.isdigit() else 0
            )

            revealed_weeks_count = 0
            for week_key in sorted_weeks:
                reveal_date = REVEAL_DATES_UTC.get(week_key)
                if reveal_date and now_utc > reveal_date:
                    revealed_weeks_count += 1
                    display_name = WEEK_DATES.get(week_key, f"Week {week_key}")
                    with st.expander(f"{display_name} Predictions"):
                        week_picks_data = []
                        for pick in weeks_with_picks[week_key]:
                            week_picks_data.append(
                                {
                                    "Player": pick.get("user_name", "Unknown"),
                                    "Star Baker": pick.get("star_baker", ""),
                                    "Technical": pick.get("technical_winner", ""),
                                    "Eliminated": pick.get("eliminated_baker", ""),
                                    "Handshake": "✓"
                                    if pick.get("hollywood_handshake")
                                    else "✗",
                                    "Season Winner": pick.get("season_winner", ""),
                                    "Submitted": str(pick.get("submitted_at", ""))[:16]
                                    if pick.get("submitted_at")
                                    else "",
                                }
                            )
                        if week_picks_data:
                            st.dataframe(
                                pd.DataFrame(week_picks_data),
                                use_container_width=True,
                                hide_index=True,
                            )

            if revealed_weeks_count == 0:
                st.caption(
                    "Picks for past weeks will be revealed here after the submission deadline has passed."
                )
        else:
            st.info("No picks submitted yet.")
