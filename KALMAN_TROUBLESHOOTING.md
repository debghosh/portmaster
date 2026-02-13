# Kalman Filter Troubleshooting Guide

## Issue: Not Seeing Kalman Column in Trading Signals

### Quick Diagnosis

**Run the diagnostic script:**
```bash
cd portinthestorm
python test_kalman.py
```

This will tell you exactly what's wrong.

---

## Common Issues & Solutions

### Issue #1: pykalman Not Installed

**Symptoms:**
- Top of Trading Signals tab shows: "⚠️ Kalman Filter Unavailable"
- Kalman column shows "N/A" for all tickers

**Solution:**
```bash
pip install pykalman
```

**If that fails:**
```bash
# Install dependencies first
pip install numpy scipy
pip install pykalman
```

**For conda users:**
```bash
conda install -c conda-forge pykalman
```

---

### Issue #2: Not Enough Data

**Symptoms:**
- pykalman is installed
- Kalman column exists but shows "N/A"
- Top of tab shows "Kalman Filter Active"

**Cause:**
- Kalman filter requires >= 100 data points
- If you're using a short date range, there's not enough data

**Solution:**
- Use longer date range (at least 6 months)
- Or use "Auto (Earliest Available)" when building portfolio

---

### Issue #3: Column Not Showing At All

**Symptoms:**
- No Kalman column in the table
- No "Agree" column in the table

**Causes:**
1. Using old version of code
2. Browser cache showing old version

**Solutions:**

**A) Clear Browser Cache:**
```
1. Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. Or clear browser cache manually
3. Restart Streamlit app
```

**B) Verify Code Version:**
```bash
# Check if file has Kalman code
grep -n "Kalman" tabs/tab_10_trading_signals.py

# Should show multiple matches
# If not, re-extract V4.1 package
```

**C) Force Streamlit Reload:**
```bash
# Stop app (Ctrl+C)
# Clear Streamlit cache
rm -rf ~/.streamlit/cache

# Restart
streamlit run alphatic_portfolio_app.py
```

---

### Issue #4: Kalman Shows But No Values

**Symptoms:**
- Kalman column exists
- Shows "N/A" for all tickers
- pykalman is installed
- Enough data (>100 days)

**Cause:**
- Calculation failing silently

**Solution:**
```bash
# Run app from terminal to see errors
streamlit run alphatic_portfolio_app.py

# Watch console for error messages like:
# "Kalman filter error for SPY: ..."
```

**Common calculation errors:**
1. Data has NaN values → Clean data
2. Data is not numeric → Check data types
3. Memory error → Reduce number of ETFs processed at once

---

### Issue #5: Columns in Wrong Order

**Symptoms:**
- Kalman column appears but in unexpected location
- Hard to read

**This is normal** - column order is:
```
Category | Ticker | SMA Signal | Score | Conf% | Kalman | Agree | Price
```

If you want different order, you can modify line 575 in `tabs/tab_10_trading_signals.py`:
```python
display_df = filtered_df[['Category', 'Ticker', 'Action_Display', 
                          'Kalman', 'Agreement',  # Move these before Score
                          'Score', 'Confidence', 'Price']].copy()
```

---

## Verification Steps

### Step 1: Check Installation
```bash
python -c "from pykalman import KalmanFilter; print('✅ pykalman installed')"
```

Expected output: `✅ pykalman installed`

If error: `ModuleNotFoundError: No module named 'pykalman'` → Install it

---

### Step 2: Check Helper Functions
```bash
python -c "from helper_functions import KALMAN_AVAILABLE; print(f'Kalman available: {KALMAN_AVAILABLE}')"
```

Expected output: `Kalman available: True`

If False → pykalman not installed or import failed

---

### Step 3: Test Kalman Calculation
```bash
python test_kalman.py
```

Expected output:
```
====================...
KALMAN FILTER DIAGNOSTIC
====================...
1. Checking pykalman installation...
   ✅ pykalman is installed
2. Testing Kalman filter calculation...
   ✅ Kalman filter calculation works
3. Testing with pandas Series...
   ✅ calculate_kalman_filter works
4. Testing full signal integration...
   ✅ Kalman signal is integrated
====================...
✅ RESULT: Kalman filter is FULLY OPERATIONAL
```

