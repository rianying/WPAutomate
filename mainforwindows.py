import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

# Helper function to calculate business days
def add_business_days(from_date, add_days):
    return np.busday_offset(from_date, add_days, roll='forward')

def generate_queries(filepath):
    df = pd.read_excel(filepath)
    value_clauses = []  # We will store the individual value clauses here

    for _, row in df.iterrows():
        no_PO = row['No PO'] if not pd.isna(row['No PO']) else ""
        no_SO = row['No SO'] if not pd.isna(row['No SO']) else ""
        customer_name = row['Customer Name'] if not pd.isna(row['Customer Name']) else ""
        order_time = row['Order Time'] if not pd.isna(row['Order Time']) else ""

        if "CRB" in no_SO or "BDG" in no_SO:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 7)
        else:
            po_expired = add_business_days(pd.to_datetime(order_time).date(), 4)

        value_clause = f'("{no_PO}", "{no_SO}", "{customer_name}", \'{order_time}\', \'{po_expired}\')'
        value_clauses.append(value_clause)

    values_str = ',\n'.join(value_clauses)  # Join all value clauses together, separated by commas
    query = f'INSERT INTO preorder(no_PO, no_SO, customer_name, order_time, po_expired) VALUES {values_str};'

    return query


def pick_file():
    filepath = filedialog.askopenfilename()
    file_path.set(filepath)
    lbl_filepath.config(text=filepath)

def execute():
    filepath = file_path.get()
    if not filepath:
        messagebox.showerror("Error", "Please select an Excel file first!")
        return

    try:
        queries = generate_queries(filepath)
        app.clipboard_clear()
        app.clipboard_append(queries)
        app.update()  # To ensure the clipboard content is updated
        messagebox.showinfo("Notification", "Generated SQL Queries have been copied to the clipboard!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

app = tk.Tk()
app.title("SQL Query Generator")

file_path = tk.StringVar()

frame = tk.Frame(app)
frame.pack(pady=20)

btn_pick_file = tk.Button(frame, text="Pick an excel file", command=pick_file)
btn_pick_file.grid(row=0, column=0, padx=10)

btn_execute = tk.Button(frame, text="Generate PO Query", command=execute)
btn_execute.grid(row=0, column=1, padx=10)

lbl_filepath = tk.Label(frame, text="")
lbl_filepath.grid(row=1, column=0, columnspan=2, pady=10)

app.mainloop()

