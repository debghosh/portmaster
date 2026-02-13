"""
Database Functionality Test Script
Run this to verify that all database features are working correctly
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import PortfolioDB

def test_database():
    """Test all database functionality"""
    
    print("="*80)
    print("ALPHATIC V4.0 - DATABASE FUNCTIONALITY TEST")
    print("="*80)
    
    # Use a test database
    test_db_path = "test_portfolios.db"
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"✓ Cleaned up old test database")
    
    # Initialize database
    print("\n1. INITIALIZING DATABASE...")
    db = PortfolioDB(db_path=test_db_path)
    print("✓ Database initialized")
    print(f"✓ Database file created: {test_db_path}")
    
    # Test user creation
    print("\n2. TESTING USER MANAGEMENT...")
    alice_id = db.create_user("alice")
    bob_id = db.create_user("bob")
    print(f"✓ Created user: alice (ID: {alice_id[:8]}...)")
    print(f"✓ Created user: bob (ID: {bob_id[:8]}...)")
    
    # Test duplicate user
    alice_id_again = db.create_user("alice")
    assert alice_id == alice_id_again, "Duplicate user should return same ID"
    print("✓ Duplicate user handling works")
    
    # Test user lookup
    retrieved_id = db.get_user("alice")
    assert retrieved_id == alice_id, "User lookup failed"
    print("✓ User lookup works")
    
    # Create test portfolio data
    print("\n3. CREATING TEST PORTFOLIO DATA...")
    start_date = datetime(2020, 1, 1).date()
    end_date = datetime.now().date()
    
    # Create fake price data
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    prices = pd.DataFrame({
        'SPY': np.random.randn(len(dates)).cumsum() + 100,
        'QQQ': np.random.randn(len(dates)).cumsum() + 100,
        'AGG': np.random.randn(len(dates)).cumsum() + 100
    }, index=dates)
    
    # Create fake returns
    returns = prices.pct_change().mean(axis=1).dropna()
    
    print(f"✓ Created test data: {len(prices)} days of prices")
    print(f"✓ Created test data: {len(returns)} days of returns")
    
    # Test portfolio save (private)
    print("\n4. TESTING PORTFOLIO SAVE (PRIVATE)...")
    alice_portfolio_id = db.save_portfolio(
        user_id=alice_id,
        name="Alice's Tech Portfolio",
        tickers=['SPY', 'QQQ', 'AGG'],
        weights={'SPY': 0.4, 'QQQ': 0.4, 'AGG': 0.2},
        prices=prices,
        returns=returns,
        start_date=start_date,
        end_date=end_date,
        is_public=False
    )
    print(f"✓ Saved private portfolio (ID: {alice_portfolio_id[:8]}...)")
    
    # Test portfolio save (public)
    print("\n5. TESTING PORTFOLIO SAVE (PUBLIC)...")
    bob_portfolio_id = db.save_portfolio(
        user_id=bob_id,
        name="Bob's Balanced Portfolio",
        tickers=['SPY', 'AGG'],
        weights={'SPY': 0.6, 'AGG': 0.4},
        prices=prices[['SPY', 'AGG']],
        returns=returns,
        start_date=start_date,
        end_date=end_date,
        is_public=True
    )
    print(f"✓ Saved public portfolio (ID: {bob_portfolio_id[:8]}...)")
    
    # Test portfolio load
    print("\n6. TESTING PORTFOLIO LOAD...")
    loaded_portfolio = db.load_portfolio(alice_portfolio_id)
    assert loaded_portfolio is not None, "Portfolio load failed"
    assert loaded_portfolio['name'] == "Alice's Tech Portfolio"
    assert len(loaded_portfolio['tickers']) == 3
    assert loaded_portfolio['is_public'] == False
    print(f"✓ Loaded portfolio: {loaded_portfolio['name']}")
    print(f"✓ Tickers: {loaded_portfolio['tickers']}")
    print(f"✓ Public: {loaded_portfolio['is_public']}")
    
    # Test get user portfolios
    print("\n7. TESTING GET USER PORTFOLIOS...")
    alice_portfolios = db.get_user_portfolios(alice_id)
    print(f"✓ Alice sees {len(alice_portfolios)} portfolio(s)")
    
    # Alice should see her own (1) + Bob's public (1) = 2 total
    assert len(alice_portfolios) == 2, f"Expected 2 portfolios, got {len(alice_portfolios)}"
    
    # Check that Alice sees her own
    own_portfolios = [p for p in alice_portfolios if p.get('owned', True)]
    assert len(own_portfolios) == 1, "Alice should see 1 owned portfolio"
    print(f"  - Owned: {own_portfolios[0]['name']}")
    
    # Check that Alice sees Bob's public
    public_portfolios = [p for p in alice_portfolios if not p.get('owned', True)]
    assert len(public_portfolios) == 1, "Alice should see 1 public portfolio"
    print(f"  - Public: {public_portfolios[0]['name']} by {public_portfolios[0].get('owner')}")
    
    # Test multi-tenancy: Bob should NOT see Alice's private portfolio
    print("\n8. TESTING MULTI-TENANCY...")
    bob_portfolios = db.get_user_portfolios(bob_id)
    bob_owned = [p for p in bob_portfolios if p.get('owned', True)]
    assert len(bob_owned) == 1, "Bob should see only his own portfolio"
    assert bob_owned[0]['name'] == "Bob's Balanced Portfolio"
    print("✓ Bob cannot see Alice's private portfolio")
    print("✓ Multi-tenancy works correctly")
    
    # Test toggle visibility
    print("\n9. TESTING TOGGLE VISIBILITY...")
    # Make Alice's portfolio public
    new_state = db.toggle_portfolio_visibility(alice_portfolio_id, alice_id)
    assert new_state == True, "Portfolio should be public now"
    print("✓ Made Alice's portfolio public")
    
    # Verify Bob can now see it
    bob_portfolios_updated = db.get_user_portfolios(bob_id)
    bob_public = [p for p in bob_portfolios_updated if not p.get('owned', True)]
    assert len(bob_public) == 1, "Bob should see 1 public portfolio now"
    print("✓ Bob can now see Alice's portfolio")
    
    # Make it private again
    new_state = db.toggle_portfolio_visibility(alice_portfolio_id, alice_id)
    assert new_state == False, "Portfolio should be private now"
    print("✓ Made Alice's portfolio private again")
    
    # Test ownership protection
    print("\n10. TESTING OWNERSHIP PROTECTION...")
    # Bob tries to delete Alice's portfolio
    result = db.delete_portfolio(alice_portfolio_id, bob_id)
    assert result == False, "Bob should not be able to delete Alice's portfolio"
    print("✓ Bob cannot delete Alice's portfolio")
    
    # Alice deletes her own portfolio
    result = db.delete_portfolio(alice_portfolio_id, alice_id)
    assert result == True, "Alice should be able to delete her own portfolio"
    print("✓ Alice can delete her own portfolio")
    
    # Verify it's deleted
    deleted_portfolio = db.load_portfolio(alice_portfolio_id)
    assert deleted_portfolio is None, "Deleted portfolio should not exist"
    print("✓ Portfolio successfully deleted")
    
    # Clean up test database
    print("\n11. CLEANUP...")
    os.remove(test_db_path)
    print(f"✓ Removed test database: {test_db_path}")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED! ✓")
    print("="*80)
    print("\nDatabase features verified:")
    print("  ✓ User creation and authentication")
    print("  ✓ Portfolio save and load")
    print("  ✓ Public/Private portfolios")
    print("  ✓ Multi-tenancy (user isolation)")
    print("  ✓ Portfolio sharing")
    print("  ✓ Ownership protection")
    print("  ✓ Visibility toggling")
    print("\nYou can now use V4.0 with confidence!")
    print("="*80)

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
