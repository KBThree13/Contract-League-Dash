from __future__ import print_function
import dash
from dash.dependencies import Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import pandas as pd

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pyasn1.type.univ import Null
from dotenv import load_dotenv

import os
import time
import json

load_dotenv()

import json

with open('managers.json') as file:
    managers = json.load(file)

###############################
#INITIALIZE GOOGLE SHEETS API
###############################

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'
#Contract League Spreadsheet
SPREADSHEET_ID = os.getenv('sheet_Id')
RANGE_NAME = '!C17:C136'
CLOCK_RANGE = 'League View!C11'
BID_RANGE = 'Bidding Backend!B7:H7'
BID_RANGE_TEST = 'Bidding Backend!B9:H9'
AUCTION_ARCHIVE_RANGE = 'Auction Archive!J11:P11'
NEXT_PLAYER_RANGE = 'League View!C6'
AUCTION_BLOCK_RANGE = 'League View!C9'


MANAGER_NAMES = managers['managers']

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

####################
#INITIALIZE DASH APP
####################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(id='app-title', children="Contract League Draft Control"),
    dcc.Input(id='timer-length-input', type='number', placeholder=30),
    html.Button(id='timer-start-button', children="Start Timer"),
    html.Button(id='draft-player-button', children="Draft Player"),
    html.H2(id='status-messages', children='Scrip Status Messages:'),
    html.Div(id='sheet-clear-status'),
    html.Div(id='clock-status'),
    html.Div(id='drafted-player-status'),
    html.Button(id='clear-data-button', children="Clear Bids")
])

#Button Click Callback: Clear Bid Data
@app.callback(
    Output(component_id='sheet-clear-status', component_property='children'),
    Input(component_id='clear-data-button', component_property='n_clicks'),
)
def update_output(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        response = clearSheet()
        return "{} - Cleared Sheets!".format(response["clearedRange"])

#Button Click Callback: Start Timer
@app.callback(
    Output(component_id='clock-status', component_property='children'),
    Input(component_id='timer-start-button', component_property='n_clicks'),
    Input('timer-length-input', "value")
)
def clock_update(n_clicks, timerLength):
    if n_clicks is None:
        raise PreventUpdate
    else:
        response = startTimer(timerLength)
        return "Timer Complete!"

#Button Click Callback: Draft Player
@app.callback(
    Output(component_id='drafted-player-status', component_property='children'),
    Input(component_id='draft-player-button', component_property='n_clicks'),
)
def draft_update(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        response = draftCurrentPlayer()
        return response

def clearSheet():
    """
    Clears the bid information on each tab of the draft sheet
    """
    for name in MANAGER_NAMES:
        EDIT_RANGE = name + RANGE_NAME
        response1 = sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=EDIT_RANGE).execute()
    
    playerRange = 'League View!C9'
    response2 = sheet.values().clear(spreadsheetId = SPREADSHEET_ID, range=playerRange).execute()

    return response1

def startTimer(t):

    response1 = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=NEXT_PLAYER_RANGE).execute()

    player = response1.get("values", [])
    
    value_range_body = {
                "range": AUCTION_BLOCK_RANGE,
                "values": [
                    player[0]
                    ]
                }

    response = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=AUCTION_BLOCK_RANGE, valueInputOption='USER_ENTERED', body=value_range_body).execute()

    clock = ['']

    while t:
        mins, sec = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, sec)
        clock[0] = timeformat
        value_input_option = 'USER_ENTERED'
        value_range_body = {
            "range": CLOCK_RANGE,
            "values": [
                clock
                ]

            }
            
        t-=1
        request = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=CLOCK_RANGE, valueInputOption=value_input_option, body=value_range_body).execute()
        time.sleep(1)
    
    clock[0] = "Final Bids!"
    value_range_body = {
            "range": CLOCK_RANGE,
            "values": [
                clock
                ]

            }
    request = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=CLOCK_RANGE, valueInputOption=value_input_option, body=value_range_body).execute()

    return response

def draftCurrentPlayer():
    #get values from the bid information sheet
    read_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=BID_RANGE).execute()
    values = read_result.get('values', [])


    #Update values in the auction archive
    if not values:
        return "No Values Returned"
    else:
        cellRow = int(values[0][0]) + 2
        newRange = "Auction Archive!B{}:H{}".format(cellRow, cellRow)
        value_input_option = 'USER_ENTERED'
        value_range_body = {
            "range": newRange,
            "majorDimension": "ROWS",
            "values":[
                values[0]
            ]
        }

        #write to the Auction Archive
        write_result = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=newRange, valueInputOption=value_input_option, body=value_range_body).execute()
        return "Player: {} was saved to the auction archive!".format(values[0][1])

if __name__ == '__main__':
    app.run_server(debug=True)