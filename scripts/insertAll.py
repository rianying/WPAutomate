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


segment_mapping = {
    'SF/HQ': ('JAKARTA', 'DKI JAKARTA'),
    'SF/BDG': ('BANDUNG', 'JAWA BARAT'),
    'SF/SKB': ('SUKABUMI', 'JAWA BARAT'),
    'SF/CJR': ('CIANJUR', 'JAWA BARAT'),
    'SF/TSM': ('TASIKMALAYA', 'JAWA BARAT'),
    'SF/TGR': ('TANGERANG', 'BANTEN'),
    'SF/BGR': ('BOGOR', 'JAWA BARAT'),
    'SF/SRG': ('SERANG', 'BANTEN'),
    'SF/SBG': ('SUBANG', 'JAWA BARAT'),
    'SF/CRB': ('CIREBON', 'JAWA BARAT'),
    'SF/BJR': ('BANJARNEGARA', 'JAWA TENGAH'),
    'SF/LBK': ('LEBAK', 'BANTEN'),
    'SF/PKL': ('PEKALONGAN', 'JAWA TENGAH'),
    'SF/PMK': ('PAMEKASAN', 'JAWA TIMUR'),
    'SF/PNR': ('PONOROGO', 'JAWA TIMUR'),
    'SF/MLG': ('MALANG', 'JAWA TIMUR'),
    'SF/SLO': ('SOLO', 'JAWA TENGAH'),
    'SF/BJN': ('BOJONEGORO', 'JAWA TIMUR'),
    'SF/LMG': ('LAMONGAN', 'JAWA TIMUR'),
    'SF/KDR': ('KEDIRI', 'JAWA TIMUR'),
    'SF/LMJ': ('LUMAJANG', 'JAWA TIMUR'),
    'SF/TGL': ('TEGAL', 'JAWA TENGAH'),
    'SF/SMG': ('SEMARANG', 'JAWA TENGAH'),
    'SF/KDS': ('KUDUS', 'JAWA TENGAH'),
    'SF/GBG': ('GROBOGAN', 'JAWA TENGAH'),
    'SF/MDN': ('MADIUN', 'JAWA TIMUR'),
    'SF/JBR': ('JEMBER', 'JAWA TIMUR'),
    'SF/SBY': ('SURABAYA', 'JAWA TIMUR'),
    'SF/PWT': ('PURWOKERTO', 'JAWA TIMUR'),
    'SF/DIY': ('YOGYAKARTA', 'DAERAH ISTIMEWA YOGYAKARTA'),
}

def extract_segment(inv_number, channel):
    if channel == 'panel':
        parts = inv_number.split('/')
        if len(parts) > 3:
            return '/'.join(parts[2:4])
        return None
    elif channel == 'smr':
        parts = inv_number.split('/')
        smr_index = parts.index('SMR') + 1
        segment = parts[smr_index]
        if not parts[smr_index + 1].startswith('23'):# It's a compound segment, add the next part to the segment
            segment += '/' + parts[smr_index + 1]
        return segment

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

    if 'SMR_JKT_DIY' in datapath:
        print('Cleaning SMR data\n')
        smr = pd.read_excel(datapath, sheet_name='SMR_JKT_DIY')
        smr = smr[['No. Pesanan', 'Tgl Pesan', 'No. PO', 'No. Pelanggan', 'Nama Pelanggan', 'Nama Penjual', 'Name Syarat Pembayaran']]
        smr.rename(columns={'No. Pesanan': "inv_number", 'Tgl Pesan': "order_time", 'No. PO': 'po_number', 'No. Pelanggan': 'customer_id', 'Nama Pelanggan': "customer_name", 'Nama Penjual': "sales_name", 'Name Syarat Pembayaran': 'term_payment',}, inplace=True)
        smr.drop_duplicates(subset=['inv_number'], inplace=True)
        smr['po_expired'] = ''
        smr['channel'] = 'smr'
        smr['note'] = ''
        smr.fillna('', inplace=True)
        smr = smr[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]
        
        combined = pd.concat([combined, smr], ignore_index=True)

    elif 'INV Panel.xlsx' in datapath:
        print('Cleaning INV Panel data\n')
        panel = pd.read_excel(panel_path, sheet_name='tb_panel')
        panel = panel[['No Faktur', 'Administration Time', 'Customer Id', 'Customer Name', 'Term Payment', 'Sales Name', 'Po Expired', 'Keterangan']]
        panel.rename(columns={'No Faktur': "inv_number", 'Administration Time': "order_time", 'Customer Id': 'customer_id', 'Customer Name': "customer_name",'Term Payment': 'term_payment', 'Sales Name': "sales_name", 'Po Expired': 'po_expired', 'Keterangan': 'note'}, inplace=True)
        panel.drop_duplicates(subset=['inv_number'], inplace=True)
        # convert po_expired into YYYY-MM-DD format
        panel['po_expired'] = pd.to_datetime(panel['po_expired'], format='%d %b %Y')
        panel['channel'] = 'panel'
        panel['po_number'] = ''
        # replace note with '' if its 0
        panel['note'] = panel['note'].replace(0, '')
        panel = panel[['inv_number','po_number','channel','customer_id','customer_name','order_time','po_expired','term_payment','sales_name','note']]

        combined = pd.concat([combined, panel], ignore_index=True)
    else:
        print('Invalid dataset\n')

    return combined

