import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import smtplib
from email.message import EmailMessage

# Page configuration
st.set_page_config(
    page_title="Great Fantasy Bake Off League",
    page_icon="🧁",
    layout="wide"
)

# --- DATA PERSISTENCE FUNCTIONS ---
def load_data():
    """Load all data from JSON files"""
    data = {
        'users': {},
        'bakers': [],
        'episodes': {},
        'picks': {},
        'results': {}
    }
    
    for key in data.keys():
        filename = f"{key}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data[key] = json.load(f)
            except:
                pass # Ignore errors if file is empty or corrupt
    
    return data

def save_data(data_type, data_to_save):
    """Save specific data type to JSON file"""
    filename = f"{data_type}.json"
    with open(filename, 'w') as f:
        json.dump(data_to_save, f, indent=2, default=str)

# --- NEW: EMAIL CONFIRMATION FUNCTION ---
def send_confirmation_email(recipient_email: str, user_name: str, week: int, picks: Dict[str, Any]):
    """Sends a confirmation email to the user with their submitted picks."""
    try:
        sender_email = st.secrets["email_credentials"]["sender_email"]
        sender_password = st.secrets["email_credentials"]["sender_password"]
    except (KeyError, FileNotFoundError):
        st.warning("Email credentials not configured in st.secrets. Confirmation email not sent.", icon="⚠️")
        return

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = f"🧁 Bake Off Fantasy Picks Confirmation - Week {week}"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; }}
            h2 {{ color: #333; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ margin-bottom: 10px; }}
            strong {{ color: #555; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Hi {user_name},</h2>
            <p>Your fantasy picks for <strong>Week {week}</strong> have been successfully submitted!</p>
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
        st.error(f"Failed to send confirmation email. Please check your SMTP configuration. Error: {e}")


# --- INITIALIZE SESSION STATE ---
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- SCORING LOGIC ---
def calculate_user_scores(data):
    """Calculate total scores for all users"""
    scores = {}
    
    for user_id, user_picks in data['picks'].items():
        weekly_points = 0
        foresight_points = 0
        
        for week, picks in user_picks.items():
            if week in data['results']:
                results = data['results'][week]
                if picks.get('star_baker') == results.get('star_baker'):
                    weekly_points += 5
                if picks.get('technical_winner') == results.get('technical_winner'):
                    weekly_points += 3
                if picks.get('handshake_prediction') and results.get('handshake_given'):
                    weekly_points += 10
        
        scores[user_id] = {
            'weekly_points': weekly_points,
            'foresight_points': foresight_points,
            'total_points': weekly_points + foresight_points
        }
    
    return scores

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧁 Fantasy Bake Off")
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏆 Leaderboard & Stats", "📝 Submit Picks", "⚙️ Admin Panel"]
)

# --- LEADERBOARD & STATS PAGE ---
if page == "🏆 Leaderboard & Stats":
    st.title("🏆 Great Fantasy Bake Off League")
    
    data = st.session_state.data
    
    if not data['users']:
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
    else:
        scores = calculate_user_scores(data)
        leaderboard_data = []
        for user_id, user_info in data['users'].items():
            user_score = scores.get(user_id, {'weekly_points': 0, 'foresight_points': 0, 'total_points': 0})
            leaderboard_data.append({
                'Player': user_info['name'],
                'Weekly Points': user_score['weekly_points'],
                'Foresight Points': user_score['foresight_points'],
                'Total Points': user_score['total_points']
            })
        
        if leaderboard_data:
            st.subheader("Current Standings")
            df = pd.DataFrame(leaderboard_data).sort_values('Total Points', ascending=False).reset_index(drop=True)
            df.index = df.index + 1
            st.dataframe(df, use_container_width=True)

        st.subheader("📊 Current Season Predictions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Winner Predictions**")
            winner_predictions = {}
            for user_picks in data['picks'].values():
                for week_picks in user_picks.values():
                    winner = week_picks.get('season_winner')
                    if winner:
                        winner_predictions[winner] = winner_predictions.get(winner, 0) + 1
            
            if winner_predictions:
                winner_df = pd.DataFrame(list(winner_predictions.items()), 
                                       columns=['Baker', 'Predictions'])
                winner_df = winner_df.sort_values('Predictions', ascending=False)
                st.dataframe(winner_df, use_container_width=True)
        
        with col2:
            st.write("**Most Recent Episode Results**")
            if data['results']:
                latest_week = max(data['results'].keys())
                latest_results = data['results'][latest_week]
                
                st.write(f"**Week {latest_week}**")
                st.write(f"⭐ Star Baker: {latest_results.get('star_baker', 'TBD')}")
                st.write(f"🏆 Technical Winner: {latest_results.get('technical_winner', 'TBD')}")
                st.write(f"🤝 Handshake Given: {'Yes' if latest_results.get('handshake_given') else 'No'}")

# --- SUBMIT PICKS PAGE ---
elif page == "📝 Submit Picks":
    st.title("📝 Submit Your Weekly Picks")
    
    data = st.session_state.data

    st.subheader("1. Player Profile")
    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None

    player_options = {uid: uinfo['name'] for uid, uinfo in data['users'].items()}
    selection = st.selectbox(
        "Select your profile or create a new one:",
        options=[None, "➕ New Player"] + list(player_options.keys()),
        format_func=lambda x: "--- Select ---" if x is None else ("Create New Profile" if x == "➕ New Player" else player_options.get(x, "Unknown")),
        key="player_selector"
    )

    if selection == "➕ New Player":
        with st.form("new_player_form"):
            st.write("Welcome! Please create your profile to join the league.")
            new_name = st.text_input("Your Name:")
            new_email = st.text_input("Your Email (for confirmations):")
            if st.form_submit_button("Create Profile"):
                if new_name and new_email and '@' in new_email and '.' in new_email:
                    user_id = f"user_{len(data['users']) + 1}"
                    data['users'][user_id] = {'name': new_name, 'email': new_email}
                    save_data('users', data['users'])
                    st.session_state.selected_user = user_id
                    st.success(f"Profile for {new_name} created! You can now submit your picks below.")
                    st.rerun()
                else:
                    st.error("Please enter a valid name and email address.")
    elif selection is not None:
        st.session_state.selected_user = selection

    if st.session_state.selected_user:
        user_id = st.session_state.selected_user
        user_name = data['users'][user_id]['name']
        st.success(f"Welcome, **{user_name}**! You're ready to submit your picks.")

        with st.expander("Manage My Profile"):
            current_email = data['users'][user_id].get('email', '')
            updated_email = st.text_input("Update My Email:", value=current_email, key=f"email_update_{user_id}")
            if st.button("Save Email"):
                if updated_email and '@' in updated_email and '.' in updated_email:
                    data['users'][user_id]['email'] = updated_email
                    save_data('users', data['users'])
                    st.toast("✅ Email updated successfully!", icon="📧")
                else:
                    st.warning("Please enter a valid email address.")
        
        st.subheader("2. Make Your Predictions")
        current_week = st.selectbox("Select Week:", list(range(2, 12)))
        
        if user_id not in data['picks']:
            data['picks'][user_id] = {}
        
        existing_picks = data['picks'][user_id].get(str(current_week), {})
        available_bakers = data.get('bakers') or [f"Baker {chr(65+i)}" for i in range(12)]
        
        with st.form(f"picks_week_{current_week}_{user_id}"):
            col1, col2 = st.columns(2)
            with col1:
                star_baker = st.selectbox("⭐ Star Baker:", available_bakers, index=available_bakers.index(existing_picks.get('star_baker', available_bakers[0])) if existing_picks.get('star_baker') in available_bakers else 0)
                technical_winner = st.selectbox("🏆 Technical Winner:", available_bakers, index=available_bakers.index(existing_picks.get('technical_winner', available_bakers[0])) if existing_picks.get('technical_winner') in available_bakers else 0)
                handshake_prediction = st.checkbox("🤝 Hollywood Handshake?", value=existing_picks.get('handshake_prediction', False))
            with col2:
                season_winner = st.selectbox("👑 Season Winner:", available_bakers, index=available_bakers.index(existing_picks.get('season_winner', available_bakers[0])) if existing_picks.get('season_winner') in available_bakers else 0)
                finalist_1 = st.selectbox("🥈 Finalist #1:", available_bakers, index=available_bakers.index(existing_picks.get('finalist_1', available_bakers[1])) if existing_picks.get('finalist_1') in available_bakers else 1)
                finalist_2 = st.selectbox("🥉 Finalist #2:", available_bakers, index=available_bakers.index(existing_picks.get('finalist_2', available_bakers[2])) if existing_picks.get('finalist_2') in available_bakers else 2)
            
            if st.form_submit_button("Submit & Lock In Picks"):
                picks_data = {
                    'star_baker': star_baker, 'technical_winner': technical_winner,
                    'handshake_prediction': handshake_prediction, 'season_winner': season_winner,
                    'finalist_1': finalist_1, 'finalist_2': finalist_2,
                    'submitted_at': datetime.now().isoformat()
                }
                data['picks'][user_id][str(current_week)] = picks_data
                save_data('picks', data['picks'])
                
                st.success(f"✅ Your picks for Week {current_week} have been submitted!")
                st.balloons()

                # --- TRIGGER EMAIL CONFIRMATION ---
                recipient_email = data['users'][user_id].get('email')
                if recipient_email:
                    send_confirmation_email(
                        recipient_email=recipient_email,
                        user_name=data['users'][user_id]['name'],
                        week=current_week,
                        picks=picks_data
                    )
                else:
                    st.warning("No email found for your profile. Confirmation could not be sent.")

# --- ADMIN PANEL PAGE ---
elif page == "⚙️ Admin Panel":
    st.title("⚙️ Commissioner Admin Panel")
    admin_password = st.text_input("Enter admin password:", type="password", key="admin_pw")
    
    if admin_password == "bakeoff2024": # Replace with a secure password
        data = st.session_state.data
        tab1, tab2, tab3, tab4 = st.tabs(["Episode Results", "Manage Bakers", "Manage Players", "Data Management"])
        
        with tab1:
            st.subheader("Enter Episode Results")
            
            result_week = st.selectbox("Select Week:", list(range(2, 12)))
            
            existing_results = data['results'].get(str(result_week), {})
            
            with st.form(f"results_week_{result_week}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    star_baker_result = st.selectbox(
                        "⭐ Actual Star Baker:",
                        options=[""] + data['bakers'],
                        index=data['bakers'].index(existing_results.get('star_baker')) + 1
                        if existing_results.get('star_baker') in data['bakers'] else 0
                    )
                    
                    technical_winner_result = st.selectbox(
                        "🏆 Technical Challenge Winner:",
                        options=[""] + data['bakers'],
                        index=data['bakers'].index(existing_results.get('technical_winner')) + 1
                        if existing_results.get('technical_winner') in data['bakers'] else 0
                    )
                
                with col2:
                    handshake_given = st.checkbox(
                        "🤝 Was a Hollywood Handshake given?",
                        value=existing_results.get('handshake_given', False)
                    )
                    
                    eliminated_baker = st.selectbox(
                        "😢 Baker Eliminated:",
                        options=[""] + data['bakers'],
                        index=data['bakers'].index(existing_results.get('eliminated_baker')) + 1
                        if existing_results.get('eliminated_baker') in data['bakers'] else 0
                    )
                
                submit_results = st.form_submit_button("Save Episode Results")
                
                if submit_results:
                    data['results'][str(result_week)] = {
                        'star_baker': star_baker_result,
                        'technical_winner': technical_winner_result,
                        'handshake_given': handshake_given,
                        'eliminated_baker': eliminated_baker,
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    save_data('results', data['results'])
                    st.success(f"✅ Results for Week {result_week} saved!")
                    
        with tab2:
            st.subheader("Manage Bakers")
            
            # Add new baker
            new_baker = st.text_input("Add new baker:")
            if st.button("Add Baker") and new_baker:
                if new_baker not in data['bakers']:
                    data['bakers'].append(new_baker)
                    save_data('bakers', data['bakers'])
                    st.success(f"Added {new_baker}")
                    st.rerun()
            
            # Remove baker
            if data['bakers']:
                baker_to_remove = st.selectbox("Remove baker:", [""] + data['bakers'])
                if st.button("Remove Baker") and baker_to_remove:
                    data['bakers'].remove(baker_to_remove)
                    save_data('bakers', data['bakers'])
                    st.success(f"Removed {baker_to_remove}")
                    st.rerun()
            
            # Show current bakers
            st.write("**Current Bakers:**")
            for baker in data['bakers']:
                st.write(f"- {baker}")
        with tab3:
            st.subheader("Manage Players & Emails")
            if not data.get('users'):
                st.info("No players have registered yet.")
            else:
                player_df = pd.DataFrame([{
                    'User ID': uid,
                    'Name': uinfo.get('name'),
                    'Email': uinfo.get('email', 'N/A')
                } for uid, uinfo in data['users'].items()])
                st.dataframe(player_df, use_container_width=True, hide_index=True)
                
                st.subheader("✏️ Edit or Remove a Player")
                # Create a list of player names for the dropdown
                player_list = list(data['users'].keys())
                player_to_edit = st.selectbox(
                    "Select a player to manage:",
                    options=[""] + player_list,
                    format_func=lambda uid: data['users'][uid]['name'] if uid else "--- Select a Player ---"
                )

                if player_to_edit:
                    user_info = data['users'][player_to_edit]
                    
                    with st.form(f"edit_player_{player_to_edit}"):
                        st.write(f"**Editing Profile for: {user_info['name']}**")
                        
                        new_name = st.text_input("Player Name", value=user_info.get('name', ''))
                        new_email = st.text_input("Player Email", value=user_info.get('email', ''))

                        # Create columns for the buttons
                        col1, col2 = st.columns([0.2, 1])
                        
                        with col1:
                            submitted = st.form_submit_button("💾 Save Changes")
                        
                        if submitted:
                            # Update the user's data
                            data['users'][player_to_edit]['name'] = new_name
                            data['users'][player_to_edit]['email'] = new_email
                            save_data('users', data['users'])
                            st.success(f"✅ Player '{new_name}' has been updated.")
                            st.rerun()

                    # --- REMOVE PLAYER SECTION ---
                    with st.expander("🗑️ Remove Player (Permanent)"):
                        st.warning(f"**Warning:** This will permanently delete **{user_info['name']}** and all of their submitted picks. This action cannot be undone.")
                        
                        if st.button(f"DELETE {user_info['name']}'s Profile", type="primary"):
                            # Remove from users data
                            del data['users'][player_to_edit]
                            save_data('users', data['users'])

                            # Also remove their picks to keep data consistent
                            if player_to_edit in data['picks']:
                                del data['picks'][player_to_edit]
                                save_data('picks', data['picks'])

                            st.success(f"🗑️ Player '{user_info['name']}' and all their data have been removed.")
                            st.rerun()

        with tab4:
            st.subheader("Data Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Export Data**")
                if st.button("Download All Data"):
                    # Create downloadable JSON
                    all_data = {
                        'users': data['users'],
                        'bakers': data['bakers'],
                        'picks': data['picks'],
                        'results': data['results'],
                        'exported_at': datetime.now().isoformat()
                    }
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(all_data, indent=2),
                        file_name=f"bakeoff_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col2:
                st.write("**Reset Data**")
                if st.button("⚠️ Reset All Data", type="secondary"):
                    if st.button("Confirm Reset", type="primary"):
                        for data_type in ['users', 'bakers', 'picks', 'results']:
                            if os.path.exists(f"{data_type}.json"):
                                os.remove(f"{data_type}.json")
                        st.session_state.data = load_data()
                        st.success("All data reset!")
                        st.rerun()
            
    elif admin_password:
        st.error("❌ Incorrect admin password")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.markdown("🧁 *May the best Star Predictor win!*")
