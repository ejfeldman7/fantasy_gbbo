import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

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

# --- INITIALIZE SESSION STATE ---
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- SCORING LOGIC (No changes here) ---
def calculate_foresight_points(prediction_week, total_weeks, base_points):
    """Calculate foresight points based on when prediction was made"""
    return (total_weeks - prediction_week + 1) * base_points

def calculate_user_scores(data):
    """Calculate total scores for all users"""
    scores = {}
    
    for user_id, user_picks in data['picks'].items():
        weekly_points = 0
        foresight_points = 0 # Placeholder for end-of-season calculation
        
        # Calculate weekly points
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

# --- LEADERBOARD & STATS PAGE (No functional changes here) ---
if page == "🏆 Leaderboard & Stats":
    st.title("🏆 Great Fantasy Bake Off League")
    
    data = st.session_state.data
    
    if not data['users']:
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
    else:
        scores = calculate_user_scores(data)
        
        # Create leaderboard dataframe
        leaderboard_data = []
        for user_id, user_info in data['users'].items():
            if user_id in scores:
                leaderboard_data.append({
                    'Player': user_info['name'],
                    'Weekly Points': scores[user_id]['weekly_points'],
                    'Foresight Points': scores[user_id]['foresight_points'],
                    'Total Points': scores[user_id]['total_points']
                })
        
        if leaderboard_data:
            st.subheader("Current Standings")
            df = pd.DataFrame(leaderboard_data)
            df = df.sort_values('Total Points', ascending=False).reset_index(drop=True)
            df.index = df.index + 1
            st.dataframe(df, use_container_width=True)
        
        # --- Tabs for different views (No functional changes here) ---
        # ... (The rest of the Leaderboard page code remains the same as your original)


# --- SUBMIT PICKS PAGE (UPDATED) ---
elif page == "📝 Submit Picks":
    st.title("📝 Submit Your Weekly Picks")
    
    data = st.session_state.data

    # --- 1. Player Profile Selection & Creation ---
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

    # Handle New Player creation in a form
    if selection == "➕ New Player":
        with st.form("new_player_form"):
            st.write("Welcome! Please create your profile to join the league.")
            new_name = st.text_input("Your Name:")
            new_email = st.text_input("Your Email (for notifications):")
            submitted = st.form_submit_button("Create Profile")

            if submitted:
                if new_name and new_email:
                    if '@' in new_email and '.' in new_email:
                        user_id = f"user_{len(data['users']) + 1}"
                        data['users'][user_id] = {'name': new_name, 'email': new_email}
                        save_data('users', data['users'])
                        st.session_state.selected_user = user_id
                        st.success(f"Profile for {new_name} created! You can now submit your picks below.")
                        st.rerun()
                    else:
                        st.error("Please enter a valid email address.")
                else:
                    st.error("Both name and email are required.")
    elif selection is not None:
        st.session_state.selected_user = selection

    # --- 2. Picks Submission Form ---
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
        
        # Use placeholder list if bakers aren't set in admin panel yet
        available_bakers = data.get('bakers') or [f"Baker {chr(65+i)}" for i in range(12)]
        
        with st.form(f"picks_week_{current_week}_{user_id}"):
            # ... (rest of your form code is the same)
            col1, col2 = st.columns(2)
            
            with col1:
                star_baker = st.selectbox(
                    "⭐ Star Baker Prediction:",
                    options=available_bakers,
                    index=available_bakers.index(existing_picks.get('star_baker', available_bakers[0])) if existing_picks.get('star_baker') in available_bakers else 0
                )
                
                technical_winner = st.selectbox(
                    "🏆 Technical Challenge Winner:",
                    options=available_bakers,
                    index=available_bakers.index(existing_picks.get('technical_winner', available_bakers[0])) if existing_picks.get('technical_winner') in available_bakers else 0
                )
                
                handshake_prediction = st.checkbox(
                    "🤝 Will someone get a Hollywood Handshake?",
                    value=existing_picks.get('handshake_prediction', False)
                )
            
            with col2:
                season_winner = st.selectbox(
                    "🏆 Season Winner Prediction:",
                    options=available_bakers,
                    index=available_bakers.index(existing_picks.get('season_winner', available_bakers[0])) if existing_picks.get('season_winner') in available_bakers else 0
                )
                
                finalist_1 = st.selectbox(
                    "🥈 Finalist #1:",
                    options=available_bakers,
                    index=available_bakers.index(existing_picks.get('finalist_1', available_bakers[1])) if existing_picks.get('finalist_1') in available_bakers else 1
                )
                
                finalist_2 = st.selectbox(
                    "🥉 Finalist #2:",
                    options=available_bakers,
                    index=available_bakers.index(existing_picks.get('finalist_2', available_bakers[2])) if existing_picks.get('finalist_2') in available_bakers else 2
                )
            
            submit_picks = st.form_submit_button("Submit & Lock In Picks")
            
            if submit_picks:
                data['picks'][user_id][str(current_week)] = {
                    'star_baker': star_baker,
                    'technical_winner': technical_winner,
                    'handshake_prediction': handshake_prediction,
                    'season_winner': season_winner,
                    'finalist_1': finalist_1,
                    'finalist_2': finalist_2,
                    'submitted_at': datetime.now().isoformat()
                }
                
                save_data('picks', data['picks'])
                st.success(f"✅ Your picks for Week {current_week} have been submitted!")
                st.balloons()


# --- ADMIN PANEL PAGE (UPDATED) ---
elif page == "⚙️ Admin Panel":
    st.title("⚙️ Commissioner Admin Panel")
    
    admin_password = st.text_input("Enter admin password:", type="password", key="admin_pw")
    
    if admin_password == "bakeoff2024":  # Replace with a more secure password
        data = st.session_state.data
        
        tab1, tab2, tab3, tab4 = st.tabs(["Episode Results", "Manage Bakers", "Manage Players", "Data Management"])
        
        with tab1:
            # ... (Episode Results code remains the same as your original)
            st.subheader("Enter Episode Results")
        
        with tab2:
            # ... (Manage Bakers code remains the same as your original)
            st.subheader("Manage Bakers")

        with tab3:
            st.subheader("Manage Players & Emails")
            if data['users']:
                player_data = []
                for uid, uinfo in data['users'].items():
                    player_data.append({
                        'User ID': uid,
                        'Name': uinfo.get('name'),
                        'Email': uinfo.get('email', 'N/A')
                    })
                player_df = pd.DataFrame(player_data)
                st.dataframe(player_df, use_container_width=True, hide_index=True)
            else:
                st.info("No players have registered yet.")

        with tab4:
            # ... (Data Management code remains the same as your original)
            st.subheader("Data Management")
            
    elif admin_password:
        st.error("❌ Incorrect admin password")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.markdown("🧁 *May the best Star Predictor win!*")
