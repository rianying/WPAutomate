customer = {
    "MT-KFAP50": "KF DANAU TAMBLINGAN 1",
    "MT-KFAP49": "KF KARANGASEM",
    "MT-KFAP47": "KF BUANA RAYA",
    "MT-KFAP46": "APT KF IMAM BONJOL 2",
    "MT-KFAP45": "APT KF 07 NANGKA UTARA",
}

# for each customer, generate a query to insert into table customer(code_market, customer_name, expedition_name) values ('MT', customer_name, 'PT. SARWA MANGGALLA RAYA)
# make it one query
# Path: newcustomer.py
query = "insert into customer(code_market, customer_name, expedition_name) values "
for key, value in customer.items():
    query += "('MT', '" + value + "', 'PT. SARWA MANGGALLA RAYA'), "
query = query[:-2]
print(query)

