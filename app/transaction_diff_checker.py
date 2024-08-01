# app/transaction_diff_checker.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from utils import load_transaction_types, process_excel_file, process_transaction_data

def highlight_differences(df1, df2):
    # Create a DataFrame with the same shape as df1 and df2, filled with empty strings
    styles = pd.DataFrame('', index=df1.index, columns=df1.columns)
    # Apply yellow background to cells that are different
    diff = df1 != df2
    styles[diff] = 'background-color: yellow'
    # Apply red background to rows that are in one df but not the other
    missing_in_df1 = df1.isna()
    missing_in_df2 = df2.isna()
    styles[missing_in_df1 & ~missing_in_df2] = 'background-color: red'
    styles[missing_in_df2 & ~missing_in_df1] = 'background-color: red'
    return styles

def transaction_diff_checker():
    st.header("Sheet Diff Checker")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file1 = st.file_uploader("Choose the first Excel file", type="xlsx", key="file_uploader1")
    
    with col2:
        uploaded_file2 = st.file_uploader("Choose the second Excel file", type="xlsx", key="file_uploader2")

    if uploaded_file1 and uploaded_file2:
        file_path1 = os.path.join('uploads', uploaded_file1.name)
        with open(file_path1, "wb") as f:
            f.write(uploaded_file1.getbuffer())
        
        file_path2 = os.path.join('uploads', uploaded_file2.name)
        with open(file_path2, "wb") as f:
            f.write(uploaded_file2.getbuffer())

        transaction_types1 = load_transaction_types(file_path1)
        transaction_types2 = load_transaction_types(file_path2)
        common_transaction_types = sorted(set(transaction_types1) & set(transaction_types2))
        
        selected_transaction_type = st.selectbox(
            "Search and select Transaction Type",
            [""] + common_transaction_types,
            index=0,
            key="transaction_select"
        )

        if st.button("Process"):
            if selected_transaction_type in common_transaction_types:
                df1 = process_excel_file(file_path1)
                df2 = process_excel_file(file_path2)
                
                processed_df1 = process_transaction_data(df1, selected_transaction_type)
                processed_df2 = process_transaction_data(df2, selected_transaction_type)
                
                # Ensure the same column order with Unique_ID for processing
                columns_order = ['Unique_ID', 'Category', 'Variable'] + [col for col in processed_df1.columns if col not in ['Unique_ID', 'Category', 'Variable']]
                processed_df1 = processed_df1[columns_order]
                processed_df2 = processed_df2[columns_order]

                # Align dataframes on Unique_ID
                processed_df1.set_index('Unique_ID', inplace=True)
                processed_df2.set_index('Unique_ID', inplace=True)
                processed_df1, processed_df2 = processed_df1.align(processed_df2, join='outer', axis=0)

                # Fill NaN for comparison and styling purposes
                filled_df1 = processed_df1.fillna('')
                filled_df2 = processed_df2.fillna('')

                # Highlight differences
                styled_df1 = filled_df1.style.apply(lambda x: highlight_differences(filled_df1, filled_df2), axis=None)
                styled_df2 = filled_df2.style.apply(lambda x: highlight_differences(filled_df2, filled_df1), axis=None)

                # Reset index to bring back Unique_ID as a column
                processed_df1.reset_index(inplace=True)
                processed_df2.reset_index(inplace=True)
                
                processed_df1.drop(columns=['Unique_ID'], inplace=True)
                processed_df2.drop(columns=['Unique_ID'], inplace=True)
                
                col1.subheader("First File Output")
                col1.dataframe(styled_df1, width=2000, height=800)
                
                col2.subheader("Second File Output")
                col2.dataframe(styled_df2, width=2000, height=800)

            else:
                st.warning("Transaction type not found. Please check the selected transaction type.")

    if not os.path.exists('uploads'):
        os.makedirs('uploads')
