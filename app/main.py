# app/main.py

import streamlit as st
from transaction_processor import transaction_processor
from transaction_diff_checker import transaction_diff_checker

st.set_page_config(layout="wide")

st.title("Excel Transaction Processor")

# Add tabs
tab1, tab2 = st.tabs(["Transaction Processor", "Transaction Diff Checker"])

with tab1:
    transaction_processor()

with tab2:
    transaction_diff_checker()