def process(data):
    df = data.copy()
    results = pd.DataFrame()
    if df['channel'].iloc[0] == 'smr':
        time_input =  pd.Timestamp.now().strftime('%H:%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_smr, 'r') as file:
            segments_start_code = json.load(file)

        new_segments = False

        for inv_number in tqdm(df['inv_number'].unique(), desc='Processing segments'):
            segment = extract_segment(inv_number, 'smr')

            if not segment:
                continue

            if segment not in segments_start_code:
                print(f"\nNew segment found: {segment}. Adding with start code '0001'\n")
                segments_start_code[segment] = '0001'
                new_segments = True
        
        if new_segments:
            with open(start_code_smr, 'w') as file:
                json.dump(segments_start_code, file, indent=4)

        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"/SMR/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue
                
                segment_entry = df.loc[matched_rows[0], 'inv_number']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping\n")
                    continue

                start_range = f"SO/SMR/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}\n")
                continue
        
        with open(start_code_smr, 'w') as file:
            json.dump(segments_start_code, file, indent=4)

    elif data['channel'].iloc[0] == 'panel':
        time_input = pd.Timestamp.now().strftime('%H:%M:%S')
        df['order_time'] = pd.to_datetime(df['order_time'], format='%d %b %Y')
        df['order_time'] = df['order_time'].dt.strftime('%Y-%m-%d') + ' ' + time_input

        with open(start_code_panel, 'r') as file:
            segments_start_code = json.load(file)

        new_segments = False

        for inv_number in tqdm(df['inv_number'].unique(), desc='Processing segments'):
            segment = extract_segment(inv_number, 'panel') 
            if not segment:
                continue

            if segment not in segments_start_code:
                print(f"\nNew segment found: {segment}. Adding with start code '0001'\n")
                segments_start_code[segment] = '0001'
                new_segments = True

        if new_segments:
            with open(start_code_panel, 'w') as file:
                json.dump(segments_start_code, file, indent=4)


        for segment, startcode in tqdm(segments_start_code.items(), desc='Processing segments'):
            try:
                pattern = f"INV/ASW/({segment}/|{segment}$)"
                segment_match = df['inv_number'].str.extract(pattern)

                matched_rows = segment_match.dropna().index

                if len(matched_rows) == 0:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue    
                
                segment_entry = df.loc[matched_rows[0], 'inv_number']

                year_month_pattern = r"/(\d{2})/([A-Z]{1,3})/"
                match = re.search(year_month_pattern, segment_entry)
                if match:
                    year, month = match.groups()
                else:
                    print(f"\nFailed to extract year and month for segment {segment}. Skipping\n")
                    continue

                start_range = f"INV/ASW/{segment}/{year}/{month}/{startcode}"
                finish_range = start_range[:-4] + "9999"
                result = df[df['inv_number'].between(start_range, finish_range)]

                if result.empty:
                    print(f"\nNo sales entry found for segment {segment}. Skipping\n")
                    continue

                results = pd.concat([results, result])

                used_codes = result['inv_number'].apply(lambda x: int(x.split("/")[-1]))
                max = used_codes.max()
                segments_start_code[segment] = str(max + 1).zfill(len(startcode))
            except Exception as e:
                print(f"\nError processing segment {segment} with log: {e}\n")
                continue
        
        with open(start_code_panel, 'w') as file:
            json.dump(segments_start_code, file, indent=4)
        
    else:
        print('\nInvalid dataset\n')
    
    return results

