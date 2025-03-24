import streamlit as st
import pandas as pd
import numpy as np

st.title("Document Vouching Tool Prototype")

st.markdown("""
This prototype validates the **Listing** (assumed correct) against the supporting documents such as invoices, delivery receipts, and purchase orders. 
For each entry in the Listing, the app searches the supporting documents for a match.
""")

# --- File Upload Section ---

# 1. Uploads the Listing file (Excel)
listing_file = st.file_uploader("Upload Listing Excel file", type=["xlsx"], key="listing_file")

# 2. Uploads Supporting Documents (CSV, JSON, or Excel for the prototype)
support_files = st.file_uploader("Upload Supporting Documents (CSV, JSON, or Excel)", 
                                 type=["csv", "json", "xlsx"], 
                                 key="support_files", 
                                 accept_multiple_files=True)

# --- Data Processing ---
if listing_file:
    try:
        # Loads the listing file; this prototype assume the sheet is named "Listing"
        listing_df = pd.read_excel(listing_file, sheet_name="Listing")
        st.subheader("Listing Data Preview")
        st.dataframe(listing_df.head())
        
        # Standardizes column names (e.g., "Invoice Number", "Amount", "Date")
        listing_df.columns = [col.strip() for col in listing_df.columns]
        
        # --- Process Supporting Documents ---
        if support_files:
            support_dfs = []
            for file in support_files:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    df = pd.read_excel(file)
                elif file.name.endswith(".json"):
                    df = pd.read_json(file)
                else:
                    st.warning(f"Unsupported file type: {file.name}")
                    continue
                df.columns = [col.strip() for col in df.columns]
                support_dfs.append(df)
            
            if support_dfs:
                support_df = pd.concat(support_dfs, ignore_index=True)
                st.subheader("Combined Supporting Documents Preview")
                st.dataframe(support_df.head())
                
                # --- Validation Function ---
                # We assume that both listing and supporting documents include:
                # "Invoice Number", "Amount", and "Date" columns.
                def validate_row(row):
                    inv_num = row["Invoice Number"]
                    # Filter supporting documents for this invoice number
                    matches = support_df[support_df["Invoice Number"] == inv_num]
                    if matches.empty:
                        return "Not Found", "No supporting document found"
                    else:
                        match_found = False
                        comments = []
                        for _, supp in matches.iterrows():
                            # Compare amounts (allowing for a small tolerance)
                            amount_match = np.isclose(row["Amount"], supp["Amount"], atol=0.01) if pd.notnull(row["Amount"]) and pd.notnull(supp["Amount"]) else False
                            # Compare dates (convert to datetime if needed)
                            try:
                                listing_date = pd.to_datetime(row["Date"]).date()
                                support_date = pd.to_datetime(supp["Date"]).date()
                                date_match = listing_date == support_date
                            except Exception:
                                date_match = False
                            if amount_match and date_match:
                                match_found = True
                                break
                            else:
                                if not amount_match:
                                    comments.append(f"Amount: {row['Amount']} vs {supp['Amount']}")
                                if not date_match:
                                    comments.append(f"Date: {row['Date']} vs {supp['Date']}")
                        if match_found:
                            return "Match", "Validated"
                        else:
                            return "Mismatch", "; ".join(comments)
                
                # Apply the validation function to each row in the listing
                validation_results = listing_df.apply(lambda row: pd.Series(validate_row(row), index=["Validation Status", "Comments"]), axis=1)
                validation_table = pd.concat([listing_df, validation_results], axis=1)
                
                st.subheader("Validation Table")
                st.dataframe(validation_table.head())
                
                # Download option for the validation table
                csv = validation_table.to_csv(index=False).encode('utf-8')
                st.download_button("Download Validation Table as CSV", csv, "validation_table.csv", "text/csv")
            else:
                st.info("No valid supporting document files were uploaded.")
        else:
            st.info("Upload supporting documents to perform validation against the listing.")
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload the Listing Excel file to begin.")