import pandas as pd
import os

def clean():
    data = pd.read_csv('SO.csv', sep=';', skiprows=4)
    data.rename(columns={'Tgl Pesan': 'order_date','Unnamed: 2': 'no_SO','Unnamed: 4': 'customer_name', 'Unnamed: 6': 'no_PO'}, inplace=True)
    selected = data[['order_date', 'no_PO', 'no_SO', 'customer_name']]
    cleaned = selected[selected['no_SO'].notna()]
    #delete SO.csv
    os.remove('SO.csv')
    cleaned.to_csv('SO.csv', index=False)
    print('SO.csv has been cleaned!')

clean()