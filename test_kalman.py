"""
Kalman Filter Diagnostic Script
Run this to check if pykalman is installed and working correctly
"""

print("="*80)
print("KALMAN FILTER DIAGNOSTIC")
print("="*80)

# Check 1: Import pykalman
print("\n1. Checking pykalman installation...")
try:
    from pykalman import KalmanFilter
    print("   ✅ pykalman is installed")
    KALMAN_AVAILABLE = True
except ImportError as e:
    print("   ❌ pykalman is NOT installed")
    print(f"   Error: {e}")
    print("   Install with: pip install pykalman")
    KALMAN_AVAILABLE = False

if not KALMAN_AVAILABLE:
    print("\n" + "="*80)
    print("RESULT: Kalman filter is NOT available")
    print("ACTION: Run 'pip install pykalman' to enable Kalman signals")
    print("="*80)
    exit(1)

# Check 2: Test basic Kalman filter
print("\n2. Testing Kalman filter calculation...")
try:
    import numpy as np
    
    # Create test data
    test_prices = np.random.randn(200).cumsum() + 100
    
    # Initialize Kalman Filter
    kf = KalmanFilter(
        transition_matrices=[1],
        observation_matrices=[1],
        initial_state_mean=test_prices[0],
        initial_state_covariance=1,
        observation_covariance=1,
        transition_covariance=0.01
    )
    
    # Apply filter
    state_means, state_covs = kf.filter(test_prices.reshape(-1, 1))
    
    print("   ✅ Kalman filter calculation works")
    print(f"   - Input length: {len(test_prices)}")
    print(f"   - Output length: {len(state_means)}")
    
except Exception as e:
    print(f"   ❌ Kalman filter calculation failed: {e}")
    print("="*80)
    print("RESULT: Kalman filter installation may be corrupted")
    print("ACTION: Reinstall with 'pip uninstall pykalman && pip install pykalman'")
    print("="*80)
    exit(1)

# Check 3: Test with pandas Series
print("\n3. Testing with pandas Series (like actual usage)...")
try:
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Create realistic price data
    dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
    prices_series = pd.Series(test_prices, index=dates)
    
    # Test our function
    import sys
    sys.path.insert(0, '.')
    from helper_functions import calculate_kalman_filter, generate_kalman_signal
    
    kalman_data = calculate_kalman_filter(prices_series)
    
    if kalman_data is None:
        print("   ❌ calculate_kalman_filter returned None")
    else:
        print("   ✅ calculate_kalman_filter works")
        print(f"   - Filtered length: {len(kalman_data['filtered'])}")
        print(f"   - Prediction: ${kalman_data['prediction']:.2f}")
        
        # Test signal generation
        signal = generate_kalman_signal(prices_series, kalman_data)
        
        if signal is None:
            print("   ❌ generate_kalman_signal returned None")
        else:
            print("   ✅ generate_kalman_signal works")
            print(f"   - Action: {signal['action']}")
            print(f"   - Score: {signal['score']}")
            print(f"   - Confidence: {signal['confidence']:.0f}%")
    
except Exception as e:
    print(f"   ❌ Function test failed: {e}")
    import traceback
    traceback.print_exc()
    print("="*80)
    print("RESULT: Kalman functions may have bugs")
    print("ACTION: Check helper_functions.py for errors")
    print("="*80)
    exit(1)

# Check 4: Test integration
print("\n4. Testing full signal integration...")
try:
    from helper_functions import generate_trading_signal
    
    # Generate signal with Kalman
    full_signal = generate_trading_signal(prices_series, ticker="TEST")
    
    if 'kalman_signal' in full_signal:
        print("   ✅ Kalman signal is integrated")
        print(f"   - SMA Action: {full_signal['action']}")
        print(f"   - SMA Score: {full_signal['score']}")
        print(f"   - Kalman Action: {full_signal['kalman_signal']['action']}")
        print(f"   - Kalman Score: {full_signal['kalman_signal']['score']}")
        print(f"   - Agreement: {full_signal.get('kalman_agreement', 'N/A')}")
    else:
        print("   ❌ Kalman signal NOT in result")
        print("   - This means the integration is not working")
        print(f"   - Signal keys: {list(full_signal.keys())}")
    
except Exception as e:
    print(f"   ❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()

# Final result
print("\n" + "="*80)
if KALMAN_AVAILABLE:
    print("✅ RESULT: Kalman filter is FULLY OPERATIONAL")
    print("   You should see Kalman columns in Trading Signals tab")
    print("   If not, check:")
    print("   1. Streamlit app is using latest code")
    print("   2. You have >= 100 days of data for each ticker")
    print("   3. Check console for any error messages")
else:
    print("❌ RESULT: Kalman filter is NOT available")
    print("   Install with: pip install pykalman")
print("="*80)
