"""
Advanced Market Regime Detection Module
Uses sector rotation, volatility, and statistical models for robust regime identification
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# S&P 500 Sector ETFs (SPDR Select Sector)
SECTOR_ETFS = {
    'XLK': 'Technology',
    'XLV': 'Healthcare',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLI': 'Industrials',
    'XLP': 'Consumer Staples',
    'XLY': 'Consumer Discretionary',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLC': 'Communication Services',
    'XLB': 'Materials'
}

# Defensive vs Cyclical classification
DEFENSIVE_SECTORS = ['XLP', 'XLU', 'XLV']  # Staples, Utilities, Healthcare
CYCLICAL_SECTORS = ['XLY', 'XLI', 'XLF', 'XLE', 'XLB']  # Discretionary, Industrial, Financial, Energy, Materials
GROWTH_SECTORS = ['XLK', 'XLC', 'XLY']  # Tech, Communication, Discretionary


def download_sector_data(start_date, end_date=None):
    """
    Download sector ETF data
    
    Returns:
        DataFrame with sector prices
    """
    if end_date is None:
        end_date = datetime.now()
    
    sector_tickers = list(SECTOR_ETFS.keys())
    
    try:
        # Download all sectors at once
        data = yf.download(
            sector_tickers,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=True
        )
        
        if data is None or data.empty:
            return None
        
        # Extract Close prices
        if 'Close' in data.columns:
            if isinstance(data.columns, pd.MultiIndex):
                prices = data['Close']
            else:
                prices = data
        else:
            prices = data
        
        return prices
        
    except Exception as e:
        print(f"Error downloading sector data: {e}")
        return None


def calculate_sector_rotation(sector_prices, spy_prices, lookback_days=60):
    """
    Calculate sector rotation metrics
    
    Args:
        sector_prices: DataFrame with sector ETF prices
        spy_prices: Series with SPY prices
        lookback_days: Period for rotation analysis
        
    Returns:
        dict with rotation metrics
    """
    if sector_prices is None or sector_prices.empty:
        return None
    
    # Calculate returns
    sector_returns = sector_prices.pct_change(lookback_days).iloc[-1]
    spy_return = spy_prices.pct_change(lookback_days).iloc[-1]
    
    # Relative strength vs SPY
    relative_strength = sector_returns - spy_return
    
    # Classify sectors
    defensive_perf = relative_strength[DEFENSIVE_SECTORS].mean()
    cyclical_perf = relative_strength[CYCLICAL_SECTORS].mean()
    growth_perf = relative_strength[GROWTH_SECTORS].mean()
    
    # Determine rotation signal
    if defensive_perf > cyclical_perf and defensive_perf > growth_perf:
        rotation_signal = "DEFENSIVE"
        rotation_strength = defensive_perf
    elif cyclical_perf > defensive_perf and cyclical_perf > growth_perf:
        rotation_signal = "CYCLICAL"
        rotation_strength = cyclical_perf
    elif growth_perf > 0:
        rotation_signal = "GROWTH"
        rotation_strength = growth_perf
    else:
        rotation_signal = "MIXED"
        rotation_strength = 0
    
    return {
        'signal': rotation_signal,
        'strength': rotation_strength,
        'defensive_perf': defensive_perf,
        'cyclical_perf': cyclical_perf,
        'growth_perf': growth_perf,
        'sector_returns': relative_strength.to_dict(),
        'top_sector': relative_strength.idxmax(),
        'bottom_sector': relative_strength.idxmin()
    }


def detect_market_regime_advanced(prices, returns, vix_level=None, sector_rotation=None):
    """
    Advanced regime detection using multiple factors
    
    Regimes:
    1. Bull Market - Low Vol: Rising prices, low volatility, growth sectors leading
    2. Bull Market - High Vol: Rising prices, high volatility, mixed sectors
    3. Bear Market - Low Vol: Falling prices, low volatility (grind down)
    4. Bear Market - High Vol: Falling prices, high volatility (crash)
    5. Sideways Market: Range-bound, unclear direction
    
    Args:
        prices: Series of prices
        returns: Series of returns
        vix_level: Current VIX level (optional)
        sector_rotation: Sector rotation dict (optional)
        
    Returns:
        dict with regime classification and confidence
    """
    # Calculate metrics
    recent_return = returns.rolling(60).mean().iloc[-1]
    volatility = returns.rolling(60).std().iloc[-1] * np.sqrt(252)
    
    # Price trend (SMA comparison)
    sma_50 = prices.rolling(50).mean().iloc[-1]
    sma_200 = prices.rolling(200).mean().iloc[-1]
    current_price = prices.iloc[-1]
    
    # Trend signals
    short_term_trend = "UP" if current_price > sma_50 else "DOWN"
    long_term_trend = "UP" if current_price > sma_200 else "DOWN"
    sma_cross = "BULLISH" if sma_50 > sma_200 else "BEARISH"
    
    # Volatility classification
    vol_high = volatility > 0.25  # >25% annualized = high vol
    
    # Base regime determination
    if recent_return > 0.0005:  # Positive trend
        if vol_high:
            base_regime = "Bull Market - High Vol"
        else:
            base_regime = "Bull Market - Low Vol"
    elif recent_return < -0.0005:  # Negative trend
        if vol_high:
            base_regime = "Bear Market - High Vol"
        else:
            base_regime = "Bear Market - Low Vol"
    else:
        base_regime = "Sideways Market"
    
    # Adjust based on sector rotation
    regime_confidence = 0.7  # Base confidence
    
    if sector_rotation:
        rotation_signal = sector_rotation['signal']
        
        # Confirm or contradict base regime
        if base_regime.startswith("Bull"):
            if rotation_signal in ["GROWTH", "CYCLICAL"]:
                regime_confidence = 0.9  # Strong confirmation
            elif rotation_signal == "DEFENSIVE":
                regime_confidence = 0.5  # Weak, possible reversal coming
                base_regime += " (Weakening)"
        
        elif base_regime.startswith("Bear"):
            if rotation_signal == "DEFENSIVE":
                regime_confidence = 0.9  # Strong confirmation
            elif rotation_signal in ["GROWTH", "CYCLICAL"]:
                regime_confidence = 0.5  # Possible bottom forming
                base_regime += " (Bottoming?)"
    
    # VIX adjustment
    if vix_level:
        if vix_level > 30 and not vol_high:
            vol_high = True
            if "High Vol" not in base_regime:
                base_regime = base_regime.replace("Low Vol", "High Vol")
    
    # Calculate regime transition probability
    transition_prob = 0.0
    
    if regime_confidence < 0.6:
        transition_prob = 0.4  # High chance of transition
    elif "Weakening" in base_regime or "Bottoming" in base_regime:
        transition_prob = 0.3
    
    return {
        'regime': base_regime,
        'confidence': regime_confidence,
        'transition_probability': transition_prob,
        'metrics': {
            'recent_return': recent_return,
            'volatility': volatility,
            'short_term_trend': short_term_trend,
            'long_term_trend': long_term_trend,
            'sma_cross': sma_cross
        },
        'sector_signal': sector_rotation['signal'] if sector_rotation else None,
        'leading_sector': sector_rotation['top_sector'] if sector_rotation else None
    }


def get_regime_characteristics(regime_name):
    """
    Get typical characteristics and investment implications for each regime
    
    Returns:
        dict with characteristics and recommendations
    """
    characteristics = {
        "Bull Market - Low Vol": {
            "description": "Healthy bull market with steady gains",
            "typical_duration": "12-36 months",
            "best_sectors": ["Technology (XLK)", "Consumer Discretionary (XLY)", "Industrials (XLI)"],
            "worst_sectors": ["Utilities (XLU)", "Consumer Staples (XLP)"],
            "allocation": "Aggressive: 80-90% stocks, 10-20% bonds",
            "risk": "Low to Moderate",
            "warning_signs": ["Defensive sector outperformance", "Rising VIX", "Yield curve inversion"]
        },
        
        "Bull Market - High Vol": {
            "description": "Choppy bull market with increased uncertainty",
            "typical_duration": "6-18 months",
            "best_sectors": ["Technology (XLK)", "Healthcare (XLV)", "Quality stocks"],
            "worst_sectors": ["Highly leveraged sectors", "Speculative growth"],
            "allocation": "Moderate: 60-70% stocks, 30-40% bonds",
            "risk": "Moderate to High",
            "warning_signs": ["Continued volatility increase", "Sector rotation to defensives", "Credit spread widening"]
        },
        
        "Bear Market - High Vol": {
            "description": "Crash or panic selling environment",
            "typical_duration": "3-12 months",
            "best_sectors": ["Consumer Staples (XLP)", "Utilities (XLU)", "Cash"],
            "worst_sectors": ["All cyclicals", "High beta stocks"],
            "allocation": "Defensive: 30-40% stocks, 60-70% bonds/cash",
            "risk": "Very High",
            "warning_signs": ["Capitulation volume", "Extreme oversold readings", "Policy response"]
        },
        
        "Bear Market - Low Vol": {
            "description": "Grinding bear market, slow decline",
            "typical_duration": "12-24 months",
            "best_sectors": ["Healthcare (XLV)", "Consumer Staples (XLP)", "Dividend stocks"],
            "worst_sectors": ["Cyclicals", "Growth stocks"],
            "allocation": "Defensive: 40-50% stocks, 50-60% bonds",
            "risk": "Moderate to High",
            "warning_signs": ["Sector rotation to growth", "Volatility spike", "Bullish SMA cross"]
        },
        
        "Sideways Market": {
            "description": "Range-bound market, unclear direction",
            "typical_duration": "6-18 months",
            "best_sectors": ["Mixed", "Tactical rotation"],
            "worst_sectors": ["None specific"],
            "allocation": "Balanced: 50-60% stocks, 40-50% bonds",
            "risk": "Moderate",
            "warning_signs": ["Breakout above/below range", "Clear sector rotation", "Volatility change"]
        }
    }
    
    # Handle modified regimes (e.g., "Bull Market - Low Vol (Weakening)")
    base_regime = regime_name.split(" (")[0]
    
    return characteristics.get(base_regime, {
        "description": "Unknown regime",
        "typical_duration": "Unknown",
        "best_sectors": [],
        "worst_sectors": [],
        "allocation": "Balanced",
        "risk": "Unknown",
        "warning_signs": []
    })
