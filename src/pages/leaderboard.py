from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.config import REVEAL_DATES_UTC, WEEK_DATES
from src.data_manager import DataManager
from src.scoring import calculate_user_scores


def show_page(data_manager: DataManager):
    st.title("🏆 Great Fantasy Bake Off League")

    # Calculate scores for all users
    try:
        user_scores = calculate_user_scores(data_manager)
    except Exception as e:
        st.error(f"Error calculating scores: {e}")
        user_scores = {}

    if not user_scores:
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
        return

    # Create leaderboard data with actual scores
    leaderboard_data = []
    for email, scores in user_scores.items():
        leaderboard_data.append(
            {
                "Player": scores["user_name"],
                "Weekly Points": scores["weekly_points"],
                "Foresight Points": scores["foresight_points"],
                "Total Points": scores["total_points"],
            }
        )

    if leaderboard_data:
        st.subheader("🏆 Current Standings")

        # Show summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Players", len(leaderboard_data))
        with col2:
            total_weekly = sum(player["Weekly Points"] for player in leaderboard_data)
            st.metric("Total Weekly Points", total_weekly)
        with col3:
            total_foresight = sum(
                player["Foresight Points"] for player in leaderboard_data
            )
            st.metric("Total Foresight Points", total_foresight)

        # Main leaderboard table
        df = (
            pd.DataFrame(leaderboard_data)
            .sort_values("Total Points", ascending=False)
            .reset_index(drop=True)
        )
        df.index += 1  # Start ranking at 1
        st.dataframe(df, use_container_width=True)

        # Show scoring information
        with st.expander("📊 How Scoring Works"):
            st.markdown("""
            **Weekly Points:**
            - Star Baker: +5 points
            - Baker Sent Home: +5 points  
            - Technical Winner: +3 points
            - Handshake (correct): +10 points
            - Handshake (wrong): -10 points
            - Contradictory picks: -5 points each
            
            **Foresight Points:**
            - Season winner prediction: (11 - week) × 10 points
            - Finalist prediction: (11 - week) × 5 points
            - Earlier predictions worth more!
            """)
    else:
        st.info("No scores to display yet. Submit some picks and enter weekly results!")

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
