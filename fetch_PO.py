import pandas as pd
import os
import json

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
            start_range = f"SO/SMR/{segment}/23/X/{startcode}".upper()
            finish_range = start_range.replace(start_range[-4:], "9999")
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
