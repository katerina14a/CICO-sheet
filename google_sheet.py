import datetime
import string
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SPREADSHEET_ID = '12IQrtvg-__WQTPhxP96TLXOI7nxIXF6Kcw_aVSAkjqQ'
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Personal CICO recorder'
CALORIES_IN_COLUMN = 'E'
WEIGHT_COLUMN = 'B'
NEW_TDEE_COLUMN = 'F'
FITBIT_CALORIES_OUT_COLUMN = 'G'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials


def format_to_range(column, row):
    cell = column + row
    cell += ':' + cell
    return cell


def write_to_sheet(calories_in, fitbit_calories_out, weight, new_tdee):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                     'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discovery_url)

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='A:A').execute()
    values = result.get('values', [])

    yesterday = datetime.date.today() - datetime.timedelta(1)
    if not values:
        print 'No data found.'
    else:
        yesterday_row = None
        today_row = None
        for i, row in enumerate(values):
            if len(row) == 0:
                continue
            try:
                column_date = datetime.datetime.strptime(row[0], '%m/%d/%Y').date()
                if column_date == yesterday:
                    yesterday_row = str(i + 1)
                    today_row = str(i + 2)
                    break
            except ValueError as e:
                # don't care if blank, move on to next one if it's a date
                continue
        if yesterday_row is None or today_row is None:
            # todo: if date row doesn't exist, add it
            # todo: copy formulas to new row
            pass

        calories_in_range = format_to_range(CALORIES_IN_COLUMN, yesterday_row)
        fitbit_tdee_range = format_to_range(FITBIT_CALORIES_OUT_COLUMN, yesterday_row)
        weight_range = format_to_range(WEIGHT_COLUMN, today_row)
        new_tdee_range = format_to_range(NEW_TDEE_COLUMN, today_row)

        print calories_in_range, fitbit_tdee_range, weight_range, new_tdee_range

        data = [
            {
                'range': calories_in_range,
                'values': [[calories_in]]
            }, {
                'range': fitbit_tdee_range,
                'values': [[fitbit_calories_out]]
            }, {
                'range': weight_range,
                'values': [[weight]]
            }, {
                'range': new_tdee_range,
                'values': [[new_tdee]]
            }
        ]
        body = {
            'valueInputOption': 'RAW',
            'data': data
        }
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body).execute()

