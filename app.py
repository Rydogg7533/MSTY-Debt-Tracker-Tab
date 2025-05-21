
import streamlit as st
from datetime import date
import pandas as pd

st.set_page_config(page_title="MSTY Tool", layout="wide")

tab = st.sidebar.selectbox("Select Tab", ["Compounding Simulator", "Cost Basis Tool", "Return on Debt"])

# -------------------------------
# Compounding Simulator
# -------------------------------
if tab == "Compounding Simulator":
    st.title("📈 Compounding Simulator")

    initial_shares = st.number_input("Initial Share Count", min_value=0, value=1000)
    reinvest_price = st.number_input("Average Reinvestment Cost Per Share ($)", min_value=0.01, value=25.00)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", min_value=0.0, value=2.0)
    months = st.number_input("Number of Months to Project", min_value=1, value=36)
    run = st.button("Run Simulation")

    if run:
        data = []
        shares = initial_shares
        total_dividends = 0
        for month in range(1, months + 1):
            dividend = shares * avg_dividend
            new_shares = dividend / reinvest_price
            shares += new_shares
            total_dividends += dividend
            data.append({
                "Month": month,
                "Dividend": round(dividend, 2),
                "New Shares": round(new_shares, 4),
                "Total Shares": round(shares, 4),
                "Cumulative Dividends": round(total_dividends, 2)
            })
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.success(f"Final Share Count: {shares:,.2f}")
        st.success(f"Total Dividends Earned: ${total_dividends:,.2f}")

# -------------------------------
# Cost Basis Tool
# -------------------------------
elif tab == "Cost Basis Tool":
    st.title("📊 Cost Basis Tracker")

    if "blocks" not in st.session_state:
        st.session_state.blocks = []

    with st.form("add_block"):
        d = st.date_input("Date of Purchase", value=date.today())
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

# -------------------------------
# Return on Debt Tool
# -------------------------------
elif tab == "Return on Debt":
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
        final_shares = initial_shares + new_shares
        final_value = final_shares * expected_price

        st.markdown(f"**Initial Shares Purchased:** {initial_shares:,.2f}")
        st.markdown(f"**Total Interest Paid:** ${interest_total:,.2f}")
        st.markdown(f"**New Shares Reinvested:** {new_shares:,.2f}")
        st.markdown(f"**Final Total Shares:** {final_shares:,.2f}")
        st.markdown(f"**Portfolio Value at Exit Price:** ${final_value:,.2f}")
