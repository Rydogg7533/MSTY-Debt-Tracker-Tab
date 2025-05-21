
import streamlit as st

def show_return_on_debt():
    st.title("Return on Debt")

    st.markdown("### Loan & Share Inputs")
    total_debt = st.number_input("Total Debt Incurred ($)", value=100000.0)
    monthly_payment = st.number_input("Monthly Debt Payment ($)", value=3000.0)
    interest_rate = st.number_input("Annual Interest Rate (%)", value=10.0) / 100
    loan_period_years = st.number_input("Loan Period (Years)", value=5)
    avg_dividend = st.number_input("Average Monthly Dividend per Share ($)", value=2.0)
    cost_basis = st.number_input("Cost Basis per Share ($)", value=25.0)
    avg_reinvest_price = st.number_input("Average Reinvestment Share Price ($)", value=30.0)
    projected_price = st.number_input("Projected Share Price at Loan End ($)", value=45.0)

    months = int(loan_period_years * 12)
    monthly_interest_rate = interest_rate / 12

    st.markdown("### Computation Results")

    total_interest_paid = 0
    remaining_debt = total_debt
    total_dividends = 0
    reinvested_amount = 0
    share_count = total_debt / cost_basis

    for month in range(months):
        interest_payment = remaining_debt * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        remaining_debt -= principal_payment
        total_interest_paid += interest_payment

        dividends_this_month = share_count * avg_dividend
        total_dividends += dividends_this_month

        reinvestable = max(dividends_this_month - monthly_payment, 0)
        reinvested_amount += reinvestable
        new_shares = reinvestable / avg_reinvest_price
        share_count += new_shares

    final_value = share_count * projected_price
    dividends_post_loan = share_count * avg_dividend

    st.metric("Total Interest Paid", f"${total_interest_paid:,.2f}")
    st.metric("Total Shares at Loan End", f"{share_count:,.2f}")
    st.metric("Portfolio Value at End", f"${final_value:,.2f}")
    st.metric("Monthly Dividends After Loan", f"${dividends_post_loan:,.2f}")

show_return_on_debt()
