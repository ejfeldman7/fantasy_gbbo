from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.config import FORESIGHT_BASE_WEEK, REVEAL_DATES_UTC, WEEK_DATES
from src.data_manager import DataManager
from src.scoring import (
    calculate_user_scores,
    calculate_weekly_breakdown,
    is_season_complete,
)

_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _rank_map(score_by_email: dict) -> dict:
    """Return {email: rank} with 1 = highest score (ties share the lower rank)."""
    ordered = sorted(score_by_email.items(), key=lambda kv: kv[1], reverse=True)
    ranks, last_score, last_rank = {}, None, 0
    for i, (email, score) in enumerate(ordered, start=1):
        if score != last_score:
            last_rank, last_score = i, score
        ranks[email] = last_rank
    return ranks


def show_page(data_manager: DataManager):
    st.title("🏆 Great Fantasy Bake Off League")

    if st.button("🔄 Refresh scores"):
        st.cache_data.clear()
        st.rerun()

    try:
        user_scores = calculate_user_scores(data_manager)
    except Exception as e:
        st.error(f"Error calculating scores: {e}")
        return

    if not user_scores:
        st.info("No players registered yet! Head to the 'Submit Picks' page to join.")
        return

    season_complete = is_season_complete(data_manager)
    breakdown = calculate_weekly_breakdown(data_manager)

    if season_complete:
        _show_champion_banner(data_manager, user_scores)

    _show_standings(user_scores, season_complete)

    if not season_complete:
        _show_this_week(breakdown, user_scores)

    _show_scoring_help()
    _show_picks_history(data_manager)


def _show_champion_banner(data_manager: DataManager, user_scores: dict):
    """Big, celebratory 'we have a winner' state once the season is over."""
    standings = sorted(
        user_scores.items(), key=lambda kv: kv[1]["total_points"], reverse=True
    )
    champ_email, champ = standings[0]

    if not st.session_state.get("_champ_celebrated"):
        st.balloons()
        st.session_state["_champ_celebrated"] = True

    st.success(
        f"### 🏆 Season Complete!\n"
        f"# 👑 {champ['user_name']} is the Champion!\n"
        f"**{champ['total_points']} points** "
        f"({champ['weekly_points']} weekly + {champ['foresight_points']} foresight)"
    )

    final = data_manager.get_final_results() or {}
    st.caption(
        f"Official finale — 🏆 Winner: **{final.get('season_winner', '?')}** · "
        f"Finalists: **{final.get('finalist_2', '?')}**, **{final.get('finalist_3', '?')}**"
    )

    # Foresight hall of fame: who backed the champion earliest?
    winner = final.get("season_winner")
    all_picks = data_manager.get_all_picks()
    earliest = {}
    for pick in all_picks:
        if winner and pick.get("season_winner") == winner:
            email = pick.get("email", "")
            wk = pick.get("week_number")
            if wk is not None and (email not in earliest or wk < earliest[email][1]):
                earliest[email] = (pick.get("user_name", "Unknown"), int(wk))
    if earliest:
        soonest = min(w for _, w in earliest.values())
        believers = sorted(
            [name for name, w in earliest.values() if w == soonest]
        )
        st.info(
            f"🔮 **Called it earliest:** {', '.join(believers)} "
            f"backed {winner} to win from Week {soonest}."
        )
    st.markdown("---")


