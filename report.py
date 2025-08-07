import pandas as pd
import csv
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

# Cutoff date variable - modify this to filter records
# Set to None to include all records, or specify a date in YYYY-MM-DD format
cutoff_date = "2025-07-01"  # Format: YYYY-MM-DD or None for all records

def parse_currency(val):
    try:
        return float(str(val).replace("Rs.", "").replace(",", ""))
    except:
        return 0.0

def transform_csv(input_file, temp_file):
    df = pd.read_csv(input_file)

    # Parse Timestamp to date only
    df['Timestamp'] = df['Timestamp'].apply(lambda x: str(x).split(' ')[0])
    
    # Filter records based on cutoff date
    # If cutoff_date is None, include all records
    if cutoff_date is not None:
        # Convert dates to datetime for proper comparison
        df['Date'] = pd.to_datetime(df['Timestamp'])
        cutoff_datetime = pd.to_datetime(cutoff_date)
        df = df[df['Date'] > cutoff_datetime]
        # Drop the temporary Date column
        df = df.drop(columns=['Date'])

    # Parse Balances into separate columns
    def parse_balances(balance_str):
        if pd.isna(balance_str):
            return ['', '', '']
        parts = balance_str.split(';')
        balance_map = {}
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if ':' in part:
                floor, val = part.split(':', 1)
                balance_map[floor.strip()] = val.strip()
        floors = ['Ground Floor', 'First Floor', 'Second Floor']
        return [balance_map.get(floor, '') for floor in floors]

    balances_expanded = df['Balances'].apply(parse_balances).tolist()
    df[['Ground Floor', 'First Floor', 'Second Floor']] = pd.DataFrame(balances_expanded, index=df.index)

    # Drop original Balances column
    df.drop(columns=['Balances'], inplace=True)

    # Reorder columns for output
    columns_order = ['Type', 'Timestamp', 'Tenant', 'Reading/Amount', 'Consumption', 'Ground Floor', 'First Floor', 'Second Floor']
    df = df[columns_order]

    # Save to temporary CSV file
    df.to_csv(temp_file, index=False)

def csv_to_pdf_with_highlights(csv_file, pdf_file):
    df = pd.read_csv(csv_file)

    col_width = 1.5 * inch
    row_height = 0.4 * inch
    margin = 0.5 * inch

    columns = list(df.columns)
    num_cols = len(columns)
    num_rows = len(df)

    # Dynamic page size
    page_width = margin * 2 + num_cols * col_width
    page_height = margin * 2 + (num_rows + 1) * row_height  # +1 for header

    c = canvas.Canvas(pdf_file, pagesize=(page_width, page_height))

    # Starting positions
    y_start = page_height - margin
    x_start = margin

    # Draw header
    y = y_start
    for i, col in enumerate(columns):
        x = x_start + i * col_width
        c.setFillColor(colors.lightgrey)
        c.rect(x, y - row_height, col_width, row_height, fill=1)
        c.setFillColor(colors.black)
        c.drawString(x + 5, y - row_height + 5, str(col))

    # Draw data rows
    for row_idx, row in df.iterrows():
        y = y_start - (row_idx + 1) * row_height

        row_type = str(row['Type']).strip().upper()
        tenant = str(row['Tenant']).strip().lower()
        fill_color = None

        if row_type == 'READING':
            if tenant == 'ground floor':
                fill_color = colors.cyan
            elif tenant == 'first floor':
                fill_color = colors.lightblue
            elif tenant == 'second floor':
                fill_color = colors.lavender

        if row_type == 'RECHARGE':
            value_cols = ['Ground Floor', 'First Floor', 'Second Floor']
            values = [parse_currency(row.get(col)) for col in value_cols]
            min_value = min(values)
            max_value = max(values)
            min_index = values.index(min_value)
            max_index = values.index(max_value)
            min_col_idx = [df.columns.get_loc(col) for col in value_cols][min_index]
            max_col_idx = [df.columns.get_loc(col) for col in value_cols][max_index]
        else:
            min_col_idx = -1
            max_col_idx = -1

        for col_idx, col in enumerate(columns):
            x = x_start + col_idx * col_width
            cell_value = str(row[col])

            if row_type == 'RECHARGE':
                if col_idx == min_col_idx:
                    c.setFillColor(colors.orangered)
                    c.rect(x, y - row_height, col_width, row_height, fill=1)
                    c.setFillColor(colors.white)
                elif col_idx == max_col_idx:
                    c.setFillColor(colors.green)
                    c.rect(x, y - row_height, col_width, row_height, fill=1)
                    c.setFillColor(colors.white)
                elif fill_color:
                    c.setFillColor(fill_color)
                    c.rect(x, y - row_height, col_width, row_height, fill=1)
                    c.setFillColor(colors.black)
                else:
                    c.setFillColor(colors.black)
                    c.rect(x, y - row_height, col_width, row_height, fill=0)
            else:
                if fill_color:
                    c.setFillColor(fill_color)
                    c.rect(x, y - row_height, col_width, row_height, fill=1)
                    c.setFillColor(colors.black)
                else:
                    c.setFillColor(colors.black)
                    c.rect(x, y - row_height, col_width, row_height, fill=0)

            c.drawString(x + 5, y - row_height + 5, cell_value)

    c.save()

def generate_pdf_from_original_csv(original_csv, pdf_file, cutoff_date_param=None):
    global cutoff_date
    if cutoff_date_param is not None:
        cutoff_date = cutoff_date_param
    
    temp_csv = "temp_output.csv"
    try:
        transform_csv(original_csv, temp_csv)
        csv_to_pdf_with_highlights(temp_csv, pdf_file)
    finally:
        # Remove temp file if exists
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

# Usage:
# You can modify the cutoff_date variable above or pass it as a parameter
# Set cutoff_date to None to include all records, or specify a date in YYYY-MM-DD format
generate_pdf_from_original_csv("transactions.csv", "transactions.pdf")
# Example with custom cutoff date: generate_pdf_from_original_csv("transactions.csv", "transactions.pdf", "2025-07-01")
# Example with no cutoff (all records): generate_pdf_from_original_csv("transactions.csv", "transactions.pdf", None)
