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

tab = st.sidebar.selectbox("Select Tool", ["📈 Compounding Simulator", "📊 Cost Basis Tool", "💸 Return on Debt", "🛡️ Hedging Tool", "📊 Simulated vs. Actual", "📉 Market Monitoring", "📤 Export Center"])

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
        st.session_state.simulation_results = df.copy()

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
                "Net Dividends": "sum",
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
                "Net Dividends": comparison_df["Net Dividends"].sum(),
                "Reinvested": comparison_df["Reinvested"].sum(),
                "Actual_Shares": comparison_df["Actual_Shares"].iloc[-1],
                "Actual_Dividends": comparison_df["Actual_Dividends"].sum(),
                "Actual_Reinvested": comparison_df["Actual_Reinvested"].sum(),
                "Reinvestment_Price": comparison_df["Reinvestment_Price"].mean(),
                "New_Shares_From_Reinvestment": comparison_df["New_Shares_From_Reinvestment"].sum()
            }])
        
        # Calculate differences
        comparison_df["Share_Difference"] = comparison_df["Actual_Shares"] - comparison_df["Shares"]
        comparison_df["Dividend_Difference"] = comparison_df["Actual_Dividends"] - comparison_df["Net Dividends"]
        comparison_df["Reinvested_Difference"] = comparison_df["Actual_Reinvested"] - comparison_df["Reinvested"]
        
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
            avg_reinv_price = comparison_df["Reinvestment_Price"].mean()
            st.metric("Avg Reinvestment Price", f"${avg_reinv_price:,.2f}")

        # Calculate weighted average reinvestment price
        total_reinvested = comparison_df["Actual_Reinvested"].sum()
        total_new_shares = comparison_df["New_Shares_From_Reinvestment"].sum()
        if total_new_shares > 0:
            weighted_avg_price = total_reinvested / total_new_shares
        else:
            weighted_avg_price = 0

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
            "Net Dividends": "${:,.2f}",
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
                                y=comparison_df['Net Dividends'],
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
    st.title("📉 MSTY Market Monitor")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.today())
    
    # Manual price input section
    st.subheader("Add Daily Price Data")
    with st.form("add_price_data"):
        date = st.date_input("Date", value=datetime.today())
        price = st.number_input("MSTY Price ($)", min_value=0.01, step=0.01)
        dividend = st.number_input("Dividend Amount ($)", min_value=0.0, step=0.01)
        volume = st.number_input("Trading Volume", min_value=0, step=1)
        submitted = st.form_submit_button("Add Entry")
        
        if submitted:
            st.session_state.market_data.append({
                "Date": date,
                "Price": price,
                "Dividend": dividend,
                "Volume": volume
            })
            if dividend > 0:
                st.session_state.last_dividend = {
                    "Date": date,
                    "Amount": dividend
                }
    
    # Clear data button
    if st.button("Clear All Market Data"):
        st.session_state.market_data = []
        st.session_state.last_dividend = None
        st.success("Market data cleared successfully!")
    
    # Display market data if available
    if st.session_state.market_data:
        df = pd.DataFrame(st.session_state.market_data)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        
        # Calculate metrics
        latest_price = df["Price"].iloc[-1]
        prev_price = df["Price"].iloc[-2] if len(df) > 1 else df["Price"].iloc[-1]
        price_change = latest_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        # Display current metrics
        st.subheader("Current Market Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${latest_price:.2f}", 
                     f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
        with col2:
            if st.session_state.last_dividend:
                st.metric("Last Dividend", 
                         f"${st.session_state.last_dividend['Amount']:.2f}",
                         f"Paid on {st.session_state.last_dividend['Date'].strftime('%Y-%m-%d')}")
            else:
                st.metric("Last Dividend", "No data", "")
        with col3:
            avg_volume = df["Volume"].mean()
            st.metric("Average Daily Volume", f"{avg_volume:,.0f}")
        
        # Price chart
        st.subheader("Price History")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df["Date"], y=df["Price"],
                                mode='lines+markers',
                                name='Price',
                                line=dict(color='blue')))
        fig1.update_layout(title='MSTY Price History',
                          xaxis_title='Date',
                          yaxis_title='Price ($)')
        st.plotly_chart(fig1)
        
        # Volume chart
        st.subheader("Volume History")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df["Date"], y=df["Volume"],
                            name='Volume'))
        fig2.update_layout(title='Trading Volume',
                          xaxis_title='Date',
                          yaxis_title='Volume')
        st.plotly_chart(fig2)
        
        # Dividend history
        st.subheader("Dividend History")
        dividend_df = df[df["Dividend"] > 0].copy()
        if not dividend_df.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=dividend_df["Date"], y=dividend_df["Dividend"],
                                name='Dividend Amount'))
            fig3.update_layout(title='Dividend Payments',
                             xaxis_title='Date',
                             yaxis_title='Amount ($)')
            st.plotly_chart(fig3)
        
        # Display raw data table
        st.subheader("Historical Data")
        st.dataframe(df.style.format({
            "Price": "${:,.2f}",
            "Dividend": "${:,.2f}",
            "Volume": "{:,.0f}"
        }))
        
        # Download data
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Market Data as CSV",
            data=csv,
            file_name="msty_market_data.csv",
            mime="text/csv"
        )
    else:
        st.info("No market data available. Please add some entries using the form above.")

