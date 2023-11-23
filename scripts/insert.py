import pandas as pd
import numpy as np
import pymysql
import os
import re
import math
import json
import shutil
import time
import sys
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from env import env


def clean(datapath):

    header = [
    'inv_number',
    'po_number',
    'channel',
    'customer_id',
    'customer_name',
    'order_time',
    'po_expired',
    'term_payment',
    'sales_name',
    'note'
]

    combined = pd.DataFrame(columns=header)

    if datapath.contains('SC_02. Sales_Order.xls'):
        smr = pd.read_excel(smr_path, sheet_name='Sheet1')
        smr = smr[['No. Pesanan', 'Tgl Pesan','No. Pelanggan','Nama Pelanggan', 'Nama Penjual', 'No. PO', 'Name Syarat Pembayaran']]
        smr.rename(columns={'No. Pesanan': "inv_number", 'Tgl Pesan': "order_time", 'No. Pelanggan': "customer_id", 'Nama Pelanggan': "customer_name",'Nama Penjual': "sales_name", 'No. PO': 'po_number' ,'Name Syarat Pembayaran': "term_payment"}, inplace=True)
        smr = smr[~smr['customer_name'].isin(['APOTEK SUMBER SARI', 'APOTEK AIMAR'])]
        smr = smr[~((smr['customer_name'] == 'APOTEK SWADAYA SEHAT') & (smr['customer_id'].str.startswith('PNL')))]
        smr.drop_duplicates(subset=['inv_number'], inplace=True)
        smr['po_expired'] = ''
        smr['channel'] = 'smr'
        smr['note'] = ''
        smr['term_payment'] = smr['term_payment'].str.replace('.', '')
        smr.fillna('', inplace=True)
        smr = smr[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]
        
        combined = pd.concat([combined, smr], ignore_index=True)

    elif datapath.contains('INV Panel.xlsx'):
        panel = pd.read_excel(panel_path, sheet_name='tb_panel')
        panel = panel[['No Faktur', 'Administration Time', 'Customer Name', 'Term Payment', 'Sales Name', 'Po Expired']]
        panel.rename(columns={'No Faktur': "inv_number", 'Administration Time': "order_time", 'Customer Name': "customer_name",'Term Payment': 'term_payment', 'Sales Name': "sales_name", 'Po Expired': 'po_expired'}, inplace=True)
        panel.drop_duplicates(subset=['inv_number'], inplace=True)
        # convert po_expired into YYYY-MM-DD format
        panel['po_expired'] = pd.to_datetime(panel['po_expired'], format='%d %b %Y')
        panel['customer_id'] = ''
        panel['channel'] = 'panel'
        panel['po_number'] = ''
        panel['note'] = ''
        panel = panel[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]

        combined = pd.concat([combined, panel], ignore_index=True)
    else:
        print('Invalid dataset')

    return combined

def process(data):
    df = data.copy()
    if df['channel'].iloc[0] == 'smr':
        time_input =  pd.Timestamp.now().strftime('%H:"%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_smr, 'r') as file:
            segments_start_code = json.load(file)
        
        results = pd.DataFrame()

        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"/SMR/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue
                
                segment_entry = df.loc[matched_rows[0], 'noSO']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and motnh for segment {segment}. Skipping")
                    continue

                start_range = f"SO/SMR/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}")
                continue
        
        with open(start_code_smr, 'w') as file:
            json.dump(segments_start_code, file)
        
        return results

    elif data['channel'].iloc[0] == 'panel':
        time_input = pd.Timestamp.now().strftime('%H:"%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_panel, 'r') as file:
            segments_start_code = json.load(file)

        results = pd.DataFrame()

        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"INV/ASW/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue
                
                segment_entry = df.loc[matched_rows[0], 'inv_number']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping")
                    continue

                start_range = f"INV/ASW/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}")
                continue
        
        with open(start_code_panel, 'w') as file:
            json.dump(segments_start_code, file)

        return results

    else:
        print('Invalid dataset')

