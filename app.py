
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="MSTY Tool", layout="wide")

tab = st.sidebar.selectbox("Select Tool", ["📈 Compounding Simulator", "📊 Cost Basis Tool", "💸 Return on Debt"])

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
    monthly_payment = st.number_input("Monthly Payment Toward Debt ($)", min_value=0.0, value=3000.0)
    share_cost = st.number_input("Cost Basis per Share ($)", min_value=0.01, value=25.0)
    loan_term = st.number_input("Loan Term (Months)", min_value=1, value=36)
    compounding_term = st.number_input("Compounding Period (Months)", min_value=1, value=36)
    reinvest_price = st.number_input("Reinvestment Share Price ($)", min_value=0.01, value=30.0)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", min_value=0.01, value=2.00)
    expected_price = st.number_input("Estimated Price per Share at End ($)", min_value=0.01, value=40.0)

    run_debt = st.button("Calculate Return on Debt")

    if run_debt:
        initial_shares = debt_amount / share_cost
        interest_total = (monthly_payment * loan_term) - debt_amount
        monthly_income = initial_shares * avg_dividend
        reinvestable = max(monthly_income - monthly_payment, 0)
        new_shares = (reinvestable / reinvest_price) * compounding_term
        final_share_count = initial_shares + new_shares
        final_value = final_share_count * expected_price

        st.markdown(f"**Initial Shares Purchased:** {initial_shares:,.2f}")
        st.markdown(f"**Total Interest Paid:** ${interest_total:,.2f}")
        st.markdown(f"**New Shares Reinvested:** {new_shares:,.2f}")
        st.markdown(f"**Final Total Shares:** {final_share_count:,.2f}")
        st.markdown(f"**Portfolio Value at Exit Price:** ${final_value:,.2f}")
