import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, Any
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

# Page configuration
st.set_page_config(
    page_title="Great Fantasy Bake Off League",
    page_icon="🧁",
    layout="wide"
)

# --- Central dictionary for week dates ---
# Easily update this for a new season. Dates are based on the 2025 calendar.
WEEK_DATES = {
    "2": "Week 2 (9/11)",
    "3": "Week 3 (9/18)",
    "4": "Week 4 (9/25)",
    "5": "Week 5 (10/2)",
    "6": "Week 6 (10/9)",
    "7": "Week 7 (10/16)",
    "8": "Week 8 (10/23)",
    "9": "Week 9 (10/30)",
    "10": "Week 10 (11/6)",
    "11": "Week 11 (11/13)",
}

# --- DATA PERSISTENCE FUNCTIONS ---
def load_data():
    """Load all data from JSON files"""
    data = {'users': {}, 'bakers': [], 'picks': {}, 'results': {}}
    for key in data.keys():
        filename = f"{key}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                    if content:
                        data[key] = json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError):
                pass  # Ignore if file is empty or doesn't exist
    return data

def save_data(data_type, data_to_save):
    """Save specific data type to JSON file"""
    filename = f"{data_type}.json"
    with open(filename, 'w') as f:
        json.dump(data_to_save, f, indent=2, default=str)

