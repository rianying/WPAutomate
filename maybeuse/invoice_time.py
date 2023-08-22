import random
from datetime import datetime, timedelta
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import os

# Function to pick CSV file using file dialog
def pick_csv():
    csv_file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if csv_file_path:
        selected_file_label.config(text=f"Selected CSV File: {csv_file_path}")
        generate_button.config(state=tk.NORMAL)
        generate_button.focus_set()  # Set focus on the Generate button

# Function to generate a single SQL UPDATE query and copy to clipboard
def generate_sql():
    csv_file_path = selected_file_label.cget("text").replace("Selected CSV File: ", "")
    data = pd.read_csv(csv_file_path)
    data['SJ_time'] = pd.to_datetime(data['SJ_time'])
    data['computed_invoice_time'] = data['SJ_time'].apply(lambda x: x + timedelta(seconds=random.randint(3600, 3*3600)))

    sql_query = "UPDATE outbound SET invoice_time = CASE\n"
    for _, row in data.iterrows():
        sql_query += f"    WHEN outbound_id = {row['outbound_id']} THEN '{row['computed_invoice_time']}'\n"
    sql_query += "    ELSE invoice_time\nEND;"
    
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, sql_query)
    
    root.clipboard_clear()
    root.clipboard_append(sql_query)
    root.update()
    os.remove(csv_file_path)
    messagebox.showinfo("Success", "Generated SQL query copied to clipboard! and 'outbound_invoice_check.csv' is deleted.")

# Create the main window
root = tk.Tk()
root.title("SQL Query Generator")

# Create a button to pick the CSV file
pick_csv_button = tk.Button(root, text="Pick CSV File", command=pick_csv)
pick_csv_button.pack(padx=10, pady=5)

# Label to display the selected CSV file
selected_file_label = tk.Label(root, text="Selected CSV File: None")
selected_file_label.pack(padx=10, pady=5)

# Create a text widget to display the SQL query
output_text = tk.Text(root, wrap=tk.WORD, width=50, height=20)
output_text.pack(padx=10, pady=10)

# Create a button to generate the SQL query and copy to clipboard
generate_button = tk.Button(root, text="Generate SQL Query", command=generate_sql, state=tk.DISABLED)
generate_button.pack(padx=10, pady=5)

# Start the GUI event loop
root.mainloop()
