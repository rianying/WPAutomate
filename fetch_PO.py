import pandas as pd
import os

def clean():
    so = r'/Volumes/PUBLIC/SC - Samuel (Intern)/SO.csv'
    data = pd.read_csv(so, sep=';', skiprows=4)
    data.rename(columns={'Tgl Pesan': 'order_date','Unnamed: 2': 'no_SO','Unnamed: 4': 'customer_name', 'Unnamed: 6': 'no_PO'}, inplace=True)
    selected = data[['order_date', 'no_PO', 'no_SO', 'customer_name']]
    cleaned = selected[selected['no_SO'].notna()]
    cleaned.to_csv('SO_cleaned.csv', index=False)
    print('SO.csv has been cleaned!')

clean()

def process_csv(data):
    df = data.copy()
    df = df[["order_date", "no_PO", "no_SO", "customer_name"]]

    month_translations = {
        "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
        "Mei": "May", "Jun": "Jun", "Jul": "Jul", "Agu": "Aug",
        "Sep": "Sep", "Okt": "Oct", "Nov": "Nov", "Des": "Dec"
    }
    for non_eng, eng in month_translations.items():
        df["order_date"] = df["order_date"].str.replace(non_eng, eng)
    
    time_input = input("Please enter the time (format HH:MM:SS): ")
    df["order_date"] = pd.to_datetime(df["order_date"], format='%d %b %Y') 
    df["order_date"] = df["order_date"].dt.strftime('%Y-%m-%d') + ' ' + time_input
    
    start_range = input("Please enter the start of the NO. SO range: ")
    finish_range = input("Please enter the finish of the NO. SO range: ")
    
    result_df = df[df['no_SO'].between(start_range, finish_range)]
    
    result_df.to_csv('PO_fetched.csv', index=False)
    os.remove('SO_cleaned.csv')
    print('PO_fetched.csv has been generated.')

cleaned_data = pd.read_csv('SO_cleaned.csv')
process_csv(cleaned_data)
