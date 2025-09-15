from typing import Dict
from src.data_manager import DataManager


def calculate_user_scores(data_manager: DataManager) -> Dict[str, Dict[str, int]]:
    """
    Calculates total scores for all users, including weekly and foresight points.

    Args:
        data_manager: DataManager instance with database access

    Returns:
        Dict mapping user emails to their score breakdown
    """
    scores = {}

    # Get all users and their picks
    users = data_manager.get_all_users()
    all_picks = data_manager.get_all_picks()
    weekly_results = data_manager.get_all_weekly_results()
    final_results = data_manager.get_final_results()

    # Create lookup dictionaries
    results_by_week = {str(result["week_number"]): result for result in weekly_results}
    picks_by_user_week = {}

    # Group picks by user and week
    for pick in all_picks:
        user_email = pick.get("email", "")
        week = str(pick.get("week_number", ""))
        if user_email not in picks_by_user_week:
            picks_by_user_week[user_email] = {}
        picks_by_user_week[user_email][week] = pick

    # Calculate scores for each user
    for user in users:
        user_email = user["email"]
        weekly_points = 0
        foresight_points = 0

        user_picks = picks_by_user_week.get(user_email, {})

        # Calculate weekly points
        for week_str, picks in user_picks.items():
            week_results = results_by_week.get(week_str)
            if week_results:
                weekly_points += _calculate_weekly_points(picks, week_results)

        # Calculate foresight points (if final results are available)
        if final_results:
            for week_str, picks in user_picks.items():
                try:
                    week_num = int(week_str)
                    foresight_points += _calculate_foresight_points_for_week(
                        picks, final_results, week_num
                    )
                except (ValueError, TypeError):
                    continue

        scores[user_email] = {
            "weekly_points": weekly_points,
            "foresight_points": foresight_points,
            "total_points": weekly_points + foresight_points,
            "user_name": user["name"],
        }

    return scores


def _calculate_weekly_points(picks: Dict, results: Dict) -> int:
    """Calculate weekly points for a single week's picks vs results."""
    points = 0

    # Positive points
    if picks.get("star_baker") == results.get("star_baker"):
        points += 5
    if picks.get("eliminated_baker") == results.get("eliminated_baker"):
        points += 5
    if picks.get("technical_winner") == results.get("technical_winner"):
        points += 3
    if picks.get("hollywood_handshake") and results.get("hollywood_handshake"):
        points += 10

    # Penalties
    if picks.get("star_baker") == results.get("eliminated_baker"):
        points -= 5
    if picks.get("eliminated_baker") == results.get("star_baker"):
        points -= 5
    if picks.get("hollywood_handshake") and not results.get("hollywood_handshake"):
        points -= 10

    return points


def _calculate_foresight_points_for_week(
    picks: Dict, final_results: Dict, week_num: int
) -> int:
    """Calculate foresight points for a single week's picks."""
    points = 0

    # Season winner prediction
    if picks.get("season_winner") == final_results.get("season_winner"):
        points += (11 - week_num) * 10

    # Finalist predictions
    finalists = [final_results.get("finalist_2"), final_results.get("finalist_3")]
    if picks.get("finalist_2") in finalists:
        points += (11 - week_num) * 5
    if picks.get("finalist_3") in finalists:
        points += (11 - week_num) * 5

    return points


def run_final_scoring(
    data_manager: DataManager, final_winner: str, finalist_2: str, finalist_3: str
) -> bool:
    """
    Save final season results and recalculate all foresight points.

    Args:
        data_manager: DataManager instance
        final_winner: Name of the season winner
        finalist_2: Name of the second finalist
        finalist_3: Name of the third finalist

    Returns:
        Boolean indicating success
    """
    return data_manager.save_final_results(final_winner, finalist_2, finalist_3)