elif tab == "📤 Export Center":
    st.title("📤 Export Center")
    
    def create_pdf_report(data_dict):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "MSTY Investment Report", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        
        for title, df in data_dict.items():
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"\n{title}", ln=True)
            pdf.set_font("Arial", size=10)
            
            # Convert DataFrame to string representation
            if isinstance(df, pd.DataFrame):
                text = df.to_string()
                pdf.multi_cell(0, 5, text)
            else:
                pdf.multi_cell(0, 5, str(df))
            pdf.cell(0, 10, "", ln=True)  # Add spacing
        
        return pdf.output(dest='S').encode('latin1')
    
    def send_email(recipient, subject, body, attachments=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = os.getenv('EMAIL_FROM')
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if attachments:
                for filename, content in attachments.items():
                    part = MIMEApplication(content)
                    part.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(part)
            
            server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
            server.starttls()
            server.login(os.getenv('EMAIL_FROM'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            st.error(f"Error sending email: {str(e)}")
            return False
    
    # Available data for export
    export_data = {}
    
    if st.session_state.simulation_results is not None:
        export_data["Simulation Results"] = st.session_state.simulation_results
    
    if st.session_state.actual_performance:
        export_data["Actual Performance"] = pd.DataFrame(st.session_state.actual_performance)
    
    if st.session_state.market_data:
        export_data["Market Data"] = pd.DataFrame(st.session_state.market_data)
    
    if "blocks" in st.session_state and st.session_state.blocks:
        export_data["Cost Basis Data"] = pd.DataFrame(st.session_state.blocks)
    
    if not export_data:
        st.warning("No data available for export. Please generate some data using other tabs first.")
    else:
        # Data selection
        st.subheader("Select Data to Export")
        selected_data = st.multiselect("Choose data to include:", list(export_data.keys()))
        
        if selected_data:
            export_format = st.radio("Export Format", ["CSV", "PDF"])
            
            # Export method
            export_method = st.radio("Export Method", ["Download", "Email"])
            
            if export_method == "Email":
                recipient_email = st.text_input("Enter your email address:")
            
            if st.button("Generate Export"):
                selected_export_data = {k: export_data[k] for k in selected_data}
                
                if export_format == "CSV":
                    for title, df in selected_export_data.items():
                        csv = df.to_csv(index=False)
                        if export_method == "Download":
                            st.download_button(
                                label=f"Download {title} CSV",
                                data=csv,
                                file_name=f"msty_{title.lower().replace(' ', '_')}.csv",
                                mime="text/csv"
                            )
                        else:  # Email
                            if recipient_email:
                                attachments = {f"msty_{title.lower().replace(' ', '_')}.csv": csv.encode()}
                                if send_email(recipient_email, 
                                           "MSTY Investment Data Export",
                                           "Please find your requested data attached.",
                                           attachments):
                                    st.success(f"Data sent to {recipient_email}")
                            else:
                                st.error("Please enter an email address.")
                
                else:  # PDF
                    try:
                        pdf_content = create_pdf_report(selected_export_data)
                        if export_method == "Download":
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_content,
                                file_name="msty_investment_report.pdf",
                                mime="application/pdf"
                            )
                        else:  # Email
                            if recipient_email:
                                attachments = {"msty_investment_report.pdf": pdf_content}
                                if send_email(recipient_email,
                                           "MSTY Investment Report",
                                           "Please find your requested report attached.",
                                           attachments):
                                    st.success(f"Report sent to {recipient_email}")
                            else:
                                st.error("Please enter an email address.")
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
            
            # Tax Summary Section
            if "Cost Basis Data" in selected_data or "Simulation Results" in selected_data:
                st.subheader("Tax Summary")
                
                # Calculate tax summary from available data
                tax_summary = pd.DataFrame()
                
                if "Simulation Results" in selected_data:
                    sim_df = export_data["Simulation Results"]
                    yearly_tax_data = sim_df.groupby(pd.to_datetime(sim_df['Date']).dt.year).agg({
                        'Net Dividends': 'sum',
                        'Taxes Paid': 'sum',
                        'Penalties Paid': 'sum'
                    }).reset_index()
                    
                    st.write("Yearly Tax Summary from Simulation:")
                    st.dataframe(yearly_tax_data.style.format({
                        'Net Dividends': '${:,.2f}',
                        'Taxes Paid': '${:,.2f}',
                        'Penalties Paid': '${:,.2f}'
                    }))
                
                if "Cost Basis Data" in selected_data:
                    cost_basis_df = export_data["Cost Basis Data"]
                    cost_basis_df['Year'] = pd.to_datetime(cost_basis_df['Date']).dt.year
                    yearly_basis = cost_basis_df.groupby('Year').agg({
                        'Shares': 'sum',
                        'Total': 'sum'
                    }).reset_index()
                    
                    st.write("Yearly Cost Basis Summary:")
                    st.dataframe(yearly_basis.style.format({
                        'Shares': '{:,.2f}',
                        'Total': '${:,.2f}'
                    }))
                
                # Option to include tax summary in export
                if st.checkbox("Include Tax Summary in Export"):
                    if "Simulation Results" in selected_data:
                        selected_export_data["Tax Summary - Simulation"] = yearly_tax_data
                    if "Cost Basis Data" in selected_data:
                        selected_export_data["Tax Summary - Cost Basis"] = yearly_basis
