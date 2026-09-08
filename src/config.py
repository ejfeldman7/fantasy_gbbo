from datetime import datetime, timezone

# =============================================================================
# SEASON CONFIGURATION — update this block each season.
# =============================================================================
#
# The league runs from Week 2 (first eliminations) through the finale. Set
# FINALE_WEEK to the final episode's week number. Everything downstream
# (foresight multiplier, "season complete" detection) is derived from it, so
# you no longer have to touch the scoring engine when the episode count changes.

FINALE_WEEK = 10

# Foresight points are worth (FORESIGHT_BASE_WEEK - week) x base. With the base
# set to FINALE_WEEK + 1, a correct pick made in the finale week is still worth
# 1x, and earlier picks scale up from there. Do not hardcode this elsewhere.
FORESIGHT_BASE_WEEK = FINALE_WEEK + 1


# Central dictionary for week dates. Update this for a new season.
#
# 2026 = GBBO Series 17. UK broadcast Tuesdays 22 Sep – 24 Nov 2026 (Channel 4);
# Netflix US drops each episode 3 days later (Friday). "Week N" = Netflix episode
# N; picks run Week 2 through the Week 10 finale. Dates below are the Netflix
# Friday drop dates (= submission deadlines).
WEEK_DATES = {
    "2": "Week 2 (10/2)",
    "3": "Week 3 (10/9)",
    "4": "Week 4 (10/16)",
    "5": "Week 5 (10/23)",
    "6": "Week 6 (10/30)",
    "7": "Week 7 (11/6)",
    "8": "Week 8 (11/13)",
    "9": "Week 9 (11/20)",
    "10": "Week 10 — Finale (11/27)",
}

# Defines when picks for a week become public (submission deadline).
# Set to Friday 00:00 PT (when the Netflix episode drops).
REVEAL_DATES_UTC = {
    # 00:00 PT = 07:00 UTC (PDT) while daylight time is in effect.
    "2": datetime(2026, 10, 2, 7, 0, 0, tzinfo=timezone.utc),
    "3": datetime(2026, 10, 9, 7, 0, 0, tzinfo=timezone.utc),
    "4": datetime(2026, 10, 16, 7, 0, 0, tzinfo=timezone.utc),
    "5": datetime(2026, 10, 23, 7, 0, 0, tzinfo=timezone.utc),
    "6": datetime(2026, 10, 30, 7, 0, 0, tzinfo=timezone.utc),
    # DST ends Sunday Nov 1, 2026 — deadlines on/after Nov 6 are PST (UTC-8):
    # 00:00 PT = 08:00 UTC.
    "7": datetime(2026, 11, 6, 8, 0, 0, tzinfo=timezone.utc),
    "8": datetime(2026, 11, 13, 8, 0, 0, tzinfo=timezone.utc),
    "9": datetime(2026, 11, 20, 8, 0, 0, tzinfo=timezone.utc),
    "10": datetime(2026, 11, 27, 8, 0, 0, tzinfo=timezone.utc),
}
