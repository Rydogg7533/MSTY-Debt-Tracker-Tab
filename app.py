
import streamlit as st
from compounding_simulator import show_compounding_simulator
from cost_basis_tracker import show_cost_basis_tracker
from return_on_debt import show_return_on_debt

st.set_page_config(page_title="MSTY Full Tool", layout="wide")
tabs = {
    "Compounding Simulator": show_compounding_simulator,
    "Cost Basis Tracker": show_cost_basis_tracker,
    "Return on Debt": show_return_on_debt
}

selected_tab = st.sidebar.radio("Select Tool", list(tabs.keys()))
tabs[selected_tab]()
