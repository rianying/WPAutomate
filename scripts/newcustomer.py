customer = {
    "MT-KFBH10": "KF PEL 029 RSUD PANGK",
    "MT-KFBH09": "KE 0471 CELENTANG",
    "MT-KFBH05": "KF 0220",
    "MT-KFBH04": "KF 0209 ROSARUM",
    "MT-KFBH03": "KF 0118",
    "MT-KFBH02": "KF 0080",
    "MT-KFBH01": "KF 0072",
    "MT-KFBL01": "KF PEL 001 RSUP DR C"
}

# for each customer, generate a query to insert into table customer(code_market, customer_name, expedition_name) values ('MT', customer_name, 'PT. SARWA MANGGALLA RAYA)
# make it one query
# Path: newcustomer.py
query = "insert into customer(code_market, customer_name, expedition_name) values "
for key, value in customer.items():
    query += "('MT', '" + value + "', 'PT. SARWA MANGGALLA RAYA'), "
query = query[:-2]
print(query)

