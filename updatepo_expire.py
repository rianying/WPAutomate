import csv
import datetime
import subprocess
import pyperclip
import os

# Read po_expire.csv and create a dictionary of customer names and corresponding po_expire values
po_expire_data = {}
with open('po_expire.csv', 'r') as po_expire_file:
    po_expire_reader = csv.DictReader(po_expire_file)
    for row in po_expire_reader:
        po_expire_data[row['customer_name']] = int(row['po_expire'])

# Calculate business days considering only Monday to Friday
def add_business_days(start_date, num_days):
    current_date = start_date
    while num_days > 0:
        current_date += datetime.timedelta(days=1)
        if current_date.weekday() < 5:  # Monday to Friday
            num_days -= 1
    return current_date

# Generate a single SQL UPDATE query using CASE statement with new lines for each entry
update_cases = []
with open('expired.csv', 'r') as sql_fetched_file:
    sql_fetched_reader = csv.DictReader(sql_fetched_file)
    for row in sql_fetched_reader:
        customer_name = row['customer_name']
        if customer_name in po_expire_data:
            po_expire_days = po_expire_data[customer_name]
            order_time = datetime.datetime.strptime(row['order_time'], '%Y-%m-%d %H:%M:%S')
            po_expiry_date = add_business_days(order_time, po_expire_days)
            po_expiry_date_str = po_expiry_date.strftime('%Y-%m-%d %H:%M:%S')
            update_case = f"  WHEN no_SO = '{row['no_SO']}' THEN '{po_expiry_date_str}'"
            update_cases.append(update_case)

if update_cases:
    case_statement = "\n".join(update_cases) + "\n  ELSE po_expired END"
    single_update_query = f"UPDATE preorder SET po_expired = CASE{case_statement};"
    transaction = single_update_query + "\n"

    # Copy the generated transaction to the clipboard
    pyperclip.copy(transaction)

    print("Single transaction with a CASE statement (with new lines for entries) has been generated and copied to the clipboard.")
    print("You can now paste the transaction wherever you need.")
    os.remove('expired.csv')
else:
    print("No eligible records found in the input data.")
