"""
Points calculation engine for Fantasy GBBO.

This module is intentionally free of Streamlit/DB imports at runtime (the
DataManager import is type-checking only) so the pure scoring functions can be
unit-tested without a database or Streamlit session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from src.config import FORESIGHT_BASE_WEEK

if TYPE_CHECKING:
    from src.data_manager import DataManager


# --- Weekly point values (single source of truth for the UI copy too) ---
POINTS_STAR_BAKER = 5
POINTS_ELIMINATED = 5
POINTS_TECHNICAL = 3
POINTS_HANDSHAKE = 10
FORESIGHT_WINNER_BASE = 10
FORESIGHT_FINALIST_BASE = 5


def _foresight_multiplier(week_num: int) -> int:
    """
    Multiplier applied to foresight base points for a pick made in `week_num`.

    Derived from config so the season length can change without touching this
    engine. Floored at 1 so a correct finale-week pick is still worth its base.
    """
    return max(FORESIGHT_BASE_WEEK - week_num, 1)


def _to_int_week(week_str: str) -> int | None:
    """Parse a week key to an int, or None if it isn't a plain number."""
    try:
        return int(week_str)
    except (ValueError, TypeError):
        return None


def calculate_user_scores(data_manager: DataManager) -> Dict[str, Dict]:
    """
    Calculates total scores for all users, including weekly and foresight points.

    Weekly points update live as episode results are entered. Foresight points
    only resolve once final results have been recorded (the finale).

    Returns:
        Dict mapping user emails to their score breakdown.
    """
    scores: Dict[str, Dict] = {}

    users = data_manager.get_all_users()
    all_picks = data_manager.get_all_picks()
    weekly_results = data_manager.get_all_weekly_results()
    final_results = data_manager.get_final_results()

    results_by_week = {str(result["week_number"]): result for result in weekly_results}
    picks_by_user_week = _group_picks_by_user_week(all_picks)

    for user in users:
        user_email = user["email"]
        user_picks = picks_by_user_week.get(user_email, {})

        weekly_points = 0
        for week_str, picks in user_picks.items():
            week_results = results_by_week.get(week_str)
            if week_results:
                weekly_points += _calculate_weekly_points(picks, week_results)

        foresight_points = 0
        if final_results:
            foresight_points = _calculate_foresight_points(user_picks, final_results)

        scores[user_email] = {
            "weekly_points": weekly_points,
            "foresight_points": foresight_points,
            "total_points": weekly_points + foresight_points,
            "user_name": user["name"],
        }

    return scores


def _group_picks_by_user_week(all_picks: List[Dict]) -> Dict[str, Dict[str, Dict]]:
    """Group a flat list of picks into {email: {week_str: pick}}."""
    grouped: Dict[str, Dict[str, Dict]] = {}
    for pick in all_picks:
        user_email = pick.get("email", "")
        week = str(pick.get("week_number", ""))
        grouped.setdefault(user_email, {})[week] = pick
    return grouped


def _calculate_weekly_points(picks: Dict, results: Dict) -> int:
    """Calculate weekly points for a single week's picks vs results."""
    points = 0

    # Positive points
    if picks.get("star_baker") and picks.get("star_baker") == results.get("star_baker"):
        points += POINTS_STAR_BAKER
    if picks.get("eliminated_baker") and picks.get("eliminated_baker") == results.get(
        "eliminated_baker"
    ):
        points += POINTS_ELIMINATED
    if picks.get("technical_winner") and picks.get("technical_winner") == results.get(
        "technical_winner"
    ):
        points += POINTS_TECHNICAL
    if picks.get("hollywood_handshake") and results.get("hollywood_handshake"):
        points += POINTS_HANDSHAKE

    # Penalties
    if picks.get("star_baker") and picks.get("star_baker") == results.get(
        "eliminated_baker"
    ):
        points -= POINTS_STAR_BAKER
    if picks.get("eliminated_baker") and picks.get("eliminated_baker") == results.get(
        "star_baker"
    ):
        points -= POINTS_ELIMINATED
    if picks.get("hollywood_handshake") and not results.get("hollywood_handshake"):
        points -= POINTS_HANDSHAKE

    return points