def generate_query(data, customer_names, po_expire):
    if data.empty:
        print('No data to be inserted')
        return None
    
    new_customer_query_values = []
    preorder_query_values = []
    validation_query_values = []

    if data['channel'].iloc[0] == 'smr':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = row['customer_id']
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_inv = '' if isinstance(row['inv_number'], float) and math.isnan(row['inv_number']) else row['inv_number']
            no_po = '' if isinstance(row['po_number'], float) and math.isnan(row['po_number']) else row['po_number']

            if customer_name == '':
                customer_name_input = input(f"Enter customer name for {no_inv}: ").strip()
                if customer_name_input not in customer_names.values():
                    regency = input(f"Enter regency for {customer_name_input}: ").strip()
                    province = input(f"Enter province for {customer_name_input}: ").strip()
                    customer_address = input(f"Enter address for {customer_name_input}: ").strip()

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name_input,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name_input not in customer_names.values():
                    customer_names[str(customer_number)] = customer_name_input
                    with open(customer_names_json, 'w') as f:
                        json.dump(customer_names, f)
                    print(f"\nAdded '{customer_name_input}' for customer number {customer_number} in customer_names.json")

                    po_expire[customer_name_input] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name_input}'")

            fat_random_minute = np.random.randint(1, 10)
            start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')
            finish_time = (pd.to_datetime(start_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')

            po_expire_value = po_expire.get(customer_name, 4)
            po_expired = order_time + np.timedelta64(po_expire_value, 'D')

            preorder_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
                    no_inv,
                    no_po,
                    'non-panel',
                    customer_number,
                    customer_name,
                    order_time,
                    po_expired,
                    row['term_payment'],
                    row['sales_name'],
                    row['note']
                )
            )
            preorder_query_values.append(preorder_value)

            validation_value = (
                "('{}','{}','{}','{}','{}')".format(
                    no_inv,
                    start_time,
                    finish_time,
                    'Process',
                    ''
                )
            )
            validation_query_values.append(validation_value)

        full_query = ''

        if new_customer_query_values:
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            preorder_query = (
                "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}".format(
                    ','.join(preorder_query_values)
                )
            )
            full_query += preorder_query + '\n\n'
        
        if validation_query_values:
            validation_query = (
                "INSERT INTO validation (inv_number, start_check, finish_check, fat_status, note) VALUES {}".format(
                    ','.join(validation_query_values)
                )
            )
            full_query += validation_query + '\n\n'

        print("New Customer log: \n{}".format(new_customer_query))
        return full_query

    elif data['channel'].iloc[0] == 'panel':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = row['customer_id']
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_inv = row['inv_number']
            no_po = ''

            if customer_name == '':
                customer_name_input = input(f"Enter customer name for {no_inv}: ").strip()
                if customer_name_input not in customer_names.values():
                    regency = input(f"Enter regency for {customer_name_input}: ").strip()
                    province = input(f"Enter province for {customer_name_input}: ").strip()
                    customer_address = input(f"Enter address for {customer_name_input}: ").strip()

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name_input,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name_input not in customer_names.values():
                    customer_names[str(customer_number)] = customer_name_input
                    with open(customer_names_json, 'w') as f:
                        json.dump(customer_names, f)
                    print(f"\nAdded '{customer_name_input}' for customer number {customer_number} in customer_names.json")

                    po_expire[customer_name_input] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name_input}'")

            fat_random_minute = np.random.randint(1, 10)
            start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')
            finish_time = (pd.to_datetime(start_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')

            po_expire_value = po_expire.get(customer_name, 4)
            po_expired = order_time + np.timedelta64(po_expire_value, 'D')

            preorder_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
                    no_inv,
                    no_po,
                    'non-panel',
                    customer_number,
                    customer_name,
                    order_time,
                    po_expired,
                    row['term_payment'],
                    row['sales_name'],
                    row['note']
                )
            )
            preorder_query_values.append(preorder_value)

        full_query = ''

        if new_customer_query_values:
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            preorder_query = (
                "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}".format(
                    ','.join(preorder_query_values)
                )
            )
            full_query += preorder_query + '\n\n'

        print("New Customer log: \n{}".format(new_customer_query))
        return full_query
    
    else:
        print('Invalid dataset')

def insert(query):
    connection = pymysql.connect(host='192.168.1.219', user='root', password='sarwa', db='osc_clone')
    try:
        query_lines = query.splitlines()
        with connection.cursor() as cursor:
            for i, line in tqdm(enumerate(query_lines), total=len(query_lines), desc="Executing queries"):
                cursor.execute(line)
        connection.commit() # commit changes
        print("Query executed successfully")
    except Exception as e:
        print("Error executing query with log: {}".format(e))
    finally:
        connection.close()


if __name__ == "__main__":
    smr_path = env.insert['smr']
    panel_path = env.insert['panel']
    customer_names_json = env.insert['customer_names']
    start_code_smr = env.insert['start_code_smr']
    start_code_panel = env.insert['start_code_panel']
    po_expire_json = env.insert['po_expire']


    with open(customer_names_json, 'r') as f:
        customer_names = json.load(f)

    with open(po_expire_json, 'r') as f:
        po_expire = json.load(f)

    try:
        while True:
            if os.path.exists(smr_path):
                cleaned = clean(smr_path)
                processed = process(cleaned)

                if not processed.empty:
                    query = generate_query(processed)
                    if query is not None:
                        insert(query)
                # move file to 'ORIGINAL' folder inside SC_DATAMART/ORIGINAL folder
                shutil.move(smr_path, smr_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            elif os.path.exists(panel_path):
                cleaned = clean(panel_path)
                processed = process(cleaned)

                if not processed.empty:
                    query = generate_query(processed)
                    if query is not None:
                        insert(query)
                # move file to 'ORIGINAL' folder inside SC_DATAMART/ORIGINAL folder
                shutil.move(panel_path, panel_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            else:
                print('Waiting for file...')

                now = datetime.now()
                current = now.strftime("%H:%M:%S")
                print("Current Time =", current)

                time.sleep(3)
    except KeyboardInterrupt:
        print('Interrupted')