def generate_query(data, customer_names, po_expire):
    missing_segment_file = env.insert['missing_segment']
    batch = 20

    if data.empty:
        print('\nNo data to be inserted\n')
        return None
    
    new_customer_query_values = []
    preorder_query_values = []
    validation_query_values = []
    full_query = ''

    if data['channel'].iloc[0] == 'smr':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = str(row['customer_id'])
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_SO = '' if isinstance(row['inv_number'], float) and math.isnan(row['inv_number']) else row['inv_number']
            no_inv = no_SO.replace('SO', 'INV')
            no_po = '' if isinstance(row['po_number'], float) and math.isnan(row['po_number']) else row['po_number']
            customer_name = customer_name.strip().replace('\n', ' ').replace('\r', '')
            note_sanitized = row['note'].strip().replace('\n', ' ').replace('\r', '')

            if customer_name == '':
                customer_name = row['customer_name']
                if customer_name not in customer_names.values():
                    segment = extract_segment(no_inv, data['channel'].iloc[0])
                    print(f"\nExtracted segment for invoice number {no_inv}: {segment}\n")  # Debug print
                    regency, province = segment_mapping.get(segment, ('', ''))
                    print(f"\nRegency: {regency}, Province: {province} for segment {segment}\n")  # Debug print
                    if regency == '' and province == '':
                        with open(missing_segment_file, 'a') as f:
                            f.write(f"{customer_number}: {customer_name}\n")
                    customer_address = ''

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name not in customer_names.values():
                    customer_name = customer_name.replace('\u00a0', ' ')
                    customer_names[str(customer_number)] = customer_name
                    with open(customer_names_json, 'w', encoding='utf-8') as f:
                        json.dump(customer_names, f, indent=4)
                    print(f"\nAdded '{customer_name}' for customer number {customer_number} in customer_names.json\n")

                    po_expire[customer_name] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name}'\n")

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
                    row['term_payment'].strip(),
                    row['sales_name'].strip(),
                    row['note'].strip()
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

        if new_customer_query_values:
            print('\n\nNew customer found\n\n')
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            total_batches = (len(preorder_query_values) + batch - 1) // batch
            for i in range(0, len(preorder_query_values), batch):
                batch_value = preorder_query_values[i:i+batch]
                preorder_query = (
                    "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}"
                    .format(','.join(batch_value))
                )
                full_query += preorder_query + '\n\n'
                print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")
        
            if validation_query_values:
                total_batches = (len(validation_query_values) + batch - 1) // batch
                for i in range(0, len(validation_query_values), batch):
                    batch_value = validation_query_values[i:i+batch]
                    validation_query = (
                        "INSERT INTO validation (inv_number, start_check, finish_check, fat_status, note) VALUES {}".format(
                            ','.join(batch_value)
                        )
                    )
                    full_query += validation_query + '\n\n'
                    print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")

    elif data['channel'].iloc[0] == 'panel':
        for index, row in tqdm(data.iterrows(), total=data.shape[0], desc='Generating queries'):
            customer_number = str(row['customer_id'])
            customer_name = customer_names.get(str(customer_number), '')
            order_time = np.datetime64(row['order_time'])
            no_inv = row['inv_number']
            no_po = ''
            po_expired = row['po_expired']

            if customer_name == '':
                customer_name = row['customer_name']
                if customer_name not in customer_names.values():
                    segment = extract_segment(no_inv, data['channel'].iloc[0])
                    print(f"\nExtracted segment for invoice number {no_inv}: {segment}\n")  # Debug print
                    regency, province = segment_mapping.get(segment, ('', ''))
                    print(f"\nRegency: {regency}, Province: {province} for segment {segment}\n")  # Debug print
                    if regency == '' and province == '':
                        with open(missing_segment_file, 'a') as f:
                            f.write(f"{customer_number}: {customer_name}\n")
                    customer_address = ''

                    new_customer_value = (
                        "('{}','{}','{}','{}','{}')".format(
                            customer_number,
                            customer_name,
                            customer_address,
                            regency,
                            province,
                        )
                    )
                    new_customer_query_values.append(new_customer_value)
                
                if customer_name not in customer_names.values():
                    customer_name = customer_name.replace('\u00a0', ' ')
                    customer_names[str(customer_number)] = customer_name
                    with open(customer_names_json, 'w', encoding='utf-8') as f:
                        json.dump(customer_names, f, indent=4)
                    print(f"\nAdded '{customer_name}' for customer number {customer_number} in customer_names.json\n")

                    po_expire[customer_name] = 7
                    with open(po_expire_json, 'w') as f:
                        json.dump(po_expire, f, indent=4)
                    print(f"\nUpdated po_expire.json with default value for '{customer_name}'\n")

            fat_random_minute = np.random.randint(1, 10)
            start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')
            finish_time = (pd.to_datetime(start_time) + pd.Timedelta(minutes=fat_random_minute)).strftime('%Y-%m-%d %H:%M:%S')

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

        if new_customer_query_values:
            new_customer_query = (
                "INSERT INTO customer (customer_id, customer_name, customer_address, regency, province) VALUES {}".format(
                    ','.join(new_customer_query_values)
                )
            )
            full_query += new_customer_query + '\n\n'
        
        if preorder_query_values:
            total_batches = (len(preorder_query_values) + batch - 1) // batch
            for i in range(0, len(preorder_query_values), batch):
                batch_value = preorder_query_values[i:i+batch]
                preorder_query = (
                    "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES {}".format(
                        ','.join(batch_value)
                    )
                )
                full_query += preorder_query + '\n\n'
                print(f"\nQuery {i//batch + 1} of {total_batches} generated successfully\n")
    else:
        print('\nInvalid dataset\n')
    
    return full_query

