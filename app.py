
import streamlit as st

# Define compounding simulator
def show_compounding_simulator():
    st.title("📈 Compounding Simulator")

    initial_investment = st.number_input("Initial Investment ($)", min_value=0.0, value=10000.0)
    annual_return_rate = st.number_input("Annual Return Rate (%)", min_value=0.0, value=5.0)
    years = st.slider("Investment Duration (Years)", min_value=1, max_value=50, value=10)
    compounding_frequency = st.selectbox("Compounding Frequency", ["Annually", "Semi-Annually", "Quarterly", "Monthly"])

    frequency_mapping = {
        "Annually": 1,
        "Semi-Annually": 2,
        "Quarterly": 4,
        "Monthly": 12
    }

    periods_per_year = frequency_mapping[compounding_frequency]
    total_periods = years * periods_per_year
    periodic_rate = annual_return_rate / 100 / periods_per_year
    future_value = initial_investment * (1 + periodic_rate) ** total_periods

    st.subheader("Results")
    st.write(f"After {years} years, your investment will grow to: ${future_value:,.2f}")

# Define return on debt tool
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
