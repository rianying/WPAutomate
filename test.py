import pandas as pd

def process_csv(file_path):
    # 1. Read the csv file
    df = pd.read_csv(file_path, sep=';')
    
    # 3. Take only TGL SO, NO. SO, and NAMA PELANGGAN
    df = df[["TGL SO", "NO. SO", "NAMA PELANGGAN"]]
    
    # 2. Remove duplicates based on the specific columns
    df = df.drop_duplicates()
    
    # Translate month abbreviations to English
    month_translations = {
        "Jan": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
        "Mei": "May", "Jun": "Jun", "Jul": "Jul", "Agu": "Aug",
        "Sep": "Sep", "Okt": "Oct", "Nov": "Nov", "Des": "Dec"
    }
    for non_eng, eng in month_translations.items():
        df["TGL SO"] = df["TGL SO"].str.replace(non_eng, eng)
    
    # 4. Change TGL SO to date time and asks user input for the time.
    time_input = input("Please enter the time (format HH:MM:SS): ")
    df["TGL SO"] = pd.to_datetime(df["TGL SO"], format='%d %b %Y') 
    df["TGL SO"] = df["TGL SO"].dt.strftime('%Y-%m-%d') + ' ' + time_input
    
    # 5. Asks user input for NO. SO range start
    start_range = input("Please enter the start of the NO. SO range: ")
    
    # 6. Asks user input for NO. SO range finish
    finish_range = input("Please enter the finish of the NO. SO range: ")
    
    # Filter the dataframe based on the NO. SO range provided by the user
    result_df = df[df['NO. SO'].between(start_range, finish_range)]
    
    # 7. Print the result
    print(result_df)

# Call the function with the path to your CSV file
process_csv("so.csv")
