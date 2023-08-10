import pandas as pd

def clean():
    data = pd.read_csv('SO.csv', sep=';', skiprows=4)
    data.rename(columns={'Unnamed: 2': 'no_SO','Unnamed: 4': 'customer_name', 'Unnamed: 6': 'no_PO'}, inplace=True)
    selected = data[['no_PO', 'no_SO', 'customer_name']]
    cleaned = selected[selected['no_SO'].notna()]
    cleaned.to_csv('CheckPO.csv', index=False)

clean()