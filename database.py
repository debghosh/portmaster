"""
Portfolio Database Module
Handles all database operations for portfolio persistence, multi-tenancy, and sharing
"""

import sqlite3
import json
import pickle
import hashlib
from datetime import datetime
from contextlib import contextmanager
import streamlit as st


class PortfolioDB:
    """
    Portfolio Database Manager
    
    Features:
    - Multi-tenancy (each user has their own portfolios)
    - Public/Private portfolios
    - Persistent storage
    - Simple authentication
    """
    
    def __init__(self, db_path="portfolios.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Portfolios table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    portfolio_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    tickers TEXT NOT NULL,
                    weights TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_public INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, name)
                )
            """)
            
            # Portfolio data (stores prices and returns as pickled DataFrames)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_data (
                    portfolio_id TEXT PRIMARY KEY,
                    prices_data BLOB,
                    returns_data BLOB,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_portfolios ON portfolios(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_public_portfolios ON portfolios(is_public)")
    
    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================
    
    def create_user(self, username):
        """Create a new user or return existing user_id"""
        user_id = hashlib.md5(username.lower().encode()).hexdigest()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
                return user_id
            except sqlite3.IntegrityError:
                # Username already exists
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                return result['user_id'] if result else None
    
    def get_user(self, username):
        """Get user_id by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            return result['user_id'] if result else None
    
    def user_exists(self, username):
        """Check if username exists"""
        return self.get_user(username) is not None
    
    # =========================================================================
    # PORTFOLIO MANAGEMENT
    # =========================================================================
    
    def save_portfolio(self, user_id, name, tickers, weights, prices, returns, 
                      start_date, end_date, is_public=False):
        """
        Save or update a portfolio
        
        Args:
            user_id: User identifier
            name: Portfolio name
            tickers: List of ticker symbols
            weights: Dictionary of {ticker: weight}
            prices: DataFrame of prices
            returns: Series of returns
            start_date: Start date
            end_date: End date
            is_public: Whether portfolio is public (default: False)
        
        Returns:
            portfolio_id if successful, None otherwise
        """
        portfolio_id = hashlib.md5(f"{user_id}_{name}".encode()).hexdigest()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Save portfolio metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO portfolios 
                    (portfolio_id, user_id, name, tickers, weights, start_date, end_date, is_public, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    portfolio_id,
                    user_id,
                    name,
                    json.dumps(tickers),
                    json.dumps(weights),
                    start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date),
                    end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date),
                    1 if is_public else 0
                ))
                
                # Save portfolio data (prices and returns)
                prices_blob = pickle.dumps(prices)
                returns_blob = pickle.dumps(returns)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO portfolio_data 
                    (portfolio_id, prices_data, returns_data)
                    VALUES (?, ?, ?)
                """, (portfolio_id, prices_blob, returns_blob))
                
                return portfolio_id
                
        except Exception as e:
            st.error(f"Error saving portfolio: {str(e)}")
            return None
    
    def load_portfolio(self, portfolio_id):
        """
        Load a complete portfolio by ID
        
        Returns:
            Dictionary with portfolio data or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Load metadata
                cursor.execute("""
                    SELECT * FROM portfolios WHERE portfolio_id = ?
                """, (portfolio_id,))
                
                portfolio_row = cursor.fetchone()
                if not portfolio_row:
                    return None
                
                # Load data
                cursor.execute("""
                    SELECT prices_data, returns_data FROM portfolio_data WHERE portfolio_id = ?
                """, (portfolio_id,))
                
                data_row = cursor.fetchone()
                if not data_row:
                    return None
                
                # Unpickle data
                prices = pickle.loads(data_row['prices_data'])
                returns = pickle.loads(data_row['returns_data'])
                
                # Parse dates
                from datetime import datetime
                start_date = datetime.strptime(portfolio_row['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(portfolio_row['end_date'], '%Y-%m-%d').date()
                
                return {
                    'portfolio_id': portfolio_row['portfolio_id'],
                    'name': portfolio_row['name'],
                    'tickers': json.loads(portfolio_row['tickers']),
                    'weights': json.loads(portfolio_row['weights']),
                    'prices': prices,
                    'returns': returns,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_public': bool(portfolio_row['is_public']),
                    'created_at': portfolio_row['created_at'],
                    'updated_at': portfolio_row['updated_at']
                }
                
        except Exception as e:
            st.error(f"Error loading portfolio: {str(e)}")
            return None
    
    def get_user_portfolios(self, user_id):
        """
        Get all portfolios for a user (both owned and public)
        
        Returns:
            List of portfolio summaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get user's own portfolios
            cursor.execute("""
                SELECT portfolio_id, name, tickers, start_date, end_date, is_public, 
                       created_at, updated_at, user_id
                FROM portfolios 
                WHERE user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,))
            
            own_portfolios = [dict(row) for row in cursor.fetchall()]
            
            # Mark as owned
            for p in own_portfolios:
                p['owned'] = True
                p['tickers'] = json.loads(p['tickers'])
            
            # Get public portfolios from other users
            cursor.execute("""
                SELECT portfolio_id, name, tickers, start_date, end_date, is_public,
                       created_at, updated_at, user_id,
                       (SELECT username FROM users WHERE users.user_id = portfolios.user_id) as owner
                FROM portfolios 
                WHERE is_public = 1 AND user_id != ?
                ORDER BY updated_at DESC
            """, (user_id,))
            
            public_portfolios = [dict(row) for row in cursor.fetchall()]
            
            # Mark as not owned
            for p in public_portfolios:
                p['owned'] = False
                p['tickers'] = json.loads(p['tickers'])
            
            return own_portfolios + public_portfolios
    
    def delete_portfolio(self, portfolio_id, user_id):
        """
        Delete a portfolio (only if user owns it)
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verify ownership
                cursor.execute("""
                    SELECT user_id FROM portfolios WHERE portfolio_id = ?
                """, (portfolio_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    st.error("You can only delete your own portfolios")
                    return False
                
                # Delete portfolio (CASCADE will delete data too)
                cursor.execute("DELETE FROM portfolios WHERE portfolio_id = ?", (portfolio_id,))
                
                return True
                
        except Exception as e:
            st.error(f"Error deleting portfolio: {str(e)}")
            return False
    
    def toggle_portfolio_visibility(self, portfolio_id, user_id):
        """
        Toggle portfolio between public and private
        
        Returns:
            New visibility state (True = public) or None on error
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verify ownership
                cursor.execute("""
                    SELECT user_id, is_public FROM portfolios WHERE portfolio_id = ?
                """, (portfolio_id,))
                
                result = cursor.fetchone()
                if not result or result['user_id'] != user_id:
                    st.error("You can only modify your own portfolios")
                    return None
                
                # Toggle visibility
                new_state = 0 if result['is_public'] else 1
                
                cursor.execute("""
                    UPDATE portfolios SET is_public = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE portfolio_id = ?
                """, (new_state, portfolio_id))
                
                return bool(new_state)
                
        except Exception as e:
            st.error(f"Error toggling visibility: {str(e)}")
            return None
    
    # =========================================================================
    # SEARCH AND DISCOVERY
    # =========================================================================
    
    def search_public_portfolios(self, search_term=None):
        """
        Search public portfolios
        
        Args:
            search_term: Optional search term for name/tickers
        
        Returns:
            List of public portfolio summaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if search_term:
                cursor.execute("""
                    SELECT p.portfolio_id, p.name, p.tickers, p.start_date, p.end_date,
                           p.created_at, p.updated_at, u.username as owner
                    FROM portfolios p
                    JOIN users u ON p.user_id = u.user_id
                    WHERE p.is_public = 1 
                    AND (p.name LIKE ? OR p.tickers LIKE ?)
                    ORDER BY p.updated_at DESC
                """, (f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute("""
                    SELECT p.portfolio_id, p.name, p.tickers, p.start_date, p.end_date,
                           p.created_at, p.updated_at, u.username as owner
                    FROM portfolios p
                    JOIN users u ON p.user_id = u.user_id
                    WHERE p.is_public = 1
                    ORDER BY p.updated_at DESC
                """)
            
            portfolios = [dict(row) for row in cursor.fetchall()]
            
            # Parse tickers JSON
            for p in portfolios:
                p['tickers'] = json.loads(p['tickers'])
            
            return portfolios


# =========================================================================
# AUTHENTICATION MODULE
# =========================================================================

def get_current_user():
    """
    Get current user from session state or prompt for login
    
    Returns:
        user_id if logged in, None otherwise
    """
    # Check if user is already logged in
    if 'user_id' in st.session_state and 'username' in st.session_state:
        return st.session_state.user_id
    
    return None


def login_widget(db):
    """
    Display login widget in sidebar
    
    Returns:
        user_id if logged in, None otherwise
    """
    if 'user_id' not in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Login")
        
        username = st.sidebar.text_input(
            "Username",
            help="Enter any username to create or login",
            key="login_username"
        )
        
        if st.sidebar.button("Login / Create Account"):
            if username and len(username) >= 3:
                user_id = db.create_user(username)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.sidebar.success(f"✅ Logged in as: {username}")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to login")
            else:
                st.sidebar.error("Username must be at least 3 characters")
        
        return None
    else:
        # User is logged in
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state.username}**")
        
        if st.sidebar.button("Logout"):
            del st.session_state.user_id
            del st.session_state.username
            st.rerun()
        
        return st.session_state.user_id
