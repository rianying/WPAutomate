import pandas as pd
from datetime import datetime
import subprocess
import platform
import os
from WPAutomate.env import env

"""
Script ini untuk membalikan sd.csv (balikan sd) menjadi format
yang dapat diimport ke excel
"""

sdcsv = env.balikan_sd['sd_csv']

transformed_data = []

# Get today's date in the desired format
today_date = datetime.now().strftime('%Y-%m-%d')

# Create an empty list to store the transformed data
def process_data(df):
    transformed_data = []

    # Get today's date in the desired format
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Continue asking for user input until 'done' is entered
    while True:
        user_input = input("4 Digit terakhir Nomor SO (kosongkan apabila selesai, koma atas apabila ada PO): ")
        if len(user_input) >= 1 and len(user_input) < 4:
            print("Nomor SO harus 4 digit.")
            continue
        # Check if the user wants to exit
        if user_input.lower() == '':
            os.remove(sdcsv)
            print('File sd.csv deleted.')
            break

        # Determine if user input has ' at the end
        has_suffix = user_input.endswith("'")

        # Remove ' from user input if present
        last_4_digits = user_input.rstrip("'")

        # Find the relevant row in the CSV based on the user input
        matching_row = df[df['No_SJ'].str.endswith(last_4_digits)]

        if not matching_row.empty:
            # Fill the 'transformed_data' list for no_SJ
            no_sj = matching_row['No_SJ'].values[0]
            no_PO = no_sj.replace("SJ", "PO")
            invoice = no_sj.replace("SJ", "INV")
            customer_name = matching_row['customer'].values[0]
            transformed_data.append([today_date, no_sj, customer_name, 'SJ', 1])

            if has_suffix:
                # User input with ' at the end, add a PO row
                no_po = matching_row['no_PO'].values[0]
                transformed_data.append([today_date, no_po, customer_name, 'PO', 1])
        else:
            print(f"Tidak ada nomor SO: '{user_input}'.")

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

    print("\n\nDataFrame content copied to clipboard.")

if __name__ == "__main__":
    sat = sdcsv

    if os.path.exists(sat):
        try:
            df = pd.read_csv(sat, sep=',')
            process_data(df)
        except Exception as e:
            print(e)
    else:
        print(f"\n\nsd.csv does not exist.")