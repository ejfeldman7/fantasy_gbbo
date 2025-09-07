import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from src.data_manager import DataManager
from src.scoring import calculate_user_scores
from src.config import WEEK_DATES, REVEAL_DATES_UTC

def show_page(data_manager: DataManager):
    st.title("🏆 Great Fantasy Bake Off League")
    data = data_manager.get_data()

    if not data.get('users'):
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
        return

    scores = calculate_user_scores(data)
    leaderboard_data = []
    for user_id, user_info in data.get('users', {}).items():
        user_score = scores.get(user_id, {'weekly_points': 0, 'foresight_points': 0, 'total_points': 0})
        leaderboard_data.append({
            'Player': user_info.get('name', f'Unknown User ({user_id})'),
            'Weekly Points': user_score['weekly_points'],
            'Foresight Points': user_score['foresight_points'],
            'Total Points': user_score['total_points']
        })

    if leaderboard_data:
        st.subheader("Current Standings")
        df = pd.DataFrame(leaderboard_data).sort_values('Total Points', ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)

    with st.expander("📋 View All Picks History"):
        if data.get('picks'):
            now_utc = datetime.now(timezone.utc)
            all_weeks = sorted(set(w for picks in data['picks'].values() for w in picks.keys()), key=int)
            
            revealed_weeks_count = 0
            for week_key in all_weeks:
                reveal_date = REVEAL_DATES_UTC.get(week_key)
                if reveal_date and now_utc > reveal_date:
                    revealed_weeks_count += 1
                    display_name = WEEK_DATES.get(week_key, f"Week {week_key}")
                    with st.expander(f"{display_name} Predictions"):
                        week_picks_data = []
                        for user_id, user_picks in data['picks'].items():
                            if week_key in user_picks:
                                picks = user_picks[week_key]
                                player_name = data['users'].get(user_id, {}).get('name', f'Deleted User ({user_id})')
                                week_picks_data.append({
                                    'Player': player_name, 'Star Baker': picks.get('star_baker', ''),
                                    'Technical': picks.get('technical_winner', ''), 'Eliminated': picks.get('eliminated_baker', ''),
                                    'Handshake': '✓' if picks.get('handshake_prediction') else '✗',
                                    'Season Winner': picks.get('season_winner', ''),
                                    'Submitted': picks.get('submitted_at', '')[:16]
                                })
                        if week_picks_data:
                            st.dataframe(pd.DataFrame(week_picks_data), use_container_width=True, hide_index=True)
            
            if 'revealed_weeks_count' in locals() and revealed_weeks_count == 0:
                st.caption("Picks for past weeks will be revealed here after the submission deadline has passed.")