def _show_standings(user_scores: dict, season_complete: bool):
    st.subheader("🏁 Final Standings" if season_complete else "🏆 Current Standings")

    rows = [
        {
            "Player": s["user_name"],
            "Weekly Points": s["weekly_points"],
            "Foresight Points": s["foresight_points"],
            "Total Points": s["total_points"],
        }
        for s in user_scores.values()
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Players", len(rows))
    col2.metric("Total Weekly Points", sum(r["Weekly Points"] for r in rows))
    col3.metric("Total Foresight Points", sum(r["Foresight Points"] for r in rows))

    df = (
        pd.DataFrame(rows)
        .sort_values("Total Points", ascending=False)
        .reset_index(drop=True)
    )
    df.insert(0, "Rank", [_MEDALS.get(i, str(i)) for i in range(1, len(df) + 1)])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _show_this_week(breakdown: dict, user_scores: dict):
    """Latest-week scoring plus week-over-week rank movement."""
    weeks = breakdown["weeks_with_results"]
    if not weeks:
        st.info("No episode results entered yet — check back after the first episode!")
        return

    latest = weeks[-1]
    week_label = WEEK_DATES.get(str(latest), f"Week {latest}")
    st.subheader(f"📺 This Week — {week_label}")

    by_user = breakdown["by_user"]

    # Cumulative-through-week helpers for rank movement.
    def cum_through(week_cutoff):
        return {
            email: sum(p for w, p in d["by_week"].items() if w <= week_cutoff)
            for email, d in by_user.items()
        }

    ranks_now = _rank_map(cum_through(latest))
    ranks_prev = _rank_map(cum_through(weeks[-2])) if len(weeks) > 1 else ranks_now

    rows = []
    for email, d in by_user.items():
        this_week_pts = d["by_week"].get(latest)
        if this_week_pts is None:
            continue  # player didn't submit / score this week
        delta = ranks_prev.get(email, ranks_now[email]) - ranks_now[email]
        move = "🔺" + str(delta) if delta > 0 else ("🔻" + str(-delta) if delta < 0 else "—")
        rows.append(
            {
                "Player": d["user_name"],
                "This Week": this_week_pts,
                "Move": move,
                "Rank": ranks_now[email],
                "Season Total": user_scores.get(email, {}).get("total_points", 0),
            }
        )

    if not rows:
        st.caption("No scored picks for this week yet.")
        return

    df = pd.DataFrame(rows).sort_values(
        ["This Week", "Season Total"], ascending=False
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    top = df.iloc[0]
    st.caption(f"⭐ Top scorer this week: **{top['Player']}** with {top['This Week']} points.")


def _show_scoring_help():
    with st.expander("📊 How Scoring Works"):
        st.markdown(
            f"""
            **Weekly Points** (update as each episode's results are entered):
            - ⭐ Star Baker: **+5**
            - 😢 Baker Sent Home: **+5**
            - 🏆 Technical Winner: **+3**
            - 🤝 Handshake predicted & given: **+10**
            - 🤝 Handshake predicted, none given: **−10** (no penalty for predicting *no* handshake)
            - Predicted Star Baker gets sent home / predicted eliminee is Star Baker: **−5**

            **Foresight Points** (resolve at the finale):
            - 👑 Correct **Season Winner**: `({FORESIGHT_BASE_WEEK} − week) × 10`
            - 🥈 Each correctly-named **Finalist** (the champion counts too): `({FORESIGHT_BASE_WEEK} − week) × 5`
            - Only your **earliest** correct week counts for each — reward for conviction, not repetition.
            - Earlier calls are worth far more: nailing the winner in Week 2 beats waiting until the semi-final.
            """
        )


def _show_picks_history(data_manager: DataManager):
    with st.expander("📋 View All Picks History"):
        all_picks = data_manager.get_all_picks()
        if not all_picks:
            st.info("No picks submitted yet.")
            return

        now_utc = datetime.now(timezone.utc)
        weeks_with_picks = {}
        for pick in all_picks:
            week = str(pick.get("week_number", ""))
            weeks_with_picks.setdefault(week, []).append(pick)

        sorted_weeks = sorted(
            weeks_with_picks.keys(), key=lambda x: int(x) if x.isdigit() else 0
        )

        revealed = 0
        for week_key in sorted_weeks:
            reveal_date = REVEAL_DATES_UTC.get(week_key)
            if not (reveal_date and now_utc > reveal_date):
                continue
            revealed += 1
            display_name = WEEK_DATES.get(week_key, f"Week {week_key}")
            picks = weeks_with_picks[week_key]

            with st.expander(f"{display_name} Predictions"):
                # "The Crowd": how the league split on Star Baker & Winner.
                _show_crowd(picks)
                week_rows = [
                    {
                        "Player": p.get("user_name", "Unknown"),
                        "Star Baker": p.get("star_baker", ""),
                        "Technical": p.get("technical_winner", ""),
                        "Eliminated": p.get("eliminated_baker", ""),
                        "Handshake": "✓" if p.get("hollywood_handshake") else "✗",
                        "Season Winner": p.get("season_winner", ""),
                        "Submitted": str(p.get("submitted_at", ""))[:16]
                        if p.get("submitted_at")
                        else "",
                    }
                    for p in picks
                ]
                st.dataframe(
                    pd.DataFrame(week_rows), use_container_width=True, hide_index=True
                )

        if revealed == 0:
            st.caption(
                "Picks for past weeks are revealed here after each submission deadline."
            )


def _show_crowd(picks: list):
    """Show how the league split on the two headline picks for a week."""
    total = len(picks)
    if total < 2:
        return

    def distribution(field):
        counts = {}
        for p in picks:
            val = p.get(field)
            if val:
                counts[val] = counts.get(val, 0) + 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

    sb = distribution("star_baker")
    sw = distribution("season_winner")
    if not sb and not sw:
        return

    c1, c2 = st.columns(2)
    with c1:
        st.caption("🔮 Star Baker — the crowd")
        for name, n in sb[:5]:
            st.write(f"{name}: {n}/{total} ({round(100 * n / total)}%)")
    with c2:
        st.caption("👑 Season Winner — the crowd")
        for name, n in sw[:5]:
            st.write(f"{name}: {n}/{total} ({round(100 * n / total)}%)")
    st.markdown("—")
