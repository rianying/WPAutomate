import pandas as pd
from datetime import datetime, timedelta
import math
import subprocess
import os

def generate_single_query(csv_file):
    df = pd.read_csv(csv_file)

    query_values = []

    for index, row in df.iterrows():
        order_time = datetime.strptime(row['order_date'], '%Y-%m-%d %H:%M:%S')
        po_expired = order_time + timedelta(days=3)

        no_PO = '' if isinstance(row['no_PO'], float) and math.isnan(row['no_PO']) else row['no_PO']
        no_SO = '' if isinstance(row['no_SO'], float) and math.isnan(row['no_SO']) else row['no_SO']
        customer_name = '' if isinstance(row['customer_name'], float) and math.isnan(row['customer_name']) else row['customer_name']

        values = (
            "('{}', '{}', '{}', '{}', '{}')".format(
                no_PO, no_SO, customer_name,
                order_time.strftime('%Y-%m-%d %H:%M:%S'),
                po_expired.strftime('%Y-%m-%d %H:%M:%S')
            )
        )
        query_values.append(values)

    insert_query = (
        "INSERT INTO preorder (no_PO, no_SO, customer_name, order_time, po_expired) VALUES\n" +
        ',\n'.join(query_values) +
        ";"
    )

    return insert_query

def copy_to_clipboard(text):
    try:
        subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
        print("Query copied to clipboard.")
    except subprocess.CalledProcessError:
        print("Error copying to clipboard.")
    os.remove(csv_file)
    print("CSV file removed.")

csv_file = 'po_fetched.csv'
query = generate_single_query(csv_file)

copy_to_clipboard(query)