---

### Step 4: Check in UI
```
1. Run: streamlit run alphatic_portfolio_app.py
2. Go to Trading Signals tab
3. Top of page should show:
   🔬 Kalman Filter Active: Advanced noise filtering enabled...
4. Table should have columns:
   ... | Kalman | Agree | ...
5. Kalman column should show values like:
   B+3, S-2, H+0, etc.
6. Agree column should show:
   ✅ ALIGNED, ⚠️ CONFLICT, ⚪ MIXED
```

---

## Understanding the Display

### Kalman Column Format:

**Format:** `[Action][Score]`

Examples:
- `B+4` = Buy with score +4 (strong bullish)
- `S-3` = Sell with score -3 (strong bearish)
- `H+0` = Hold with score 0 (neutral)
- `N/A` = Not available (not enough data or pykalman not installed)

### Agreement Column:

- `✅ ALIGNED` = Both SMA and Kalman agree (high confidence)
- `⚠️ CONFLICT` = SMA and Kalman disagree (caution)
- `⚪ MIXED` = Neutral or partial agreement (lower conviction)
- `(empty)` = Kalman not available

---

## Still Not Working?

### Debug Checklist:

- [ ] pykalman installed (`pip install pykalman`)
- [ ] Using V4.1 code (check file dates)
- [ ] Streamlit restarted after installing pykalman
- [ ] Browser cache cleared (Ctrl+Shift+R)
- [ ] At least 100 days of data per ticker
- [ ] No errors in console when app runs
- [ ] test_kalman.py passes all checks

### Get More Help:

1. **Run full diagnostic:**
   ```bash
   python test_kalman.py > kalman_diagnostic.txt 2>&1
   ```

2. **Check console output:**
   - Look for errors starting with "Kalman filter error for..."
   - These show which ticker failed and why

3. **Create minimal test:**
   ```python
   # test_minimal.py
   import pandas as pd
   import numpy as np
   from helper_functions import generate_trading_signal, KALMAN_AVAILABLE
   
   print(f"Kalman available: {KALMAN_AVAILABLE}")
   
   # Create test data
   dates = pd.date_range(end='2025-02-13', periods=200, freq='D')
   prices = pd.Series(np.random.randn(200).cumsum() + 100, index=dates)
   
   # Generate signal
   signal = generate_trading_signal(prices, ticker="TEST")
   
   print(f"Has Kalman: {'kalman_signal' in signal}")
   if 'kalman_signal' in signal:
       print(f"Kalman action: {signal['kalman_signal']['action']}")
       print(f"Kalman score: {signal['kalman_signal']['score']}")
       print(f"Agreement: {signal.get('kalman_agreement', 'N/A')}")
   ```

---

## Expected Behavior

### When Working Correctly:

**Trading Signals Tab:**
```
🔬 Kalman Filter Active: Advanced noise filtering enabled...

Table showing:
Ticker | SMA Signal | Score | Conf% | Kalman | Agree | Price
SPY    | 🟢 Buy     | +4    | 75%   | B+3    | ✅ ALIGNED | $450
QQQ    | 🔴 Sell    | -2    | 60%   | S-1    | ✅ ALIGNED | $375
AGG    | 🟡 Hold    | +1    | 50%   | B+2    | ⚪ MIXED    | $105
```

### When pykalman Not Installed:

**Trading Signals Tab:**
```
⚠️ Kalman Filter Unavailable: Install with pip install pykalman...

Table showing:
Ticker | SMA Signal | Score | Conf% | Kalman | Agree | Price
SPY    | 🟢 Buy     | +4    | 75%   | N/A    |       | $450
QQQ    | 🔴 Sell    | -2    | 60%   | N/A    |       | $375
```

---

## Performance Notes

**Kalman Filter Speed:**
- First calculation: ~100-200ms per ticker
- Cached results: Instant
- 62 ETFs: ~10-15 seconds total first time
- Subsequent views: <1 second (cached)

**Memory Usage:**
- Adds ~5MB RAM per 62 ETFs
- Not significant for modern systems

---

**Last Updated:** 2026-02-13  
**Version:** 4.1  
**Status:** Kalman fully implemented, debugging guide complete
