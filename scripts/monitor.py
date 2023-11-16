import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import signal
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import json
from datetime import datetime
from env import env

"""
Script ini untuk memonitor Logbook Google Sheets
dan menotifikasi via WA apabila ada entry baru
"""

def handle_exit(sig, frame):
    print("\nProgram exited")
    sys.exit(0)

def exponential_backoff(base_interval, max_interval, multiplier):
    """
    Calculate the next backoff interval based on the current interval, a multiplier, and a max cap.
    
    :param base_interval: The starting interval in seconds.
    :param max_interval: The maximum interval to which backoff can increase, to avoid very long waiting.
    :param multiplier: The factor by which the interval increases.
    :return: A new backoff interval which is the minimum of the calculated backoff or the max cap.
    """
    new_interval = base_interval * multiplier
    return min(new_interval, max_interval)

twilio_account_sid = env.twilio_env['twilio_account_sid']
twilio_auth_token = env.twilio_env['twilio_auth_token']
twilio_phone_number = env.twilio_env['twilio_phone_number']
to_phone_number = env.twilio_env['to_phone_number']
spreadsheet_url = env.twilio_env['url']

# Load Google Sheets API credentials from credentials.json
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(env.google_env, scope)
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

base_sleep_interval = 300  # 5 minutes in seconds
current_sleep_interval = base_sleep_interval
max_sleep_interval = 3600  # Cap at 60 minutes
backoff_multiplier = 2

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
        time.sleep(base_sleep_interval)
        current_sleep_interval = base_sleep_interval
    
    except KeyboardInterrupt:
        handle_exit(None, None)
    
    except gspread.exceptions.APIError as api_error:
        if 'RATE_LIMIT_EXCEEDED' in str(api_error):
            current_sleep_interval = exponential_backoff(current_sleep_interval, max_sleep_interval, backoff_multiplier)
            print(f"Time: {datetime.now()}. Error: {api_error}. Sleeping for {current_sleep_interval} seconds.")
        else:
            print("An error occurred:", api_error)
