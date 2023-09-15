import pandas as pd
from datetime import datetime
import subprocess
import os


# Create an empty list to store the transformed data
transformed_data = []

# Get today's date in the desired format
today_date = datetime.now().strftime('%Y-%m-%d')

# Iterate through each row in the original DataFrame
def process_data(df):
    for index, row in df.iterrows():
        no_sj = row['No_SJ']
        customer_name = row['customer_name']
        
        # Define document types and their corresponding page counts
        document_types = ['INV', 'SJ']
        page_counts = [3, 2]  # Swapped page counts
        
        # Create new rows for each document type and page count combination
        for doc_type, pages in zip(document_types, page_counts):
            if doc_type == 'SJ':
                transformed_data.append([today_date, no_sj, customer_name, doc_type, pages])
            else:
                transformed_data.append([today_date, no_sj.replace('SJ', 'INV'), customer_name, doc_type, pages])

    # Create a new DataFrame from the transformed data
    transformed_df = pd.DataFrame(transformed_data, columns=['Tanggal', 'No Dokumen', 'Nama Customer', 'Jenis Dokumen', 'Lembar Dokumen'])

    # Convert the DataFrame to tab-separated format
    clipboard_content = transformed_df.to_csv(index=False, sep='\t')

    # Copy the content to clipboard using subprocess
    subprocess.run(['pbcopy'], input=clipboard_content.encode('utf-8'))
    os.remove('/Users/rian/Documents/GitHub/WPAutomate/balikansf.csv')

    print("\n\nDataFrame content copied to clipboard.")
    print("balikansf.csv removed.")

if __name__ == "__main__":
    balikansf = '/Users/rian/Documents/GitHub/WPAutomate/balikansf.csv'

    if os.path.exists(balikansf):
        try:
            df = pd.read_csv(balikansf, sep=',')
            process_data(df)
        except Exception as e:
            print(e)
    else:
        print(f"\n\n{balikansf} does not exist.")