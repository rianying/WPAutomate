import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import subprocess
import os

# Helper function to calculate business days
def add_business_days(from_date, add_days):
    return np.busday_offset(from_date, add_days, roll='forward')

def generate_queries(csv_file_path):
    df = pd.read_csv(csv_file_path)  # Read the CSV file

    value_clauses_preorder = []
    value_clauses_order_checking_start = []
    value_clauses_order_checking_finish = []

    for _, row in df.iterrows():
        no_SO = row['no_SO'] if not pd.isna(row['no_SO']) else ""
        customer_name = row['customer_name'] if not pd.isna(row['customer_name']) else ""
        order_time = row['order_time'] if not pd.isna(row['order_time']) else ""  # Extract order_time from the current row

        fat_random_minutes = random.randint(1, 10)  # Generate random number of minutes between 1 and 10
        fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')

        if "CRB" in no_SO or "BDG" in no_SO:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 7)
        else:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 4)

        value_clause_preorder = f'("{no_SO}", "{customer_name}", \'{order_time}\', \'{po_expired}\')'
        value_clauses_preorder.append(value_clause_preorder)

        value_clause_order_checking_start = f'("{no_SO}", \'{fat_start_time}\', "{customer_name}")'
        value_clauses_order_checking_start.append(value_clause_order_checking_start)

        no_SJ = no_SO.replace("SO", "SJ")
        fat_random_minutes = random.randint(1, 10)  # Generate random number of minutes between 1 and 10
        fat_checking_finish = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        value_clause_order_checking_finish = f'("{no_SO}", "{no_SJ}", \'{fat_checking_finish}\', "{customer_name}", "Process")'
        value_clauses_order_checking_finish.append(value_clause_order_checking_finish)

    values_str_order_checking_start = ',\n'.join(value_clauses_order_checking_start)  # Join all value clauses for order_checking_start table together, separated by commas
    values_str_order_checking_finish = ',\n'.join(value_clauses_order_checking_finish)  # Join all value clauses for order_checking_finish table together, separated by commas

    query_order_checking_start = f'INSERT INTO order_checking_start(no_SO, start_check, customer_name) VALUES {values_str_order_checking_start};\n/'
    query_order_checking_finish = f'INSERT INTO orders_checking_finish(no_SO, no_SJ, FAT_checking_finish, customer, status_FAT) VALUES {values_str_order_checking_finish};\n/'

    return query_order_checking_start, query_order_checking_finish

def copy_to_clipboard(text):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))

if __name__ == "__main__":
    csv_file_path = '/Users/rian/Documents/GitHub/WPAutomate/maybeuse/CheckPO.csv'  # Replace this with the actual path of your CSV file

    try:
        queries_order_checking_start, queries_order_checking_finish = generate_queries(csv_file_path)
        queries_combined = f"{queries_order_checking_start}\n\n{queries_order_checking_finish}"

        # Copy to clipboard
        copy_to_clipboard(queries_combined)

        print("Generated SQL Queries have been copied to the clipboard!")

        # Delete the CSV file
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            print(f"\n{csv_file_path} has been deleted.")
        else:
            print(f"\n{csv_file_path} does not exist.")

    except Exception as e:
        print("Error:", str(e))