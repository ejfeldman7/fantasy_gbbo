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

# Data persistence functions
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
                pass
    
    return data

def save_data(data_type, data):
    """Save specific data type to JSON file"""
    filename = f"{data_type}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()

def calculate_foresight_points(prediction_week, total_weeks, base_points):
    """Calculate foresight points based on when prediction was made"""
    return (total_weeks - prediction_week + 1) * base_points

def calculate_user_scores(data):
    """Calculate total scores for all users"""
    scores = {}
    
    for user_id, user_picks in data['picks'].items():
        weekly_points = 0
        foresight_points = 0
        
        # Calculate weekly points
        for week, picks in user_picks.items():
            if week in data['results']:
                results = data['results'][week]
                
                # Star Baker (5 points)
                if picks.get('star_baker') == results.get('star_baker'):
                    weekly_points += 5
                
                # Technical Winner (3 points)
                if picks.get('technical_winner') == results.get('technical_winner'):
                    weekly_points += 3
                
                # Hollywood Handshake (10 points)
                if picks.get('handshake_prediction') and results.get('handshake_given'):
                    weekly_points += 10
        
        # Calculate foresight points (simplified - would need final results)
        # This would be calculated at season end based on all weekly predictions
        
        scores[user_id] = {
            'weekly_points': weekly_points,
            'foresight_points': foresight_points,
            'total_points': weekly_points + foresight_points
        }
    
    return scores

# Sidebar navigation
st.sidebar.title("🧁 Fantasy Bake Off")
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏆 Leaderboard & Stats", "📝 Submit Picks", "⚙️ Admin Panel"]
)

# LEADERBOARD & STATS PAGE
if page == "🏆 Leaderboard & Stats":
    st.title("🏆 Great Fantasy Bake Off League")
    st.subheader("Current Standings")
    
    data = st.session_state.data
    
    if not data['users']:
        st.info("No players registered yet! Head to the picks page to join the league.")
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
            df = pd.DataFrame(leaderboard_data)
            df = df.sort_values('Total Points', ascending=False).reset_index(drop=True)
            df.index = df.index + 1
            st.dataframe(df, use_container_width=True)
        
        # Season predictions summary
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

# SUBMIT PICKS PAGE
elif page == "📝 Submit Picks":
    st.title("📝 Submit Your Weekly Picks")
    
    data = st.session_state.data
    
    # User registration/selection
    st.subheader("Player Information")
    
    if data['users']:
        existing_users = list(data['users'].keys())
        user_option = st.selectbox("Select your player profile:", ["New Player"] + existing_users)
        
        if user_option == "New Player":
            user_name = st.text_input("Enter your name:")
            if user_name:
                user_id = f"user_{len(data['users']) + 1}"
                data['users'][user_id] = {'name': user_name}
                st.session_state.selected_user = user_id
        else:
            st.session_state.selected_user = user_option
            st.write(f"Welcome back, {data['users'][user_option]['name']}!")
    else:
        user_name = st.text_input("Enter your name to join the league:")
        if user_name:
            user_id = "user_1"
            data['users'][user_id] = {'name': user_name}
            st.session_state.selected_user = user_id
    
    # Week selection and picks submission
    if hasattr(st.session_state, 'selected_user'):
        st.subheader("Weekly Predictions")
        
        # Get current week (this would be dynamically determined)
        current_week = st.selectbox("Select Week:", list(range(2, 12)))  # Episodes 2-11
        
        # Check if picks already submitted for this week
        user_id = st.session_state.selected_user
        if user_id not in data['picks']:
            data['picks'][user_id] = {}
        
        existing_picks = data['picks'][user_id].get(str(current_week), {})
        
        # Available bakers (would be dynamically updated)
        if not data['bakers']:
            data['bakers'] = ["Baker A", "Baker B", "Baker C", "Baker D", "Baker E", 
                            "Baker F", "Baker G", "Baker H", "Baker I", "Baker J", 
                            "Baker K", "Baker L"]
        
        with st.form(f"picks_week_{current_week}"):
            col1, col2 = st.columns(2)
            
            with col1:
                star_baker = st.selectbox(
                    "⭐ Star Baker Prediction:",
                    options=data['bakers'],
                    index=data['bakers'].index(existing_picks.get('star_baker', data['bakers'][0]))
                    if existing_picks.get('star_baker') in data['bakers'] else 0
                )
                
                technical_winner = st.selectbox(
                    "🏆 Technical Challenge Winner:",
                    options=data['bakers'],
                    index=data['bakers'].index(existing_picks.get('technical_winner', data['bakers'][0]))
                    if existing_picks.get('technical_winner') in data['bakers'] else 0
                )
                
                handshake_prediction = st.checkbox(
                    "🤝 Will someone get a Hollywood Handshake?",
                    value=existing_picks.get('handshake_prediction', False)
                )
            
            with col2:
                season_winner = st.selectbox(
                    "🏆 Season Winner Prediction:",
                    options=data['bakers'],
                    index=data['bakers'].index(existing_picks.get('season_winner', data['bakers'][0]))
                    if existing_picks.get('season_winner') in data['bakers'] else 0
                )
                
                finalist_1 = st.selectbox(
                    "🥈 Finalist #1:",
                    options=data['bakers'],
                    index=data['bakers'].index(existing_picks.get('finalist_1', data['bakers'][1]))
                    if existing_picks.get('finalist_1') in data['bakers'] else 1
                )
                
                finalist_2 = st.selectbox(
                    "🥉 Finalist #2:",
                    options=data['bakers'],
                    index=data['bakers'].index(existing_picks.get('finalist_2', data['bakers'][2]))
                    if existing_picks.get('finalist_2') in data['bakers'] else 2
                )
            
            submit_picks = st.form_submit_button("Submit Picks")
            
            if submit_picks:
                # Save picks
                data['picks'][user_id][str(current_week)] = {
                    'star_baker': star_baker,
                    'technical_winner': technical_winner,
                    'handshake_prediction': handshake_prediction,
                    'season_winner': season_winner,
                    'finalist_1': finalist_1,
                    'finalist_2': finalist_2,
                    'submitted_at': datetime.now().isoformat()
                }
                
                # Save to file
                save_data('users', data['users'])
                save_data('picks', data['picks'])
                save_data('bakers', data['bakers'])
                
                st.success(f"✅ Your picks for Week {current_week} have been submitted!")
                st.balloons()

# ADMIN PANEL PAGE
elif page == "⚙️ Admin Panel":
    st.title("⚙️ Commissioner Admin Panel")
    
    # Password protection
    admin_password = st.text_input("Enter admin password:", type="password")
    
    if admin_password == "bakeoff2024":  # Change this to a secure password
        data = st.session_state.data
        
        tab1, tab2, tab3, tab4 = st.tabs(["Episode Results", "Manage Bakers", "Email & Deadlines", "Data Management"])
        
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

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🧁 *May the best Star Predictor win!*")
