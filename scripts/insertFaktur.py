import pandas as pd
import numpy as np
import os
import json
import pymysql
import subprocess
import random
from datetime import datetime, timedelta
import math
import platform
import time
import re
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from env import env

"""
Script otomasi preorder dan validasi PO
"""

def execute_query(full_query):
    """Execute multiple SQL queries one by one."""
    queries = full_query.strip().split("delimiter")  # Splitting full_query into individual queries
    connection = pymysql.connect(host="192.168.1.291", user="root", password="sarwa", db="osc_clone")
    for query in queries:
        if query.strip():  # Check if the query is not just whitespace
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                connection.commit()
            except Exception as e:
                print(f"Error executing query: {e}")
                connection.rollback()  # Rollback in case of an error
    connection.close()

# Functions from fetch_PO.py
start_code_path = env.insertFaktur['start_code']
def clean(input_file, output_file):
    data = pd.read_csv(input_file, sep=';', skiprows=4)
    data.rename(columns={'Tgl Pesan': 'order_date', 'Unnamed: 2': 'no_SO', 'No. Pesanan': 'customer_number', 'Unnamed: 4': 'customer_name', 'Unnamed: 6': 'no_PO'}, inplace=True)
    selected = data[['order_date', 'no_PO', 'no_SO', 'customer_number']]
    cleaned = selected[selected['no_SO'].notna()]
    print(f'\n{input_file} has been cleaned and saved as {output_file}!')
    return cleaned

def process_csv(data):
    df = data.copy()

    month_translations = {
        "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
        "Mei": "May", "Jun": "Jun", "Jul": "Jul", "Agu": "Aug",
        "Sep": "Sep", "Okt": "Oct", "Nop": "Nov", "Des": "Dec"
    }
    for ind, eng in month_translations.items():
        df["order_date"] = df["order_date"].str.replace(ind, eng)
    
    time_input = pd.Timestamp.now().strftime('%H:%M:%S')
    df["order_date"] = pd.to_datetime(df["order_date"], format='%d %b %Y') 
    df["order_date"] = df["order_date"].dt.strftime('%Y-%m-%d') + ' ' + time_input
    
    # Load segment and start code from JSON file
    with open(start_code_path, 'r') as file:
        segments_startcodes = json.load(file)

    # Initialize an empty DataFrame to store results for all segments
    all_results_df = pd.DataFrame()
    
    # Process each segment and start code
    for segment, startcode in segments_startcodes.items():
        try:
            # Use regex to match both types of segments and extract them
            pattern = f"/SMR/({segment}/|{segment}$)"
            segment_match = df['no_SO'].str.extract(pattern)
            
            # Find the index of rows that matched the segment pattern
            matched_rows = segment_match.dropna().index
            
            # If no entry found for the current segment, skip to the next iteration
            if len(matched_rows) == 0:
                print(f"\nNo 'no_SO' entry found for segment: {segment}. Skipping...")
                continue
            
            segment_entry = df.loc[matched_rows[0], 'no_SO']  # Use the first matched row as sample

            # Extract year and month using regex
            year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
            match = re.search(year_month_pattern, segment_entry)
            if match:
                year, month = match.groups()
            else:
                print(f"\nFailed to extract year and month for segment: {segment}. Skipping...")
                continue
            
            # Construct start_range using the extracted year and month, and the current segment and startcode
            start_range = f"SO/SMR/{segment}/{year}/{month}/{startcode}"
            finish_range = start_range[:-4] + "9999"
            result_df = df[df['no_SO'].between(start_range, finish_range)]
            
            # Check if result_df is empty
            if result_df.empty:
                print(f"\nNo new orders found for segment: {segment}. Skipping...")
                continue
            
            # Concatenate the results for this segment to the overall results DataFrame
            all_results_df = pd.concat([all_results_df, result_df])

            # Update the start code for this segment in the JSON file
            # Extract the used codes from 'no_SO' and convert them to integers
            used_codes = result_df['no_SO'].apply(lambda x: int(x.split("/")[-1]))
            # Find the maximum used code
            max_used_code = used_codes.max()
            # Update the start code to be the maximum used code + 1, formatted with leading zeros
            segments_startcodes[segment] = str(max_used_code + 1).zfill(len(startcode))
            
        except Exception as e:
            print(f"\nAn error occurred while processing segment: {segment}. Error: {str(e)}. Skipping...")
            continue

    with open(start_code_path, 'w') as file:
        json.dump(segments_startcodes, file)

    return all_results_df

