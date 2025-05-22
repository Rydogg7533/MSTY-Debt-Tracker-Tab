import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import io
import base64

# Load environment variables
load_dotenv()

st.set_page_config(page_title="MSTY Tool", layout="wide")

# Initialize session state for simulation results if not exists
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'actual_performance' not in st.session_state:
    st.session_state.actual_performance = []
if 'market_data' not in st.session_state:
    st.session_state.market_data = []
if 'last_dividend' not in st.session_state:
    st.session_state.last_dividend = None
if 'market_history' not in st.session_state:
    st.session_state.market_history = []

tab = st.sidebar.selectbox("Select Tool", ["📈 Compounding Simulator", "📊 Cost Basis Tool", "💸 Return on Debt", "🛡️ Hedging Tool", "📊 Simulated vs. Actual", "📉 Market Monitoring", "�� Export Center"])

if tab == "📈 Compounding Simulator":
    st.title("📈 Compounding Simulator")

    # Input Parameters
    initial_shares = st.number_input("Initial Share Count", min_value=0, value=1000)
    cost_basis = st.number_input("Initial Purchase Cost Basis ($)", min_value=0.01, value=25.00)
    reinvest_price = st.number_input("Average Reinvestment Cost Per Share ($)", min_value=0.01, value=25.00)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", min_value=0.0, value=2.0)
    months = st.slider("Holding Period (Months)", 1, 120, 24)

    acct_type = st.selectbox("Account Type", ["Taxable", "Tax Deferred", "Non Taxable"])
    if acct_type == "Taxable":
        fed_tax = st.slider("Federal Tax Rate (%)", 0, 50, 20)
        state_tax = st.slider("State Tax Rate (%)", 0, 20, 5)
        defer_taxes = st.checkbox("Defer Taxes to Oct 15 Extension Deadline?")
        state = st.selectbox("Select State", ["Other", "CA", "NY", "TX", "UT", "FL"])
    else:
        fed_tax = 0
        state_tax = 0
        defer_taxes = False
        state = "N/A"

    reinvest_dividends = st.checkbox("Reinvest Dividends?")
    if reinvest_dividends:
        withdrawal = 0
        reinvest_percent = st.slider("Percent of Dividends to Reinvest (%)", 0, 100, 100)
    else:
        reinvest_percent = 0
        withdrawal = st.number_input("Withdraw this Dollar Amount Monthly ($)", min_value=0, value=2000)

    current_price = st.number_input("Current Price per Share ($)", min_value=0.01, value=25.0)
    view_mode = st.selectbox("How would you like to view the projection?", ["Monthly", "Yearly", "Total"])
    run = st.button("Run Simulation")

    if run:
        shares = initial_shares
        monthly_data = []
        total_dividends = 0
        total_reinvested = 0
        total_tax_paid = 0
        total_penalties = 0
        tax_due = 0

        today = datetime.today()
        start_month = today.month
        start_year = today.year

        for i in range(1, months + 1):
            current_month = (start_month + i - 1) % 12 or 12
            current_year = start_year + ((start_month + i - 1) // 12)
            date_label = f"{current_year}-{current_month:02d}"

            gross_div = shares * avg_dividend
            if acct_type == "Taxable":
                tax = (fed_tax + state_tax) / 100 * gross_div
                if defer_taxes:
                    tax_due += tax
                    tax = 0
            else:
                tax = 0

            net_div = gross_div - tax
            if reinvest_dividends:
                reinvest_amount = net_div * (reinvest_percent / 100)
            else:
                reinvest_amount = max(0, net_div - withdrawal)

            new_shares = reinvest_amount / reinvest_price
            shares += new_shares

            if defer_taxes and current_month == 10:
                penalty = tax_due * 0.03  # simplified penalty
                total_penalties += penalty
                total_tax_paid += tax_due
                tax_due = 0
            else:
                penalty = 0

            monthly_data.append({
                "Date": date_label,
                "Shares": round(shares, 4),
                "Net Dividends": round(net_div, 2),
                "Reinvested": round(reinvest_amount, 2),
                "New Shares": round(new_shares, 4),
                "Taxes Paid": round(tax, 2),
                "Cumulative Taxes": round(total_tax_paid, 2),
                "Penalties Paid": round(penalty, 2)
            })

            total_dividends += net_div
            total_reinvested += reinvest_amount

        df = pd.DataFrame(monthly_data)

        if view_mode == "Yearly":
            df['Year'] = pd.to_datetime(df['Date']).dt.year
            df = df.groupby("Year").agg({
                "Shares": "last",
                "Net Dividends": "sum",
                "Reinvested": "sum",
                "New Shares": "sum",
                "Taxes Paid": "sum",
                "Cumulative Taxes": "last",
                "Penalties Paid": "sum"
            }).reset_index()
        elif view_mode == "Total":
            df = pd.DataFrame([{
                "Shares": df["Shares"].iloc[-1],
                "Net Dividends": df["Net Dividends"].sum(),
                "Reinvested": df["Reinvested"].sum(),
                "New Shares": df["New Shares"].sum(),
                "Taxes Paid": df["Taxes Paid"].sum(),
                "Cumulative Taxes": df["Cumulative Taxes"].iloc[-1],
                "Penalties Paid": df["Penalties Paid"].sum()
            }])

        st.success(f"📈 Final Share Count: {shares:,.2f}")
        st.success(f"💸 Total Dividends Collected: ${total_dividends:,.2f}")
        st.success(f"🔁 Total Reinvested: ${total_reinvested:,.2f}")
        st.success(f"💰 Total Taxes Paid: ${total_tax_paid:,.2f}")
        st.success(f"⚠️ Total Penalties Paid: ${total_penalties:,.2f}")
        st.dataframe(df.style.format({
            "Shares": "{:,.2f}",
            "Net Dividends": "${:,.2f}",
            "Reinvested": "${:,.2f}",
            "New Shares": "{:,.2f}",
            "Taxes Paid": "${:,.2f}",
            "Cumulative Taxes": "${:,.2f}",
            "Penalties Paid": "${:,.2f}"
        }))

elif tab == "📊 Cost Basis Tool":
    st.title("📊 Cost Basis Tracker")

    if "blocks" not in st.session_state:
        st.session_state.blocks = []

    with st.form("add_block"):
        d = st.date_input("Date of Purchase", value=datetime.today())
        shares = st.number_input("Shares Purchased", min_value=0.0, step=1.0)
        price = st.number_input("Price per Share", min_value=0.0)
        submitted = st.form_submit_button("Add Entry")
        if submitted:
            st.session_state.blocks.append({"Date": d, "Shares": shares, "Price": price})

    if st.session_state.blocks:
        df = pd.DataFrame(st.session_state.blocks)
        df["Total"] = df["Shares"] * df["Price"]
        total_shares = df["Shares"].sum()
        total_cost = df["Total"].sum()
        avg_cost = total_cost / total_shares if total_shares else 0
        st.dataframe(df)
        st.markdown(f"**Total Shares:** {total_shares:,.2f}")
        st.markdown(f"**Average Cost Basis:** ${avg_cost:,.2f}")

elif tab == "💸 Return on Debt":
    st.title("💸 Return on Debt")

    debt_amount = st.number_input("Total Debt Incurred ($)", min_value=0.0, value=100000.0)
    monthly_principal = st.number_input("Monthly Principal Payment Toward Debt ($)", min_value=0.0, value=3000.0)
    interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=5.0)
    share_cost = st.number_input("Cost Basis per Share ($)", min_value=0.01, value=25.0)
    loan_term = st.number_input("Loan Term (Months)", min_value=1, value=36)
    compounding_term = st.number_input("Compounding Period (Months)", min_value=1, value=36)
    reinvest_price = st.number_input("Reinvestment Share Price ($)", min_value=0.01, value=30.0)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", min_value=0.01, value=2.00)
    expected_price = st.number_input("Estimated Price per Share at End ($)", min_value=0.01, value=40.0)

    run_debt = st.button("Calculate Return on Debt")

    if run_debt:
        initial_shares = debt_amount / share_cost
        monthly_interest = (debt_amount * (interest_rate / 100)) / 12
        total_interest = monthly_interest * loan_term
        monthly_income = initial_shares * avg_dividend
        reinvestable = max(monthly_income - monthly_principal, 0)
        new_shares = (reinvestable / reinvest_price) * compounding_term
        final_share_count = initial_shares + new_shares
        final_value = final_share_count * expected_price

        st.markdown(f"**Initial Shares Purchased:** {initial_shares:,.2f}")
        st.markdown(f"**Total Interest Paid:** ${total_interest:,.2f}")
        st.markdown(f"**New Shares Reinvested:** {new_shares:,.2f}")
        st.markdown(f"**Final Total Shares:** {final_share_count:,.2f}")
        st.markdown(f"**Portfolio Value at Exit Price:** ${final_value:,.2f}")

