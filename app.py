
import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="MSTY Full Tool", layout="wide")
tab = st.sidebar.selectbox("Select Tab", ["Compounding Simulator", "Cost Basis Tool", "Return on Debt"])

if tab == "Compounding Simulator":
    st.title("Compounding Simulator")
    initial_shares = st.number_input("Initial Share Count", value=1000)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", value=2.00)
    reinvest_price = st.number_input("Average Reinvestment Cost Per Share ($)", value=25.00)
    months = st.number_input("Number of Months", value=12)

    data = []
    shares = initial_shares
    for m in range(1, int(months)+1):
        dividend_income = shares * avg_dividend
        new_shares = dividend_income / reinvest_price
        shares += new_shares
        data.append({
            "Month": m,
            "Dividend Income": round(dividend_income, 2),
            "New Shares": round(new_shares, 4),
            "Total Shares": round(shares, 4)
        })
    df = pd.DataFrame(data)
    st.dataframe(df)
    st.success(f"Final Share Count: {shares:,.2f}")

elif tab == "Cost Basis Tool":
    st.title("Cost Basis Tracker")
    if "blocks" not in st.session_state:
        st.session_state.blocks = []
    with st.form("add_block_form"):
        date = st.date_input("Date")
        shares = st.number_input("Shares Purchased", step=1)
        cost_basis = st.number_input("Cost Basis Per Share ($)")
        submitted = st.form_submit_button("Add Block")
        if submitted:
            st.session_state.blocks.append({"Date": date, "Shares": shares, "Cost Basis": cost_basis})
    if st.session_state.blocks:
        df_blocks = pd.DataFrame(st.session_state.blocks)
        df_blocks["Total Cost"] = df_blocks["Shares"] * df_blocks["Cost Basis"]
        total_shares = df_blocks["Shares"].sum()
        total_cost = df_blocks["Total Cost"].sum()
        avg_cost_basis = total_cost / total_shares if total_shares > 0 else 0
        st.dataframe(df_blocks)
        st.info(f"Average Cost Basis: ${avg_cost_basis:,.2f}")

elif tab == "Return on Debt":
    st.title("Return on Debt")
    debt = st.number_input("Total Debt Incurred ($)", value=180000)
    monthly_payment = st.number_input("Monthly Payment Toward Debt ($)", value=5000)
    purchase_price = st.number_input("Purchase Cost Basis per Share ($)", value=25.00)
    reinvest_price = st.number_input("Average Reinvestment Share Price ($)", value=30.00)
    avg_dividend = st.number_input("Average Dividend per Share per Month ($)", value=2.00)
    loan_months = st.number_input("Loan Term (months)", value=36)

    shares_bought = debt / purchase_price
    interest_paid = (monthly_payment * loan_months) - debt
    monthly_dividend = shares_bought * avg_dividend
    reinvestable = max(monthly_dividend - monthly_payment, 0)
    new_shares_per_month = reinvestable / reinvest_price
    final_share_count = shares_bought + (new_shares_per_month * loan_months)

    st.markdown(f"""
- **Total Shares Purchased with Debt:** {shares_bought:,.2f}
- **Total Interest Paid:** ${interest_paid:,.2f}
- **Reinvested Monthly:** ${reinvestable:,.2f}
- **New Shares Reinvested Monthly:** {new_shares_per_month:,.2f}
- **Final Share Count:** {final_share_count:,.2f}
    """)
