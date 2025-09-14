from datetime import datetime, timezone

import streamlit as st
from streamlit_extras.let_it_rain import rain

from src.config import REVEAL_DATES_UTC, WEEK_DATES
from src.data_manager import DataManager
from src.email_utils import send_confirmation_email


def show_page(data_manager: DataManager, user_email: str):
    st.title("📝 Submit Your Weekly Picks")

    # Get user information from database
    user = data_manager.get_user_by_email(user_email)
    if not user:
        st.error("User not found. Please log in again.")
        return

    user_name = user["name"]
    st.success(f"Welcome, **{user_name}**! You're ready to submit your picks.")

    # Check if admin has enabled all weeks
    admin_override = st.session_state.get("admin_allow_all_weeks", False)

    if admin_override:
        # Show all weeks when admin override is active
        available_weeks = list(WEEK_DATES.keys())
        st.info("🎛️ **Admin Mode**: All weeks available for picks")
    else:
        # Normal date-based filtering
        now_utc = datetime.now(timezone.utc)
        available_weeks = [k for k, v in REVEAL_DATES_UTC.items() if now_utc < v]

        if not available_weeks:
            st.warning("All submission deadlines have passed for this season.")
            return

    selected_week = st.selectbox(
        "Select Week:",
        options=available_weeks,
        format_func=lambda k: WEEK_DATES.get(k, f"Week {k}"),
    )

    # Get existing picks for this user and week from database
    existing_picks = data_manager.get_user_picks(user_email, selected_week) or {}

    # Get active bakers from database
    bakers = data_manager.get_active_bakers()
    if not bakers:
        bakers = [
            f"Baker {chr(65 + i)}" for i in range(12)
        ]  # fallback if no bakers in DB

    st.markdown(
        """
    Each week you are making two different sets of predictions. You can resubmit your picks any time before the deadline.
    """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2. Make Your Weekly Predictions")
        sb = st.selectbox(
            "⭐ Star Baker:",
            bakers,
            index=bakers.index(existing_picks.get("star_baker", bakers[0]))
            if existing_picks.get("star_baker") in bakers
            else 0,
            key=f"sb_{user['id']}_{selected_week}",
        )
        tw = st.selectbox(
            "🏆 Technical Winner:",
            bakers,
            index=bakers.index(existing_picks.get("technical_winner", bakers[0]))
            if existing_picks.get("technical_winner") in bakers
            else 0,
            key=f"tw_{user['id']}_{selected_week}",
        )
        eb = st.selectbox(
            "😢 Sent Home:",
            bakers,
            index=bakers.index(existing_picks.get("eliminated_baker", bakers[0]))
            if existing_picks.get("eliminated_baker") in bakers
            else 0,
            key=f"elim_{user['id']}_{selected_week}",
        )
        hh = st.checkbox(
            "🤝 Hollywood Handshake?",
            value=existing_picks.get("hollywood_handshake", False),
            key=f"hh_{user['id']}_{selected_week}",
        )
    with col2:
        st.subheader("3. Make your End of Season Predictions")
        sw = st.selectbox(
            "👑 Season Winner:",
            bakers,
            index=bakers.index(existing_picks.get("season_winner", bakers[0]))
            if existing_picks.get("season_winner") in bakers
            else 0,
            key=f"sw_{user['id']}_{selected_week}",
        )
        f1 = st.selectbox(
            "🥈 Finalist A:",
            bakers,
            index=bakers.index(existing_picks.get("finalist_2", bakers[1]))
            if existing_picks.get("finalist_2") in bakers and len(bakers) > 1
            else 1,
            key=f"f1_{user['id']}_{selected_week}",
        )
        f2 = st.selectbox(
            "🥈 Finalist B:",
            bakers,
            index=bakers.index(existing_picks.get("finalist_3", bakers[2]))
            if existing_picks.get("finalist_3") in bakers and len(bakers) > 2
            else 2,
            key=f"f2_{user['id']}_{selected_week}",
        )

    st.markdown("---")
    if eb in {sb, tw}:
        st.warning(
            f"**Conflict:** You have **{eb}** as both eliminated and a weekly winner."
        )
    if eb in {sw, f1, f2}:
        st.warning(
            f"**Conflict:** You have **{eb}** as both eliminated and a season finalist/winner."
        )
    if len({sw, f1, f2}) < 3:
        st.warning(
            "**Conflict:** Your Season Winner and Finalists must be three different people."
        )

    if st.button("Submit & Lock In Picks", key=f"submit_{user['id']}_{selected_week}"):
        picks_data = {
            "star_baker": sb,
            "technical_winner": tw,
            "eliminated_baker": eb,
            "hollywood_handshake": hh,
            "season_winner": sw,
            "finalist_2": f1,  # Database uses finalist_2 and finalist_3
            "finalist_3": f2,
        }

        # Save picks to database
        if data_manager.save_user_picks(user_email, selected_week, picks_data):
            week_display = WEEK_DATES.get(selected_week, f"Week {selected_week}")
            st.success(f"✅ Picks for {week_display} have been submitted!")
            rain(emoji="🍰", font_size=54, falling_speed=3, animation_length="5s")
            st.info("DEBUG PICKS SENT TO EMAIL:", picks_data)
            # Send confirmation email
            send_confirmation_email(user_email, user_name, week_display, picks_data)
        else:
            st.error("Failed to save your picks. Please try again.")
