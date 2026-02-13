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
        # SECTOR ROTATION LIKELIHOOD
        # =============================================================================
        
        st.markdown("---")
        st.markdown("### 🔄 Sector Rotation Likelihood Analysis")
        
        st.info("""
        **What is Sector Rotation?**
        
        Sector rotation is the movement of investment capital from one market sector to another as investors 
        anticipate different phases of the economic cycle. Understanding rotation patterns helps predict 
        regime changes 3-6 months in advance.
        """)
        
        # Get recent prices for rotation analysis (needed here and later)
        recent_prices = sector_prices.tail(60) if len(sector_prices) >= 60 else sector_prices
        
        # Calculate recent returns (last 60 days) - needed for rotation analysis
        recent_returns = {}
        for sector in recent_prices.columns:
            if len(recent_prices[sector].dropna()) >= 2:
                start_val = recent_prices[sector].dropna().iloc[0]
                end_val = recent_prices[sector].dropna().iloc[-1]
                if start_val > 0:
                    recent_returns[sector] = ((end_val - start_val) / start_val * 100)
                else:
                    recent_returns[sector] = 0
            else:
                recent_returns[sector] = 0
        
        # Calculate sector group averages (needed throughout)
        defensive_recent = np.mean([recent_returns.get(s, 0) for s in DEFENSIVE_SECTORS if s in recent_returns])
        cyclical_recent = np.mean([recent_returns.get(s, 0) for s in CYCLICAL_SECTORS if s in recent_returns])
        growth_recent = np.mean([recent_returns.get(s, 0) for s in GROWTH_SECTORS if s in recent_returns])
        
        # Calculate rotation metrics from recent data
        if len(recent_prices) >= 60:
            # Compare last 30 days vs previous 30 days
            period1_start = -60
            period1_end = -30
            period2_start = -30
            
            period1_returns = {}
            period2_returns = {}
            acceleration = {}
            
            for sector in sector_prices.columns:
                if sector in recent_prices.columns:
                    # Period 1 (60-30 days ago)
                    p1_start_price = recent_prices[sector].iloc[period1_start]
                    p1_end_price = recent_prices[sector].iloc[period1_end]
                    period1_returns[sector] = ((p1_end_price - p1_start_price) / p1_start_price * 100) if p1_start_price > 0 else 0
                    
                    # Period 2 (last 30 days)
                    p2_start_price = recent_prices[sector].iloc[period2_start]
                    p2_end_price = recent_prices[sector].iloc[-1]
                    period2_returns[sector] = ((p2_end_price - p2_start_price) / p2_start_price * 100) if p2_start_price > 0 else 0
                    
                    # Acceleration (change in momentum)
                    acceleration[sector] = period2_returns[sector] - period1_returns[sector]
            
            # Analyze rotation patterns
            defensive_accel = np.mean([acceleration.get(s, 0) for s in DEFENSIVE_SECTORS if s in acceleration])
            cyclical_accel = np.mean([acceleration.get(s, 0) for s in CYCLICAL_SECTORS if s in acceleration])
            growth_accel = np.mean([acceleration.get(s, 0) for s in GROWTH_SECTORS if s in acceleration])
            
            # Calculate velocity (rate of change)
            defensive_velocity = defensive_recent - defensive_accel
            cyclical_velocity = cyclical_recent - cyclical_accel  
            growth_velocity = growth_recent - growth_accel
            
            # Determine rotation likelihood
            st.markdown("#### 📊 Rotation Momentum Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Defensive Acceleration", 
                         f"{defensive_accel:+.1f}%",
                         help="Change in defensive sector momentum (30-day vs prior 30-day)")
                st.caption("Recent: {:.1f}%".format(defensive_recent))
            
            with col2:
                st.metric("Cyclical Acceleration",
                         f"{cyclical_accel:+.1f}%",
                         help="Change in cyclical sector momentum")
                st.caption("Recent: {:.1f}%".format(cyclical_recent))
            
            with col3:
                st.metric("Growth Acceleration",
                         f"{growth_accel:+.1f}%",
                         help="Change in growth sector momentum")
                st.caption("Recent: {:.1f}%".format(growth_recent))
            
            # Rotation likelihood assessment
            st.markdown("---")
            st.markdown("#### 🎯 Rotation Likelihood Assessment")
            
            # Calculate rotation probability
            rotation_signals = []
            rotation_score = 0
            
            # Signal 1: Defensive outperforming AND accelerating
            if defensive_recent > cyclical_recent and defensive_accel > 2:
                rotation_signals.append("✅ Defensive sectors gaining momentum → Late cycle warning")
                rotation_score += 3
            
            # Signal 2: Cyclical weakening
            if cyclical_accel < -2:
                rotation_signals.append("⚠️ Cyclical sectors decelerating → Economic slowdown signal")
                rotation_score += 2
            
            # Signal 3: Growth underperforming defensives
            if defensive_recent > growth_recent and growth_accel < 0:
                rotation_signals.append("⚠️ Growth lagging defensives → Risk-off rotation starting")
                rotation_score += 2
            
            # Signal 4: Defensive AND cyclical both weak (bear signal)
            if defensive_accel < -2 and cyclical_accel < -2:
                rotation_signals.append("🔴 Both defensive and cyclical weak → Deep bear market")
                rotation_score += 4
            
            # Signal 5: Cyclical accelerating strongly
            if cyclical_accel > 3:
                rotation_signals.append("✅ Cyclical acceleration → Early cycle recovery signal")
                rotation_score -= 2  # Positive signal (reduces rotation risk)
            
            # Signal 6: Growth strongly outperforming
            if growth_recent > defensive_recent + 5 and growth_accel > 0:
                rotation_signals.append("✅ Growth momentum strong → Mid-cycle bull market")
                rotation_score -= 2
            
            # Determine likelihood
            if rotation_score >= 6:
                likelihood = "VERY HIGH"
                likelihood_color = "red"
                likelihood_pct = 80
                recommendation = "🚨 HIGH PROBABILITY of defensive rotation. Consider reducing cyclical exposure NOW."
            elif rotation_score >= 4:
                likelihood = "HIGH"
                likelihood_color = "orange"
                likelihood_pct = 60
                recommendation = "⚠️ Elevated rotation risk. Monitor closely, prepare defensive positions."
            elif rotation_score >= 2:
                likelihood = "MODERATE"
                likelihood_color = "yellow"
                likelihood_pct = 40
                recommendation = "📊 Some rotation signals present. Stay alert but no immediate action needed."
            elif rotation_score <= -3:
                likelihood = "LOW (Bullish)"
                likelihood_color = "green"
                likelihood_pct = 20
                recommendation = "✅ Low rotation risk. Growth/cyclical momentum strong. Stay aggressive."
            else:
                likelihood = "LOW"
                likelihood_color = "blue"
                likelihood_pct = 25
                recommendation = "➡️ Rotation unlikely. Current trends stable."
            
            # Display likelihood
            st.markdown(f"""
            <div style="background: {likelihood_color}; color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                <h2 style="margin: 0;">Sector Rotation Likelihood: {likelihood}</h2>
                <h3 style="margin: 0.5rem 0; opacity: 0.9;">Probability: ~{likelihood_pct}%</h3>
                <p style="margin: 0.5rem 0; font-size: 1rem;">{recommendation}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show signals
            if rotation_signals:
                st.markdown("**🔍 Detected Rotation Signals:**")
                for signal in rotation_signals:
                    st.markdown(f"- {signal}")
            else:
                st.markdown("**✅ No significant rotation signals detected**")
            
            # Historical context
            st.markdown("---")
            st.markdown("#### 📚 Historical Rotation Patterns")
            
            st.markdown("""
            **Typical Rotation Sequence:**
            
            1. **Early Bull Market (Recovery):**
               - Cyclicals (XLI, XLY, XLF) lead
               - Financials especially strong
               - Energy often rebounds
               - Duration: 3-12 months
            
            2. **Mid Bull Market (Expansion):**
               - Growth/Tech (XLK, XLC) lead
               - Consumer Discretionary strong
               - Broad participation
               - Duration: 12-36 months
            
            3. **Late Bull Market (Pre-Top):**
               - Defensives (XLP, XLU, XLV) start outperforming
               - Cyclicals weaken
               - Narrowing leadership
               - Duration: 3-9 months (WARNING PERIOD)
            
            4. **Bear Market (Decline):**
               - Defensives outperform (but may still decline)
               - Cyclicals underperform severely
               - Flight to quality
               - Duration: 6-18 months
            
            **⏰ Time Lag:**
            Sector rotation typically LEADS regime changes by 3-6 months. When you see 
            defensive rotation starting, you have a window to adjust before the bear market arrives.
            """)
            
            # Actionable guidance
            st.markdown("---")
            st.markdown("#### 💡 What To Do Now")
            
            if likelihood_pct >= 60:
                st.error("""
                **HIGH ROTATION RISK - ACTION REQUIRED:**
                
                1. **Reduce Cyclical Exposure:**
                   - Trim XLI, XLY, XLF, XLE by 25-50%
                   - Take profits in momentum names
                
                2. **Increase Defensive Allocation:**
                   - Add XLP (Consumer Staples)
                   - Add XLU (Utilities)
                   - Add XLV (Healthcare)
                   - Target: 30-40% defensive
                
                3. **Raise Cash:**
                   - Move to 15-20% cash position
                   - Prepare for opportunities
                
                4. **Set Alerts:**
                   - Monitor rotation weekly
                   - Exit if rotation accelerates
                """)
            elif likelihood_pct >= 40:
                st.warning("""
                **MODERATE ROTATION RISK - PREPARE:**
                
                1. **Monitor Weekly:** Track defensive vs cyclical performance
                2. **Reduce New Buys:** Don't add aggressively to cyclicals
                3. **Review Stops:** Ensure stop losses in place
                4. **Build Watch List:** Identify defensive names to rotate into
                """)
            else:
                st.success("""
                **LOW ROTATION RISK - STAY COURSE:**
                
                1. **Maintain Current Allocation:** No changes needed
                2. **Monitor Monthly:** Check for changes in trends
                3. **Stay Invested:** Rotation unlikely in near term
                4. **Add on Dips:** Good environment for accumulation
                """)
        
        else:
            st.warning("Insufficient data for rotation likelihood analysis. Need 60+ days of sector data.")
        
        # =============================================================================
        # CURRENT REGIME RECOMMENDATIONS (Original section)
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
        
        # Note: recent_returns, defensive_recent, cyclical_recent, growth_recent 
        # already calculated above in rotation likelihood section
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Defensive Sectors", f"{defensive_recent:.1f}%" if not pd.isna(defensive_recent) else "N/A", 
                     help="XLP, XLU, XLV - Last 3 months")
        
        with col2:
            st.metric("Cyclical Sectors", f"{cyclical_recent:.1f}%" if not pd.isna(cyclical_recent) else "N/A",
                     help="XLY, XLI, XLF, XLE, XLB - Last 3 months")
        
        with col3:
            st.metric("Growth Sectors", f"{growth_recent:.1f}%" if not pd.isna(growth_recent) else "N/A",
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
