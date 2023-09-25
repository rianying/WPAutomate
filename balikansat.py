import pandas as pd
from datetime import datetime
import subprocess
import os

transformed_data = []

# Get today's date in the desired format
today_date = datetime.now().strftime('%Y-%m-%d')

# Create an empty list to store the transformed data
def process_data(df):
    transformed_data = []

    # Get today's date in the desired format
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Create an empty DataFrame 'balikanSAT'
    balikanSAT = pd.DataFrame(columns=['Tanggal', 'Nomor Dokumen', 'Nama Customer', 'Jenis dokumen'])

    # Continue asking for user input until 'done' is entered
    while True:
        user_input = input("4 Digit terakhir Nomor SO (kosongkan apabila selesai, koma atas apabila ada PO): ")
        if len(user_input) >= 1 and len(user_input) < 4:
            print("Nomor SO harus 4 digit.")
            continue
        # Check if the user wants to exit
        if user_input.lower() == '':
            os.remove('/Users/rian/Documents/GitHub/WPAutomate/sat.csv')
            print('File sat.csv deleted.')
            break

        # Determine if user input has ' at the end
        has_suffix = user_input.endswith("'")

        # Remove ' from user input if present
        last_4_digits = user_input.rstrip("'")

        # Find the relevant row in the CSV based on the user input
        matching_row = df[df['no_SO'].str.endswith(last_4_digits)]

        if not matching_row.empty:
            # Fill the 'transformed_data' list for no_SJ
            no_sj = matching_row['no_SO'].values[0]
            no_SO = no_sj.replace("SJ", "SO")
            customer_name = matching_row['customer_name'].values[0]
            transformed_data.append([today_date, no_sj, customer_name, 'SJ', 1])

            if has_suffix:
                # User input with ' at the end, add a PO row
                no_po = matching_row['no_PO'].values[0]
                transformed_data.append([today_date, no_po, customer_name, 'PO', 1])

            # Fill the 'transformed_data' list for no_PO
            transformed_data.append([today_date, None, customer_name, 'BPB', 1])
        else:
            print(f"Tidak ada nomor SO: '{user_input}'.")

    # Create a new DataFrame from the transformed data
    transformed_df = pd.DataFrame(transformed_data, columns=['Tanggal', 'Nomor Dokumen', 'Nama Customer', 'Jenis dokumen', 'Jumlah Lembar'])

    # Convert the DataFrame to tab-separated format
    clipboard_content = transformed_df.to_csv(index=False, sep='\t')

    # Copy the content to clipboard using subprocess
    subprocess.run(['pbcopy'], input=clipboard_content.encode('utf-8'))

    print("\n\nDataFrame content copied to clipboard.")

if __name__ == "__main__":
    sat = '/Users/rian/Documents/GitHub/WPAutomate/sat.csv'

    if os.path.exists(sat):
        try:
            df = pd.read_csv(sat, sep=',')
            process_data(df)
        except Exception as e:
            print(e)
    else:
        print(f"\n\nsat.csv does not exist.")