def generate_single_query(df, customer_names, po_expire_data):
    if df.empty:
        print("\nNo new orders found.")
        return None
    
    new_customer_query_values = []
    preorder_query_values = []
    validation_values = []

    for index, row in df.iterrows():

        customer_number = row['customer_number']
        if str(customer_number).startswith('MT-KF'):
            continue

        order_time = np.datetime64(row['order_date'])

        no_PO = '' if isinstance(row['no_PO'], float) and math.isnan(row['no_PO']) else row['no_PO']
        no_SO = '' if isinstance(row['no_SO'], float) and math.isnan(row['no_SO']) else row['no_SO']
        
        customer_name = customer_names.get(str(customer_number), '')


        if customer_name == '':
            customer_name_input = input(f"Enter customer name for {no_SO}: ").strip()
            if customer_name_input not in customer_names.values():
                code_market = input(f"Enter segment for {customer_name_input}: ")
                regency = input(f"Enter regency for {customer_name_input}: ")
                province = input(f"Enter province for {customer_name_input}: ")
                customer_address = input(f"Enter customer address for {customer_name_input}: ")

                new_customer_values = (
                "('{}', '{}', '{}', '{}', '{}')".format(
                    customer_number, customer_name_input, customer_address, regency, province
                    )
                )
                new_customer_query_values.append(new_customer_values)


            if customer_name_input not in customer_names.values():
                customer_names[str(customer_number)] = customer_name_input
                with open(customer_names_json, 'w') as f:
                    json.dump(customer_names, f, indent=4)
                print(f"\nAdded '{customer_name_input}' for customer number {customer_number} in customer_names.json")

                po_expire_data[customer_name_input] = 7
                with open(po_expire_file, 'w') as f:
                    json.dump(po_expire_data, f, indent=4)
                print(f"\nUpdated po_expire.json with default value for '{customer_name_input}'")
        
        if 'SO' in no_SO:
            fat_random_minutes = random.randint(1, 10)
            fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            fat_finish_time = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            
            po_expire_value = po_expire_data.get(customer_name, 4)  # Default to 4 days if not found
            po_expired = order_time + np.timedelta64(po_expire_value, 'D')
            
            pre_order_values = (
                "('{}', '{}', '{}', '{}', '{}','{}','{}','{}')".format(
                    no_SO, 
                    no_PO, 
                    'panel', 
                    customer_number, 
                    customer_name, 
                    np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                    np.datetime_as_string(po_expired, unit='s').replace('T', ' '),
                    'COD'
                )
            )
            preorder_query_values.append(pre_order_values)

            validation_value = (
                "('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    no_SO,
                    fat_start_time,
                    fat_finish_time,
                    'Process',
                    str(input('Note:'))
                )
            )
            validation_values.append(validation_value)
        else:
            p_expire_value = po_expire_data.get(customer_name, 4)  # Default to 4 days if not found
            p_expire = order_time + np.timedelta64(p_expire_value, 'D')
            pre_order_values = (
                "('{}', '{}', '{}', '{}', '{}','{}','{}','{}')".format(
                    no_SO, 
                    no_PO, 
                    'panel', 
                    customer_number, 
                    customer_name, 
                    np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                    np.datetime_as_string(p_expire, unit='s').replace('T', ' '),
                    'COD'
                )
            )
            preorder_query_values.append(pre_order_values)

    full_query = ""

    # Construct the new customer insert query if there are new customers to add
    if new_customer_query_values:
        new_customer_insert_query = "INSERT INTO customer (code_market, customer_name, regency, province, expedition_name, customer_address) VALUES\n"
        new_customer_insert_query += ',\n'.join(new_customer_query_values) + "delimiter"
        full_query += new_customer_insert_query  # Append this query to the full query

    # Construct the preorder insert query
    if preorder_query_values:
        preorder_insert_query = "\nINSERT INTO preorder (no_PO, no_SO, customer_name, order_time, po_expired) VALUES\n"
        preorder_insert_query += ',\n'.join(preorder_query_values) + "delimiter"
        full_query += preorder_insert_query  # Append this query to the full query

    if validation_values:
        validation_insert_query = "\nINSERT INTO validation (no_SO, start_check, finish_check, status, note) VALUES\n"
        validation_insert_query += ',\n'.join(validation_values) + "delimiter"
        full_query += validation_insert_query

    # Print all new customer queries for debugging purposes
    print("New Customer Queries: ", new_customer_query_values)

    # Return the full combined query
    return full_query

if __name__ == "__main__":
    cleaned_file = env.preorder['so_cleaned']
    po_fetched = env.preorder['po_fetched']
    customer_names_json = env.preorder['customer_names']
    po_expire_file = env.preorder['po_expire']
    
    with open(customer_names_json, 'r') as f:
        customer_names = json.load(f)
    
    with open(po_expire_file, 'r') as f:
        po_expire_data = json.load(f)

    try:
        while True:
            input_file = env.preorder['input_file']

            if os.path.exists(input_file):
                try:
                    cleaned_data = clean(input_file)
                    processed_data = process_csv(cleaned_data)

                    if not processed_data.empty:
                        query = generate_single_query(processed_data, customer_names, po_expire_data)
                        if query is not None:
                            execute_query(query)

                    os.remove(input_file)
                    print("\nSO file removed.")
                except Exception as e:
                    print(f'\n\nError: {e}')
            
            else:
                print("\nNo new SO")
            
            # Print current time
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("\nCurrent Time = {}\n".format(current_time))
            
            time.sleep(3)
    
    except KeyboardInterrupt:
        print("\nExiting the script. Goodbye!")
        # Here, you might perform any cleanup operations or save logs before exiting.

