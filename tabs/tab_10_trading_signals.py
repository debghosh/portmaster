"""
Tab: Trading Signals
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from helper_functions import *


def render(tab10, portfolio_returns, prices, weights, tickers, metrics, current):
    """Render the Trading Signals tab"""
    
    def normalize_action(raw_action):
        """
        Normalize all trading signal actions to Buy/Hold/Sell
        Input: Accumulate, Hold, Distribute (from generate_trading_signal)
        Output: Buy, Hold, Sell
        """
        action_mapping = {
            'Accumulate': 'Buy',
            'Hold': 'Hold',
            'Distribute': 'Sell'
        }
        return action_mapping.get(raw_action, 'Hold')
    
    with tab10:
        st.markdown("# 🚦 Trading Signals")
        st.markdown("**Your Portfolio:** Actionable recommendations with dual signal confirmation")
        
        # Check Kalman filter availability
        from helper_functions import KALMAN_AVAILABLE
        
        if KALMAN_AVAILABLE:
            st.success("🔬 **Kalman Filter Active:** Dual-signal system provides higher confidence recommendations")
        else:
            st.warning("⚠️ **Kalman Filter Unavailable:** Install with `pip install pykalman` for dual-signal confirmation")
        
        st.markdown("---")
        
        if 'prices' in current:
            prices = current['prices']
            tickers = current['tickers']
            weights = current['weights']
            
            st.markdown("### 🎯 Your Portfolio Holdings - Actionable Signals")
            
            # Generate detailed signals for portfolio tickers
            for ticker in tickers:
                if ticker in prices.columns:
                    # Get comprehensive signal
                    signal = generate_trading_signal(prices[ticker], ticker)
                    
                    # Extract data
                    sma_action = normalize_action(signal['action'])
                    sma_score = signal['score']
                    confidence = signal['confidence']
                    current_price = prices[ticker].iloc[-1]
                    weight = weights.get(ticker, 0) * 100
                    
                    # Get Kalman signal if available
                    kalman_signal = signal.get('kalman_signal')
                    kalman_agreement = signal.get('kalman_agreement', '')
                    
                    # Create expander for each ticker
                    with st.expander(f"**{ticker}** ({weight:.1f}% of portfolio) - ${current_price:.2f}", expanded=True):
                        
                        # Top row: Signals comparison
                        col1, col2, col3 = st.columns([2, 2, 3])
                        
                        with col1:
                            st.markdown("**📊 SMA Signal**")
                            if sma_score >= 4:
                                emoji = "🟢🟢"
                                color = "green"
                            elif sma_score >= 2:
                                emoji = "🟢"
                                color = "green"
                            elif sma_score <= -4:
                                emoji = "🔴🔴"
                                color = "red"
                            elif sma_score <= -2:
                                emoji = "🔴"
                                color = "red"
                            else:
                                emoji = "🟡"
                                color = "orange"
                            
                            st.markdown(f":{color}[{emoji} **{sma_action}** (Score: {sma_score:+.1f})]")
                            st.caption(f"Confidence: {confidence:.0f}%")
                        
                        with col2:
                            st.markdown("**🔬 Kalman Signal**")
                            if kalman_signal:
                                k_action = kalman_signal['action']
                                k_score = kalman_signal['score']
                                k_conf = kalman_signal['confidence']
                                
                                # Decode action
                                if 'Strong Buy' in k_action:
                                    k_emoji = "🟢🟢"
                                    k_color = "green"
                                    k_short = "Strong Buy"
                                elif 'Buy' in k_action:
                                    k_emoji = "🟢"
                                    k_color = "green"
                                    k_short = "Buy"
                                elif 'Strong Sell' in k_action:
                                    k_emoji = "🔴🔴"
                                    k_color = "red"
                                    k_short = "Strong Sell"
                                elif 'Sell' in k_action:
                                    k_emoji = "🔴"
                                    k_color = "red"
                                    k_short = "Sell"
                                else:
                                    k_emoji = "🟡"
                                    k_color = "orange"
                                    k_short = "Hold"
                                
                                st.markdown(f":{k_color}[{k_emoji} **{k_short}** (Score: {k_score:+d})]")
                                st.caption(f"Confidence: {k_conf:.0f}%")
                                
                                # Add calculation breakdown button/expander
                                if 'calculations' in kalman_signal:
                                    with st.expander("📐 See Kalman Calculation", expanded=False):
                                        st.markdown("**How This Score Was Calculated:**")
                                        st.code('\n'.join(kalman_signal['calculations']), language='text')
                                        
                                        # Show key metrics
                                        if 'metrics' in kalman_signal:
                                            metrics = kalman_signal['metrics']
                                            st.markdown("**Key Metrics:**")
                                            st.markdown(f"- Current Price: ${metrics.get('current_price', 0):.2f}")
                                            st.markdown(f"- Filtered Price: ${metrics.get('filtered_price', 0):.2f}")
                                            st.markdown(f"- Price vs Filter: {metrics.get('price_vs_filter', 0):.2f}%")
                                            st.markdown(f"- 20-Day Momentum: {metrics.get('kalman_momentum', 0):.2f}%")
                                            st.markdown(f"- Predicted Change: {metrics.get('prediction_change', 0):.2f}%")
                            else:
                                st.markdown("*Not available*")
                                st.caption("Need 100+ days data")
                        
                        with col3:
                            st.markdown("**🎯 Agreement**")
                            if kalman_agreement:
                                if "ALIGNED" in kalman_agreement:
                                    st.markdown(f":green[✅ **ALIGNED** - High Conviction]")
                                    st.caption("Both signals agree → Trust this signal")
                                elif "CONFLICT" in kalman_agreement:
                                    st.markdown(f":orange[⚠️ **CONFLICT** - Caution]")
                                    st.caption("Signals disagree → Wait for clarity")
                                else:
                                    st.markdown(f":gray[⚪ **MIXED** - Lower Conviction]")
                                    st.caption("Partial agreement → Monitor")
                            else:
                                st.markdown("*SMA only*")
                        
                        # Actionable Recommendation
                        st.markdown("---")
                        st.markdown("**💡 Actionable Recommendation:**")
                        
                        # Generate recommendation based on signals
                        if kalman_signal and "ALIGNED" in kalman_agreement:
                            # Both agree - high conviction
                            if sma_score >= 4 and k_score >= 3:
                                st.success(f"""
                                **🚀 STRONG BUY OPPORTUNITY**
                                
                                **Action:** Consider adding to your {ticker} position
                                - Both signals strongly bullish (SMA: {sma_score:+.1f}, Kalman: {k_score:+d})
                                - High confidence: SMA {confidence:.0f}%, Kalman {k_conf:.0f}%
                                - Currently {weight:.1f}% of portfolio
                                
                                **Suggestion:** If you want more {ticker} exposure, this is a good entry point.
                                """)
                            elif sma_score >= 2 and k_score >= 1:
                                st.info(f"""
                                **📈 BUY SIGNAL**
                                
                                **Action:** Good time to hold or add modestly to {ticker}
                                - Both signals bullish (SMA: {sma_score:+.1f}, Kalman: {k_score:+d})
                                - Moderate confidence
                                - Currently {weight:.1f}% of portfolio
                                
                                **Suggestion:** Maintain current allocation or add slightly if underweight.
                                """)
                            elif sma_score <= -4 and k_score <= -3:
                                st.error(f"""
                                **🔻 STRONG SELL SIGNAL**
                                
                                **Action:** Consider reducing your {ticker} position
                                - Both signals strongly bearish (SMA: {sma_score:+.1f}, Kalman: {k_score:+d})
                                - High confidence: SMA {confidence:.0f}%, Kalman {k_conf:.0f}%
                                - Currently {weight:.1f}% of portfolio
                                
                                **Suggestion:** Trim position or exit entirely. Redeploy to stronger opportunities.
                                """)
                            elif sma_score <= -2 and k_score <= -1:
                                st.warning(f"""
                                **📉 SELL SIGNAL**
                                
                                **Action:** Consider reducing {ticker} exposure
                                - Both signals bearish (SMA: {sma_score:+.1f}, Kalman: {k_score:+d})
                                - Moderate conviction
                                - Currently {weight:.1f}% of portfolio
                                
                                **Suggestion:** Reduce position size or wait for improvement before adding.
                                """)
                            else:
                                st.info(f"""
                                **➡️ HOLD**
                                
                                **Action:** Maintain current {ticker} position
                                - Both signals neutral/mixed
                                - Currently {weight:.1f}% of portfolio
                                
                                **Suggestion:** No action needed. Monitor for clearer signals.
                                """)
                        
                        elif kalman_signal and "CONFLICT" in kalman_agreement:
                            # Signals conflict - caution
                            st.warning(f"""
                            **⚠️ CONFLICTING SIGNALS - EXERCISE CAUTION**
                            
                            **Action:** Hold {ticker} and wait for alignment
                            - SMA says: **{sma_action}** (Score: {sma_score:+.1f})
                            - Kalman says: **{k_short}** (Score: {k_score:+d})
                            - Signals disagree → Low conviction
                            
                            **What this means:** The market is unclear. One method sees opportunity, the other sees risk.
                            
                            **Suggestion:** 
                            - **Don't buy** new positions when signals conflict
                            - **Don't sell** existing positions yet - wait 1-2 weeks
                            - **Monitor daily** for signal alignment
                            - When both align (✅), act decisively
                            
                            **Currently {weight:.1f}% of portfolio** - maintain for now.
                            """)
                        
                        else:
                            # SMA only (no Kalman)
                            if sma_score >= 4:
                                st.success(f"""
                                **📈 STRONG BUY** (SMA-only signal)
                                
                                **Action:** Consider adding to {ticker}
                                - Score: {sma_score:+.1f}, Confidence: {confidence:.0f}%
                                - Currently {weight:.1f}% of portfolio
                                
                                **Note:** Kalman not available. For higher conviction, use longer date range (100+ days).
                                """)
                            elif sma_score >= 2:
                                st.info(f"""
                                **📊 BUY** (SMA-only signal)
                                
                                **Action:** Hold or add modestly
                                - Score: {sma_score:+.1f}, Confidence: {confidence:.0f}%
                                
                                **Suggestion:** Maintain or increase position slightly.
                                """)
                            elif sma_score <= -4:
                                st.error(f"""
                                **📉 STRONG SELL** (SMA-only signal)
                                
                                **Action:** Consider reducing {ticker}
                                - Score: {sma_score:+.1f}, Confidence: {confidence:.0f}%
                                
                                **Suggestion:** Trim or exit position.
                                """)
                            elif sma_score <= -2:
                                st.warning(f"""
                                **⚠️ SELL** (SMA-only signal)
                                
                                **Action:** Reduce exposure
                                - Score: {sma_score:+.1f}, Confidence: {confidence:.0f}%
                                
                                **Suggestion:** Lower allocation.
                                """)
                            else:
                                st.info(f"""
                                **➡️ HOLD**
                                
                                **Action:** Maintain position
                                - Neutral signals
                                
                                **Suggestion:** No changes needed.
                                """)
                        
                        # Key technical indicators (collapsed by default)
                        with st.expander("📊 Technical Details", expanded=False):
                            tech_col1, tech_col2 = st.columns(2)
                            with tech_col1:
                                rsi_val = signal.get('rsi')
                                st.metric("RSI", f"{rsi_val:.1f}" if rsi_val is not None else "N/A")
                                
                                macd_val = signal.get('macd')
                                st.metric("MACD", f"{macd_val:.3f}" if macd_val is not None else "N/A")
                            with tech_col2:
                                sma50_val = signal.get('price_vs_sma50')
                                st.metric("vs SMA-50", f"{sma50_val:.1f}%" if sma50_val is not None else "N/A")
                                
                                sma200_val = signal.get('price_vs_sma200')
                                st.metric("vs SMA-200", f"{sma200_val:.1f}%" if sma200_val is not None else "N/A")
            
            st.markdown("---")
            
            # Summary of portfolio
            st.markdown("### 📋 Portfolio Summary")
            
            col1, col2, col3 = st.columns(3)
            
            # Count signals across portfolio
            buy_count = sum(1 for ticker in tickers if ticker in prices.columns and 
                          normalize_action(generate_trading_signal(prices[ticker], ticker)['action']) == 'Buy')
            hold_count = sum(1 for ticker in tickers if ticker in prices.columns and 
                           normalize_action(generate_trading_signal(prices[ticker], ticker)['action']) == 'Hold')
            sell_count = sum(1 for ticker in tickers if ticker in prices.columns and 
                           normalize_action(generate_trading_signal(prices[ticker], ticker)['action']) == 'Sell')
            
            with col1:
                st.metric("🟢 Buy Signals", buy_count, help="Tickers showing buy signals")
            with col2:
                st.metric("🟡 Hold Signals", hold_count, help="Tickers showing hold signals")
            with col3:
                st.metric("🔴 Sell Signals", sell_count, help="Tickers showing sell signals")
            
            # Overall portfolio action
            if buy_count > sell_count and buy_count > hold_count:
                st.success("**📈 Portfolio Outlook: BULLISH** - Majority of holdings showing buy signals")
            elif sell_count > buy_count and sell_count > hold_count:
                st.warning("**📉 Portfolio Outlook: BEARISH** - Majority of holdings showing sell signals")
            else:
                st.info("**➡️ Portfolio Outlook: NEUTRAL** - Mixed signals across holdings")
        
        # =============================================================================
        # ETF UNIVERSE SIGNALS
        # =============================================================================
            st.info("👆 Build a portfolio first to see trading signals")
        
        

        st.markdown("---")
        st.markdown("---")
        
        # =============================================================================
        # ETF UNIVERSE TRADING SIGNALS
        # =============================================================================
        
        st.markdown("""
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        border-radius: 15px; color: white; margin: 2rem 0;">
                <h2 style="margin: 0; font-size: 2rem;">📡 Trading Signals for the ETF Universe</h2>
                <p style="font-size: 1.1rem; margin-top: 0.5rem; opacity: 0.9;">
                    Real-time signals for all available ETFs
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🌐 ETF Universe Signals")
        
        try:
            import time
            start_time = time.time()
            
            # Define the EXPANDED ETF Universe (62 ETFs)
            etf_universe = {
                '🏢 Core Market': ['SPY', 'VOO', 'IVV', 'VTI', 'ITOT'],
                
                '🚀 Growth/Tech': ['QQQ', 'VUG', 'VGT', 'IWF', 'SCHG', 'MGK', 'ARKK'],
                
                '💰 Dividend': ['SCHD', 'VIG', 'VYM', 'DGRO', 'NOBL', 'DVY', 'HDV'],
                
                '🎯 Value': ['VTV', 'VLUE', 'IVE', 'SCHV', 'IWD'],
                
                '🔷 Small Cap': [
                    'VB', 'IJR', 'SCHA',  # Total small cap
                    'VBR', 'AVUV', 'DFSV', 'SLYV',  # Small cap value (AVUV = quality!)
                    'VBK', 'IJT', 'SLYG'  # Small cap growth
                ],
                
                '🔶 Mid Cap': ['VO', 'IJH', 'SCHM', 'MDY'],
                
                '🛡️ Bonds': ['AGG', 'BND', 'TLT', 'IEF', 'SHY', 'TIP', 'LQD', 'MUB', 'HYG', 'JNK'],
                
                '🌍 International': ['VEA', 'VWO', 'VXUS', 'IEFA', 'IXUS', 'EFA'],
                
                '⚡ Sectors': ['XLK', 'XLV', 'XLF', 'XLE', 'XLI'],  # Tech, Health, Financial, Energy, Industrial
                
                '🎨 Factors': ['QUAL', 'MTUM', 'USMV', 'SIZE']
            }
            
            # Flatten the universe
            all_etfs = []
            for category, tickers_list in etf_universe.items():
                for ticker in tickers_list:
                    all_etfs.append((category, ticker))
            
            # CRITICAL: Determine data source
            # If portfolio exists, use its date range and data for consistency
            # Otherwise, download fresh data with 180-day lookback
            
            use_portfolio_data = 'prices' in current and current['prices'] is not None
            
            if use_portfolio_data:
                # Use portfolio's data source for consistency
                portfolio_prices = current['prices']
                portfolio_tickers = set(current['tickers'])
                start_date_ref = current.get('start_date')
                end_date_ref = current.get('end_date')
                
                # Info message about data source  
                if start_date_ref and end_date_ref:
                    st.info(f"📊 Using portfolio data (through {end_date_ref.strftime('%Y-%m-%d')}) for consistent signals. "
                           f"Click '🔄 Refresh Portfolio Data' in sidebar to update to today's date.")
            else:
                # No portfolio - use fresh 180-day download
                end_date_ref = datetime.now().date()
                start_date_ref = (datetime.now() - timedelta(days=180)).date()
                portfolio_prices = None
                portfolio_tickers = set()
                st.info(f"📊 Using 180-day lookback ({start_date_ref.strftime('%Y-%m-%d')} to {end_date_ref.strftime('%Y-%m-%d')})")
            
            # Download and process
            status_text = st.empty()
            status_text.text("📥 Downloading data for all ETFs in batch...")
            
            # OPTIMIZATION: Separate tickers into portfolio vs non-portfolio
            portfolio_etfs = []
            non_portfolio_etfs = []
            
            for category, ticker in all_etfs:
                if use_portfolio_data and ticker in portfolio_tickers and ticker in portfolio_prices.columns:
                    portfolio_etfs.append((category, ticker))
                else:
                    non_portfolio_etfs.append((category, ticker))
            
            # BATCH DOWNLOAD: Download all non-portfolio ETFs at once (MUCH FASTER!)
            non_portfolio_prices = None
            if non_portfolio_etfs:
                non_portfolio_ticker_list = [ticker for _, ticker in non_portfolio_etfs]
                status_text.text(f"📥 Batch downloading {len(non_portfolio_ticker_list)} ETFs... (this is much faster!)")
                
                non_portfolio_prices = download_ticker_data(
                    non_portfolio_ticker_list, 
                    start_date_ref, 
                    end_date_ref
                )
            
            # Now process signals (fast - just calculations, no downloads)
            status_text.text("⚡ Calculating trading signals...")
            progress_bar = st.progress(0)
            
            signals_data = []
            errors = []
            total_etfs = len(all_etfs)
            
            for idx, (category, ticker) in enumerate(all_etfs):
                progress_pct = (idx + 1) / total_etfs
                progress_bar.progress(progress_pct)
                status_text.text(f"⚡ Calculating signal for {ticker}... ({idx + 1}/{total_etfs})")
                
                try:
                    # Get prices from appropriate source
                    if use_portfolio_data and ticker in portfolio_tickers and ticker in portfolio_prices.columns:
                        # Use portfolio data
                        etf_prices = portfolio_prices[ticker].dropna()
                    else:
                        # Use batch downloaded data
                        if non_portfolio_prices is None or non_portfolio_prices.empty:
                            errors.append(f"{ticker}: Batch download failed")
                            continue
                        
                        if ticker not in non_portfolio_prices.columns:
                            errors.append(f"{ticker}: Not in batch download")
                            continue
                        
                        etf_prices = non_portfolio_prices[ticker].dropna()
                    
                    if len(etf_prices) <= 50:
                        errors.append(f"{ticker}: Insufficient data ({len(etf_prices)} days)")
                        continue
                    
                    # Generate signal using SAME function
                    signal = generate_trading_signal(etf_prices, ticker)
                    
                    if signal is None:
                        errors.append(f"{ticker}: Signal generation failed")
                        continue
                    
                    # Normalize the action
                    normalized_action = normalize_action(signal.get('action', 'Hold'))
                    
                    score = signal.get('score', 0)
                    confidence = signal.get('confidence', 0)
                    current_price = etf_prices.iloc[-1]
                    
                    # Determine emoji and color
                    if normalized_action == 'Buy':
                        action_emoji, action_color = '🟢', '#28a745'
                    elif normalized_action == 'Sell':
                        action_emoji, action_color = '🔴', '#dc3545'
                    else:
                        action_emoji, action_color = '🟡', '#ffc107'
                    
                    # Check for Kalman signal
                    kalman_info = ""
                    kalman_agreement = ""
                    
                    # Debug: Check if Kalman is in the signal
                    if 'kalman_signal' in signal and signal['kalman_signal'] is not None:
                        kalman_sig = signal['kalman_signal']
                        kalman_agreement = signal.get('kalman_agreement', '')
                        
                        # Create Kalman info string
                        kalman_action = kalman_sig.get('action', 'N/A')
                        kalman_score = kalman_sig.get('score', 0)
                        
                        # Format based on action
                        if 'Buy' in kalman_action:
                            action_letter = 'B'
                        elif 'Sell' in kalman_action:
                            action_letter = 'S'
                        else:
                            action_letter = 'H'
                        
                        kalman_info = f"{action_letter}{kalman_score:+d}"
                    else:
                        # Kalman not available - show why
                        kalman_info = "N/A"
                        kalman_agreement = ""
                    
                    signals_data.append({
                        'Category': category,
                        'Ticker': ticker,
                        'Action': normalized_action,
                        'Action_Display': f"{action_emoji} {normalized_action}",
                        'Score': score,
                        'Confidence': f"{confidence:.0f}%",
                        'Price': f"${current_price:.2f}",
                        'Action_Color': action_color,
                        'Kalman': kalman_info,
                        'Agreement': kalman_agreement
                    })
                    
                except Exception as e:
                    errors.append(f"{ticker}: {str(e)[:50]}")
                    continue
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Success message with timing
            elapsed_time = time.time() - start_time
            st.success(f"✅ Processed {len(signals_data)} ETFs in {elapsed_time:.1f} seconds! (Batch download = {len(non_portfolio_etfs)} ETFs in one request)")
            
            # Show errors if any
            if len(errors) > 0:
                with st.expander(f"⚠️ {len(errors)} ETFs had issues (click to view)"):
                    for error in errors[:20]:
                        st.text(error)
            
            # Display table if we have signals
            if signals_data:
                signals_df = pd.DataFrame(signals_data)
                
                # VERIFICATION: Compare with portfolio signals if available
                if use_portfolio_data:
                    st.markdown("---")
                    st.markdown("### ✅ Signal Verification")
                    
                    # Get portfolio signals for comparison
                    portfolio_signals = {}
                    if 'prices' in current:
                        portfolio_prices_ref = current['prices']
                        for ticker in current['tickers']:
                            if ticker in portfolio_prices_ref.columns:
                                sig = generate_trading_signal(portfolio_prices_ref[ticker], ticker)
                                portfolio_signals[ticker] = {
                                    'action': normalize_action(sig['action']),
                                    'score': sig['score']
                                }
                    
                    # Find overlapping tickers
                    etf_universe_tickers = set(signals_df['Ticker'].unique())
                    overlapping = etf_universe_tickers.intersection(portfolio_signals.keys())
                    
                    if overlapping:
                        st.info(f"📊 Comparing signals for {len(overlapping)} tickers in both Portfolio and ETF Universe")
                        
                        verification_data = []
                        mismatches = 0
                        
                        for ticker in sorted(overlapping):
                            portfolio_action = portfolio_signals[ticker]['action']
                            portfolio_score = portfolio_signals[ticker]['score']
                            
                            etf_row = signals_df[signals_df['Ticker'] == ticker].iloc[0]
                            etf_action = etf_row['Action']
                            etf_score = etf_row['Score']
                            
                            match_status = "✅ Match" if portfolio_action == etf_action else "⚠️ MISMATCH"
                            if portfolio_action != etf_action:
                                mismatches += 1
                            
                            verification_data.append({
                                'Ticker': ticker,
                                'Portfolio Signal': portfolio_action,
                                'Portfolio Score': portfolio_score,
                                'ETF Universe Signal': etf_action,
                                'ETF Universe Score': etf_score,
                                'Status': match_status
                            })
                        
                        verification_df = pd.DataFrame(verification_data)
                        st.dataframe(verification_df, use_container_width=True, hide_index=True)
                        
                        if mismatches == 0:
                            st.success(f"✅ Perfect! All {len(overlapping)} signals match between Portfolio and ETF Universe")
                        else:
                            st.error(f"⚠️ {mismatches} mismatches found! Signals should be identical for same tickers.")
                    
                    st.markdown("---")
                
                st.markdown("#### 🔍 Filter & Sort")
                col1, col2 = st.columns(2)
                
                with col1:
                    filter_action = st.multiselect(
                        "Filter by Action:",
                        ['Buy', 'Hold', 'Sell'],
                        default=['Buy', 'Hold', 'Sell'],
                        key='etf_universe_filter'
                    )
                
                with col2:
                    sort_by = st.selectbox(
                        "Sort by:",
                        ['Action', 'Score', 'Confidence', 'Ticker'],
                        key='etf_universe_sort'
                    )
                
                filtered_df = signals_df[signals_df['Action'].isin(filter_action)]
                
                if sort_by == 'Action':
                    action_order = {'Buy': 0, 'Hold': 1, 'Sell': 2}
                    filtered_df['sort_key'] = filtered_df['Action'].map(action_order)
                    filtered_df = filtered_df.sort_values('sort_key').drop('sort_key', axis=1)
                elif sort_by == 'Score':
                    filtered_df = filtered_df.sort_values('Score', ascending=False)
                elif sort_by == 'Confidence':
                    filtered_df['conf_num'] = filtered_df['Confidence'].str.rstrip('%').astype(float)
                    filtered_df = filtered_df.sort_values('conf_num', ascending=False).drop('conf_num', axis=1)
                else:
                    filtered_df = filtered_df.sort_values('Ticker')
                
                st.markdown(f"#### 📊 Showing {len(filtered_df)} ETFs")
                
                # Select columns for display
                display_df = filtered_df[['Category', 'Ticker', 'Action_Display', 'Score', 'Confidence', 'Kalman', 'Agreement', 'Price']].copy()
                display_df.columns = ['Category', 'Ticker', 'SMA Signal', 'Score', 'Conf%', 'Kalman', 'Agree', 'Price']
                
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)
                
                # Kalman Filter Legend
                st.markdown("---")
                st.markdown("### 🔬 Understanding the Signals")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **SMA Signal (Traditional):**
                    - 🟢 Buy / 🔴 Sell / 🟡 Hold
                    - Uses SMA-50, SMA-200, RSI, MACD
                    - Score: -6 to +6
                    - ±2: Buy/Sell | ±4: Strong Buy/Sell
                    """)
                
                with col2:
                    st.markdown("""
                    **Kalman Column (Advanced):**
                    - **B** = Buy | **S** = Sell | **H** = Hold
                    - **+3** = Score (higher = stronger)
                    - Examples:
                      - **B+4** = Strong Buy (bullish +4)
                      - **S-3** = Sell (bearish -3)
                      - **H+0** = Hold (neutral)
                    """)
                
                st.markdown("""
                **Agreement Column:**
                - ✅ **ALIGNED** = Both signals agree → **HIGH CONFIDENCE** → Best trades
                - ⚠️ **CONFLICT** = Signals disagree → **CAUTION** → Wait for clarity
                - ⚪ **MIXED** = Partial agreement → **LOWER CONVICTION** → Monitor
                
                **💡 Pro Tip:** Focus on ✅ ALIGNED signals with high scores (±4) for best risk/reward trades.
                """)
                
                # Summary
                st.markdown("---")
                st.markdown("### 📈 Signal Summary")
                
                col1, col2, col3 = st.columns(3)
                buy_count = len(signals_df[signals_df['Action'] == 'Buy'])
                hold_count = len(signals_df[signals_df['Action'] == 'Hold'])
                sell_count = len(signals_df[signals_df['Action'] == 'Sell'])
                
                with col1:
                    st.metric("🟢 Buy Signals", buy_count)
                with col2:
                    st.metric("🟡 Hold Signals", hold_count)
                with col3:
                    st.metric("🔴 Sell Signals", sell_count)
                
                # Top Opportunities
                st.markdown("---")
                st.markdown("### 🎯 Top Opportunities")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🟢 Top Buy Signals (Highest Score)**")
                    buy_signals = signals_df[signals_df['Action'] == 'Buy'].sort_values('Score', ascending=False).head(5)
                    if not buy_signals.empty:
                        for _, row in buy_signals.iterrows():
                            st.markdown(f"• **{row['Ticker']}** - Score: {row['Score']}, Confidence: {row['Confidence']}")
                    else:
                        st.info("No Buy signals currently")
                
                with col2:
                    st.markdown("**🔴 Top Sell Signals (Lowest Score)**")
                    sell_signals = signals_df[signals_df['Action'] == 'Sell'].sort_values('Score', ascending=True).head(5)
                    if not sell_signals.empty:
                        for _, row in sell_signals.iterrows():
                            st.markdown(f"• **{row['Ticker']}** - Score: {row['Score']}, Confidence: {row['Confidence']}")
                    else:
                        st.info("No Sell signals currently")
                
                st.markdown("---")
                st.info("💡 **Note:** These signals are based on technical analysis. Always do your own research and consider your investment goals, risk tolerance, and time horizon.")
            
            else:
                st.error("❌ Unable to generate signals for ETF universe.")
                st.markdown("**Possible causes:**")
                st.markdown("- Internet connection issues")
                st.markdown("- yfinance API rate limiting")
                if len(errors) > 0:
                    st.markdown(f"- Check the error expander above for details ({len(errors)} errors)")
        
        except Exception as e:
            st.error(f"❌ Error in ETF Universe section: {str(e)}")
            import traceback
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())

