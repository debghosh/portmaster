"""
Sidebar Panel Module
Handles the left sidebar with portfolio builder and management
"""

import streamlit as st
import json
from datetime import datetime
from helper_functions import (
    get_earliest_start_date, 
    download_ticker_data, 
    calculate_portfolio_returns,
    optimize_portfolio
)
import numpy as np


def render():
    """Render the sidebar panel with portfolio builder and management"""
    
    st.sidebar.markdown("## 📊 Alphatic Portfolio Analyzer ✨")
    st.sidebar.markdown("---")
    
    # =============================================================================
    # SIDEBAR ETF UNIVERSE HELPER
    # =============================================================================
    
    st.sidebar.markdown("### 📚 ETF Universe (62 ETFs)")
    
    with st.sidebar.expander("Complete ETF Reference - Click to Expand"):
        st.markdown("""
            **🏢 Core Market (5):**
            - SPY, VOO, IVV (S&P 500)
            - VTI, ITOT (Total Market)
            
            **🚀 Growth/Tech (7):**
            - QQQ (Nasdaq-100)
            - VUG, IWF, MGK (Growth)
            - VGT, SCHG (Tech)
            - ARKK (Innovation)
            
            **💰 Dividend (7):**
            - SCHD, VIG, HDV (Quality Div)
            - VYM, DGRO, NOBL, DVY (Div Growth)
            
            **🎯 Value (5):**
            - VTV, VLUE (Value)
            - IVE, SCHV, IWD (Large Value)
            
            **🔷 Small Cap (10):**
            - VB, IJR, SCHA (Total Small)
            - **AVUV**, DFSV, VBR, SLYV (SC Value)
            - VBK, IJT, SLYG (SC Growth)
            
            **🔶 Mid Cap (4):**
            - VO, IJH, SCHM, MDY
            
            **🛡️ Bonds (10):**
            - AGG, BND (Aggregate)
            - TLT, IEF (Treasury)
            - SHY (Short-term)
            - TIP (Inflation)
            - LQD (Investment Grade)
            - MUB (Muni)
            - HYG, JNK (High Yield)
            
            **🌍 International (6):**
            - VEA, IEFA, EFA (Developed)
            - VWO (Emerging)
            - VXUS, IXUS (Total Intl)
            
            **⚡ Sectors (5):**
            - XLK (Tech), XLV (Health)
            - XLF (Financial), XLE (Energy)
            - XLI (Industrial)
            
            **🎨 Factors (4):**
            - QUAL (Quality)
            - MTUM (Momentum)
            - USMV (Low Vol)
            - SIZE (Small Cap)
            
            **⭐ NEW: AVUV** = Avantis Small Cap Value with quality screening!
            
            **💡 Tip:** Click "Trading Signals" tab to see signals for all 62 ETFs!
        """)
    
    st.sidebar.markdown("---")
    
    # Portfolio Builder Section
    st.sidebar.markdown("### 🔨 Build Portfolio")
    
    # Input for new portfolio name
    portfolio_name = st.sidebar.text_input("Portfolio Name", value="My Portfolio")
    
    # Ticker input
    ticker_input = st.sidebar.text_area(
        "Enter Tickers (one per line or comma-separated)",
        value="SPY\nQQQ\nAGG",
        height=100
    )
    
    # Parse tickers
    if ticker_input:
        tickers_list = [t.strip().upper() for t in ticker_input.replace(',', '\n').split('\n') if t.strip()]
    else:
        tickers_list = []
    
    # Allocation method
    allocation_method = st.sidebar.radio(
        "Allocation Method",
        ["Equal Weight", "Custom Weights", "Optimize (Max Sharpe)"]
    )
    
    # Custom weights if selected
    custom_weights = {}
    if allocation_method == "Custom Weights" and tickers_list:
        st.sidebar.markdown("**Set Custom Weights (must sum to 100%):**")
        for ticker in tickers_list:
            weight = st.sidebar.number_input(
                f"{ticker} %",
                min_value=0.0,
                max_value=100.0,
                value=100.0 / len(tickers_list),
                step=1.0,
                key=f"weight_{ticker}"
            )
            custom_weights[ticker] = weight / 100.0
        
        weight_sum = sum(custom_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            st.sidebar.warning(f"⚠️ Weights sum to {weight_sum*100:.1f}% (should be 100%)")
    
    # Date range selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Date Range")
    
    date_method = st.sidebar.radio(
        "Start Date Method",
        ["Auto (Earliest Available)", "Custom Date"]
    )
    
    if date_method == "Custom Date":
        start_date = st.sidebar.date_input(
            "Start Date",
            value=datetime(2020, 1, 1).date()
        )
    else:
        start_date = None
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=datetime.now().date()
    )
    
    # Build Portfolio Button
    if st.sidebar.button("🚀 Build Portfolio", type="primary"):
        if not tickers_list:
            st.sidebar.error("Please enter at least one ticker!")
        else:
            with st.spinner("Building portfolio..."):
                # Determine start date if auto
                if start_date is None:
                    st.info("Determining earliest available start date...")
                    auto_start_date = get_earliest_start_date(tickers_list)
                    if auto_start_date:
                        start_date = auto_start_date
                        st.success(f"✅ Using earliest start date: {start_date.strftime('%Y-%m-%d')}")
                    else:
                        st.error("Could not determine start date. Please use custom date.")
                        st.stop()
                
                # Download data
                prices = download_ticker_data(tickers_list, start_date, end_date)
                
                if prices is not None and not prices.empty:
                    # Determine weights
                    if allocation_method == "Equal Weight":
                        weights = {ticker: 1/len(tickers_list) for ticker in tickers_list}
                    elif allocation_method == "Custom Weights":
                        weights = custom_weights
                    else:  # Optimize
                        optimal_weights = optimize_portfolio(prices)
                        weights = {ticker: w for ticker, w in zip(tickers_list, optimal_weights)}
                    
                    # Calculate portfolio returns
                    weights_array = np.array([weights[ticker] for ticker in prices.columns])
                    portfolio_returns = calculate_portfolio_returns(prices, weights_array)
                    
                    # Validate portfolio returns
                    if portfolio_returns is None or len(portfolio_returns) == 0:
                        st.sidebar.error("""
                        ⚠️ **Could not calculate returns!**
                        
                        **Possible causes:**
                        - Date range too short (need at least 2 days)
                        - Start date = End date
                        - No overlapping data for all tickers
                        
                        **Solutions:**
                        - Use "Auto (Earliest Available)" start date
                        - Ensure end date is at least 30 days after start
                        - Verify all tickers have data in date range
                        """)
                        st.stop()
                    
                    # Check minimum data requirement
                    if len(portfolio_returns) < 30:
                        st.sidebar.warning(f"⚠️ Only {len(portfolio_returns)} days of data. Recommend at least 30 days for reliable metrics.")
                    
                    # Store in session state
                    st.session_state.portfolios[portfolio_name] = {
                        'tickers': tickers_list,
                        'weights': weights,
                        'prices': prices,
                        'returns': portfolio_returns,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    st.session_state.current_portfolio = portfolio_name
                    
                    st.sidebar.success(f"✅ Portfolio '{portfolio_name}' created successfully with {len(portfolio_returns)} days of data!")
                    st.sidebar.info("📊 Returns include dividends reinvested (Total Return)")
                else:
                    st.sidebar.error("Failed to download price data. Please check tickers and dates.")
    
    # Portfolio Management
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📁 Manage Portfolios")
    
    if st.session_state.portfolios:
        # Select portfolio
        selected_portfolio = st.sidebar.selectbox(
            "Select Portfolio",
            list(st.session_state.portfolios.keys()),
            index=list(st.session_state.portfolios.keys()).index(st.session_state.current_portfolio) 
            if st.session_state.current_portfolio else 0
        )
        st.session_state.current_portfolio = selected_portfolio
        
        # Show portfolio info
        current_portfolio = st.session_state.portfolios[selected_portfolio]
        st.sidebar.info(f"📅 Data through: {current_portfolio['end_date'].strftime('%Y-%m-%d')}")
        
        # Refresh portfolio data button
        if st.sidebar.button("🔄 Refresh Portfolio Data", help="Update price data to current date while keeping same tickers and weights"):
            with st.spinner("Refreshing portfolio data..."):
                try:
                    portfolio = st.session_state.portfolios[selected_portfolio]
                    
                    # Keep original start date, update end date to today
                    start_date = portfolio['start_date']
                    end_date = datetime.now().date()
                    tickers_list = portfolio['tickers']
                    weights = portfolio['weights']
                    
                    # Download fresh data
                    prices = download_ticker_data(tickers_list, start_date, end_date)
                    
                    if prices is not None and not prices.empty:
                        # Calculate portfolio returns
                        weights_array = np.array([weights[ticker] for ticker in prices.columns])
                        portfolio_returns = calculate_portfolio_returns(prices, weights_array)
                        
                        # Validate returns
                        if portfolio_returns is None or len(portfolio_returns) == 0:
                            st.sidebar.error("⚠️ Could not calculate returns after refresh. Date range may be too short.")
                        else:
                            # Update portfolio
                            st.session_state.portfolios[selected_portfolio].update({
                                'prices': prices,
                                'returns': portfolio_returns,
                                'end_date': end_date
                            })
                            
                            st.sidebar.success(f"✅ Portfolio refreshed to {end_date.strftime('%Y-%m-%d')} with {len(portfolio_returns)} days of data")
                            st.rerun()
                    else:
                        st.sidebar.error("Failed to download fresh data")
                except Exception as e:
                    st.sidebar.error(f"Refresh failed: {str(e)}")
        
        # Delete portfolio
        if st.sidebar.button("🗑️ Delete Selected Portfolio"):
            del st.session_state.portfolios[selected_portfolio]
            st.session_state.current_portfolio = list(st.session_state.portfolios.keys())[0] if st.session_state.portfolios else None
            st.sidebar.success("Portfolio deleted!")
            st.rerun()
        
        # Export/Import
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💾 Export/Import")
        
        if st.sidebar.button("📥 Export All Portfolios"):
            export_data = {}
            for name, portfolio in st.session_state.portfolios.items():
                export_data[name] = {
                    'tickers': portfolio['tickers'],
                    'weights': portfolio['weights'],
                    'start_date': portfolio['start_date'].isoformat(),
                    'end_date': portfolio['end_date'].isoformat()
                }
            
            json_str = json.dumps(export_data, indent=2)
            st.sidebar.download_button(
                label="Download portfolios.json",
                data=json_str,
                file_name="alphatic_portfolios.json",
                mime="application/json"
            )
