import pandas as pd
from datetime import datetime
import subprocess
import os
import platform
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from env import env

"""
Script ini untuk membalikan idm.csv (balikan idm) menjadi format
yang dapat diimport ke excel
"""

idmcsv = env.balikan_idm_env['idm_csv']

# Create an empty list to store the transformed data
transformed_data = []

# Get today's date in the desired format
today_date = datetime.now().strftime('%Y-%m-%d')

# Create an empty DataFrame 'balikanSAT'
balikanSAT = pd.DataFrame(columns=['Tanggal', 'Nomor Dokumen', 'Nama Customer', 'Jenis dokumen'])

# Continue asking for user input until 'done' is entered
def process_user_input(df):
    transformed_data = []
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    while True:
        user_input = input("4 Digit terakhir Nomor SJ (Kosongkan apabila selesai): ")
        
        if len(user_input) >= 1 and len(user_input) < 4:
            print("Nomor SJ harus 4 digit.")
            continue

        # Check if the user wants to exit
        if user_input.lower() == '':
            os.remove(idmcsv)
            print('File idm.csv deleted.')
            break

        # Determine if user input has ' at the end
        has_suffix = user_input.endswith("'")

        # Remove ' from user input if present
        last_4_digits = user_input.rstrip("'")

        # Find the relevant row in the CSV based on the user input
        matching_row = df[df['no_SJ'].str.endswith(last_4_digits)]

        if not matching_row.empty:
            # Fill the 'transformed_data' list for no_SJ
            no_sj = matching_row['no_SJ'].values[0]
            customer_name = matching_row['customer_name'].values[0]
            transformed_data.append([today_date, no_sj, customer_name, 'SJ', 1])

            no_po = matching_row['no_PO'].values[0]
            transformed_data.append([today_date, no_po, customer_name, 'PO', 2])

            # Fill the 'transformed_data' list for no_PO
            transformed_data.append([today_date, None, customer_name, 'BPB', 1])

            # Fill the 'transformed_data' list for resi_indopaket
            transformed_data.append([today_date, None, customer_name, 'RESI INDOPAKET', 1])
        else:
            print(f"No matching record found for input '{user_input}'.")

    # Create a new DataFrame from the transformed data
    transformed_df = pd.DataFrame(transformed_data, columns=['Tanggal', 'Nomor Dokumen', 'Nama Customer', 'Jenis dokumen', 'Jumlah Lembar'])

    # Convert the DataFrame to tab-separated format
    clipboard_content = transformed_df.to_csv(index=False, sep='\t')

    # Copy the content to clipboard using subprocess
    if platform.system() == 'Darwin':
        subprocess.run(['pbcopy'], input=clipboard_content.encode('utf-8'))
        print("\n\nDataFrame content copied to clipboard.")
    elif platform.system() == 'Windows':
        subprocess.run(['clip'], input=clipboard_content.encode('utf-8'))
        print("\n\nDataFrame content copied to clipboard.")
    else:
        print("Unsupported operating system.")

if __name__ == "__main__":
    idm = idmcsv

    if os.path.exists(idm):
        try:
            df = pd.read_csv(idm, sep=',')
            process_user_input(df)
        except Exception as e:
            print(e)
    else:
        print(f"\n\n{idm} does not exist.")
