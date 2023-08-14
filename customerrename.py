import pandas as pd
import json

# Read the CSV files
no_so_customer_df = pd.read_csv('wordpress.csv')
so_cleaned_df = pd.read_csv('accurate.csv')

# Merge the dataframes based on 'no_SO'
merged_df = pd.merge(so_cleaned_df, no_so_customer_df, on='no_SO', how='left')

# Replace customer_name with the matching value from no_SOcustomer.csv
merged_df['customer_name'] = merged_df['customer_name_y'].fillna(merged_df['customer_name_x'])

# Drop unnecessary columns and retain distinct customer_numbers
distinct_customers_df = merged_df.drop(columns=['customer_name_x', 'customer_name_y']).drop_duplicates(subset=['customer_number'])

# Create a dictionary with customer_number as key and customer_name as value
customer_data = dict(zip(distinct_customers_df['customer_number'], distinct_customers_df['customer_name']))

# Save the dictionary to a JSON file
with open('customer_names.json', 'w') as json_file:
    json.dump(customer_data, json_file, indent=4)

print("Distinct customer numbers and names saved to 'customer_names.json'")
