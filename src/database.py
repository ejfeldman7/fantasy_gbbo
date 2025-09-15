"""
Database management module for Fantasy GBBO using PostgreSQL/Neon
"""

import streamlit as st
import pandas as pd
from sqlalchemy import text
from typing import Dict, List, Optional, Any
from datetime import datetime


class DatabaseManager:
    """Handles all database operations for the Fantasy GBBO app."""

    def __init__(self):
        """Initializes the connection and ensures tables exist."""
        # Use "neon" to match the name in secrets.toml
        self.conn = st.connection("neon", type="sql")
        self._initialize_tables()

    def _initialize_tables(self):
        """
        Create tables if they don't exist.
        Uses a single session and transaction to create all tables.
        """
        with self.conn.session as s:
            # Users table
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            )

            # Bakers table
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS bakers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    is_eliminated BOOLEAN DEFAULT FALSE,
                    elimination_week INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            )

            # Weekly picks table
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS weekly_picks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    week_number INTEGER NOT NULL,
                    star_baker VARCHAR(100),
                    technical_winner VARCHAR(100),
                    eliminated_baker VARCHAR(100),
                    hollywood_handshake BOOLEAN,
                    season_winner VARCHAR(100),
                    finalist_2 VARCHAR(100),
                    finalist_3 VARCHAR(100),
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, week_number)
                );
            """)
            )

            # Weekly results table
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS weekly_results (
                    id SERIAL PRIMARY KEY,
                    week_number INTEGER UNIQUE NOT NULL,
                    star_baker VARCHAR(100),
                    technical_winner VARCHAR(100),
                    eliminated_baker VARCHAR(100),
                    hollywood_handshake BOOLEAN,
                    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            )

            # Final results table
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS final_results (
                    id SERIAL PRIMARY KEY,
                    season_winner VARCHAR(100),
                    finalist_2 VARCHAR(100),
                    finalist_3 VARCHAR(100),
                    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            )

            # Week settings table for managing pick availability
            s.execute(
                text("""
                CREATE TABLE IF NOT EXISTS week_settings (
                    week_number INTEGER PRIMARY KEY,
                    original_deadline TIMESTAMP,
                    admin_override BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            )
            s.commit()

    # --- User management methods ---

    def add_user(self, name: str, email: str) -> bool:
        """Add a new user using a parameterized query."""
        try:
            with self.conn.session as s:
                s.execute(
                    text("INSERT INTO users (name, email) VALUES (:name, :email)"),
                    params=dict(name=name, email=email),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error adding user: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email. .query() is appropriate here."""
        try:
            result = self.conn.query(
                "SELECT * FROM users WHERE email = :email",
                params=dict(email=email),
                ttl="1m",
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting user: {e}")
            return None

    def get_all_users(self) -> pd.DataFrame:
        """Get all users. .query() is appropriate here."""
        return self.conn.query("SELECT * FROM users ORDER BY name", ttl="1m")

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their picks."""
        try:
            with self.conn.session as s:
                s.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    params=dict(user_id=user_id),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error deleting user: {e}")
            return False

    # --- Baker management methods ---

    def add_baker(self, name: str) -> bool:
        """Add a new baker."""
        try:
            with self.conn.session as s:
                s.execute(
                    text("INSERT INTO bakers (name) VALUES (:name)"),
                    params=dict(name=name),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error adding baker: {e}")
            return False

    def get_active_bakers(self) -> List[str]:
        """Get list of active (non-eliminated) bakers."""
        result = self.conn.query(
            "SELECT name FROM bakers WHERE is_eliminated = FALSE ORDER BY name",
            ttl="1m",
        )
        return result["name"].tolist() if not result.empty else []

    def get_all_bakers(self) -> pd.DataFrame:
        """Get all bakers."""
        return self.conn.query("SELECT * FROM bakers ORDER BY name", ttl="1m")

    def eliminate_baker(self, name: str, week: int) -> bool:
        """Mark a baker as eliminated."""
        try:
            with self.conn.session as s:
                s.execute(
                    text(
                        "UPDATE bakers SET is_eliminated = TRUE, elimination_week = :week WHERE name = :name"
                    ),
                    params=dict(week=week, name=name),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error eliminating baker: {e}")
            return False

    def delete_baker(self, baker_id: int) -> bool:
        """Delete a baker by ID."""
        try:
            with self.conn.session as s:
                s.execute(
                    text("DELETE FROM bakers WHERE id = :baker_id"),
                    params=dict(baker_id=baker_id),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error deleting baker: {e}")
            return False

    # --- Picks management methods ---

    def save_picks(self, user_id: int, week: int, picks: Dict[str, Any]) -> bool:
        """Save or update weekly picks for a user."""
        try:
            # Check if picks already exist
            existing = self.conn.query(
                "SELECT id FROM weekly_picks WHERE user_id = :user_id AND week_number = :week",
                params=dict(user_id=user_id, week=week),
                ttl=0,
            )

            with self.conn.session as s:
                if not existing.empty:
                    # Update existing picks
                    sql = text("""
                        UPDATE weekly_picks SET
                            star_baker = :star_baker, technical_winner = :technical_winner,
                            eliminated_baker = :eliminated_baker, hollywood_handshake = :hollywood_handshake,
                            season_winner = :season_winner, finalist_2 = :finalist_2, finalist_3 = :finalist_3,
                            submitted_at = CURRENT_TIMESTAMP
                        WHERE user_id = :user_id AND week_number = :week
                    """)
                else:
                    # Insert new picks
                    sql = text("""
                        INSERT INTO weekly_picks (
                            user_id, week_number, star_baker, technical_winner,
                            eliminated_baker, hollywood_handshake, season_winner,
                            finalist_2, finalist_3
                        ) VALUES (
                            :user_id, :week, :star_baker, :technical_winner,
                            :eliminated_baker, :hollywood_handshake, :season_winner,
                            :finalist_2, :finalist_3
                        )
                    """)

                s.execute(
                    sql,
                    params={
                        "user_id": user_id,
                        "week": week,
                        "star_baker": picks.get("star_baker"),
                        "technical_winner": picks.get("technical_winner"),
                        "eliminated_baker": picks.get("eliminated_baker"),
                        "hollywood_handshake": picks.get("hollywood_handshake"),
                        "season_winner": picks.get("season_winner"),
                        "finalist_2": picks.get("finalist_2"),
                        "finalist_3": picks.get("finalist_3"),
                    },
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error saving picks: {e}")
            return False

    def get_user_picks(self, user_id: int, week: int) -> Optional[Dict]:
        """Get picks for a specific user and week."""
        try:
            result = self.conn.query(
                "SELECT * FROM weekly_picks WHERE user_id = :user_id AND week_number = :week",
                params=dict(user_id=user_id, week=week),
                ttl="1m",
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting user picks: {e}")
            return None

    def get_all_picks(self) -> pd.DataFrame:
        """Get all picks across all weeks and users."""
        return self.conn.query(
            """
            SELECT wp.*, u.name as user_name, u.email
            FROM weekly_picks wp
            JOIN users u ON wp.user_id = u.id
            ORDER BY wp.week_number, u.name
        """,
            ttl="30s",
        )

    def get_all_picks_for_week(self, week: int) -> pd.DataFrame:
        """Get all picks for a specific week."""
        return self.conn.query(
            """
            SELECT wp.*, u.name as user_name, u.email
            FROM weekly_picks wp
            JOIN users u ON wp.user_id = u.id
            WHERE wp.week_number = :week
            ORDER BY u.name
        """,
            params=dict(week=week),
            ttl="30s",
        )

    # --- Results management methods ---

    def save_weekly_results(self, week: int, results: Dict[str, Any]) -> bool:
        """Save weekly results."""
        try:
            existing = self.conn.query(
                "SELECT id FROM weekly_results WHERE week_number = :week",
                params=dict(week=week),
                ttl=0,
            )

            with self.conn.session as s:
                if not existing.empty:
                    sql = text("""
                        UPDATE weekly_results SET
                            star_baker = :star_baker, technical_winner = :technical_winner,
                            eliminated_baker = :eliminated_baker, hollywood_handshake = :hollywood_handshake,
                            entered_at = CURRENT_TIMESTAMP
                        WHERE week_number = :week
                    """)
                else:
                    sql = text("""
                        INSERT INTO weekly_results (
                            week_number, star_baker, technical_winner,
                            eliminated_baker, hollywood_handshake
                        ) VALUES (:week, :star_baker, :technical_winner, :eliminated_baker, :hollywood_handshake)
                    """)
                s.execute(
                    sql,
                    params={
                        "week": week,
                        "star_baker": results.get("star_baker"),
                        "technical_winner": results.get("technical_winner"),
                        "eliminated_baker": results.get("eliminated_baker"),
                        "hollywood_handshake": results.get("hollywood_handshake"),
                    },
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error saving results: {e}")
            return False

    def get_weekly_results(self, week: int) -> Optional[Dict]:
        """Get weekly results for a specific week."""
        try:
            result = self.conn.query(
                "SELECT * FROM weekly_results WHERE week_number = :week",
                params=dict(week=week),
                ttl="1m",
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting weekly results: {e}")
            return None

    def get_all_weekly_results(self) -> pd.DataFrame:
        """Get all weekly results."""
        return self.conn.query(
            "SELECT * FROM weekly_results ORDER BY week_number", ttl="1m"
        )

    def save_final_results(self, winner: str, finalist_2: str, finalist_3: str) -> bool:
        """Save final season results."""
        try:
            with self.conn.session as s:
                # Clear existing final results to ensure only one row
                s.execute(text("DELETE FROM final_results"))
                # Insert new final results
                s.execute(
                    text("""
                        INSERT INTO final_results (season_winner, finalist_2, finalist_3)
                        VALUES (:winner, :finalist_2, :finalist_3)
                    """),
                    params=dict(
                        winner=winner, finalist_2=finalist_2, finalist_3=finalist_3
                    ),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error saving final results: {e}")
            return False

    def get_final_results(self) -> Optional[Dict]:
        """Get final season results."""
        try:
            result = self.conn.query("SELECT * FROM final_results LIMIT 1", ttl="1m")
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting final results: {e}")
            return None

    def backup_all_data(self) -> Dict[str, Any]:
        """Create a backup of all data."""
        try:
            backup = {
                "users": self.get_all_users().to_dict("records"),
                "bakers": self.get_all_bakers().to_dict("records"),
                "weekly_picks": self.get_all_picks().to_dict("records"),
                "weekly_results": self.get_all_weekly_results().to_dict("records"),
                "final_results": self.get_final_results(),
                "backup_timestamp": datetime.now().isoformat(),
            }
            return backup
        except Exception as e:
            st.error(f"Error creating backup: {e}")
            return {}

    # --- Week Settings Management ---

    def initialize_week_settings(self, week_dates_config: Dict) -> bool:
        """Initialize week settings from config if they don't exist."""
        try:
            with self.conn.session as s:
                for week_str, deadline in week_dates_config.items():
                    week_num = int(week_str)
                    # Check if week already exists
                    existing = self.conn.query(
                        "SELECT week_number FROM week_settings WHERE week_number = :week",
                        params=dict(week=week_num),
                        ttl=0,
                    )

                    if existing.empty:
                        s.execute(
                            text("""
                                INSERT INTO week_settings (week_number, original_deadline) 
                                VALUES (:week, :deadline)
                            """),
                            params=dict(week=week_num, deadline=deadline),
                        )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error initializing week settings: {e}")
            return False

    def _ensure_timezone_aware(self, dt, default_tz=None):
        """Helper method to ensure datetime is timezone-aware."""
        from datetime import timezone
        import pandas as pd
        
        if default_tz is None:
            default_tz = timezone.utc
        
        if dt is None:
            return None
            
        try:
            if isinstance(dt, pd.Timestamp):
                if dt.tz is None:
                    return dt.tz_localize(default_tz)
                else:
                    return dt.tz_convert(default_tz)
            elif hasattr(dt, 'tzinfo'):
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=default_tz)
                else:
                    return dt
            else:
                # Fallback: convert to pandas timestamp and localize
                return pd.Timestamp(dt).tz_localize(default_tz)
        except Exception:
            # Last resort: return None to indicate failure
            return None

    def get_available_weeks(self, current_time) -> List[str]:
        """Get list of weeks that are currently available for picks."""
        try:
            # Get all week settings
            week_settings = self.conn.query("SELECT * FROM week_settings", ttl="30s")
            available_weeks = []

            # Ensure current_time is timezone-aware
            current_time = self._ensure_timezone_aware(current_time)
            if current_time is None:
                st.error("Invalid current_time provided")
                return []

            for _, week in week_settings.iterrows():
                week_num = str(week["week_number"])
                admin_override = week.get("admin_override", False)
                original_deadline = week.get("original_deadline")

                # Allow if admin override is enabled
                if admin_override:
                    available_weeks.append(week_num)
                    continue
                    
                # Check original deadline
                if original_deadline is not None:
                    original_deadline = self._ensure_timezone_aware(original_deadline)
                    if original_deadline is not None and current_time < original_deadline:
                        available_weeks.append(week_num)

            return available_weeks
        except Exception as e:
            st.error(f"Error getting available weeks: {e}")
            return []

    def set_week_override(self, week_number: int, override_enabled: bool) -> bool:
        """Set admin override for a specific week."""
        try:
            with self.conn.session as s:
                s.execute(
                    text("""
                        UPDATE week_settings 
                        SET admin_override = :override, updated_at = CURRENT_TIMESTAMP 
                        WHERE week_number = :week
                    """),
                    params=dict(override=override_enabled, week=week_number),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error setting week override: {e}")
            return False

    def get_week_settings(self) -> List[Dict]:
        """Get all week settings."""
        try:
            result = self.conn.query(
                "SELECT * FROM week_settings ORDER BY week_number", ttl="30s"
            )
            return result.to_dict("records") if not result.empty else []
        except Exception as e:
            st.error(f"Error getting week settings: {e}")
            return []

    def reset_all_data(self) -> bool:
        """Reset all data (use with caution!)."""
        try:
            with self.conn.session as s:
                # Delete in order to respect foreign key constraints
                s.execute(text("DELETE FROM weekly_picks"))
                s.execute(text("DELETE FROM weekly_results"))
                s.execute(text("DELETE FROM final_results"))
                s.execute(text("DELETE FROM week_settings"))
                s.execute(text("DELETE FROM bakers"))
                s.execute(text("DELETE FROM users"))
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error resetting data: {e}")
            return False
