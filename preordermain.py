import pandas as pd
import numpy as np
import os
import json
import subprocess
import random
from datetime import datetime, timedelta
import math
import time
import re

# Functions from fetch_PO.py

def clean(input_file, output_file):
    data = pd.read_csv(input_file, sep=';', skiprows=4)
    data.rename(columns={'Tgl Pesan': 'order_date', 'Unnamed: 2': 'no_SO', 'No. Pesanan': 'customer_number', 'Unnamed: 4': 'customer_name', 'Unnamed: 6': 'no_PO'}, inplace=True)
    selected = data[['order_date', 'no_PO', 'no_SO', 'customer_number']]
    cleaned = selected[selected['no_SO'].notna()]
    #cleaned['segment'] = cleaned['no_SO'].str.split('/').str[2]
    cleaned.to_csv(output_file, index=False)
    print(f'{input_file} has been cleaned and saved as {output_file}!')

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
    with open("/Users/rian/Documents/GitHub/WPAutomate/startcode.json", 'r') as file:
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
                print(f"No 'no_SO' entry found for segment: {segment}. Skipping...")
                continue
            
            segment_entry = df.loc[matched_rows[0], 'no_SO']  # Use the first matched row as sample

            # Extract year and month using regex
            year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
            match = re.search(year_month_pattern, segment_entry)
            if match:
                year, month = match.groups()
            else:
                print(f"Failed to extract year and month for segment: {segment}. Skipping...")
                continue
            
            # Construct start_range using the extracted year and month, and the current segment and startcode
            start_range = f"SO/SMR/{segment}/{year}/{month}/{startcode}"
            finish_range = start_range[:-4] + "9999"
            result_df = df[df['no_SO'].between(start_range, finish_range)]
            
            # Check if result_df is empty
            if result_df.empty:
                print(f"No new orders found for segment: {segment}. Skipping...")
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
            print(f"An error occurred while processing segment: {segment}. Error: {str(e)}. Skipping...")
            continue
    
    # Save the concatenated results to a single CSV file
    output_file = 'PO_fetched.csv'
    all_results_df.to_csv(output_file, index=False)
    print(f'{output_file} has been generated.')

    with open("/Users/rian/Documents/GitHub/WPAutomate/startcode.json", 'w') as file:
        json.dump(segments_startcodes, file)

# Functions from preorder.py

def generate_single_query(csv_file, customer_names, po_expire_data):
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        print("No new orders found.")
        os.remove(input_file)
        print("SO file removed.")
        return None
    
    preorder_query_values = []
    fat_start_values = []
    fat_finish_values = []

    for index, row in df.iterrows():
        order_time = np.datetime64(row['order_date'])

        no_PO = '' if isinstance(row['no_PO'], float) and math.isnan(row['no_PO']) else row['no_PO']
        no_SO = '' if isinstance(row['no_SO'], float) and math.isnan(row['no_SO']) else row['no_SO']
        
        customer_number = row['customer_number']
        customer_name = customer_names.get(str(customer_number), '')

        if customer_name == '':
            customer_name = input(f"Enter customer name for {no_SO}: ")

            if customer_name not in customer_names.values():
                customer_names[str(customer_number)] = customer_name
                with open(json_file, 'w') as f:
                    json.dump(customer_names, f, indent=4)
                print(f"\nAdded '{customer_name}' for customer number {customer_number} in customer_names.json")

                po_expire_data[customer_name] = 4
                with open(po_expire_file, 'w') as f:
                    json.dump(po_expire_data, f, indent=4)
                print(f"\nUpdated po_expire.json with default value for '{customer_name}'")
        
        if 'SO' in no_SO:
            fat_random_minutes = random.randint(1, 10)
            fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            fat_finish_time = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
            
            po_expire_value = po_expire_data.get(customer_name, 4)  # Default to 4 days if not found
            po_expired = order_time + np.timedelta64(po_expire_value, 'D')
            
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
            p_expire_value = po_expire_data.get(customer_name, 4)  # Default to 4 days if not found
            p_expire = order_time + np.timedelta64(p_expire_value, 'D')
            pre_order_values = (
                "('{}', '{}', '{}', '{}', '{}')".format(
                    no_PO, no_SO, customer_name,
                    np.datetime_as_string(order_time, unit='s').replace('T', ' '),
                    np.datetime_as_string(p_expire, unit='s').replace('T', ' ')
                )
            )
            preorder_query_values.append(pre_order_values)

    
    if preorder_query_values:
        insert_query = "INSERT INTO preorder (no_PO, no_SO, customer_name, order_time, po_expired) VALUES\n"
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
    cleaned_file = '/Users/rian/Documents/GitHub/WPAutomate/SO_cleaned.csv'
    csv_file = '/Users/rian/Documents/GitHub/WPAutomate/PO_fetched.csv'
    json_file = '/Users/rian/Documents/GitHub/WPAutomate/customer_names.json'
    po_expire_file = '/Users/rian/Documents/GitHub/WPAutomate/po_expire.json'
    
    with open(json_file, 'r') as f:
        customer_names = json.load(f)
    
    with open(po_expire_file, 'r') as f:
        po_expire_data = json.load(f)

    try:
        while True:
            input_file = r'/Volumes/PUBLIC/SC - RIAN (Intern)/1.csv'

            if os.path.exists(input_file):
                try:
                    clean(input_file, cleaned_file)
                    cleaned_data = pd.read_csv(cleaned_file)
                    process_csv(cleaned_data)
                    os.remove(cleaned_file)
                    print(f'{cleaned_file} has been removed.')
                except Exception as e:
                    print(f'\n\nError: {e}')
            
                if os.path.exists(csv_file):
                    query = generate_single_query(csv_file, customer_names, po_expire_data)
                    if query is not None:
                        copy_to_clipboard(query)
                        os.remove(csv_file)
                        print("CSV file removed.")
                        os.remove(input_file)
                        print("SO file removed.")
                else:
                    print(f"CSV file '{csv_file}' does not exist.")
            else:
                print("No new SO")
            #PRINT TIME NOW
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("Current Time = {}\n".format(current_time))
            time.sleep(3)
    
    except KeyboardInterrupt:
        print("\nExiting the script. Goodbye!")
        # Here, you might perform any cleanup operations or save logs before exiting.

