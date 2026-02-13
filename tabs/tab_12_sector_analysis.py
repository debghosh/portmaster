"""
Tab: Sector Analysis
30-year heat map of S&P sector performance mapped to market regimes
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt

# Import sector definitions
from market_regime_advanced import SECTOR_ETFS, DEFENSIVE_SECTORS, CYCLICAL_SECTORS, GROWTH_SECTORS


def calculate_annual_returns(sector_prices):
    """
    Calculate annual returns for each sector
    
    Returns:
        DataFrame with years as rows, sectors as columns
    """
    # Resample to annual
    annual_returns = {}
    
    for sector in sector_prices.columns:
        yearly = sector_prices[sector].resample('Y').last()
        returns = yearly.pct_change() * 100
        annual_returns[sector] = returns
    
    df = pd.DataFrame(annual_returns)
    df.index = df.index.year
    
    return df


def identify_historical_regimes(spy_prices):
    """
    Identify market regimes for historical periods
    Based on known market history
    
    Returns:
        dict mapping year to regime
    """
    # This is based on well-known market history
    regime_map = {}
    
    # 1990s Bull Market
    for year in range(1995, 2000):
        regime_map[year] = "Bull Market - Low Vol"
    
    # Dot-com crash
    for year in range(2000, 2003):
        regime_map[year] = "Bear Market - High Vol"
    
    # Mid-2000s recovery
    for year in range(2003, 2007):
        regime_map[year] = "Bull Market - Low Vol"
    
    # Financial Crisis
    regime_map[2007] = "Bear Market - Low Vol"
    regime_map[2008] = "Bear Market - High Vol"
    regime_map[2009] = "Bear Market - High Vol"  # Early 2009
    
    # Post-crisis bull market
    for year in range(2010, 2018):
        regime_map[year] = "Bull Market - Low Vol"
    
    # 2018 volatility
    regime_map[2018] = "Bull Market - High Vol"
    
    # Late cycle
    regime_map[2019] = "Bull Market - Low Vol"
    
    # COVID crash and recovery
    regime_map[2020] = "Bear Market - High Vol"  # March crash
    
    # Post-COVID bull
    for year in range(2021, 2022):
        regime_map[year] = "Bull Market - High Vol"
    
    # 2022 bear market
    regime_map[2022] = "Bear Market - Low Vol"
    
    # 2023-2024 recovery
    regime_map[2023] = "Bull Market - High Vol"
    regime_map[2024] = "Bull Market - Low Vol"
    regime_map[2025] = "Bull Market - Low Vol"
    
    return regime_map


def render(tab):
    """Render the Sector Analysis tab"""
    
    with tab:
        st.markdown("# 📊 Sector Analysis")
        st.markdown("**30-Year Sector Performance** mapped to Market Regimes")
        st.markdown("---")
        
        st.info("""
        **What This Shows:**
        - Annual returns for all 11 S&P sectors (1995-2025)
        - Color-coded heat map (green = outperformance, red = underperformance)
        - Market regime labels (Bull/Bear, High/Low Volatility)
        - Sector performance patterns by regime type
        
        **How to Use:**
        - Identify which sectors perform best in current market regime
        - Anticipate regime changes by watching sector rotation
        - Tactical allocation: overweight sectors that perform well in current regime
        """)
        
        # Download sector data
        st.markdown("### 📥 Loading Sector Data...")
        
        with st.spinner("Downloading 30 years of sector data..."):
            try:
                # Download sector ETFs (back to 1998 when most were created)
                start_date = datetime(1995, 1, 1)
                end_date = datetime.now()
                
                sector_tickers = list(SECTOR_ETFS.keys())
                
                sector_data = yf.download(
                    sector_tickers,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True
                )
                
                if 'Close' in sector_data.columns:
                    if isinstance(sector_data.columns, pd.MultiIndex):
                        sector_prices = sector_data['Close']
                    else:
                        sector_prices = sector_data
                else:
                    sector_prices = sector_data
                
                # Calculate annual returns
                annual_returns = calculate_annual_returns(sector_prices)
                
                # Get regime classifications
                spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False, auto_adjust=True)
                regime_map = identify_historical_regimes(spy_data)
                
                st.success(f"✅ Loaded data for {len(sector_prices.columns)} sectors from {annual_returns.index.min()} to {annual_returns.index.max()}")
                
            except Exception as e:
                st.error(f"Error loading sector data: {e}")
                st.stop()
        
        # =============================================================================
        # HEAT MAP VISUALIZATION
        # =============================================================================
        
        st.markdown("---")
        st.markdown("### 🔥 Sector Performance Heat Map (30 Years)")
        
        # Prepare data for heat map
        heatmap_data = annual_returns.copy()
        
        # Add regime column
        heatmap_data['Regime'] = heatmap_data.index.map(lambda x: regime_map.get(x, "Unknown"))
        
        # Create plotly heat map
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.drop('Regime', axis=1).values,
            x=[SECTOR_ETFS.get(col, col) for col in heatmap_data.drop('Regime', axis=1).columns],
            y=heatmap_data.index,
            colorscale='RdYlGn',
            zmid=0,
            text=heatmap_data.drop('Regime', axis=1).round(1).values,
            texttemplate='%{text}%',
            textfont={"size": 10},
            colorbar=dict(title="Annual Return (%)")
        ))
        
        # Add regime labels on the side
        regime_colors = {
            "Bull Market - Low Vol": "lightgreen",
            "Bull Market - High Vol": "yellow",
            "Bear Market - High Vol": "red",
            "Bear Market - Low Vol": "orange",
            "Sideways Market": "gray",
            "Unknown": "white"
        }
        
        fig.update_layout(
            title="Annual Sector Returns (%) with Market Regimes",
            xaxis_title="Sector",
            yaxis_title="Year",
            height=800,
            yaxis=dict(autorange='reversed')  # Most recent at top
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Regime legend
        st.markdown("**Market Regime Legend:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🟢 **Bull Market - Low Vol:** Healthy uptrend, low volatility")
            st.markdown("🟡 **Bull Market - High Vol:** Choppy uptrend, elevated volatility")
            st.markdown("🔴 **Bear Market - High Vol:** Crash/panic selling")
        with col2:
            st.markdown("🟠 **Bear Market - Low Vol:** Grinding bear market")
            st.markdown("⚪ **Sideways Market:** Range-bound, unclear direction")
        
        # =============================================================================
        # REGIME-BASED PERFORMANCE
        # =============================================================================
        
        st.markdown("---")
        st.markdown("### 📈 Average Sector Performance by Market Regime")
        
        # Calculate average performance per regime
        regime_performance = {}
        
        for regime in set(regime_map.values()):
            # Get years in this regime
            regime_years = [year for year, r in regime_map.items() if r == regime and year in heatmap_data.index]
            
            if regime_years:
                # Average returns for those years
                avg_returns = heatmap_data.loc[regime_years].drop('Regime', axis=1).mean()
                regime_performance[regime] = avg_returns.to_dict()
        
        # Create DataFrame
        regime_df = pd.DataFrame(regime_performance).T
        regime_df.columns = [SECTOR_ETFS.get(col, col) for col in regime_df.columns]
        
        # Display as styled table
        st.dataframe(
            regime_df.style.background_gradient(cmap='RdYlGn', axis=1).format("{:.1f}%"),
            use_container_width=True
        )
        
        # Best/Worst sectors per regime
        st.markdown("---")
        st.markdown("### 🎯 Top & Bottom Performers by Regime")
        
        for regime, returns in regime_performance.items():
            with st.expander(f"**{regime}**"):
                sorted_sectors = sorted(returns.items(), key=lambda x: x[1], reverse=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🟢 Top 3 Performers:**")
                    for i, (sector, ret) in enumerate(sorted_sectors[:3], 1):
                        sector_name = SECTOR_ETFS.get(sector, sector)
                        st.markdown(f"{i}. **{sector_name}** ({sector}): {ret:.1f}%")
                
                with col2:
                    st.markdown("**🔴 Bottom 3 Performers:**")
                    for i, (sector, ret) in enumerate(sorted_sectors[-3:], 1):
                        sector_name = SECTOR_ETFS.get(sector, sector)
                        st.markdown(f"{i}. **{sector_name}** ({sector}): {ret:.1f}%")
        
        # =============================================================================
        # CURRENT REGIME RECOMMENDATIONS
        # =============================================================================
        
        st.markdown("---")
        st.markdown("### 💡 Tactical Allocation for Current Regime")
        
        # Determine current regime (from most recent data)
        current_year = datetime.now().year
        current_regime = regime_map.get(current_year, "Unknown")
        
        st.success(f"**Current Market Regime:** {current_regime}")
        
        if current_regime in regime_performance:
            current_returns = regime_performance[current_regime]
            sorted_current = sorted(current_returns.items(), key=lambda x: x[1], reverse=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🟢 Overweight (Top 4):**")
                for sector, ret in sorted_current[:4]:
                    sector_name = SECTOR_ETFS.get(sector, sector)
                    st.markdown(f"- **{sector_name}** ({sector}): Avg {ret:.1f}%")
            
            with col2:
                st.markdown("**🟡 Neutral (Middle 3):**")
                mid_start = len(sorted_current) // 2 - 1
                for sector, ret in sorted_current[mid_start:mid_start+3]:
                    sector_name = SECTOR_ETFS.get(sector, sector)
                    st.markdown(f"- **{sector_name}** ({sector}): Avg {ret:.1f}%")
            
            with col3:
                st.markdown("**🔴 Underweight (Bottom 4):**")
                for sector, ret in sorted_current[-4:]:
                    sector_name = SECTOR_ETFS.get(sector, sector)
                    st.markdown(f"- **{sector_name}** ({sector}): Avg {ret:.1f}%")
        
        # =============================================================================
        # SECTOR ROTATION SIGNALS
        # =============================================================================
        
        st.markdown("---")
        st.markdown("### 🔄 Sector Rotation Analysis")
        
        st.info("""
        **Leading Indicators of Regime Change:**
        - **Defensive Outperformance** (XLP, XLU, XLV) → Often signals late cycle or bear market incoming
        - **Cyclical Outperformance** (XLY, XLI, XLF) → Often signals early cycle or bull market
        - **Tech/Growth Outperformance** (XLK, XLC) → Often signals mid-cycle bull market
        """)
        
        # Calculate recent sector performance (last 3 months)
        recent_prices = sector_prices.tail(60)
        recent_returns = ((recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100).to_dict()
        
        # Classify current rotation
        defensive_recent = np.mean([recent_returns.get(s, 0) for s in DEFENSIVE_SECTORS if s in recent_returns])
        cyclical_recent = np.mean([recent_returns.get(s, 0) for s in CYCLICAL_SECTORS if s in recent_returns])
        growth_recent = np.mean([recent_returns.get(s, 0) for s in GROWTH_SECTORS if s in recent_returns])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Defensive Sectors", f"{defensive_recent:.1f}%", 
                     help="XLP, XLU, XLV - Last 3 months")
        
        with col2:
            st.metric("Cyclical Sectors", f"{cyclical_recent:.1f}%",
                     help="XLY, XLI, XLF, XLE, XLB - Last 3 months")
        
        with col3:
            st.metric("Growth Sectors", f"{growth_recent:.1f}%",
                     help="XLK, XLC, XLY - Last 3 months")
        
        # Rotation signal
        if defensive_recent > cyclical_recent and defensive_recent > growth_recent:
            st.warning("⚠️ **DEFENSIVE ROTATION** - Possible late cycle or bear market warning")
        elif cyclical_recent > defensive_recent and cyclical_recent > growth_recent:
            st.success("✅ **CYCLICAL ROTATION** - Healthy early/mid cycle signal")
        elif growth_recent > defensive_recent:
            st.info("📈 **GROWTH ROTATION** - Mid-cycle bull market signal")
        else:
            st.info("➡️ **MIXED ROTATION** - No clear sector leadership")
