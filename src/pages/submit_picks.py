import streamlit as st
from streamlit_extras.let_it_rain import rain
from datetime import datetime, timezone
from src.data_manager import DataManager
from src.email_utils import send_confirmation_email
from src.config import WEEK_DATES, REVEAL_DATES_UTC
from src.auth import is_email_allowed # New import for validation

def show_page(data_manager: DataManager):
    st.title("📝 Submit Your Weekly Picks")
    data = data_manager.get_data()
    st.subheader("1. Player Profile")

    if 'selected_user' not in st.session_state:
        st.session_state.selected_user = None
        
    player_options = {uid: uinfo.get('name', f'Unknown User ({uid})') for uid, uinfo in data.get('users', {}).items()}
    selection = st.selectbox("Select your profile or create a new one:", options=[None, "➕ New Player"] + list(player_options.keys()), format_func=lambda x: "--- Select ---" if x is None else ("Create New Profile" if x == "➕ New Player" else player_options.get(x, "Unknown")))

    if selection == "➕ New Player":
        with st.form("new_player_form"):
            new_name = st.text_input("Your Name:")
            new_email = st.text_input("Your Email Address:")
            if st.form_submit_button("Create Profile"):
                if new_name and new_email and '@' in new_email and '.' in new_email:
                    if is_email_allowed(new_email):
                        email_exists = any(user.get('email', '').lower() == new_email.lower() for user in data.get('users', {}).values())
                        if email_exists:
                            st.error("This email address is already registered. Please select your profile from the dropdown menu.")
                        else:
                            user_id = f"user_{len(data.get('users', {})) + 1}"
                            data['users'][user_id] = {'name': new_name, 'email': new_email}
                            data_manager.save_data('users')
                            st.session_state.selected_user = user_id
                            st.success(f"Profile for {new_name} created!")
                            st.rerun()
                    else:
                        st.error("This email address has not been approved for the league. Please contact the commissioner to be added.")
                else: 
                    st.error("Please enter a valid name and email address.")

    elif selection:
        st.session_state.selected_user = selection

    if st.session_state.selected_user:
        user_id = st.session_state.selected_user
        user_name = data['users'].get(user_id, {}).get('name', "Player")
        user_email = data['users'].get(user_id, {}).get('email', "")
        st.success(f"Welcome, **{user_name}**! You're ready to submit your picks.")
        
        now_utc = datetime.now(timezone.utc)
        available_weeks = [k for k, v in REVEAL_DATES_UTC.items() if now_utc < v]

        if not available_weeks:
            st.warning("All submission deadlines have passed for this season.")
            return

        selected_week = st.selectbox("Select Week:", options=available_weeks, format_func=lambda k: WEEK_DATES.get(k, f"Week {k}"))
        
        existing_picks = data['picks'].get(user_id, {}).get(selected_week, {})
        bakers = data.get('bakers') or [f"Baker {chr(65+i)}" for i in range(12)]

        st.markdown("""
        Each week you are making two different sets of predictions. You can resubmit your picks any time before the deadline.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("2. Make Your Weekly Predictions")
            sb = st.selectbox("⭐ Star Baker:", bakers, index=bakers.index(existing_picks.get('star_baker', bakers[0])) if existing_picks.get('star_baker') in bakers else 0, key=f"sb_{user_id}_{selected_week}")
            tw = st.selectbox("🏆 Technical Winner:", bakers, index=bakers.index(existing_picks.get('technical_winner', bakers[0])) if existing_picks.get('technical_winner') in bakers else 0, key=f"tw_{user_id}_{selected_week}")
            eb = st.selectbox("😢 Sent Home:", bakers, index=bakers.index(existing_picks.get('eliminated_baker', bakers[0])) if existing_picks.get('eliminated_baker') in bakers else 0, key=f"elim_{user_id}_{selected_week}")
            hh = st.checkbox("🤝 Hollywood Handshake?", value=existing_picks.get('handshake_prediction', False), key=f"hh_{user_id}_{selected_week}")
        with col2:
            st.subheader("3. Make your End of Season Predictions")
            sw = st.selectbox("👑 Season Winner:", bakers, index=bakers.index(existing_picks.get('season_winner', bakers[0])) if existing_picks.get('season_winner') in bakers else 0, key=f"sw_{user_id}_{selected_week}")
            f1 = st.selectbox("🥈 Finalist A:", bakers, index=bakers.index(existing_picks.get('finalist_1', bakers[1])) if 'finalist_1' in existing_picks and existing_picks['finalist_1'] in bakers and len(bakers) > 1 else 1, key=f"f1_{user_id}_{selected_week}")
            f2 = st.selectbox("🥈 Finalist B:", bakers, index=bakers.index(existing_picks.get('finalist_2', bakers[2])) if 'finalist_2' in existing_picks and existing_picks['finalist_2'] in bakers and len(bakers) > 2 else 2, key=f"f2_{user_id}_{selected_week}")

        st.markdown("---")
        if eb in {sb, tw}:
            st.warning(f"**Conflict:** You have **{eb}** as both eliminated and a weekly winner.")
        if eb in {sw, f1, f2}:
            st.warning(f"**Conflict:** You have **{eb}** as both eliminated and a season finalist/winner.")
        if len({sw, f1, f2}) < 3:
            st.warning("**Conflict:** Your Season Winner and Finalists must be three different people.")

        if st.button("Submit & Lock In Picks", key=f"submit_{user_id}_{selected_week}"):
            picks_data = {'star_baker': sb, 'technical_winner': tw, 'eliminated_baker': eb, 'handshake_prediction': hh, 'season_winner': sw, 'finalist_1': f1, 'finalist_2': f2, 'submitted_at': datetime.now().isoformat()}
            if user_id not in data['picks']:
                data['picks'][user_id] = {}
            data['picks'][user_id][selected_week] = picks_data
            data_manager.save_data('picks')
            
            week_display = WEEK_DATES.get(selected_week, f"Week {selected_week}")
            st.success(f"✅ Your picks for {week_display} have been submitted!")
            rain(emoji="🍰", font_size=54, falling_speed=3, animation_length="5s")

            if user_email:
                send_confirmation_email(user_email, user_name, week_display, picks_data)

