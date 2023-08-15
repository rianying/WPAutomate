import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import subprocess
import os
import json
import random
from fetch_PO import clean, process_csv

def generate_single_query(csv_file, customer_names, po_expire_data):
    df = pd.read_csv(csv_file)

    preorder_query_values = []
    fat_start_values = []
    fat_finish_values = []

    for index, row in df.iterrows():
        order_time = np.datetime64(row['order_date'])

        no_PO = '' if isinstance(row['no_PO'], float) and math.isnan(row['no_PO']) else row['no_PO']
        no_SO = '' if isinstance(row['no_SO'], float) and math.isnan(row['no_SO']) else row['no_SO']
        
        # Fetch customer_name from customer_names dictionary
        customer_number = row['customer_number']
        customer_name = customer_names.get(str(customer_number), '')
        fat_random_minutes = random.randint(1, 10)
        fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        fat_finish_time = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Fetch po_expire from po_expire_data dictionary
        po_expire = po_expire_data.get(customer_name, 0)  # Default to 0 if not found
        
        # Check if no_SO contains 'CRB' or 'BDG'
        if 'CRB' in no_SO or 'BDG' in no_SO:
            po_expired = order_time + np.timedelta64(po_expire + 7, 'D')
        else:
            po_expired = order_time + np.timedelta64(po_expire, 'D')

        pre_order_values = (
            "('{}', '{}', '{}', '{}', '{}')".format(
                no_PO, no_SO, customer_name,
                np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                np.datetime_as_string(po_expired, unit='D')
            )
        )
        preorder_query_values.append(pre_order_values)

        fat_start_value = (
            "('{}', '{}', '{}')".format(
                no_SO, fat_start_time, customer_name
            )
        )
        fat_start_values.append(fat_start_value)

        fat_finish_value = (
            "('{}', '{}', '{}', '{}', '{}')".format(
                no_SO, no_SO.replace('SO', 'SJ'), fat_finish_time, customer_name, 'Process'
            )
        )
        fat_finish_values.append(fat_finish_value)

    insert_query = (
        "INSERT INTO preorder (no_PO, no_SO, customer_name, order_time, po_expired) VALUES\n" +
        ',\n'.join(preorder_query_values) +
        ";\n/"
        "\nINSERT INTO order_checking_start (no_SO, start_check, customer_name) VALUES\n" +
        ',\n'.join(fat_start_values) +
        ";\n/"
        "\nINSERT INTO orders_checking_finish (no_SO, no_SJ, FAT_checking_finish, customer, status_FAT) VALUES\n" +
        ',\n'.join(fat_finish_values) +
        ";\n/"
    )

    return insert_query

def copy_to_clipboard(text):
    try:
        subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
        print("Query copied to clipboard.")
    except subprocess.CalledProcessError:
        print("Error copying to clipboard.")

if __name__ == "__main__":
    csv_file = 'PO_fetched.csv'
    json_file = 'customer_names.json'
    po_expire_file = 'po_expire.csv'
    
    # Load customer names from JSON file
    with open(json_file, 'r') as f:
        customer_names = json.load(f)
    
    # Read po_expire.csv into a DataFrame and create a dictionary
    po_expire_data = {}
    po_expire_df = pd.read_csv(po_expire_file)
    for _, row in po_expire_df.iterrows():
        po_expire_data[row['customer_name']] = row['po_expire']

    query = generate_single_query(csv_file, customer_names, po_expire_data)
    
    copy_to_clipboard(query)
    
    os.remove(csv_file)
    print("CSV file removed.")
