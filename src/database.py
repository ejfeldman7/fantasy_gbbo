"""
Database management module for Fantasy GBBO using PostgreSQL/Neon
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class DatabaseManager:
    """Handles all database operations for the Fantasy GBBO app"""
    
    def __init__(self):
        self.conn = st.connection("neon", type="sql")
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Create tables if they don't exist"""
        
        # Users table
        self.conn.query("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, ttl=0)
        
        # Bakers table
        self.conn.query("""
            CREATE TABLE IF NOT EXISTS bakers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                is_eliminated BOOLEAN DEFAULT FALSE,
                elimination_week INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, ttl=0)
        
        # Weekly picks table
        self.conn.query("""
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
            )
        """, ttl=0)
        
        # Weekly results table
        self.conn.query("""
            CREATE TABLE IF NOT EXISTS weekly_results (
                id SERIAL PRIMARY KEY,
                week_number INTEGER UNIQUE NOT NULL,
                star_baker VARCHAR(100),
                technical_winner VARCHAR(100),
                eliminated_baker VARCHAR(100),
                hollywood_handshake BOOLEAN,
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, ttl=0)
        
        # Final results table
        self.conn.query("""
            CREATE TABLE IF NOT EXISTS final_results (
                id SERIAL PRIMARY KEY,
                season_winner VARCHAR(100),
                finalist_2 VARCHAR(100),
                finalist_3 VARCHAR(100),
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, ttl=0)
    
    # User management methods
    def add_user(self, name: str, email: str) -> bool:
        """Add a new user"""
        try:
            self.conn.query(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                params=[name, email],
                ttl=0
            )
            return True
        except Exception as e:
            st.error(f"Error adding user: {e}")
            return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            result = self.conn.query(
                "SELECT * FROM users WHERE email = %s",
                params=[email],
                ttl="1m"
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting user: {e}")
            return None
    
    def get_all_users(self) -> pd.DataFrame:
        """Get all users"""
        return self.conn.query("SELECT * FROM users ORDER BY name", ttl="1m")
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their picks"""
        try:
            self.conn.query("DELETE FROM users WHERE id = %s", params=[user_id], ttl=0)
            return True
        except Exception as e:
            st.error(f"Error deleting user: {e}")
            return False
    
    # Baker management methods
    def add_baker(self, name: str) -> bool:
        """Add a new baker"""
        try:
            self.conn.query(
                "INSERT INTO bakers (name) VALUES (%s)",
                params=[name],
                ttl=0
            )
            return True
        except Exception as e:
            st.error(f"Error adding baker: {e}")
            return False
    
    def get_active_bakers(self) -> List[str]:
        """Get list of active (non-eliminated) bakers"""
        result = self.conn.query(
            "SELECT name FROM bakers WHERE is_eliminated = FALSE ORDER BY name",
            ttl="1m"
        )
        return result['name'].tolist() if not result.empty else []
    
    def get_all_bakers(self) -> pd.DataFrame:
        """Get all bakers"""
        return self.conn.query("SELECT * FROM bakers ORDER BY name", ttl="1m")
    
    def eliminate_baker(self, name: str, week: int) -> bool:
        """Mark a baker as eliminated"""
        try:
            self.conn.query(
                "UPDATE bakers SET is_eliminated = TRUE, elimination_week = %s WHERE name = %s",
                params=[week, name],
                ttl=0
            )
            return True
        except Exception as e:
            st.error(f"Error eliminating baker: {e}")
            return False
    
    def delete_baker(self, baker_id: int) -> bool:
        """Delete a baker"""
        try:
            self.conn.query("DELETE FROM bakers WHERE id = %s", params=[baker_id], ttl=0)
            return True
        except Exception as e:
            st.error(f"Error deleting baker: {e}")
            return False
    
    # Picks management methods
    def save_picks(self, user_id: int, week: int, picks: Dict[str, Any]) -> bool:
        """Save or update weekly picks for a user"""
        try:
            # Check if picks already exist
            existing = self.conn.query(
                "SELECT id FROM weekly_picks WHERE user_id = %s AND week_number = %s",
                params=[user_id, week],
                ttl=0
            )
            
            if not existing.empty:
                # Update existing picks
                self.conn.query("""
                    UPDATE weekly_picks SET
                        star_baker = %s,
                        technical_winner = %s,
                        eliminated_baker = %s,
                        hollywood_handshake = %s,
                        season_winner = %s,
                        finalist_2 = %s,
                        finalist_3 = %s,
                        submitted_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND week_number = %s
                """, params=[
                    picks.get('star_baker'),
                    picks.get('technical_winner'),
                    picks.get('eliminated_baker'),
                    picks.get('hollywood_handshake'),
                    picks.get('season_winner'),
                    picks.get('finalist_2'),
                    picks.get('finalist_3'),
                    user_id,
                    week
                ], ttl=0)
            else:
                # Insert new picks
                self.conn.query("""
                    INSERT INTO weekly_picks (
                        user_id, week_number, star_baker, technical_winner,
                        eliminated_baker, hollywood_handshake, season_winner,
                        finalist_2, finalist_3
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, params=[
                    user_id, week,
                    picks.get('star_baker'),
                    picks.get('technical_winner'),
                    picks.get('eliminated_baker'),
                    picks.get('hollywood_handshake'),
                    picks.get('season_winner'),
                    picks.get('finalist_2'),
                    picks.get('finalist_3')
                ], ttl=0)
            return True
        except Exception as e:
            st.error(f"Error saving picks: {e}")
            return False
    
    def get_user_picks(self, user_id: int, week: int) -> Optional[Dict]:
        """Get picks for a specific user and week"""
        try:
            result = self.conn.query(
                "SELECT * FROM weekly_picks WHERE user_id = %s AND week_number = %s",
                params=[user_id, week],
                ttl="30s"
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting user picks: {e}")
            return None
    
    def get_all_picks_for_week(self, week: int) -> pd.DataFrame:
        """Get all picks for a specific week"""
        return self.conn.query("""
            SELECT wp.*, u.name as user_name, u.email 
            FROM weekly_picks wp
            JOIN users u ON wp.user_id = u.id
            WHERE wp.week_number = %s
            ORDER BY u.name
        """, params=[week], ttl="30s")
    
    def get_all_picks(self) -> pd.DataFrame:
        """Get all picks with user information"""
        return self.conn.query("""
            SELECT wp.*, u.name as user_name, u.email 
            FROM weekly_picks wp
            JOIN users u ON wp.user_id = u.id
            ORDER BY wp.week_number, u.name
        """, ttl="1m")
    
    # Results management methods
    def save_weekly_results(self, week: int, results: Dict[str, Any]) -> bool:
        """Save weekly results"""
        try:
            # Check if results already exist
            existing = self.conn.query(
                "SELECT id FROM weekly_results WHERE week_number = %s",
                params=[week],
                ttl=0
            )
            
            if not existing.empty:
                # Update existing results
                self.conn.query("""
                    UPDATE weekly_results SET
                        star_baker = %s,
                        technical_winner = %s,
                        eliminated_baker = %s,
                        hollywood_handshake = %s,
                        entered_at = CURRENT_TIMESTAMP
                    WHERE week_number = %s
                """, params=[
                    results.get('star_baker'),
                    results.get('technical_winner'),
                    results.get('eliminated_baker'),
                    results.get('hollywood_handshake'),
                    week
                ], ttl=0)
            else:
                # Insert new results
                self.conn.query("""
                    INSERT INTO weekly_results (
                        week_number, star_baker, technical_winner,
                        eliminated_baker, hollywood_handshake
                    ) VALUES (%s, %s, %s, %s, %s)
                """, params=[
                    week,
                    results.get('star_baker'),
                    results.get('technical_winner'),
                    results.get('eliminated_baker'),
                    results.get('hollywood_handshake')
                ], ttl=0)
            return True
        except Exception as e:
            st.error(f"Error saving results: {e}")
            return False
    
    def get_weekly_results(self, week: int) -> Optional[Dict]:
        """Get results for a specific week"""
        try:
            result = self.conn.query(
                "SELECT * FROM weekly_results WHERE week_number = %s",
                params=[week],
                ttl="1m"
            )
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting weekly results: {e}")
            return None
    
    def get_all_weekly_results(self) -> pd.DataFrame:
        """Get all weekly results"""
        return self.conn.query("SELECT * FROM weekly_results ORDER BY week_number", ttl="1m")
    
    def save_final_results(self, winner: str, finalist_2: str, finalist_3: str) -> bool:
        """Save final season results"""
        try:
            # Clear existing final results
            self.conn.query("DELETE FROM final_results", ttl=0)
            
            # Insert new final results
            self.conn.query("""
                INSERT INTO final_results (season_winner, finalist_2, finalist_3)
                VALUES (%s, %s, %s)
            """, params=[winner, finalist_2, finalist_3], ttl=0)
            return True
        except Exception as e:
            st.error(f"Error saving final results: {e}")
            return False
    
    def get_final_results(self) -> Optional[Dict]:
        """Get final season results"""
        try:
            result = self.conn.query("SELECT * FROM final_results LIMIT 1", ttl="1m")
            return result.iloc[0].to_dict() if not result.empty else None
        except Exception as e:
            st.error(f"Error getting final results: {e}")
            return None
    
    # Data management methods
    def backup_all_data(self) -> Dict[str, Any]:
        """Create a backup of all data"""
        try:
            backup = {
                'users': self.get_all_users().to_dict('records'),
                'bakers': self.get_all_bakers().to_dict('records'),
                'picks': self.get_all_picks().to_dict('records'),
                'weekly_results': self.get_all_weekly_results().to_dict('records'),
                'final_results': self.get_final_results(),
                'backup_timestamp': datetime.now().isoformat()
            }
            return backup
        except Exception as e:
            st.error(f"Error creating backup: {e}")
            return {}
    
    def reset_all_data(self) -> bool:
        """Reset all data (use with caution!)"""
        try:
            # Delete in order to respect foreign key constraints
            self.conn.query("DELETE FROM weekly_picks", ttl=0)
            self.conn.query("DELETE FROM weekly_results", ttl=0)
            self.conn.query("DELETE FROM final_results", ttl=0)
            self.conn.query("DELETE FROM bakers", ttl=0)
            self.conn.query("DELETE FROM users", ttl=0)
            return True
        except Exception as e:
            st.error(f"Error resetting data: {e}")
            return False
