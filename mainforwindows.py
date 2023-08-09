import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import random
import os

# Helper function to calculate business days
def add_business_days(from_date, add_days):
    return np.busday_offset(from_date, add_days, roll='forward')

def generate_queries(filepath):
    df = pd.read_csv(filepath)  # Updated this line to read from CSV

    value_clauses_preorder = []
    value_clauses_order_checking_start = []
    value_clauses_order_checking_finish = []

    for _, row in df.iterrows():
        no_PO = row['no_PO'] if not pd.isna(row['no_PO']) else ""
        no_SO = row['no_SO'] if not pd.isna(row['no_SO']) else ""
        customer_name = row['customer_name'] if not pd.isna(row['customer_name']) else ""
        order_time = row['order_time'] if not pd.isna(row['order_time']) else ""

        if "CRB" in no_SO or "BDG" in no_SO:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 7)
        else:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 4)

        value_clause_preorder = f'("{no_PO}", "{no_SO}", "{customer_name}", \'{order_time}\', \'{po_expired}\')'
        value_clauses_preorder.append(value_clause_preorder)

        fat_random_minutes = random.randint(1, 10)
        fat_start_time = (pd.to_datetime(order_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        value_clause_order_checking_start = f'("{no_SO}", \'{fat_start_time}\', "{customer_name}")'
        value_clauses_order_checking_start.append(value_clause_order_checking_start)

        no_SJ = no_SO.replace("SO", "SJ")
        fat_random_minutes = random.randint(1, 10)
        fat_checking_finish = (pd.to_datetime(fat_start_time) + pd.Timedelta(minutes=fat_random_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        value_clause_order_checking_finish = f'("{no_SO}", "{no_SJ}", \'{fat_checking_finish}\', "{customer_name}", "Process")'
        value_clauses_order_checking_finish.append(value_clause_order_checking_finish)

    values_str_preorder = ',\n'.join(value_clauses_preorder)
    values_str_order_checking_start = ',\n'.join(value_clauses_order_checking_start)
    values_str_order_checking_finish = ',\n'.join(value_clauses_order_checking_finish)

    query_preorder = f'INSERT INTO preorder(no_PO, no_SO, customer_name, order_time, po_expired) VALUES {values_str_preorder};'
    query_order_checking_start = f'INSERT INTO order_checking_start(no_SO, start_check, customer_name) VALUES {values_str_order_checking_start};'
    query_order_checking_finish = f'INSERT INTO order_checking_finish(no_SO, no_SJ, FAT_checking_finish, customer, status_FAT) VALUES {values_str_order_checking_finish};'

    return query_preorder, query_order_checking_start, query_order_checking_finish

def pick_file():
    # Updated the file type to CSV
    filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    file_path.set(filepath)
    lbl_filepath.config(text=filepath)

def execute():
    filepath = file_path.get()
    if not filepath:
        messagebox.showerror("Error", "Please select a CSV file first!")
        return

    try:
        queries_preorder, queries_order_checking_start, queries_order_checking_finish = generate_queries(filepath)
        queries_combined = f"{queries_preorder}\n\n{queries_order_checking_start}\n\n{queries_order_checking_finish}"
        app.clipboard_clear()
        app.clipboard_append(queries_combined)
        app.update()  # To ensure the clipboard content is updated
        messagebox.showinfo("Notification", "Generated SQL Queries have been copied to the clipboard!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    if os.path.exists(filepath):
        os.remove(filepath)
        messagebox.showinfo("Notification", "The file has been deleted!")
    else:
        messagebox.showerror("Error", "The file does not exist!")

app = tk.Tk()
app.title("SQL Query Generator")

file_path = tk.StringVar()

frame = tk.Frame(app)
frame.pack(pady=20)

btn_pick_file = tk.Button(frame, text="Pick a CSV file", command=pick_file)  # Updated the button text
btn_pick_file.grid(row=0, column=0, padx=10)

btn_execute = tk.Button(frame, text="Generate PO Query", command=execute)
btn_execute.grid(row=0, column=1, padx=10)

lbl_filepath = tk.Label(frame, text="")
lbl_filepath.grid(row=1, column=0, columnspan=2, pady=10)

app.mainloop()
