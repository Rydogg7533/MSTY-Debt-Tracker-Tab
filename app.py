
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Compounding Simulator Logic
def show_compounding_simulator():
    st.title("📈 Compounding Simulator")

    initial_shares = st.number_input("Initial Share Count", min_value=0, value=10000)
    avg_cost_basis = st.number_input("Initial Purchase Cost Basis ($)", min_value=0.0, value=25.0)
    holding_months = st.slider("Holding Period (Months)", min_value=1, max_value=120, value=24)
    avg_div = st.number_input("Average Monthly Dividend per Share ($)", min_value=0.0, value=2.0)

    fed_tax = st.slider("Federal Tax Rate (%)", 0, 50, 20)
    state_tax = st.slider("State Tax Rate (%)", 0, 20, 5)
    dependents = st.number_input("Number of Dependents", min_value=0, value=0)
    acct_type = st.selectbox("Account Type", ["Taxable", "Tax Deferred", "Non Taxable"])

    withdraw_monthly = 0
    reinvest = st.checkbox("Reinvest Dividends?")
    if reinvest:
        reinvest_percent = st.slider("Percent of Dividends to Reinvest (%)", 0, 100, 100)
    else:
        reinvest_percent = 0
        withdraw_monthly = st.number_input("Withdraw this Dollar Amount Monthly ($)", min_value=0, value=2000)

    reinvest_price = st.number_input("Average Reinvestment Cost Per Share ($)", min_value=1.0, value=25.0)
    defer_taxes = st.checkbox("Defer Taxes Until October 15?")
    frequency = st.selectbox("Output View", ["Monthly", "Yearly", "Total"])
    run_sim = st.button("Run Simulation")

    if run_sim:
        df = []
        shares = initial_shares
        tax_due = 0
        total_tax_paid = 0
        cumulative_shares = shares
        cumulative_added = 0
        today = datetime.today()
        tax_year = today.year
        penalty_rate = 0.01  # estimate 1% monthly penalty after deadline

        for i in range(holding_months):
            current_date = today + relativedelta(months=i)
            gross_div = shares * avg_div
            monthly_tax = 0

            if acct_type == "Taxable":
                tax_rate = (fed_tax + state_tax) / 100
                monthly_tax = gross_div * tax_rate
            elif acct_type == "Tax Deferred":
                tax_rate = (fed_tax + state_tax) / 100
                monthly_tax = gross_div * tax_rate if current_date.month == 10 else 0
            else:
                monthly_tax = 0

            if defer_taxes and acct_type == "Taxable":
                if current_date.month == 10:
                    penalty_months = i - (10 - today.month)
                    penalties = penalty_rate * penalty_months * monthly_tax
                    monthly_tax += penalties

            if reinvest:
                reinvest_amount = (gross_div - monthly_tax) * (reinvest_percent / 100)
            else:
                reinvest_amount = max(0, gross_div - monthly_tax - withdraw_monthly)

            new_shares = reinvest_amount / reinvest_price
            cumulative_shares += new_shares
            cumulative_added += new_shares

            df.append({
                "Date": current_date.strftime("%Y-%m"),
                "Gross Dividend": gross_div,
                "Taxes Paid": monthly_tax,
                "New Shares Added": new_shares,
                "Cumulative Shares": cumulative_shares,
                "Reinvested": reinvest_amount
            })

        table = pd.DataFrame(df)

        if frequency == "Yearly":
            table['Year'] = pd.to_datetime(table['Date']).dt.year
            table = table.groupby('Year').agg({
                "Gross Dividend": "sum",
                "Taxes Paid": "sum",
                "New Shares Added": "sum",
                "Cumulative Shares": "last",
                "Reinvested": "sum"
            }).reset_index().rename(columns={"Year": "Period"})
        elif frequency == "Total":
            table = pd.DataFrame([{
                "Period": "Total",
                "Gross Dividend": table["Gross Dividend"].sum(),
                "Taxes Paid": table["Taxes Paid"].sum(),
                "New Shares Added": table["New Shares Added"].sum(),
                "Cumulative Shares": table["Cumulative Shares"].iloc[-1],
                "Reinvested": table["Reinvested"].sum()
            }])
        else:
            table.insert(0, "Period", table.pop("Date"))

        st.subheader("Simulation Results")
        st.dataframe(table.style.format({
            "Gross Dividend": "${:,.2f}",
            "Taxes Paid": "${:,.2f}",
            "Reinvested": "${:,.2f}",
            "New Shares Added": "{:,.2f}",
            "Cumulative Shares": "{:,.2f}"
        }))

# Return on Debt Tool
def show_return_on_debt():
    st.title("💸 Return on Debt Calculator")

    debt_amount = st.number_input("Total Debt Incurred ($)", min_value=0.0)
    monthly_payment = st.number_input("Monthly Payment ($)", min_value=0.0)
    cost_basis = st.number_input("Cost Basis per Share ($)", min_value=0.0)
    loan_term = st.number_input("Loan Term (Months)", min_value=1)
    compound_period = st.number_input("Compounding Duration (Months)", min_value=1)
    reinvest_price = st.number_input("Avg Reinvestment Share Price ($)", min_value=0.0)
    monthly_dividend = st.number_input("Avg Monthly Dividend per Share ($)", min_value=0.0)
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0)
    end_price = st.number_input("Projected Share Price ($)", min_value=0.0)

    if st.button("Calculate"):
        shares_purchased = debt_amount / cost_basis
        dividends_total = shares_purchased * monthly_dividend
        monthly_reinvest = max(dividends_total - monthly_payment, 0)
        reinvested_shares = (monthly_reinvest * compound_period) / reinvest_price
        final_share_count = shares_purchased + reinvested_shares
        portfolio_value = final_share_count * end_price
        total_interest_paid = monthly_payment * loan_term - debt_amount
        net_value = portfolio_value - debt_amount

        st.markdown(f"**Shares Purchased with Debt:** {shares_purchased:,.2f}")
        st.markdown(f"**Final Share Count:** {final_share_count:,.2f}")
        st.markdown(f"**Portfolio Value:** ${portfolio_value:,.2f}")
        st.markdown(f"**Interest Paid Over Loan:** ${total_interest_paid:,.2f}")
        st.markdown(f"**Net Portfolio Value After Debt:** ${net_value:,.2f}")

# Navigation
st.set_page_config(page_title="MSTY Tool", layout="wide")
st.sidebar.title("MSTY Tool Navigation")
page = st.sidebar.radio("Select a tool:", ["📈 Compounding Simulator", "💸 Return on Debt"])

if page == "📈 Compounding Simulator":
    show_compounding_simulator()
elif page == "💸 Return on Debt":
    show_return_on_debt()
