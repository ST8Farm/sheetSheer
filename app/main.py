# app/main.py

import streamlit as st
from transaction_processor import transaction_processor
from transaction_diff_checker import transaction_diff_checker
from single_file_transaction_diff_checker import single_file_transaction_diff_checker

st.set_page_config(layout="wide")

st.title("Excel Transaction Processor")

# Add tabs
tab1, tab2, tab3 = st.tabs(["Transaction Processor", "Sheet Diff Checker", "Transaction Diff Checker"])

with tab1:
    transaction_processor()

with tab2:
    transaction_diff_checker()

with tab3:
    single_file_transaction_diff_checker()
