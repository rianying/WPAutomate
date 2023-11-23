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
from datetime import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from env import env


def clean(datapath):
    if datapath.contains('SC_02. Sales_Order.xls'):
        smr = pd.read_excel(datapath, sheet_name='Sheet1')
        smr = smr[['No. Pesanan', 'Tgl Pesan','No. Pelanggan','Nama Pelanggan', 'Nama Penjual', 'No. PO', 'Name Syarat Pembayaran']]
        smr.rename(columns={'No. Pesanan': "noSO", 'Tgl Pesan': "tanggal", 'No. Pelanggan': "idCustomer", 'Nama Pelanggan': "namaCustomer",'Nama Penjual': "sales", 'No. PO': 'noPO' ,'Name Syarat Pembayaran Faktur': "termPembayaran"}, inplace=True)
        smr = smr[~smr['namaCustomer'].isin(['APOTEK SUMBER SARI', 'APOTEK AIMAR'])]
        smr = smr[~((smr['namaCustomer'] == 'APOTEK SWADAYA SEHAT') & (smr['idCustomer'].str.startswith('PNL')))]
        smr.drop_duplicates(subset=['noSO'], inplace=True)
        smr['type'] = 'smr'
        return smr
    elif datapath.contains('SC_01. Invoice_ASW.xls'):
        panel = pd.read_excel(datapath, sheet_name='Sheet1')
        panel = panel[['No. Faktur', 'Tgl Faktur', 'Keterangan', 'No. Pelanggan', 'Nama Pelanggan','Nama Penjual','Name Syarat Pembayaran Faktur']]
        panel.rename(columns={'No. Faktur': "faktur", 'Tgl Faktur': "tanggal", 'Keterangan': 'keterangan', 'No. Pelanggan': "idCustomer", 'Nama Pelanggan': "namaCustomer",'Nama Penjual': "sales", 'Name Syarat Pembayaran Faktur': "termPembayaran"}, inplace=True)
        panel['keterangan'].fillna('', inplace=True)
        panel.drop_duplicates(subset=['faktur'], inplace=True)
        panel['type'] = 'panel'
        return panel
    else:
        print('Invalid dataset')

