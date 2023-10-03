import pandas as pd
import os

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
        "Sep": "Sep", "Okt": "Oct", "Nov": "Nov", "Des": "Dec"
    }
    for ind, eng in month_translations.items():
        df["order_date"] = df["order_date"].str.replace(ind, eng)
    
    time_input = input("Please enter the time (format HH:MM:SS): ")
    df["order_date"] = pd.to_datetime(df["order_date"], format='%d %b %Y') 
    df["order_date"] = df["order_date"].dt.strftime('%Y-%m-%d') + ' ' + time_input
    
    segment = input("Please enter the segment: ").upper()
    startcode = input("Please enter the start code: ")
    start_range = f"SO/SMR/{segment}/23/X/{startcode}".upper()
    if start_range:
        finish_range = start_range.replace(start_range[-4:], "9999")
        result_df = df[df['no_SO'].between(start_range, finish_range)]
    else:
        result_df = df
    
    output_file = '/Users/rian/Documents/GitHub/WPAutomate/PO_fetched.csv'
    result_df.to_csv(output_file, index=False)
    print(f'{output_file} has been generated.')

input_file = r'/Volumes/PUBLIC/SC - RIAN (Intern)/SO.csv'
cleaned_file = '/Users/rian/Documents/GitHub/WPAutomate/SO_cleaned.csv'

if os.path.exists(input_file):
    try:
        clean(input_file, cleaned_file)
        cleaned_data = pd.read_csv(cleaned_file)
        process_csv(cleaned_data)
        os.remove(cleaned_file)
        print(f'{cleaned_file} has been removed.')
    except Exception as e:
        print(f'\n\nError: {e}')
else:
    print(f'\n\nSO File not found. Please check if the file exists in {input_file}')
