import pymysql
import pandas as pd

# Load the CSV file
preorder = 'env/preorderlatest.csv'
validasi = 'env/validasilatest.csv'


# Database connection parameters
host = '192.168.1.219'
user = 'root'
password = 'sarwa'
database = 'osc_clone'

# Connect to the database
connection = pymysql.connect(host=host, user=user, password=password, database=database)
def insertproduct(df_path):
    df = pd.read_csv(df_path)

    # replace nan/null values with ''
    df = df.fillna('')
    try:
        with connection.cursor() as cursor:
            # SQL query to insert data
            sql = "INSERT INTO product (product_name, lenght, width, height, weight, content, retail_weight) VALUES (%s, %s, %s, %s, %s, %s, %s)"

            # Iterate over the rows of the dataframe
            for index, row in df.iterrows():
                cursor.execute(sql, (row['product_name'], row['length'], row['width'], row['height'], row['weight'], row['content'], row['retail_weight']))

            # Commit the changes
            connection.commit()

    finally:
        connection.close()

def insertpreorder(df_path):
    df = pd.read_csv(df_path)

    # replace nan/null values with ''
    df = df.fillna('')
    try:
        with connection.cursor() as cursor:
            # SQL query to insert data
            sql = "INSERT INTO preorder (inv_number, po_number, channel, customer_id, customer_name, order_time, po_expired, term_payment, sales_name, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            # Iterate over the rows of the dataframe
            for index, row in df.iterrows():
                count = 1
                cursor.execute(
                    sql,
                    (
                        row['no_SO'],
                        row['no_PO'],
                        'panel' if row['no_SO'].startswith('INV') else 'non-panel',
                        count,
                        row['customer_name'],
                        row['order_time'],
                        row['po_expired'],
                        'COD',
                        '',
                        ''
                    )
                )
                count += 1
                print('Inserted row ' + str(index) + ' of ' + str(len(df)) + '\n')
            # Commit the changes
            connection.commit()

    finally:
        connection.close()

def insertvalidasi(df_path):
    df = pd.read_csv(df_path)

    # replace nan/null values with ''
    df = df.dropna()
    try:
        with connection.cursor() as cursor:
            # SQL query to insert data
            sql = "INSERT INTO validation (inv_number, start_check, finish_check, fat_status, note) VALUES (%s, %s, %s, %s, %s)"

            # Iterate over the rows of the dataframe
            for index, row in df.iterrows():
                count = 1
                cursor.execute(
                    sql,
                    (
                        row['No_SO'],
                        row['start_check'],
                        row['FAT_checking_finish'],
                        row['status_FAT'],
                        ''
                    )
                )
                count += 1
                print('Inserted row ' + str(index) + ' of ' + str(len(df)) + '\n')
            # Commit the changes
            connection.commit()

    finally:
        connection.close()

insertvalidasi(validasi)