def _calculate_foresight_points(
    user_picks_by_week: Dict[str, Dict], final_results: Dict
) -> int:
    """
    Calculate a user's total foresight points from all of their weekly picks.

    Rules (see info page for player-facing copy):
      * Winner bonus: 10 x multiplier for the EARLIEST week the user named the
        actual champion in their Season Winner slot.
      * Finalist credit: for each of the three actual finalists (the champion
        counts as a finalist), 5 x multiplier for the EARLIEST week the user
        named that person anywhere in their three prediction slots.

    "Earliest week" capping means conviction is rewarded once, not compounded
    every week you re-submit the same correct pick.
    """
    winner = final_results.get("season_winner")
    actual_finalists = {
        name
        for name in (
            final_results.get("season_winner"),
            final_results.get("finalist_2"),
            final_results.get("finalist_3"),
        )
        if name
    }
    if not actual_finalists:
        return 0

    points = 0

    # Winner bonus — earliest week the champion was picked as Season Winner.
    if winner:
        winner_weeks = [
            wk
            for week_str, picks in user_picks_by_week.items()
            if picks.get("season_winner") == winner
            and (wk := _to_int_week(week_str)) is not None
        ]
        if winner_weeks:
            points += _foresight_multiplier(min(winner_weeks)) * FORESIGHT_WINNER_BASE

    # Finalist credit — earliest week each actual finalist was named anywhere.
    for person in actual_finalists:
        named_weeks = [
            wk
            for week_str, picks in user_picks_by_week.items()
            if person
            in (
                picks.get("season_winner"),
                picks.get("finalist_2"),
                picks.get("finalist_3"),
            )
            and (wk := _to_int_week(week_str)) is not None
        ]
        if named_weeks:
            points += _foresight_multiplier(min(named_weeks)) * FORESIGHT_FINALIST_BASE

    return points


def calculate_weekly_breakdown(data_manager: DataManager) -> Dict:
    """
    Per-week weekly-point breakdown, used to show "This Week" scoring and
    week-over-week rank movement on the leaderboard.

    Returns:
        {
          "weeks_with_results": [sorted int weeks that have results],
          "by_user": {
             email: {"user_name": str, "by_week": {week_int: points}}
          }
        }
    """
    users = data_manager.get_all_users()
    all_picks = data_manager.get_all_picks()
    weekly_results = data_manager.get_all_weekly_results()

    results_by_week = {str(r["week_number"]): r for r in weekly_results}
    weeks_with_results = sorted(
        w for w in (_to_int_week(k) for k in results_by_week) if w is not None
    )
    picks_by_user_week = _group_picks_by_user_week(all_picks)

    by_user: Dict[str, Dict] = {}
    for user in users:
        email = user["email"]
        user_picks = picks_by_user_week.get(email, {})
        by_week: Dict[int, int] = {}
        for week_str, picks in user_picks.items():
            wk = _to_int_week(week_str)
            week_results = results_by_week.get(week_str)
            if wk is not None and week_results:
                by_week[wk] = _calculate_weekly_points(picks, week_results)
        by_user[email] = {"user_name": user["name"], "by_week": by_week}

    return {"weeks_with_results": weeks_with_results, "by_user": by_user}


def is_season_complete(data_manager: DataManager) -> bool:
    """True once final results have been entered (the champion is known)."""
    return bool(data_manager.get_final_results())


def run_final_scoring(
    data_manager: DataManager, final_winner: str, finalist_2: str, finalist_3: str
) -> bool:
    """
    Save final season results and recalculate all foresight points.

    Returns:
        Boolean indicating success.
    """
    return data_manager.save_final_results(final_winner, finalist_2, finalist_3)