def process(data):
    df = data.copy()
    if df['type'].iloc[0] == 'smr':
        time_input =  pd.Timestamp.now().strftime('%H:"%M:%S')
        df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d %b %Y')
        df['tanggal'] = df['tanggal'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_smr, 'r') as file:
            segments_start_code = json.load(file)
        
        results = pd.DataFrame()

        for segment, startcode in segments_start_code.items():
            try:
                pattern = f"/SMR/({segment}/|{segment}$)"
                segment_match = df['noSO'].str.extract(pattern)

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
                result = df[df['noSO'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue

                results = pd.concat([results, result])

                used_codes = result['noSO'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}")
                continue
        
        with open(start_code_smr, 'w') as file:
            json.dump(segments_start_code, file)
        
        return results

    elif data['type'].iloc[0] == 'panel':
        time_input = pd.Timestamp.now().strftime('%H:"%M:%S')
        df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d %b %Y')
        df['tanggal'] = df['tanggal'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_panel, 'r') as file:
            segments_start_code = json.load(file)

        results = pd.DataFrame()

        for segment, startcode in segments_start_code.items():
            try:
                pattern = f"/PANEL/({segment}/|{segment}$)"
                segment_match = df['faktur'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue
                
                segment_entry = df.loc[matched_rows[0], 'faktur']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping")
                    continue

                start_range = f"INV/SMR/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['faktur'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping")
                    continue

                results = pd.concat([results, result])

                used_codes = result['faktur'].apply(lambda x: int(x.split("/")[-1]))
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

    if data['type'].iloc[0] == 'smr':
        for index, row in data.iterrows():
            customer_number = row['idCustomer']
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['tanggal'])
            no_so = '' if isinstance(row['noPO'], float) and math.isnan(row['noPO']) else row['noPO']
            no_inv = no_so.replace('SO', 'INV')
            no_po = '' if isinstance(row['noPO'], float) and math.isnan(row['noPO']) else row['noPO']

            if customer_name == '':
                customer_name_input = input(f"Enter customer name for {no_so}: ").strip()
                if customer_name_input not in customer_names.values():
                    regency = input(f"Enter regency for {customer_name_input}: ").strip()
                    province = input(f"Enter province for {customer_name_input}: ").strip()
                    customer_address = input(f"Enter address for {customer_name_input}: ").strip()

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name_input,
                            regency,
                            province,
                            customer_address,
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
                    customer_number,
                    customer_name,
                    order_time,
                    no_inv,
                    no_po,
                    row['sales'],
                    row['termPembayaran'],
                    row['type'],
                    po_expired,
                    row['tanggal']
                )
            )
            preorder_query_values.append(preorder_value)

            validation_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
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
                "INSERT INTO customer (idCustomer, namaCustomer, regency, province, address) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            preorder_query = (
                "INSERT INTO preorder (idCustomer, namaCustomer, orderTime, noInv, noPO, sales, termPembayaran, type, poExpired, tanggal) VALUES {}".format(
                    ','.join(preorder_query_values)
                )
            )
            full_query += preorder_query + '\n\n'
        
        if validation_query_values:
            validation_query = (
                "INSERT INTO validation (noInv, startTime, finishTime, status, notes) VALUES {}".format(
                    ','.join(validation_query_values)
                )
            )
            full_query += validation_query + '\n\n'

        print("New Customer log: \n{}".format(new_customer_query))
        return full_query

    elif data['type'].iloc[0] == 'panel':
        for index, row in data.iterrows():
            customer_number = row['idCustomer']
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['tanggal'])
            no_so = '' if isinstance(row['noPO'], float) and math.isnan(row['noPO']) else row['noPO']
            no_inv = no_so.replace('SO', 'INV')
            no_po = '' if isinstance(row['noPO'], float) and math.isnan(row['noPO']) else row['noPO']

            if customer_name == '':
                customer_name_input = input(f"Enter customer name for {no_so}: ").strip()
                if customer_name_input not in customer_names.values():
                    regency = input(f"Enter regency for {customer_name_input}: ").strip()
                    province = input(f"Enter province for {customer_name_input}: ").strip()
                    customer_address = input(f"Enter address for {customer_name_input}: ").strip()

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name_input,
                            regency,
                            province,
                            customer_address,
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
                "('{}','{}','{}','{}','{}','{}','{}','{}')".format(
                    customer_name,
                    order_time,
                    no_inv,
                    no_po,
                    row['sales'],
                    row['termPembayaran'],
                    po_expired,
                    row['tanggal']
                )
            )
            preorder_query_values.append(preorder_value)

            validation_value = (
                "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
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
                "INSERT INTO customer (idCustomer, namaCustomer, regency, province, address) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            preorder_query = (
                "INSERT INTO preorder (namaCustomer, orderTime, noInv, noPO, sales, termPembayaran, poExpired, tanggal) VALUES {}".format(
                    ','.join(preorder_query_values)
                )
            )
            full_query += preorder_query + '\n\n'

        if validation_query_values:
            validation_query = (
                "INSERT INTO validation (noInv, startTime, finishTime, status, notes) VALUES {}".format(
                    ','.join(validation_query_values)
                )
            )
            full_query += validation_query + '\n\n'

        print("New Customer log: \n{}".format(new_customer_query))

        return full_query
    else:
        print('Invalid dataset')

def insert(query):
    connection = pymysql.connect(host='192.168.1.219', user='root', password='sarwa', db='osc_clone')
    try:
        with connection.cursor() as cursor:
            cursor.execute(query) # execute query
            # print each query line with format {query num}: {total query line}
            for i, line in enumerate(query.splitlines()):
                print(f"Executed: {i}: {line}")
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
                shutil.move(smr_path, smr_path.replace('SC_DATAMART', 'SC_DATAMART/ORIGINAL'))

            elif os.path.exists(panel_path):
                cleaned = clean(panel_path)
                processed = process(cleaned)

                if not processed.empty:
                    query = generate_query(processed)
                    if query is not None:
                        insert(query)
                # move file to 'ORIGINAL' folder inside SC_DATAMART/ORIGINAL folder
                shutil.move(panel_path, panel_path.replace('SC_DATAMART', 'SC_DATAMART/ORIGINAL'))

            else:
                print('Waiting for file...')

                now = datetime.now()
                current = now.strftime("%H:%M:%S")
                print("Current Time =", current)

                time.sleep(3)
    except KeyboardInterrupt:
        print('Interrupted')