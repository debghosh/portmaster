"""
Sidebar Panel with Database Integration
Handles portfolio building, saving, loading with multi-tenancy support
"""

import streamlit as st
import numpy as np
from datetime import datetime
from helper_functions import (
    download_ticker_data,
    calculate_portfolio_returns,
    optimize_portfolio,
    get_earliest_start_date
)
from database import PortfolioDB, login_widget


def render_sidebar():
    """Render the complete sidebar with database integration"""
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = PortfolioDB()
    
    db = st.session_state.db
    
    # =============================================================================
    # USER AUTHENTICATION
    # =============================================================================
    
    user_id = login_widget(db)
    
    if not user_id:
        # Show ETF universe but no portfolio builder
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📚 ETF Universe (62 ETFs)")
        st.sidebar.info("👆 Login to create and save portfolios")
        show_etf_universe()
        return
    
    # =============================================================================
    # ETF UNIVERSE HELPER
    # =============================================================================
    
    show_etf_universe()
    
    st.sidebar.markdown("---")
    
    # =============================================================================
    # PORTFOLIO BUILDER
    # =============================================================================
    
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
        ["Equal Weight", "Custom Weights", "Optimize (Max Sharpe)"],
        index=0
    )
    
    # Custom weights if selected
    custom_weights = {}
    if allocation_method == "Custom Weights" and tickers_list:
        st.sidebar.markdown("**Enter Weights (must sum to 1.0):**")
        for ticker in tickers_list:
            custom_weights[ticker] = st.sidebar.number_input(
                f"{ticker}",
                min_value=0.0,
                max_value=1.0,
                value=1.0/len(tickers_list),
                step=0.05,
                key=f"weight_{ticker}"
            )
        
        total_weight = sum(custom_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            st.sidebar.warning(f"⚠️ Weights sum to {total_weight:.2f}, not 1.0")
    
    # Date range
    use_auto_start = st.sidebar.checkbox("Auto (Earliest Available)", value=True)
    
    if not use_auto_start:
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
    
    # Privacy setting
    is_public = st.sidebar.checkbox(
        "🌍 Make Portfolio Public",
        value=False,
        help="Public portfolios are visible to all users"
    )
    
    # Build Portfolio Button
    if st.sidebar.button("🚀 Build & Save Portfolio", type="primary"):
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
                    
                    # Save to database
                    portfolio_id = db.save_portfolio(
                        user_id=user_id,
                        name=portfolio_name,
                        tickers=tickers_list,
                        weights=weights,
                        prices=prices,
                        returns=portfolio_returns,
                        start_date=start_date,
                        end_date=end_date,
                        is_public=is_public
                    )
                    
                    if portfolio_id:
                        # Also store in session state for immediate use
                        st.session_state.portfolios = st.session_state.get('portfolios', {})
                        st.session_state.portfolios[portfolio_name] = {
                            'portfolio_id': portfolio_id,
                            'tickers': tickers_list,
                            'weights': weights,
                            'prices': prices,
                            'returns': portfolio_returns,
                            'start_date': start_date,
                            'end_date': end_date,
                            'is_public': is_public
                        }
                        st.session_state.current_portfolio = portfolio_name
                        
                        visibility = "🌍 Public" if is_public else "🔒 Private"
                        st.sidebar.success(f"✅ Portfolio '{portfolio_name}' saved successfully! ({visibility})")
                        st.sidebar.success(f"📊 {len(portfolio_returns)} days of data")
                        st.sidebar.info("💾 Portfolio saved to database permanently!")
                    else:
                        st.sidebar.error("Failed to save portfolio to database")
                else:
                    st.sidebar.error("Failed to download price data. Please check tickers and dates.")
    
    # =============================================================================
    # LOAD SAVED PORTFOLIOS
    # =============================================================================
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Saved Portfolios")
    
    # Get user's portfolios from database
    user_portfolios = db.get_user_portfolios(user_id)
    
    if user_portfolios:
        # Separate into owned and public
        owned_portfolios = [p for p in user_portfolios if p.get('owned', True)]
        public_portfolios = [p for p in user_portfolios if not p.get('owned', True)]
        
        # Show owned portfolios
        if owned_portfolios:
            st.sidebar.markdown("**Your Portfolios:**")
            
            for portfolio in owned_portfolios:
                with st.sidebar.expander(f"📊 {portfolio['name']}"):
                    # Show portfolio info
                    tickers_str = ", ".join(portfolio['tickers'][:5])
                    if len(portfolio['tickers']) > 5:
                        tickers_str += f" +{len(portfolio['tickers'])-5} more"
                    
                    st.text(f"Tickers: {tickers_str}")
                    st.text(f"Date: {portfolio['start_date']} to {portfolio['end_date']}")
                    
                    visibility = "🌍 Public" if portfolio['is_public'] else "🔒 Private"
                    st.text(f"Visibility: {visibility}")
                    
                    col1, col2 = st.columns(2)
                    
                    # Load button
                    if col1.button("📂 Load", key=f"load_{portfolio['portfolio_id']}"):
                        loaded = db.load_portfolio(portfolio['portfolio_id'])
                        if loaded:
                            # Store in session state
                            st.session_state.portfolios = st.session_state.get('portfolios', {})
                            st.session_state.portfolios[loaded['name']] = loaded
                            st.session_state.current_portfolio = loaded['name']
                            st.sidebar.success(f"✅ Loaded: {loaded['name']}")
                            st.rerun()
                    
                    # Delete button
                    if col2.button("🗑️ Delete", key=f"del_{portfolio['portfolio_id']}"):
                        if db.delete_portfolio(portfolio['portfolio_id'], user_id):
                            st.sidebar.success("Portfolio deleted")
                            st.rerun()
                    
                    # Toggle visibility button
                    current_visibility = "Public" if portfolio['is_public'] else "Private"
                    toggle_text = "Make Private" if portfolio['is_public'] else "Make Public"
                    
                    if st.button(f"🔄 {toggle_text}", key=f"toggle_{portfolio['portfolio_id']}"):
                        new_state = db.toggle_portfolio_visibility(portfolio['portfolio_id'], user_id)
                        if new_state is not None:
                            visibility = "Public" if new_state else "Private"
                            st.sidebar.success(f"Portfolio is now {visibility}")
                            st.rerun()
        
        # Show public portfolios from other users
        if public_portfolios:
            st.sidebar.markdown("**Public Portfolios:**")
            
            for portfolio in public_portfolios:
                with st.sidebar.expander(f"🌍 {portfolio['name']} by {portfolio.get('owner', 'Unknown')}"):
                    tickers_str = ", ".join(portfolio['tickers'][:5])
                    if len(portfolio['tickers']) > 5:
                        tickers_str += f" +{len(portfolio['tickers'])-5} more"
                    
                    st.text(f"Tickers: {tickers_str}")
                    st.text(f"Date: {portfolio['start_date']} to {portfolio['end_date']}")
                    st.text(f"By: {portfolio.get('owner', 'Unknown')}")
                    
                    # Load button (read-only)
                    if st.button("👁️ View", key=f"view_{portfolio['portfolio_id']}"):
                        loaded = db.load_portfolio(portfolio['portfolio_id'])
                        if loaded:
                            st.session_state.portfolios = st.session_state.get('portfolios', {})
                            st.session_state.portfolios[loaded['name']] = loaded
                            st.session_state.current_portfolio = loaded['name']
                            st.sidebar.info(f"👁️ Viewing: {loaded['name']} (read-only)")
                            st.rerun()
    else:
        st.sidebar.info("No saved portfolios yet. Build one above!")


def show_etf_universe():
    """Display ETF universe reference"""
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
