from datetime import datetime, timezone

# Central dictionary for week dates. Update this for a new season.
WEEK_DATES = {
    "2": "Week 2 (9/12)",
    "3": "Week 3 (9/19)",
    "4": "Week 4 (9/26)",
    "5": "Week 5 (10/3)",
    "6": "Week 6 (10/10)",
    "7": "Week 7 (10/17)",
    "8": "Week 8 (10/24)",
    "9": "Week 9 (10/31)",
    "10": "Week 10 (11/7)",
}

# Defines when picks for a week become public (submission deadline).
# Set to Friday 00:00 PT.
REVEAL_DATES_UTC = {
    # All are Fridays. 00:00 PT = 07:00 UTC (PDT)
    "2": datetime(2025, 9, 12, 7, 0, 0, tzinfo=timezone.utc),
    "3": datetime(2025, 9, 19, 7, 0, 0, tzinfo=timezone.utc),
    "4": datetime(2025, 9, 26, 7, 0, 0, tzinfo=timezone.utc),
    "5": datetime(2025, 10, 3, 7, 0, 0, tzinfo=timezone.utc),
    "6": datetime(2025, 10, 10, 7, 0, 0, tzinfo=timezone.utc),
    "7": datetime(2025, 10, 17, 7, 0, 0, tzinfo=timezone.utc),
    "8": datetime(2025, 10, 24, 7, 0, 0, tzinfo=timezone.utc),
    "9": datetime(2025, 10, 31, 7, 0, 0, tzinfo=timezone.utc),
    # DST ends Sunday Nov 2. So the next deadline is PST (UTC-8)
    # 00:00 PT = 08:00 UTC (PST)
    "10": datetime(2025, 11, 7, 8, 0, 0, tzinfo=timezone.utc),
}
