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
        
        customer_number = row['customer_number']
        customer_name = customer_names.get(str(customer_number), '')
        
        if 'SO' in no_SO:
            fat_random_minutes = random.randint(1, 10)
            fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            fat_finish_time = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            
            po_expire_info = po_expire_data.get(customer_name)
            if po_expire_info:
                po_expire_value = int(po_expire_info['po_expire'])  # Convert the string to an integer
                po_expired = order_time + np.timedelta64(po_expire_value, 'D')
            else:
                po_expired = order_time + np.timedelta64(4, 'D')  # Default to 4 days
            
            pre_order_values = (
                "('{}', '{}', '{}', '{}', '{}')".format(
                    no_PO, no_SO, customer_name,
                    np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                    np.datetime_as_string(po_expired, unit='s').replace('T', ' ')
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
        else:
            pre_order_values = (
                "('{}', '{}', '{}', '{}', '{}')".format(
                    no_PO, no_SO, customer_name,
                    np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                    np.datetime_as_string(order_time, unit='s').replace('T', ' ')
                )
            )
            preorder_query_values.append(pre_order_values)

    insert_query = "INSERT INTO preorder (no_PO, no_SO, customer_name, order_time, po_expired) VALUES\n"
    if preorder_query_values:
        insert_query += ',\n'.join(preorder_query_values) + ";\n/"
    
    if fat_start_values:
        insert_query += "\nINSERT INTO order_checking_start (no_SO, start_check, customer_name) VALUES\n"
        insert_query += ',\n'.join(fat_start_values) + ";\n/"
    
    if fat_finish_values:
        insert_query += "\nINSERT INTO orders_checking_finish (no_SO, no_SJ, FAT_checking_finish, customer, status_FAT) VALUES\n"
        insert_query += ',\n'.join(fat_finish_values) + ";\n/"

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
    po_expire_file = 'po_expire.json'  # Change to JSON file
    
    with open(json_file, 'r') as f:
        customer_names = json.load(f)
    
    # Load po_expire.json and create a dictionary with customer names as keys and po_expire information as values
    with open(po_expire_file, 'r') as f:
        po_expire_data = {entry['customer_name']: entry for entry in json.load(f)}
    
    query = generate_single_query(csv_file, customer_names, po_expire_data)
    
    copy_to_clipboard(query)
    
    os.remove(csv_file)
    print("CSV file removed.")