# --- EMAIL CONFIRMATION FUNCTION ---
def send_confirmation_email(recipient_email: str, user_name: str, week_display: str, picks: Dict[str, Any]):
    """Sends a confirmation email to the user with their submitted picks."""
    try:
        creds = st.secrets["email_credentials"]
        sender_name = creds["sender_name"]
        sender_email = creds["sender_email"]
        sender_password = creds["sender_password"]
    except (KeyError, FileNotFoundError):
        st.warning("Email credentials not configured in st.secrets. Confirmation email not sent.", icon="⚠️")
        return

    msg = EmailMessage()
    msg['Subject'] = f"🧁 Bake Off Fantasy Picks Confirmation - {week_display}"
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = recipient_email

    body = f"""
    <html>
    <head>
        <style>body{{font-family:sans-serif;}} .container{{padding:20px; border:1px solid #ddd; border-radius:8px; max-width:600px;}}</style>
    </head>
    <body>
        <div class="container">
            <h2>Hi {user_name},</h2>
            <p>Your fantasy picks for <strong>{week_display}</strong> have been successfully submitted!</p>
            <p>Here's a summary of your selections:</p>
            <ul>
                <li><strong>⭐ Star Baker:</strong> {picks.get('star_baker', 'N/A')}</li>
                <li><strong>🏆 Technical Winner:</strong> {picks.get('technical_winner', 'N/A')}</li>
                <li><strong>🤝 Handshake Prediction:</strong> {'Yes' if picks.get('handshake_prediction') else 'No'}</li>
            </ul>
            <h3>Your Season Predictions:</h3>
            <ul>
                <li><strong>👑 Season Winner:</strong> {picks.get('season_winner', 'N/A')}</li>
                <li><strong>🥈 Finalist #1:</strong> {picks.get('finalist_1', 'N/A')}</li>
                <li><strong>🥉 Finalist #2:</strong> {picks.get('finalist_2', 'N/A')}</li>
            </ul>
            <p>Good luck! May your predictions rise to the occasion. 🎂</p>
        </div>
    </body>
    </html>
    """
    msg.set_content("This is a fallback for plain-text email clients.")
    msg.add_alternative(body, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        st.info(f"A confirmation email has been sent to {recipient_email}.")
    except Exception as e:
        st.error(f"Failed to send confirmation email. Check SMTP credentials. Error: {e}")

# --- INITIALIZE SESSION STATE & SCORING LOGIC ---
if 'data' not in st.session_state:
    st.session_state.data = load_data()

def calculate_user_scores(data):
    scores = {}
    for user_id, user_picks in data.get('picks', {}).items():
        weekly_points = 0
        foresight_points = 0
        for week, picks in user_picks.items():
            results = data.get('results', {}).get(week)
            if results:
                if picks.get('star_baker') == results.get('star_baker'): weekly_points += 5
                if picks.get('technical_winner') == results.get('technical_winner'): weekly_points += 3
                if picks.get('handshake_prediction') and results.get('handshake_given'): weekly_points += 10
        scores[user_id] = {'weekly_points': weekly_points, 'foresight_points': foresight_points, 'total_points': weekly_points + foresight_points}
    return scores

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧁 Fantasy Bake Off")
page = st.sidebar.selectbox("Navigate to:", ["🏆 Leaderboard & Stats", "📝 Submit Picks", "📖 Info Page", "⚙️ Admin Panel"])

# --- LEADERBOARD & STATS PAGE ---
if page == "🏆 Leaderboard & Stats":
    st.title("🏆 Great Fantasy Bake Off League")
    data = st.session_state.data
    if not data.get('users'):
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
    else:
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
            df.index = df.index + 1
            st.dataframe(df, use_container_width=True)

        with st.expander("📋 View All Picks History"):
            if data.get('picks'):
                all_weeks = sorted(set(w for picks in data['picks'].values() for w in picks.keys()), key=int)
                for week_key in all_weeks:
                    display_name = WEEK_DATES.get(week_key, f"Week {week_key}")
                    with st.expander(f"{display_name} Predictions"):
                        week_picks_data = []
                        for user_id, user_picks in data['picks'].items():
                            if week_key in user_picks:
                                picks = user_picks[week_key]
                                user_record = data.get('users', {}).get(user_id, {})
                                player_name = user_record.get('name', f'Deleted User ({user_id})')
                                week_picks_data.append({
                                    'Player': player_name,
                                    'Star Baker': picks.get('star_baker', ''),
                                    'Technical': picks.get('technical_winner', ''),
                                    'Handshake': '✓' if picks.get('handshake_prediction') else '✗',
                                    'Season Winner': picks.get('season_winner', ''),
                                    'Submitted': picks.get('submitted_at', '')[:16] if picks.get('submitted_at') else ''
                                })
                        if week_picks_data:
                            st.dataframe(pd.DataFrame(week_picks_data), use_container_width=True, hide_index=True)

# --- SUBMIT PICKS PAGE ---
elif page == "📝 Submit Picks":
    st.title("📝 Submit Your Weekly Picks")
    data = st.session_state.data
    st.subheader("1. Player Profile")

    if 'selected_user' not in st.session_state: st.session_state.selected_user = None
    player_options = {uid: uinfo.get('name', f'Unknown User ({uid})') for uid, uinfo in data.get('users', {}).items()}
    selection = st.selectbox("Select your profile or create a new one:", options=[None, "➕ New Player"] + list(player_options.keys()), format_func=lambda x: "--- Select ---" if x is None else ("Create New Profile" if x == "➕ New Player" else player_options.get(x, "Unknown")))

    if selection == "➕ New Player":
        with st.form("new_player_form"):
            new_name = st.text_input("Your Name:")
            new_email = st.text_input("Your Email (for confirmations):")
            if st.form_submit_button("Create Profile"):
                if new_name and new_email and '@' in new_email and '.' in new_email:
                    user_id = f"user_{len(data.get('users', {})) + 1}"
                    if 'users' not in data: data['users'] = {}
                    data['users'][user_id] = {'name': new_name, 'email': new_email}
                    save_data('users', data['users'])
                    st.session_state.selected_user = user_id
                    st.success(f"Profile for {new_name} created!")
                    st.rerun()
                else: st.error("Please enter a valid name and email address.")
    elif selection: st.session_state.selected_user = selection

    if st.session_state.selected_user:
        user_id = st.session_state.selected_user
        user_name = data.get('users', {}).get(user_id, {}).get('name', "Player")
        user_email = data.get('users', {}).get(user_id, {}).get('email', "")
        st.success(f"Welcome, **{user_name}**! You're ready to submit your picks.")

        week_options = list(WEEK_DATES.keys())
        selected_week_key = st.selectbox("Select Week:", options=week_options, format_func=lambda key: WEEK_DATES.get(key, f"Week {key}"))

        if user_id not in data['picks']: data['picks'][user_id] = {}
        existing_picks = data['picks'][user_id].get(selected_week_key, {})
        available_bakers = data.get('bakers') or [f"Baker {chr(65+i)}" for i in range(12)]

        st.markdown("""
        Each week you are making two different sets of predictions. 
        - First, you'll select Star Baker and Technical Winner for next week, with a bonus guess on if a handshake will be awarded.
        - Second, you'll make a prediction about the end of the season. Who will win? Who will the other two finalists be?
        You can stick with the same picks from week to week, if those bakers are still active, or you can switch as needed.

        Additionally, if you submit your choices, feel free to come back to this page and submit again. 
        
        You should receive an email confirming your submission shortly after hitting submit.
        """)
        with st.form(f"picks_week_{selected_week_key}_{user_id}"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("2. Make Your Weekly Predictions")
                star_baker = st.selectbox("⭐ Who will be Star Baker:", available_bakers, index=available_bakers.index(existing_picks.get('star_baker', available_bakers[0])) if existing_picks.get('star_baker') in available_bakers else 0)
                technical_winner = st.selectbox("🏆 Who will win the Technical:", available_bakers, index=available_bakers.index(existing_picks.get('technical_winner', available_bakers[0])) if existing_picks.get('technical_winner') in available_bakers else 0)
                handshake_prediction = st.checkbox("🤝 Will there be a Hollywood Handshake?", value=existing_picks.get('handshake_prediction', False))
            with col2:
                st.subheader("3. Make your End of Season Predictions")
                season_winner = st.selectbox("👑 Season Winner:", available_bakers, index=available_bakers.index(existing_picks.get('season_winner', available_bakers[0])) if existing_picks.get('season_winner') in available_bakers else 0)
                finalist_1 = st.selectbox("🥈 Finalist #1:", available_bakers, index=available_bakers.index(existing_picks.get('finalist_1', available_bakers[1])) if existing_picks.get('finalist_1') in available_bakers else 1)
                finalist_2 = st.selectbox("🥉 Finalist #2:", available_bakers, index=available_bakers.index(existing_picks.get('finalist_2', available_bakers[2])) if existing_picks.get('finalist_2') in available_bakers else 2)
            
            if st.form_submit_button("Submit & Lock In Picks"):
                picks_data = {'star_baker': star_baker, 'technical_winner': technical_winner, 'handshake_prediction': handshake_prediction, 'season_winner': season_winner, 'finalist_1': finalist_1, 'finalist_2': finalist_2, 'submitted_at': datetime.now().isoformat()}
                data['picks'][user_id][selected_week_key] = picks_data
                save_data('picks', data['picks'])
                
                display_week_name = WEEK_DATES.get(selected_week_key, f"Week {selected_week_key}")
                st.success(f"✅ Your picks for {display_week_name} have been submitted!")
                st.balloons()

                if user_email:
                    send_confirmation_email(recipient_email=user_email, user_name=user_name, week_display=display_week_name, picks=picks_data)

# --- INFO PAGE ---
elif page == "📖 Info Page":
    st.title("📖 Info Page")
    st.header("Welcome to the Great Fantasy Bake Off League!")
    st.markdown("""
    On your marks, get set, predict! This season, we’re adding a new layer of fun to our weekly viewing with a fantasy league. 
    The goal is simple: prove you have the best eye for baking talent by accurately predicting both the weekly events and the season's ultimate champions.
    
    The game is all about prediction. Each week you'll make a new set of picks, and your foresight will be rewarded with points. May the best Star Predictor win!
    """)
    st.markdown("---")

    st.subheader("How to Play: Your Weekly Signature Bake")
    st.markdown("""
    Each week of the competition (starting with Episode 2), you will submit a fresh set of predictions before the episode airs.
    Your weekly submission must include five predictions:
    - **Star Baker**: Who will be the week's top baker?
    - **Technical Challenge Winner**: Who will come in first in the technical?
    - **Hollywood Handshake**: Will anyone get a handshake? (Optional, high-reward pick).
    - **Predicted Season Winner**: Who do you think will win the entire competition?
    - **Predicted Finalists (x2)**: Who will the other two finalists be?

    Your predictions for the season winner and finalists can change week to week as you see how the bakers perform.
    """)
    st.markdown("---")
    
    st.subheader("Scoring: The Recipe for Victory")
    st.markdown("Your grand total will be a combination of two types of points: **Weekly Points** and **Foresight Points**.")
    
    st.write("#### 1. Weekly Points")
    st.markdown("These are straightforward points for correctly predicting the episode's key events.")
    st.markdown("""
    | Correct Prediction         | Points Awarded |
    |----------------------------|----------------|
    | Hollywood Handshake        | 10 points      |
    | Star Baker                 | 5 points       |
    | Technical Challenge Winner | 3 points       |
    """)

    st.write("#### 2. Foresight Points: The Weighted Bonus")
    st.markdown("""
    This is where strategy comes in. You get points for correctly predicting the season's winner and finalists, 
    but correct predictions made **earlier in the season are worth exponentially more**.

    Your season outcome predictions are logged each week. At the end of the season, we'll go back and award points for every single time you correctly predicted the outcome.
    - **The Formula**: A correct pick is multiplied by a factor that decreases each week. A correct **winner** prediction is worth **20 base points**, and a correct **finalist** is worth **10**.
    - **Example**: Correctly predicting the season winner in Week 2 is worth **180 points** `((11-2) x 20)`. Waiting until the semi-final in Week 9 to make that same correct prediction is only worth **40 points** `((11-9) x 20)`.

    This system rewards those who can spot the champion from the very beginning!
    """)
    st.markdown("---")

    st.subheader("Rules of the Tent")
    st.markdown("""
    - **Submission Deadline**: All weekly predictions must be submitted to the commissioner at least one hour before the episode's UK airtime.
    - **Baker Withdrawals**: If a baker leaves the competition for personal or medical reasons, it does not count as a standard elimination. Any predictions involving that baker for that week are considered void, and no points are awarded or lost.
    """)
    st.info("That's it! Keep your eyes on the bakes, trust your instincts, and get ready for a fantastic season. Good luck!")

# --- ADMIN PANEL PAGE ---
elif page == "⚙️ Admin Panel":
    st.title("⚙️ Commissioner Admin Panel")
    admin_password = st.text_input("Enter admin password:", type="password", key="admin_pw")
    
    if admin_password == "bakeoff2024":
        data = st.session_state.data
        tab1, tab2, tab3, tab4 = st.tabs(["Episode Results", "Manage Bakers", "Manage Players", "Data Management"])

        with tab1:
            st.subheader("Enter Episode Results")
            week_options = list(WEEK_DATES.keys())
            result_week_key = st.selectbox("Select Week:", options=week_options, format_func=lambda key: WEEK_DATES.get(key, f"Week {key}"), key="admin_week_select")
            
            existing_results = data.get('results', {}).get(result_week_key, {})
            baker_options = [""] + data.get('bakers', [])
            
            with st.form(f"results_week_{result_week_key}"):
                col1, col2 = st.columns(2)
                with col1:
                    star_baker_result = st.selectbox("⭐ Actual Star Baker:", baker_options, index=baker_options.index(existing_results.get('star_baker')) if existing_results.get('star_baker') in baker_options else 0)
                    technical_winner_result = st.selectbox("🏆 Technical Challenge Winner:", baker_options, index=baker_options.index(existing_results.get('technical_winner')) if existing_results.get('technical_winner') in baker_options else 0)
                with col2:
                    handshake_given = st.checkbox("🤝 Was a Hollywood Handshake given?", value=existing_results.get('handshake_given', False))
                    eliminated_baker = st.selectbox("😢 Baker Eliminated:", baker_options, index=baker_options.index(existing_results.get('eliminated_baker')) if existing_results.get('eliminated_baker') in baker_options else 0)

                if st.form_submit_button("Save Episode Results"):
                    if 'results' not in data: data['results'] = {}
                    data['results'][result_week_key] = {'star_baker': star_baker_result, 'technical_winner': technical_winner_result, 'handshake_given': handshake_given, 'eliminated_baker': eliminated_baker, 'updated_at': datetime.now().isoformat()}
                    save_data('results', data['results'])
                    st.success(f"✅ Results for {WEEK_DATES.get(result_week_key)} saved!")

        with tab2:
            st.subheader("Manage Bakers")
            new_baker = st.text_input("Add new baker:")
            if st.button("Add Baker") and new_baker:
                if 'bakers' not in data: data['bakers'] = []
                if new_baker not in data['bakers']:
                    data['bakers'].append(new_baker)
                    save_data('bakers', data['bakers'])
                    st.success(f"Added {new_baker}")
                    st.rerun()

            if data.get('bakers'):
                baker_to_remove = st.selectbox("Remove baker:", [""] + data['bakers'])
                if st.button("Remove Baker") and baker_to_remove:
                    data['bakers'].remove(baker_to_remove)
                    save_data('bakers', data['bakers'])
                    st.success(f"Removed {baker_to_remove}")
                    st.rerun()

            st.write("**Current Bakers:**", ", ".join(data.get('bakers', [])))

        with tab3:
            st.subheader("Manage Players & Emails")
            if not data.get('users'):
                st.info("No players have registered yet.")
            else:
                player_df = pd.DataFrame([{'User ID': uid, 'Name': uinfo.get('name'), 'Email': uinfo.get('email', 'N/A')} for uid, uinfo in data['users'].items()])
                st.dataframe(player_df, use_container_width=True, hide_index=True)
                st.markdown("---")
                st.subheader("✏️ Edit or Remove a Player")

                player_list = list(data.get('users', {}).keys())
                player_to_edit = st.selectbox("Select a player to manage:", options=[""] + player_list, format_func=lambda uid: data.get('users', {}).get(uid, {}).get('name', 'Unknown') if uid else "--- Select a Player ---")

                if player_to_edit:
                    user_info = data.get('users', {}).get(player_to_edit, {})
                    user_name_safe = user_info.get('name', 'This Player')
                    with st.form(f"edit_player_{player_to_edit}"):
                        st.write(f"**Editing Profile for: {user_name_safe}**")
                        new_name = st.text_input("Player Name", value=user_info.get('name', ''))
                        new_email = st.text_input("Player Email", value=user_info.get('email', ''))
                        if st.form_submit_button("💾 Save Changes"):
                            data['users'][player_to_edit]['name'] = new_name
                            data['users'][player_to_edit]['email'] = new_email
                            save_data('users', data['users'])
                            st.success(f"✅ Player '{new_name}' has been updated.")
                            st.rerun()

                    with st.expander("🗑️ Remove Player (Permanent)"):
                        st.warning(f"**Warning:** This will permanently delete **{user_name_safe}** and all of their submitted picks. This action cannot be undone.")
                        if st.button(f"DELETE {user_name_safe}'s Profile", type="primary"):
                            del data['users'][player_to_edit]
                            save_data('users', data['users'])
                            if player_to_edit in data.get('picks', {}):
                                del data['picks'][player_to_edit]
                                save_data('picks', data['picks'])
                            st.success(f"🗑️ Player '{user_name_safe}' and all their data have been removed.")
                            st.rerun()

        with tab4:
            st.subheader("Data Management")
            if st.button("Download All Data as JSON"):
                all_data_str = json.dumps(st.session_state.data, indent=2)
                st.download_button(label="📥 Click to Download", data=all_data_str, file_name=f"bakeoff_backup_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")

            with st.expander("⚠️ Reset All Data (Permanent)"):
                st.warning("This will delete all users, picks, and results. This cannot be undone.")
                if st.button("RESET ALL LEAGUE DATA", type="primary"):
                    for key in ['users', 'bakers', 'picks', 'results']:
                        if os.path.exists(f"{key}.json"):
                            os.remove(f"{key}.json")
                    st.session_state.data = load_data()
                    st.success("All league data has been reset.")
                    st.rerun()

    elif admin_password:
        st.error("❌ Incorrect admin password")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.markdown("🧁 *May the best Star Predictor win!*")
