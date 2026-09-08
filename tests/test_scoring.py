"""Unit tests for the pure scoring functions (no DB / Streamlit needed)."""

from src.config import FORESIGHT_BASE_WEEK
from src.scoring import (
    _calculate_foresight_points,
    _calculate_weekly_points,
    _foresight_multiplier,
)


def mult(week: int) -> int:
    return FORESIGHT_BASE_WEEK - week


# --------------------------------------------------------------------------
# Weekly points
# --------------------------------------------------------------------------


def test_all_weekly_picks_correct_with_handshake():
    picks = {
        "star_baker": "Alice",
        "eliminated_baker": "Bob",
        "technical_winner": "Cara",
        "hollywood_handshake": True,
    }
    results = {
        "star_baker": "Alice",
        "eliminated_baker": "Bob",
        "technical_winner": "Cara",
        "hollywood_handshake": True,
    }
    # 5 + 5 + 3 + 10
    assert _calculate_weekly_points(picks, results) == 23


def test_handshake_no_penalty_when_predicting_none_given():
    # Player predicted NO handshake, one was given -> no penalty.
    picks = {"hollywood_handshake": False}
    results = {"hollywood_handshake": True}
    assert _calculate_weekly_points(picks, results) == 0


def test_handshake_penalty_when_predicted_but_not_given():
    picks = {"hollywood_handshake": True}
    results = {"hollywood_handshake": False}
    assert _calculate_weekly_points(picks, results) == -10


def test_star_baker_sent_home_penalty():
    # Predicted Star Baker was actually eliminated.
    picks = {"star_baker": "Alice"}
    results = {"eliminated_baker": "Alice"}
    assert _calculate_weekly_points(picks, results) == -5


def test_eliminated_pick_was_star_baker_penalty():
    picks = {"eliminated_baker": "Alice"}
    results = {"star_baker": "Alice"}
    assert _calculate_weekly_points(picks, results) == -5


def test_blank_picks_score_zero_not_matched_as_equal():
    # Empty picks must not accidentally match empty result fields.
    picks = {"star_baker": "", "eliminated_baker": None}
    results = {"star_baker": "", "eliminated_baker": None}
    assert _calculate_weekly_points(picks, results) == 0


# --------------------------------------------------------------------------
# Foresight multiplier is config-driven
# --------------------------------------------------------------------------


def test_multiplier_derived_from_config():
    assert _foresight_multiplier(2) == FORESIGHT_BASE_WEEK - 2
    assert _foresight_multiplier(FORESIGHT_BASE_WEEK - 1) == 1


def test_multiplier_floored_at_one():
    # A pick at/after the base week never scores zero or negative.
    assert _foresight_multiplier(FORESIGHT_BASE_WEEK) == 1
    assert _foresight_multiplier(FORESIGHT_BASE_WEEK + 3) == 1


# --------------------------------------------------------------------------
# Foresight points
# --------------------------------------------------------------------------

FINAL = {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"}


def test_no_foresight_without_final_results():
    picks = {"3": {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"}}
    assert _calculate_foresight_points(picks, {}) == 0


def test_perfect_sheet_from_week_two():
    picks = {"2": {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"}}
    # winner bonus 10*mult + three finalists (Alice, Bob, Cara) 5*mult each
    expected = mult(2) * 10 + 3 * (mult(2) * 5)
    assert _calculate_foresight_points(picks, FINAL) == expected


def test_winner_named_in_finalist_slot_still_earns_finalist_credit():
    # The reported 2025 bug: champion (Alice) placed in a finalist slot.
    # She should still count as a correctly-identified finalist.
    picks = {"3": {"season_winner": "Bob", "finalist_2": "Alice", "finalist_3": "Cara"}}
    # No winner bonus (season_winner=Bob is wrong), but all three actual
    # finalists were named somewhere: Alice(f2), Bob(sw), Cara(f3).
    expected = 3 * (mult(3) * 5)
    assert _calculate_foresight_points(picks, FINAL) == expected


def test_foresight_capped_to_earliest_correct_week():
    # Same correct winner pick submitted in weeks 4 and 6 -> only week 4 counts.
    picks = {
        "4": {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"},
        "6": {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"},
    }
    expected = mult(4) * 10 + 3 * (mult(4) * 5)
    assert _calculate_foresight_points(picks, FINAL) == expected


def test_earliest_week_taken_per_person_across_changing_picks():
    # Alice named as winner from week 2; Bob only added in week 5.
    picks = {
        "2": {"season_winner": "Alice", "finalist_2": "Zed", "finalist_3": "Cara"},
        "5": {"season_winner": "Alice", "finalist_2": "Bob", "finalist_3": "Cara"},
    }
    # winner Alice earliest wk2; finalists: Alice wk2, Cara wk2, Bob wk5.
    expected = mult(2) * 10 + (mult(2) * 5) + (mult(2) * 5) + (mult(5) * 5)
    assert _calculate_foresight_points(picks, FINAL) == expected


def test_completely_wrong_sheet_scores_zero():
    picks = {"2": {"season_winner": "Zed", "finalist_2": "Yan", "finalist_3": "Xir"}}
    assert _calculate_foresight_points(picks, FINAL) == 0
