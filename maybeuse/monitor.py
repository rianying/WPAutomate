import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import signal
import sys
import json

def handle_exit(sig, frame):
    print("\nProgram exited")
    sys.exit(0)

# Load sensitive credentials from twilio.json
with open('twilio.json') as json_file:
    credentials = json.load(json_file)

twilio_account_sid = credentials['twilio_account_sid']
twilio_auth_token = credentials['twilio_auth_token']
twilio_phone_number = credentials['twilio_phone_number']
to_phone_number = credentials['to_phone_number']
spreadsheet_url = credentials['spreadsheet_url']

# Load Google Sheets API credentials from credentials.json
credentials_file = 'credentials.json'
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
client = gspread.authorize(credentials)

# Open the spreadsheet using its URL
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.worksheet('Active Logbook')

# Initialize the last checked row
last_row = 1

# Set up the Twilio client
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Set up the Ctrl+C signal handler
signal.signal(signal.SIGINT, handle_exit)

while True:
    try:
        # Get the current last row value
        current_last_row = len(sheet.get_all_values())

        # Check for new entries
        if current_last_row > last_row:
            new_entry_segment = None  # Initialize with None
            new_entry_time = None
            new_entry_so = sheet.cell(current_last_row, 3).value  # Assuming 'NO SO' is in the third column

            for row_num in range(current_last_row, 0, -1):
                segment = sheet.cell(row_num, 2).value
                if segment:  # If segment is not empty, update new_entry_segment and break
                    new_entry_segment = segment
                    break
            
            for row_num in range(current_last_row, 0, -1):
                ot = sheet.cell(row_num, 4).value
                if ot:  # If segment is not empty, update new_entry_segment and break
                    new_entry_time = ot
                    break

            print(f"\n\nNew entry added at Row: {current_last_row}, Segment: {new_entry_segment} - {new_entry_so}. Order time: {new_entry_time}\n\n")

            # Send a WhatsApp message using Twilio
            # message = twilio_client.messages.create(
            #     from_=twilio_phone_number,
            #     body=f"New entry added: {new_entry_segment} - {new_entry_so}. Order time: {new_entry_time} at Row: {current_last_row}.\n\nCheck it now: {spreadsheet_url}",
            #     to=to_phone_number
            # )

            last_row = current_last_row
        else:
            print('No new entry found. Last checked row: {} with the value of {} - {}. Order time: {}'.format(last_row, new_entry_segment, new_entry_so, new_entry_time))

        time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        handle_exit(None, None)  # Handle Ctrl+C
