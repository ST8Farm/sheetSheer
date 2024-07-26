# app/transaction_processor.py

import streamlit as st
import pandas as pd
import os
import logging
from utils import load_transaction_types, process_excel_file, present_transaction_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def transaction_processor():
    st.header("Transaction Processor")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="file_uploader")

    if uploaded_file is not None:
        file_path = os.path.join('uploads', uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.info(f"Uploaded file: {uploaded_file.name}")

        transaction_types = load_transaction_types(file_path)
        logging.info(f"Transaction types loaded: {transaction_types}")

        selected_transaction_type = st.selectbox(
            "Search and select Transaction Type",
            [""] + transaction_types,
            index=0,
            key="transaction_select"
        )

        if st.button("Process"):
            if selected_transaction_type in transaction_types:
                df = process_excel_file(file_path)
                if df.empty:
                    logging.warning("Processed DataFrame is empty")
                result = present_transaction_data(df, selected_transaction_type)
                st.text(result)
            else:
                st.warning("Transaction type not found. Please check the selected transaction type.")

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

if __name__ == "__main__":
    transaction_processor()
