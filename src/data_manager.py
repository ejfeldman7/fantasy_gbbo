"""
Updated data manager that uses PostgreSQL instead of JSON files
"""

from .database import DatabaseManager
from typing import Dict, List, Optional, Any
import streamlit as st
from sqlalchemy import text


class DataManager:
    """
    Compatibility layer that maintains the same interface as the original
    file-based DataManager but uses PostgreSQL backend
    """

    def __init__(self):
        self.db = DatabaseManager()

    # User management methods (maintain original interface)
    def add_user(self, name: str, email: str) -> bool:
        """Add a new user"""
        return self.db.add_user(name, email)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.db.get_user_by_email(email)

    def get_all_users(self) -> List[Dict]:
        """Get all users as a list of dictionaries"""
        df = self.db.get_all_users()
        return df.to_dict("records") if not df.empty else []

    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        return self.db.delete_user(user_id)

    def update_user(self, user_id: int, name: str, email: str) -> bool:
        """Update user information"""
        try:
            with self.db.conn.session as s:
                s.execute(
                    text(
                        "UPDATE users SET name = :name, email = :email WHERE id = :user_id"
                    ),
                    params=dict(name=name, email=email, user_id=user_id),
                )
                s.commit()
            return True
        except Exception as e:
            st.error(f"Error updating user: {e}")
            return False

    # Baker management methods
    def add_baker(self, name: str) -> bool:
        """Add a new baker"""
        return self.db.add_baker(name)

    def get_active_bakers(self) -> List[str]:
        """Get list of active bakers"""
        return self.db.get_active_bakers()

    def get_all_bakers(self) -> List[Dict]:
        """Get all bakers as a list of dictionaries"""
        df = self.db.get_all_bakers()
        return df.to_dict("records") if not df.empty else []

    def eliminate_baker(self, name: str, week: int) -> bool:
        """Eliminate a baker"""
        return self.db.eliminate_baker(name, week)

    def delete_baker(self, baker_id: int) -> bool:
        """Delete a baker"""
        return self.db.delete_baker(baker_id)

    # Picks management methods
    def save_user_picks(
        self, user_email: str, week: int, picks: Dict[str, Any]
    ) -> bool:
        """Save user picks (maintains original interface using email)"""
        user = self.get_user_by_email(user_email)
        if not user:
            st.error("User not found")
            return False
        return self.db.save_picks(user["id"], week, picks)

    def get_user_picks(self, user_email: str, week: int) -> Optional[Dict]:
        """Get user picks by email"""
        user = self.get_user_by_email(user_email)
        if not user:
            return None
        return self.db.get_user_picks(user["id"], week)

    def get_all_picks_for_week(self, week: int) -> List[Dict]:
        """Get all picks for a specific week"""
        df = self.db.get_all_picks_for_week(week)
        return df.to_dict("records") if not df.empty else []

    def get_all_picks(self) -> List[Dict]:
        """Get all picks"""
        df = self.db.get_all_picks()
        return df.to_dict("records") if not df.empty else []

    # Results management methods
    def save_weekly_results(self, week: int, results: Dict[str, Any]) -> bool:
        """Save weekly results"""
        return self.db.save_weekly_results(week, results)

    def get_weekly_results(self, week: int) -> Optional[Dict]:
        """Get weekly results"""
        return self.db.get_weekly_results(week)

    def get_all_weekly_results(self) -> List[Dict]:
        """Get all weekly results"""
        df = self.db.get_all_weekly_results()
        return df.to_dict("records") if not df.empty else []

    def save_final_results(self, winner: str, finalist_2: str, finalist_3: str) -> bool:
        """Save final results"""
        return self.db.save_final_results(winner, finalist_2, finalist_3)

    def get_final_results(self) -> Optional[Dict]:
        """Get final results"""
        return self.db.get_final_results()

    # Data management methods
    def backup_data(self) -> Dict[str, Any]:
        """Create a backup of all data"""
        return self.db.backup_all_data()

    def reset_all_data(self) -> bool:
        """Reset all data"""
        return self.db.reset_all_data()

    # Legacy compatibility methods (if needed)
    def load_data(self):
        """Placeholder for legacy compatibility - no longer needed with DB"""
        pass

    def save_data(self):
        """Placeholder for legacy compatibility - no longer needed with DB"""
        pass