def insert(query):
    connection = pymysql.connect(host='192.168.1.219', user='root', password='sarwa', db='osc_clone')
    try:
        query_lines = query.splitlines()
        with connection.cursor() as cursor:
            for i, line in tqdm(enumerate(query_lines), total=len(query_lines), desc="Executing queries"):
                if line.strip():  # Check if the line is not empty
                    try:
                        cursor.execute(line)
                        print(f"\nQuery {i+1} executed successfully\n")
                    except Exception as e:
                        print(f"\nError executing Query {i+1}: {e}\n")  # Print detailed error
        connection.commit()
        print("\nAll queries executed successfully\n")
    except Exception as e:
        print("\nERROR IN DATABASE OPERATION: {}\n".format(e))
    finally:
        connection.close()



if __name__ == "__main__":
    print('\n===============STARTING===============\n')
    smr_path = env.insert['smr']
    panel_path = env.insert['panel']
    customer_names_json = env.insert['customer_names']
    start_code_smr = env.insert['start_code_smr']
    start_code_panel = env.insert['start_code_panel']
    po_expire_json = env.insert['po_expire']


    print('\n===============Loading customer names files===============\n')
    with open(customer_names_json, 'r', encoding='utf-8') as f:
        customer_names = json.load(f)

    print('\n===============Loading start code files===============\n')
    with open(po_expire_json, 'r') as f:
        po_expire = json.load(f)

    print('\n===============Starting loop===============\n')
    try:
        while True:
            smr_exists = os.path.exists(smr_path)
            panel_exists = os.path.exists(panel_path)

            if smr_exists:
                print(f'\n{smr_path} file found, cleaning it\n')
                cleaned = clean(smr_path)
                print('\nProcessing cleaned file\n')
                processed = process(cleaned)

                if not processed.empty:
                    print('\nGenerating query\n')
                    query = generate_query(processed, customer_names, po_expire)
                    if query is not None:
                        print('\nInserting query\n')
                        insert(query)
                
                print('\nMoving SMR file\n')
                shutil.move(smr_path, smr_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            if panel_exists:
                print(f'\n{panel_path} file found, cleaning it\n')
                cleaned = clean(panel_path)
                print('\nProcessing cleaned file\n')
                processed = process(cleaned)

                if not processed.empty:
                    print('\nGenerating query\n')
                    query = generate_query(processed, customer_names, po_expire)
                    if query is not None:
                        print('\nInserting query\n')
                        insert(query)

                print('\nMoving Panel file\n')
                shutil.move(panel_path, panel_path.replace('PANEL&SMR', 'PANEL&SMR/ORIGINAL'))

            if not smr_exists and not panel_exists:
                print('No files found. Waiting...')
                now = datetime.now()
                current = now.strftime("%H:%M:%S")
                print("\nCurrent Time =", current)
                print('To exit, press CTRL+C')
                time.sleep(3)

    except KeyboardInterrupt:
        print('\nKEYBOARD INTERRUPT DETECTED. EXITING...')