elif tab == "🛡️ Hedging Tool":
    st.title("🛡️ MSTR Hedging Tool")
    
    # Fetch MSTR data
    try:
        mstr = yf.Ticker("MSTR")
        current_mstr_price = mstr.info['regularMarketPrice']
        st.success(f"Current MSTR Price: ${current_mstr_price:,.2f}")
    except:
        current_mstr_price = st.number_input("MSTR Current Price ($)", min_value=0.01, value=500.0)
        st.warning("Could not fetch live MSTR price. Using manual input.")

    # User inputs with explanations
    st.subheader("Your Position Details")
    col1, col2 = st.columns(2)
    with col1:
        msty_holdings = st.number_input("Your MSTY Holdings (shares)", min_value=0)
        msty_price = st.number_input("Current MSTY Price ($)", min_value=0.01, value=25.0)
        expected_exit_price = st.number_input("Expected Bottom/Exit Price ($)", 
                                            min_value=0.01, 
                                            value=msty_price * 0.7,
                                            help="The price level at which you want maximum protection or expect to exit the position")
    with col2:
        correlation = st.slider("MSTR-MSTY Correlation", min_value=0.0, max_value=1.0, value=0.85,
                              help="Historical correlation between MSTR and MSTY prices. Higher values indicate stronger price relationship.")
        hedge_percentage = st.slider("Desired Hedge Percentage", min_value=0, max_value=100, value=50,
                                   help="Percentage of your position you want to hedge. 100% provides maximum protection but higher cost.")

    # Calculate initial position metrics
    msty_position_value = msty_holdings * msty_price
    hedge_value_needed = msty_position_value * (hedge_percentage / 100)
    
    # Calculate max loss with protection against division by zero
    if msty_position_value > 0:
        max_loss_without_hedge = msty_position_value - (msty_holdings * expected_exit_price)
        max_loss_percentage = f"-{(max_loss_without_hedge/msty_position_value*100):,.1f}%"
    else:
        max_loss_without_hedge = 0
        max_loss_percentage = "0%"

    # Display position summary
    st.subheader("Position Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("MSTY Position Value", f"${msty_position_value:,.2f}")
    with col2:
        st.metric("Hedge Value Needed", f"${hedge_value_needed:,.2f}")
    with col3:
        st.metric("Max Potential Loss", f"${max_loss_without_hedge:,.2f}",
                 delta=max_loss_percentage)

    # Detailed hedge calculation explanation
    st.subheader("Hedge Calculation Details")
    st.write("""
    The hedge is calculated using the following steps:
    1. Calculate total MSTY position value
    2. Determine hedge value needed based on hedge percentage
    3. Convert MSTY hedge value to MSTR equivalent using correlation
    4. Calculate number of put contracts needed (each contract = 100 shares)
    5. Determine optimal strike price based on expected exit price
    """)

    # Show the math
    mstr_equivalent = hedge_value_needed / (current_mstr_price * correlation)
    contracts_needed = mstr_equivalent / 100
    
    # Calculate equivalent MSTR price for expected exit
    mstr_equivalent_exit = expected_exit_price / msty_price * current_mstr_price
    
    st.write(f"""
    **Detailed Calculations:**
    - MSTY Position Value = {msty_holdings:,.0f} shares × ${msty_price:.2f} = ${msty_position_value:,.2f}
    - Hedge Value Needed = ${msty_position_value:,.2f} × {hedge_percentage}% = ${hedge_value_needed:,.2f}
    - MSTR Equivalent Shares = ${hedge_value_needed:,.2f} ÷ (${current_mstr_price:.2f} × {correlation:.2f}) = {mstr_equivalent:.2f} shares
    - Contracts Needed = {mstr_equivalent:.2f} shares ÷ 100 shares/contract = {contracts_needed:.2f} contracts
    - Equivalent MSTR Exit Price = ${current_mstr_price:.2f} × (${expected_exit_price:.2f} ÷ ${msty_price:.2f}) = ${mstr_equivalent_exit:.2f}
    """)

    # Fetch options chain
    if st.button("Fetch Put Options"):
        try:
            # Get options expiration dates
            exp_dates = mstr.options
            
            if exp_dates:
                # Convert expiration dates to more readable format and add days until expiry
                exp_dates_info = []
                for date in exp_dates:
                    exp_date = datetime.strptime(date, '%Y-%m-%d')
                    days_to_exp = (exp_date - datetime.now()).days
                    exp_dates_info.append({
                        'date': date,
                        'days': days_to_exp,
                        'display': f"{date} ({days_to_exp} days)"
                    })
                
                selected_date = st.selectbox(
                    "Select Expiration Date",
                    options=[info['date'] for info in exp_dates_info],
                    format_func=lambda x: next(info['display'] for info in exp_dates_info if info['date'] == x)
                )
                
                # Get options chain for selected date
                opts = mstr.option_chain(selected_date)
                puts_df = opts.puts.copy()
                
                # Calculate relevant fields
                puts_df['Strike_Diff'] = abs(puts_df['strike'] - mstr_equivalent_exit)
                puts_df['Strike_Pct'] = (puts_df['strike'] - current_mstr_price) / current_mstr_price * 100
                puts_df = puts_df.sort_values('Strike_Diff')
                
                # Find optimal strikes based on different strategies
                try:
                    target_put = puts_df.iloc[0]  # Closest to target exit price
                except IndexError:
                    st.error("No put options data available for the selected date.")
                    st.stop()

                # Find ATM put (closest to current price)
                puts_df['Current_Price_Diff'] = abs(puts_df['strike'] - current_mstr_price)
                atm_put = puts_df.sort_values('Current_Price_Diff').iloc[0]
                
                # Find OTM puts
                otm_puts = puts_df[puts_df['strike'] < current_mstr_price].sort_values('strike', ascending=False)
                
                st.subheader("Hedge Recommendations")
                
                # Calculate total hedge cost for different strategies
                def calculate_hedge_cost(strike_price, option_price):
                    contracts = round(contracts_needed, 2)
                    total_cost = contracts * option_price * 100
                    max_protection = contracts * strike_price * 100
                    protection_at_exit = contracts * max(0, strike_price - mstr_equivalent_exit) * 100
                    return contracts, total_cost, max_protection, protection_at_exit
                
                # Display recommendations for different strike prices
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Target Exit Strategy**")
                    target_contracts, target_cost, target_protection, target_exit_prot = calculate_hedge_cost(target_put['strike'], target_put['ask'])
                    st.write(f"""
                    - Strike Price: ${target_put['strike']:,.2f}
                    - Contracts Needed: {target_contracts:.2f}
                    - Premium per Contract: ${target_put['ask']:,.2f}
                    - Total Cost: ${target_cost:,.2f}
                    - Protection at Exit: ${target_exit_prot:,.2f}
                    """)
                
                with col2:
                    st.write("**At-the-Money (ATM) Strategy**")
                    atm_contracts, atm_cost, atm_protection, atm_exit_prot = calculate_hedge_cost(atm_put['strike'], atm_put['ask'])
                    st.write(f"""
                    - Strike Price: ${atm_put['strike']:,.2f}
                    - Contracts Needed: {atm_contracts:.2f}
                    - Premium per Contract: ${atm_put['ask']:,.2f}
                    - Total Cost: ${atm_cost:,.2f}
                    - Protection at Exit: ${atm_exit_prot:,.2f}
                    """)
                
                with col3:
                    if not otm_puts.empty:
                        st.write("**Out-of-the-Money (OTM) Strategy**")
                        otm_put = otm_puts.iloc[0]
                        otm_contracts, otm_cost, otm_protection, otm_exit_prot = calculate_hedge_cost(otm_put['strike'], otm_put['ask'])
                        st.write(f"""
                        - Strike Price: ${otm_put['strike']:,.2f}
                        - Contracts Needed: {otm_contracts:.2f}
                        - Premium per Contract: ${otm_put['ask']:,.2f}
                        - Total Cost: ${otm_cost:,.2f}
                        - Protection at Exit: ${otm_exit_prot:,.2f}
                        """)
                
                # Display full options chain with enhanced information
                st.subheader("Available Put Options")
                display_cols = ['strike', 'Strike_Pct', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
                display_df = puts_df[display_cols].head(10).copy()
                display_df.columns = ['Strike', '% From Current', 'Last Price', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Implied Volatility']
                
                st.dataframe(display_df.style.format({
                    'Strike': '${:,.2f}',
                    '% From Current': '{:,.1f}%',
                    'Last Price': '${:,.2f}',
                    'Bid': '${:,.2f}',
                    'Ask': '${:,.2f}',
                    'Volume': '{:,.0f}',
                    'Open Interest': '{:,.0f}',
                    'Implied Volatility': '{:.1%}'
                }))
                
                # Hedge visualization
                st.subheader("Hedge Visualization")
                fig = go.Figure()
                
                # Add current position value
                fig.add_hline(y=msty_position_value, line_dash="dash", line_color="green",
                            annotation_text="Current Position Value")
                
                # Add expected exit price line
                fig.add_hline(y=msty_holdings * expected_exit_price, line_dash="dash", line_color="red",
                            annotation_text="Expected Exit Value")
                
                # Add hedged position scenarios
                price_range = np.linspace(current_mstr_price * 0.5, current_mstr_price * 1.5, 100)
                
                # Target exit hedge scenario
                target_hedged_values = [msty_position_value - max(0, (target_put['strike'] - p) * mstr_equivalent)
                                      for p in price_range]
                fig.add_trace(go.Scatter(x=price_range, y=target_hedged_values,
                                       name=f"Target Exit Hedged (Strike: ${target_put['strike']:,.2f})"))
                
                # ATM hedge scenario
                atm_hedged_values = [msty_position_value - max(0, (atm_put['strike'] - p) * mstr_equivalent)
                                   for p in price_range]
                fig.add_trace(go.Scatter(x=price_range, y=atm_hedged_values,
                                       name=f"ATM Hedged (Strike: ${atm_put['strike']:,.2f})"))
                
                # OTM hedge scenario if available
                if not otm_puts.empty:
                    otm_hedged_values = [msty_position_value - max(0, (otm_put['strike'] - p) * mstr_equivalent)
                                       for p in price_range]
                    fig.add_trace(go.Scatter(x=price_range, y=otm_hedged_values,
                                           name=f"OTM Hedged (Strike: ${otm_put['strike']:,.2f})"))
                
                fig.update_layout(
                    title="Position Value vs MSTR Price",
                    xaxis_title="MSTR Price ($)",
                    yaxis_title="Position Value ($)",
                    hovermode="x unified"
                )
                st.plotly_chart(fig)
                
                # Add cost-benefit analysis
                st.subheader("Cost-Benefit Analysis")
                analysis_df = pd.DataFrame({
                    'Strategy': ['Target Exit', 'ATM', 'OTM'] if not otm_puts.empty else ['Target Exit', 'ATM'],
                    'Strike Price': [target_put['strike'], atm_put['strike'], otm_put['strike']] if not otm_puts.empty else [target_put['strike'], atm_put['strike']],
                    'Total Cost': [target_cost, atm_cost, otm_cost] if not otm_puts.empty else [target_cost, atm_cost],
                    'Protection at Exit': [target_exit_prot, atm_exit_prot, otm_exit_prot] if not otm_puts.empty else [target_exit_prot, atm_exit_prot],
                    'Cost % of Position': [target_cost/msty_position_value*100, atm_cost/msty_position_value*100, otm_cost/msty_position_value*100] if not otm_puts.empty else [target_cost/msty_position_value*100, atm_cost/msty_position_value*100],
                    'Protection % at Exit': [target_exit_prot/max_loss_without_hedge*100, atm_exit_prot/max_loss_without_hedge*100, otm_exit_prot/max_loss_without_hedge*100] if not otm_puts.empty else [target_exit_prot/max_loss_without_hedge*100, atm_exit_prot/max_loss_without_hedge*100]
                })
                
                st.dataframe(analysis_df.style.format({
                    'Strike Price': '${:,.2f}',
                    'Total Cost': '${:,.2f}',
                    'Protection at Exit': '${:,.2f}',
                    'Cost % of Position': '{:.1f}%',
                    'Protection % at Exit': '{:.1f}%'
                }))
                
            else:
                st.error("No options data available for MSTR")
        except Exception as e:
            st.error(f"Error fetching options data: {str(e)}")
            st.info("If the error persists, you may need to wait a few minutes and try again.")

elif tab == "📊 Simulated vs. Actual":
    st.title("📊 Simulated vs. Actual Performance")

    # Add actual performance data
    st.subheader("Add Actual Performance Data")
    with st.form("add_actual_performance"):
        date = st.date_input("Date", value=datetime.today())
        actual_shares = st.number_input("Actual Shares", min_value=0.0, step=1.0)
        actual_dividends = st.number_input("Actual Dividends Received ($)", min_value=0.0, step=1.0)
        actual_reinvested = st.number_input("Amount Reinvested ($)", min_value=0.0, step=1.0)
        reinvestment_price = st.number_input("Reinvestment Price per Share ($)", min_value=0.01, step=0.01)
        submitted = st.form_submit_button("Add Entry")
        
        if submitted:
            new_shares_from_reinvestment = actual_reinvested / reinvestment_price if reinvestment_price > 0 else 0
            st.session_state.actual_performance.append({
                "Date": date.strftime("%Y-%m"),
                "Actual_Shares": actual_shares,
                "Actual_Dividends": actual_dividends,
                "Actual_Reinvested": actual_reinvested,
                "Reinvestment_Price": reinvestment_price,
                "New_Shares_From_Reinvestment": new_shares_from_reinvestment
            })

    # View selection
    view_mode = st.selectbox("View Mode", ["Monthly", "Yearly", "Total"])
    
    if st.session_state.simulation_results is not None and len(st.session_state.actual_performance) > 0:
        # Create comparison DataFrame
        actual_df = pd.DataFrame(st.session_state.actual_performance)
        sim_df = st.session_state.simulation_results.copy()
        
        # Merge simulation and actual data
        comparison_df = pd.merge(sim_df, actual_df, on="Date", how="outer")
        
        if view_mode == "Yearly":
            comparison_df['Year'] = pd.to_datetime(comparison_df['Date']).dt.year
            comparison_df = comparison_df.groupby("Year").agg({
                "Shares": "last",
                "Net_Dividends": "sum",
                "Reinvested": "sum",
                "Actual_Shares": "last",
                "Actual_Dividends": "sum",
                "Actual_Reinvested": "sum",
                "Reinvestment_Price": "mean",
                "New_Shares_From_Reinvestment": "sum"
            }).reset_index()
        elif view_mode == "Total":
            comparison_df = pd.DataFrame([{
                "Shares": comparison_df["Shares"].iloc[-1],
                "Net_Dividends": comparison_df["Net_Dividends"].sum(),
                "Reinvested": comparison_df["Reinvested"].sum(),
                "Actual_Shares": comparison_df["Actual_Shares"].iloc[-1],
                "Actual_Dividends": comparison_df["Actual_Dividends"].sum(),
                "Actual_Reinvested": comparison_df["Actual_Reinvested"].sum(),
                "Reinvestment_Price": comparison_df["Reinvestment_Price"].mean(),
                "New_Shares_From_Reinvestment": comparison_df["New_Shares_From_Reinvestment"].sum()
            }])
        
        # Calculate differences
        comparison_df["Share_Difference"] = comparison_df["Actual_Shares"] - comparison_df["Shares"]
        comparison_df["Dividend_Difference"] = comparison_df["Actual_Dividends"] - comparison_df["Net_Dividends"]
        comparison_df["Reinvested_Difference"] = comparison_df["Actual_Reinvested"] - comparison_df["Reinvested"]
        
        # Calculate weighted average reinvestment price
        total_reinvested = comparison_df["Actual_Reinvested"].sum()
        total_new_shares = comparison_df["New_Shares_From_Reinvestment"].sum()
        if total_new_shares > 0:
            weighted_avg_price = total_reinvested / total_new_shares
        else:
            weighted_avg_price = 0

        # Display comparison metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            share_diff = comparison_df["Share_Difference"].iloc[-1]
            st.metric("Share Difference", f"{share_diff:,.2f}", 
                     delta=f"{(share_diff/comparison_df['Shares'].iloc[-1]*100):,.1f}%" if comparison_df['Shares'].iloc[-1] > 0 else "0%")
        with col2:
            div_diff = comparison_df["Dividend_Difference"].sum()
            st.metric("Dividend Difference", f"${div_diff:,.2f}", 
                     delta=f"{(div_diff/comparison_df['Net_Dividends'].sum()*100):,.1f}%" if comparison_df['Net_Dividends'].sum() > 0 else "0%")
        with col3:
            reinv_diff = comparison_df["Reinvested_Difference"].sum()
            st.metric("Reinvestment Difference", f"${reinv_diff:,.2f}", 
                     delta=f"{(reinv_diff/comparison_df['Reinvested'].sum()*100):,.1f}%" if comparison_df['Reinvested'].sum() > 0 else "0%")
        with col4:
            st.metric("Weighted Avg Reinvestment Price", f"${weighted_avg_price:,.2f}")

        # Display reinvestment summary
        st.subheader("Reinvestment Summary")
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            st.metric("Total Amount Reinvested", f"${total_reinvested:,.2f}")
        with summary_col2:
            st.metric("Total Shares from Reinvestment", f"{total_new_shares:,.2f}")
        with summary_col3:
            st.metric("Weighted Avg Reinvestment Price", f"${weighted_avg_price:,.2f}")
        
        # Display detailed comparison table
        st.subheader("Detailed Comparison")
        st.dataframe(comparison_df.style.format({
            "Shares": "{:,.2f}",
            "Net_Dividends": "${:,.2f}",
            "Reinvested": "${:,.2f}",
            "Actual_Shares": "{:,.2f}",
            "Actual_Dividends": "${:,.2f}",
            "Actual_Reinvested": "${:,.2f}",
            "Reinvestment_Price": "${:,.2f}",
            "New_Shares_From_Reinvestment": "{:,.2f}",
            "Share_Difference": "{:,.2f}",
            "Dividend_Difference": "${:,.2f}",
            "Reinvested_Difference": "${:,.2f}"
        }))
        
        # Visualization
        if view_mode != "Total":
            # Share Growth Comparison
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=comparison_df['Year'] if view_mode == "Yearly" else comparison_df['Date'],
                                    y=comparison_df['Shares'],
                                    name='Simulated Shares',
                                    line=dict(color='blue')))
            fig1.add_trace(go.Scatter(x=comparison_df['Year'] if view_mode == "Yearly" else comparison_df['Date'],
                                    y=comparison_df['Actual_Shares'],
                                    name='Actual Shares',
                                    line=dict(color='green')))
            fig1.update_layout(title='Share Growth Comparison',
                             xaxis_title='Time Period',
                             yaxis_title='Number of Shares')
            st.plotly_chart(fig1)
            
            # Dividend Comparison
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=comparison_df['Year'] if view_mode == "Yearly" else comparison_df['Date'],
                                y=comparison_df['Net_Dividends'],
                                name='Simulated Dividends'))
            fig2.add_trace(go.Bar(x=comparison_df['Year'] if view_mode == "Yearly" else comparison_df['Date'],
                                y=comparison_df['Actual_Dividends'],
                                name='Actual Dividends'))
            fig2.update_layout(title='Dividend Comparison',
                             xaxis_title='Time Period',
                             yaxis_title='Dividends ($)',
                             barmode='group')
            st.plotly_chart(fig2)
    else:
        if st.session_state.simulation_results is None:
            st.warning("Please run a simulation first in the Compounding Simulator tab.")
        if len(st.session_state.actual_performance) == 0:
            st.warning("Please add actual performance data to compare.")

