# app/single_file_transaction_diff_checker.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from utils import load_transaction_types, process_excel_file, process_transaction_data
from tabulate import tabulate

def highlight_differences(df1, df2):
    def style_cell(val1, val2):
        if pd.isna(val1) and not pd.isna(val2):
            return 'background-color: lightgreen'  # Added
        elif not pd.isna(val1) and pd.isna(val2):
            return 'background-color: lightcoral'  # Removed
        elif not pd.isna(val1) and not pd.isna(val2) and val1 != val2:
            return 'background-color: yellow'  # Changed
        return ''

    # Create a DataFrame of styles
    styles = pd.DataFrame('', index=df1.index, columns=df1.columns)
    
    for col in df1.columns:
        styles[col] = [style_cell(val1, val2) for val1, val2 in zip(df1[col], df2[col])]
    
    return styles

def generate_difference_explanation(df1, df2, type1, type2):
    changes = []
    
    # Check for added or removed rows
    df1_rows = set(df1.index)
    df2_rows = set(df2.index)
    added_rows = df2_rows - df1_rows
    removed_rows = df1_rows - df2_rows
    
    for row in added_rows:
        changes.append({
            'Category': df2.loc[row, 'Category'],
            'Variable': df2.loc[row, 'Variable'],
            'Column': 'Entire Row',
            'Change Type': 'Added',
            'From': '',
            'To': f"New row in {type2}"
        })
    
    for row in removed_rows:
        changes.append({
            'Category': df1.loc[row, 'Category'],
            'Variable': df1.loc[row, 'Variable'],
            'Column': 'Entire Row',
            'Change Type': 'Removed',
            'From': f"Existing row in {type1}",
            'To': ''
        })
    
    # Check for changes in existing rows
    common_rows = df1_rows.intersection(df2_rows)
    for row in common_rows:
        for col in df1.columns:
            if col not in ['Category', 'Variable']:
                val1 = df1.loc[row, col]
                val2 = df2.loc[row, col]
                if pd.isna(val1) and not pd.isna(val2):
                    changes.append({
                        'Category': df1.loc[row, 'Category'],
                        'Variable': df1.loc[row, 'Variable'],
                        'Column': col,
                        'Change Type': 'Added',
                        'From': 'NaN',
                        'To': str(val2)
                    })
                elif not pd.isna(val1) and pd.isna(val2):
                    changes.append({
                        'Category': df1.loc[row, 'Category'],
                        'Variable': df1.loc[row, 'Variable'],
                        'Column': col,
                        'Change Type': 'Removed',
                        'From': str(val1),
                        'To': 'NaN'
                    })
                elif not pd.isna(val1) and not pd.isna(val2) and val1 != val2:
                    changes.append({
                        'Category': df1.loc[row, 'Category'],
                        'Variable': df1.loc[row, 'Variable'],
                        'Column': col,
                        'Change Type': 'Changed',
                        'From': str(val1),
                        'To': str(val2)
                    })
    
    changes_df = pd.DataFrame(changes)
    
    # Order the changes_df
    changes_df['Change Order'] = changes_df['Change Type'].map({'Removed': 1, 'Changed': 2, 'Added': 3})
    changes_df.sort_values(by=['Change Order', 'Category', 'Variable'], inplace=True)
    changes_df.drop(columns=['Change Order'], inplace=True)
    
    return changes_df

def single_file_transaction_diff_checker():
    st.header("Single File Transaction Diff Checker")

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="single_file_uploader")

    if uploaded_file:
        file_path = os.path.join('uploads', uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        transaction_types = load_transaction_types(file_path)
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_transaction_type_1 = st.selectbox(
                "Select the first Transaction Type",
                [""] + transaction_types,
                index=0,
                key="transaction_select_1"
            )
        
        with col2:
            selected_transaction_type_2 = st.selectbox(
                "Select the second Transaction Type",
                [""] + transaction_types,
                index=0,
                key="transaction_select_2"
            )

        if st.button("Compare Transactions"):
            if selected_transaction_type_1 and selected_transaction_type_2:
                df = process_excel_file(file_path)
                
                processed_df1 = process_transaction_data(df, selected_transaction_type_1)
                processed_df2 = process_transaction_data(df, selected_transaction_type_2)

                # Ensure the same column order with Unique_ID for processing
                columns_order = ['Unique_ID', 'Category', 'Variable'] + [col for col in processed_df1.columns if col not in ['Unique_ID', 'Category', 'Variable']]
                processed_df1 = processed_df1[columns_order]
                processed_df2 = processed_df2[columns_order]

                # Align dataframes on Unique_ID
                processed_df1.set_index('Unique_ID', inplace=True)
                processed_df2.set_index('Unique_ID', inplace=True)
                processed_df1, processed_df2 = processed_df1.align(processed_df2, join='outer', axis=0)

                # Ensure Category and Variable are populated in both DataFrames
                processed_df1['Category'] = processed_df1['Category'].combine_first(processed_df2['Category'])
                processed_df1['Variable'] = processed_df1['Variable'].combine_first(processed_df2['Variable'])
                processed_df2['Category'] = processed_df1['Category']
                processed_df2['Variable'] = processed_df1['Variable']

                # Remove duplicate columns
                processed_df1 = processed_df1.loc[:, ~processed_df1.columns.duplicated()]
                processed_df2 = processed_df2.loc[:, ~processed_df2.columns.duplicated()]

                # Fill NaN for comparison and styling purposes
                filled_df1 = processed_df1.fillna('')
                filled_df2 = processed_df2.fillna('')

                # Filter rows with differences
                diff_mask = ((filled_df1 != filled_df2) & ((filled_df1 != '') | (filled_df2 != ''))).any(axis=1)
                diff_df1 = processed_df1[diff_mask]
                diff_df2 = processed_df2[diff_mask]

                # Generate explanation of differences
                changes_df = generate_difference_explanation(diff_df1, diff_df2, selected_transaction_type_1, selected_transaction_type_2)

                # Display explanation of differences with title
                st.subheader("Explanation of Differences")
                comparison_title = f"Comparison of Transaction Types: {selected_transaction_type_1} vs {selected_transaction_type_2}"
                comparison_result = tabulate(changes_df, headers='keys', tablefmt='grid', showindex=False)
                st.text(f"{comparison_title}\n\n{comparison_result}")
                # Reset index to remove Unique_ID completely
                diff_df1.reset_index(drop=True, inplace=True)
                diff_df2.reset_index(drop=True, inplace=True)
                
                # Remove Unique_ID from display
                styled_df1 = diff_df1.style.apply(lambda x: highlight_differences(diff_df1, diff_df2), axis=None)
                styled_df2 = diff_df2.style.apply(lambda x: highlight_differences(diff_df1, diff_df2), axis=None)

                col1, col2 = st.columns(2)
                
                col1.subheader(f"Transaction Type: {selected_transaction_type_1} Output (Differences Only)")
                col1.dataframe(styled_df1, width=2000, height=800)
                
                col2.subheader(f"Transaction Type: {selected_transaction_type_2} Output (Differences Only)")
                col2.dataframe(styled_df2, width=2000, height=800)

            else:
                st.warning("Please select both transaction types.")

    if not os.path.exists('uploads'):
        os.makedirs('uploads')
