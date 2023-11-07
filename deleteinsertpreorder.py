import csv

# Initialize an empty list to store the no_SO values
no_SO_values = []

# Replace 'yourfile.csv' with the path to your actual CSV file
with open('/Users/rian/Downloads/CheckPO.csv', newline='') as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        # Assuming empty customer_name cells are represented by empty strings
        if row['no_SO'].strip():  # This will ensure that only non-empty no_SO values are added
            no_SO_values.append(row['no_SO'].strip())

# Generate the SQL query using the list of no_SO values
sql_query = "DELETE FROM preorder WHERE no_SO IN ({});".format(
    ', '.join("'{}'".format(no_SO) for no_SO in no_SO_values)
)

print(sql_query)