elif tab == "📉 Market Monitoring":
    st.title("📉 Market Monitoring")
    
    # Create tabs for different monitoring views
    monitor_tab = st.tabs(["MSTR Price", "Options Analysis", "Covered Call Market"])
    
    with monitor_tab[0]:  # MSTR Price Tab
        # Fetch MSTR data
        try:
            mstr = yf.Ticker("MSTR")
            current_mstr_price = mstr.info['regularMarketPrice']
            prev_close = mstr.info['previousClose']
            price_change = current_mstr_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MSTR Current Price", 
                         f"${current_mstr_price:,.2f}",
                         f"{price_change:,.2f} ({price_change_pct:,.1f}%)")
            with col2:
                st.metric("24h Volume", 
                         f"{mstr.info['volume']:,.0f}",
                         f"{((mstr.info['volume']/mstr.info['averageVolume'])-1)*100:,.1f}% vs Avg")
            with col3:
                st.metric("Market Cap",
                         f"${mstr.info['marketCap']/1e9:,.2f}B")
            
            # Historical price chart
            st.subheader("MSTR Price History")
            timeframes = {
                "1D": "1d",
                "5D": "5d",
                "1M": "1mo",
                "3M": "3mo",
                "6M": "6mo",
                "YTD": "ytd",
                "1Y": "1y",
                "5Y": "5y"
            }
            selected_timeframe = st.selectbox("Select Timeframe", list(timeframes.keys()))
            
            hist = mstr.history(period=timeframes[selected_timeframe], interval="1d")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='MSTR'
            ))
            fig.update_layout(
                title=f"MSTR Price ({selected_timeframe})",
                yaxis_title="Price ($)",
                xaxis_title="Date",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume chart
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Bar(
                x=hist.index,
                y=hist['Volume'],
                name='Volume'
            ))
            fig_volume.update_layout(
                title="Trading Volume",
                yaxis_title="Volume",
                xaxis_title="Date",
                height=300
            )
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Key statistics
            st.subheader("Key Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("52 Week High", f"${mstr.info['fiftyTwoWeekHigh']:,.2f}")
                st.metric("50 Day Avg", f"${mstr.info['fiftyDayAverage']:,.2f}")
                st.metric("Beta", f"{mstr.info.get('beta', 'N/A')}")
            with col2:
                st.metric("52 Week Low", f"${mstr.info['fiftyTwoWeekLow']:,.2f}")
                st.metric("200 Day Avg", f"${mstr.info['twoHundredDayAverage']:,.2f}")
                st.metric("Shares Outstanding", f"{mstr.info['sharesOutstanding']:,.0f}")
            with col3:
                st.metric("52 Week Range", 
                         f"${mstr.info['fiftyTwoWeekLow']:,.2f} - ${mstr.info['fiftyTwoWeekHigh']:,.2f}")
                st.metric("Avg Volume", f"{mstr.info['averageVolume']:,.0f}")
                st.metric("Float", f"{mstr.info.get('floatShares', 'N/A'):,.0f}")
            
        except Exception as e:
            st.error(f"Error fetching MSTR data: {str(e)}")
            st.info("If the error persists, you may need to wait a few minutes and try again.")
    
    with monitor_tab[1]:  # Options Analysis Tab
        st.subheader("Options Market Analysis")
        
        try:
            # Fetch all available expiration dates
            exp_dates = mstr.options
            
            # Options market overview metrics
            total_call_oi = 0
            total_put_oi = 0
            total_call_volume = 0
            total_put_volume = 0
            put_call_ratios = []
            
            # Collect data for all expiration dates
            options_data = []
            for date in exp_dates:
                opt_chain = mstr.option_chain(date)
                
                # Calculate metrics for this expiration
                calls_oi = opt_chain.calls['openInterest'].sum()
                puts_oi = opt_chain.puts['openInterest'].sum()
                calls_vol = opt_chain.calls['volume'].sum()
                puts_vol = opt_chain.puts['volume'].sum()
                
                total_call_oi += calls_oi
                total_put_oi += puts_oi
                total_call_volume += calls_vol
                total_put_volume += puts_vol
                
                # Calculate Put/Call ratio
                pc_ratio_oi = puts_oi / calls_oi if calls_oi > 0 else 0
                pc_ratio_vol = puts_vol / calls_vol if calls_vol > 0 else 0
                
                options_data.append({
                    'Expiration': date,
                    'Calls_OI': calls_oi,
                    'Puts_OI': puts_oi,
                    'Calls_Volume': calls_vol,
                    'Puts_Volume': puts_vol,
                    'PC_Ratio_OI': pc_ratio_oi,
                    'PC_Ratio_Volume': pc_ratio_vol
                })
            
            # Display overall options market metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Call Open Interest", f"{total_call_oi:,.0f}")
                st.metric("Total Put Open Interest", f"{total_put_oi:,.0f}")
            with col2:
                st.metric("Total Call Volume", f"{total_call_volume:,.0f}")
                st.metric("Total Put Volume", f"{total_put_volume:,.0f}")
            with col3:
                overall_pc_ratio_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                overall_pc_ratio_vol = total_put_volume / total_call_volume if total_call_volume > 0 else 0
                st.metric("Put/Call Ratio (OI)", f"{overall_pc_ratio_oi:.2f}")
                st.metric("Put/Call Ratio (Volume)", f"{overall_pc_ratio_vol:.2f}")
            
            # Options Chain Analysis
            st.subheader("Options Chain Analysis by Expiration")
            
            # Convert to DataFrame for display
            options_df = pd.DataFrame(options_data)
            st.dataframe(options_df.style.format({
                'Calls_OI': '{:,.0f}',
                'Puts_OI': '{:,.0f}',
                'Calls_Volume': '{:,.0f}',
                'Puts_Volume': '{:,.0f}',
                'PC_Ratio_OI': '{:.2f}',
                'PC_Ratio_Volume': '{:.2f}'
            }))
            
            # Detailed Options Analysis for selected expiration
            st.subheader("Detailed Options Analysis")
            selected_exp = st.selectbox("Select Expiration Date", exp_dates)
            
            if selected_exp:
                opt_chain = mstr.option_chain(selected_exp)
                
                # Analyze call options distribution
                calls_df = opt_chain.calls.copy()
                calls_df['moneyness'] = (calls_df['strike'] - current_mstr_price) / current_mstr_price
                
                # Plot options distribution
                fig = go.Figure()
                
                # Call options distribution
                fig.add_trace(go.Bar(
                    x=calls_df['strike'],
                    y=calls_df['openInterest'],
                    name='Calls Open Interest',
                    marker_color='green',
                    opacity=0.6
                ))
                
                # Put options distribution
                puts_df = opt_chain.puts.copy()
                fig.add_trace(go.Bar(
                    x=puts_df['strike'],
                    y=puts_df['openInterest'],
                    name='Puts Open Interest',
                    marker_color='red',
                    opacity=0.6
                ))
                
                # Add current price line
                fig.add_vline(x=current_mstr_price, line_dash="dash", line_color="blue",
                            annotation_text="Current Price")
                
                fig.update_layout(
                    title=f"Options Open Interest Distribution ({selected_exp})",
                    xaxis_title="Strike Price ($)",
                    yaxis_title="Open Interest",
                    barmode='overlay'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display options chain details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Calls Analysis")
                    calls_analysis = calls_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']]
                    st.dataframe(calls_analysis.style.format({
                        'strike': '${:,.2f}',
                        'lastPrice': '${:,.2f}',
                        'volume': '{:,.0f}',
                        'openInterest': '{:,.0f}',
                        'impliedVolatility': '{:.1%}'
                    }))
                
                with col2:
                    st.subheader("Puts Analysis")
                    puts_analysis = puts_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']]
                    st.dataframe(puts_analysis.style.format({
                        'strike': '${:,.2f}',
                        'lastPrice': '${:,.2f}',
                        'volume': '{:,.0f}',
                        'openInterest': '{:,.0f}',
                        'impliedVolatility': '{:.1%}'
                    }))
        
        except Exception as e:
            st.error(f"Error analyzing options data: {str(e)}")
    
    with monitor_tab[2]:  # Covered Call Market Tab
        st.subheader("Covered Call Market Analysis")
        
        # List of ETFs/Funds known to write covered calls on MSTR
        covered_call_funds = {
            'QYLD': 'Global X NASDAQ-100 Covered Call ETF',
            'XYLD': 'Global X S&P 500 Covered Call ETF',
            'JEPI': 'JPMorgan Equity Premium Income ETF'
            # Add more funds as they become available
        }
        
        try:
            # Analyze each fund's potential MSTR exposure
            fund_data = []
            
            for symbol, name in covered_call_funds.items():
                fund = yf.Ticker(symbol)
                
                try:
                    aum = fund.info.get('totalAssets', 0)
                    volume = fund.info.get('volume', 0)
                    
                    fund_data.append({
                        'Symbol': symbol,
                        'Name': name,
                        'AUM': aum,
                        'Daily Volume': volume
                    })
                except:
                    continue
            
            if fund_data:
                funds_df = pd.DataFrame(fund_data)
                st.dataframe(funds_df.style.format({
                    'AUM': '${:,.0f}',
                    'Daily Volume': '{:,.0f}'
                }))
            
            # Covered Call Market Metrics
            st.subheader("Covered Call Market Metrics")
            
            # Calculate metrics for near-the-money calls
            try:
                current_price = mstr.info['regularMarketPrice']
                next_exp = mstr.options[0]  # Nearest expiration
                calls = mstr.option_chain(next_exp).calls
                
                # Find near-the-money calls (within 5% of current price)
                ntm_calls = calls[
                    (calls['strike'] >= current_price * 0.95) &
                    (calls['strike'] <= current_price * 1.05)
                ]
                
                # Calculate covered call market metrics
                total_ntm_premium = (ntm_calls['lastPrice'] * ntm_calls['openInterest']).sum()
                avg_call_premium = ntm_calls['lastPrice'].mean()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Near-the-Money Call Premium", f"${avg_call_premium:,.2f}")
                    st.metric("Total Premium Value", f"${total_ntm_premium:,.2f}")
                with col2:
                    st.metric("Active Covered Calls", f"{ntm_calls['openInterest'].sum():,.0f}")
                    st.metric("Daily Volume", f"{ntm_calls['volume'].sum():,.0f}")
                
                # Premium Yield Analysis
                if avg_call_premium > 0:
                    monthly_yield = (avg_call_premium / current_price) * 100
                    annual_yield = monthly_yield * 12
                    
                    st.metric("Estimated Monthly Yield", f"{monthly_yield:.1f}%")
                    st.metric("Estimated Annual Yield", f"{annual_yield:.1f}%")
                
            except Exception as e:
                st.error(f"Error calculating covered call metrics: {str(e)}")
            
            # Historical Trends Analysis
            st.subheader("Market Convergence/Divergence Analysis")
            
            # Update market history
            update_market_history()
            
            if len(st.session_state.market_history) > 1:
                history_df = pd.DataFrame(st.session_state.market_history)
                
                # Create convergence/divergence plot
                fig_conv = go.Figure()
                
                # Plot covered call ratio trend
                fig_conv.add_trace(go.Scatter(
                    x=history_df['date'],
                    y=history_df['covered_call_ratio'],
                    name='Covered Call Ratio',
                    line=dict(color='blue')
                ))
                
                # Plot market activity ratio trend
                fig_conv.add_trace(go.Scatter(
                    x=history_df['date'],
                    y=history_df['market_activity_ratio'],
                    name='Market Activity Ratio',
                    line=dict(color='red')
                ))
                
                # Calculate and plot convergence/divergence
                history_df['convergence'] = history_df['covered_call_ratio'] - history_df['market_activity_ratio']
                fig_conv.add_trace(go.Bar(
                    x=history_df['date'],
                    y=history_df['convergence'],
                    name='Convergence/Divergence',
                    marker_color='green',
                    opacity=0.3
                ))
                
                fig_conv.update_layout(
                    title="Options Market Convergence/Divergence Analysis",
                    xaxis_title="Date",
                    yaxis_title="Ratio",
                    height=400,
                    showlegend=True
                )
                st.plotly_chart(fig_conv, use_container_width=True)
                
                # Market trend metrics
                st.subheader("Market Trend Metrics")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Calculate trend indicators
                    latest_conv = history_df['convergence'].iloc[-1]
                    conv_change = latest_conv - history_df['convergence'].iloc[-2]
                    
                    st.metric(
                        "Current Convergence",
                        f"{latest_conv:.3f}",
                        f"{conv_change:+.3f}"
                    )
                    
                    # Market pressure indicator
                    pressure = "Increasing" if conv_change > 0 else "Decreasing"
                    st.metric(
                        "Market Pressure",
                        pressure,
                        f"{abs(conv_change/latest_conv)*100:.1f}% change" if latest_conv != 0 else "N/A"
                    )
                
                with col2:
                    # Calculate moving averages
                    history_df['ma5'] = history_df['convergence'].rolling(5).mean()
                    history_df['ma10'] = history_df['convergence'].rolling(10).mean()
                    
                    latest_ma5 = history_df['ma5'].iloc[-1]
                    latest_ma10 = history_df['ma10'].iloc[-1]
                    
                    st.metric(
                        "5-Day Moving Average",
                        f"{latest_ma5:.3f}" if not pd.isna(latest_ma5) else "N/A"
                    )
                    st.metric(
                        "10-Day Moving Average",
                        f"{latest_ma10:.3f}" if not pd.isna(latest_ma10) else "N/A"
                    )
                
                # Historical data table
                st.subheader("Historical Data")
                display_df = history_df[[
                    'date', 'price', 'covered_call_ratio', 'market_activity_ratio', 'convergence'
                ]].copy()
                st.dataframe(display_df.style.format({
                    'price': '${:,.2f}',
                    'covered_call_ratio': '{:.3f}',
                    'market_activity_ratio': '{:.3f}',
                    'convergence': '{:.3f}'
                }))
            else:
                st.info("Collecting market history data. Check back tomorrow for trend analysis.")
            
        except Exception as e:
            st.error(f"Error analyzing covered call market: {str(e)}")

def update_market_history():
    """Update market history with current metrics"""
    try:
        mstr = yf.Ticker("MSTR")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get options data
        exp_dates = mstr.options
        total_call_oi = 0
        total_put_oi = 0
        total_call_volume = 0
        total_put_volume = 0
        ntm_call_oi = 0
        ntm_call_volume = 0
        
        current_price = mstr.info['regularMarketPrice']
        
        for date in exp_dates:
            opt_chain = mstr.option_chain(date)
            
            # Total market metrics
            total_call_oi += opt_chain.calls['openInterest'].sum()
            total_put_oi += opt_chain.puts['openInterest'].sum()
            total_call_volume += opt_chain.calls['volume'].sum()
            total_put_volume += opt_chain.puts['volume'].sum()
            
            # Near-the-money call metrics
            ntm_calls = opt_chain.calls[
                (opt_chain.calls['strike'] >= current_price * 0.95) &
                (opt_chain.calls['strike'] <= current_price * 1.05)
            ]
            ntm_call_oi += ntm_calls['openInterest'].sum()
            ntm_call_volume += ntm_calls['volume'].sum()
        
        # Calculate market ratios
        covered_call_ratio = ntm_call_oi / total_call_oi if total_call_oi > 0 else 0
        market_activity_ratio = ntm_call_volume / total_call_volume if total_call_volume > 0 else 0
        
        # Store metrics
        metrics = {
            'date': current_date,
            'price': current_price,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'total_call_volume': total_call_volume,
            'total_put_volume': total_put_volume,
            'ntm_call_oi': ntm_call_oi,
            'ntm_call_volume': ntm_call_volume,
            'covered_call_ratio': covered_call_ratio,
            'market_activity_ratio': market_activity_ratio
        }
        
        # Add to history if it's a new day
        if not st.session_state.market_history or st.session_state.market_history[-1]['date'] != current_date:
            st.session_state.market_history.append(metrics)
            
            # Keep only last 30 days of history
            if len(st.session_state.market_history) > 30:
                st.session_state.market_history.pop(0)
                
    except Exception as e:
        st.error(f"Error updating market history: {str(e)}")
