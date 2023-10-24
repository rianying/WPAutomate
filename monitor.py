import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import signal
import sys
import json
from datetime import datetime

def handle_exit(sig, frame):
    print("\nProgram exited")
    sys.exit(0)

# Load sensitive credentials from twilio.json
with open('twillio.json') as json_file:
    credentials = json.load(json_file)

twilio_account_sid = credentials['twilio_account_sid']
twilio_auth_token = credentials['twilio_auth_token']
twilio_phone_number = credentials['twilio_phone_number']
to_phone_number = credentials['to_phone_number']
spreadsheet_url = credentials['url']

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

sleep_interval = 3  # Initial sleep interval is 5 minutes

while True:
    try:
        # Get the current last row value
        current_last_row = len(sheet.get_all_values())
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Check for new entries
        if current_last_row > last_row:
            new_entry_segment = None
            new_entry_time = None
            new_entry_so = sheet.cell(current_last_row, 3).value  # Assuming 'NO SO' is in the third column

            for row_num in range(current_last_row, 0, -1):
                segment = sheet.cell(row_num, 2).value
                if segment:
                    new_entry_segment = segment
                    break
            
            for row_num in range(current_last_row, 0, -1):
                ot = sheet.cell(row_num, 4).value
                if ot:
                    new_entry_time = ot
                    break

            print(f"\nTime: {current_time}\nNew entry found and added to Row: {current_last_row}, Segment: {new_entry_segment} - {new_entry_so}. Order time: {new_entry_time}\n\n")

            message = twilio_client.messages.create(
                from_=twilio_phone_number,
                body=f"New entry added: {new_entry_segment} - {new_entry_so}. Order time: {new_entry_time} at Row: {current_last_row}.\n\nCheck it now: {spreadsheet_url}",
                to=to_phone_number
            )

            last_row = current_last_row
        else:
            print('\nTime: {}\nNo new entry found. Last checked row: {} with the value of {} - {}. Order time: {}'.format(current_time, last_row, new_entry_segment, new_entry_so, new_entry_time))
        time.sleep(sleep_interval)

    except KeyboardInterrupt:
        handle_exit(None, None)

    except gspread.exceptions.APIError as api_error:
        if 'RATE_LIMIT_EXCEEDED' in str(api_error):
            sleep_interval += 60  # Increment the sleep interval by 1 minute
            print("Read requests per minute exceeded, upping the time distance to {} minutes}".format(sleep_interval))
        else:
            print("An error occurred:", api_error)
