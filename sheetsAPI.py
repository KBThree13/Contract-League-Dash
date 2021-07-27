from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import schedule
import time

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'
#Contract League Spreadsheet
SPREADSHEET_ID = '14bwtjF6HcA0htqClbFukR2Px29LAXAeIEW2wZHrlPU4'
RANGE_NAME = 'Auction Archive!J11:P11'

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    #result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
    #                            range=RANGE_NAME).execute()
    result = sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()

    value_input_option = 'USER_ENTERED'
    value_range_body = {
        "range": RANGE_NAME,
        "values": [
            ["9", "Josh Allen", "Is", "This", "Working?"]
        ]

        }

    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, valueInputOption=value_input_option, body=value_range_body)
    response = request.execute()






    


    #values = result.get('values', [])

    #if not values:
    #    print('No data found.')
    #else:
        #print('Sheet Data:')
        #for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
         #   print('%s' % row)

if __name__ == '__main__':
    main()